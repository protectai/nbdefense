import hashlib
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

from detect_secrets.core.potential_secret import PotentialSecret
from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.settings import transient_settings

from nbdefense.codebase import Codebase
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import (
    Issue,
    IssueBlock,
    IssueCode,
    Issues,
    LineCellIssue,
    Severity,
)
from nbdefense.notebook import Cell, OutputCellType
from nbdefense.plugins.plugin import Plugin, ScanTarget
from nbdefense.settings import Settings, UnknownSettingsValueError

logger = logging.getLogger(__name__)


class Secret:
    def __init__(self, secret: PotentialSecret, cell: Cell) -> None:
        self.found_secret: PotentialSecret = secret
        self.cell: Cell = cell


class RedactSecretEnum(str, Enum):
    """
    Redact secrets settings
    Possible values are `PARTIAL`, `ALL`, `HASH`

    `PARTIAL` will show only leading and trailing characters.

    `ALL` will shadow the full secret.

    `HASH` will replace the full secret with its hashed value.
    """

    PARTIAL = "partial"
    ALL = "all"
    HASH = "hash"

    def to_json(self) -> str:
        return self.name


class SecretPluginSettings(Settings):
    def __init__(
        self, plugin_class_name: str, is_enabled: bool, settings: Dict[str, Any] = {}
    ) -> None:
        super().__init__(plugin_class_name, is_enabled, settings)

    def detect_secrets_config(self) -> Dict[str, List[Dict[str, str]]]:
        detect_secrets_plugins = self.get("secrets_plugins")

        return {"plugins_used": detect_secrets_plugins}


class SecretsPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def scan_target() -> ScanTarget:
        return ScanTarget.NOTEBOOKS

    @staticmethod
    def name() -> str:
        return "Secrets Plugin"

    @staticmethod
    def get_settings(
        plugin_class_name: str, is_enabled: bool = True, settings: Dict[str, Any] = {}
    ) -> SecretPluginSettings:
        return SecretPluginSettings(plugin_class_name, is_enabled, settings)

    @staticmethod
    def scan(codebase: Codebase, settings: SecretPluginSettings) -> List[NBDefenseError]:  # type: ignore[override]
        if codebase.quiet:
            logger.setLevel(logging.CRITICAL)
        secrets = SecretsCollection()
        notebooks = codebase.notebooks()

        detect_secrets_config = settings.detect_secrets_config()
        if not detect_secrets_config["plugins_used"]:
            logger.warning(f"Skipping secrets scan because no plugins are enabled")
            return [
                NBDefenseError(
                    ErrorType.SCAN,
                    SecretsPlugin.name(),
                    "Secrets scan was skipped because no plugins were enabled.",
                )
            ]

        notebook_scan_errors: List[NBDefenseError] = []

        for notebook in notebooks:
            try:
                notebooks.set_description(f"Scanning notebook: {notebook.path}")  # type: ignore[attr-defined]
                notebook_file = notebook.as_python_file()
                output_file = notebook.get_output_text_file()

                potential_secrets = []

                if not notebook_file:
                    logger.warning(
                        f"Skipping secrets scan for notebook {notebook.path} because it couldn't be converted"
                    )
                    continue

                with transient_settings(detect_secrets_config):
                    secrets.scan_file(str(output_file))
                    secrets.scan_file(str(notebook_file))

                notebook_secrets_path = None
                output_secrets_path = None

                for file in secrets.files:
                    if notebook_file.samefile(file):
                        notebook_secrets_path = file
                    if output_file.samefile(file):
                        output_secrets_path = file

                if notebook_secrets_path is not None:
                    for found_secret in secrets[notebook_secrets_path]:
                        cell = notebook.get_input_file_line_number_to_cell(
                            found_secret.line_number
                        )
                        if cell:
                            potential_secrets.append(Secret(found_secret, cell))

                if output_secrets_path is not None:
                    for found_secret in secrets[output_secrets_path]:
                        cell = notebook.get_output_file_line_number_to_cell(
                            found_secret.line_number
                        )
                        if cell:
                            potential_secrets.append(Secret(found_secret, cell))

                for secret in potential_secrets:
                    SecretsPlugin.add_secret_detected_issue(
                        notebook.issues, secret, notebook.path
                    )
            except Exception as error:
                logger.warning(
                    f"Skipping Secrets scan for notebook {notebook.path} because of the following error: {str(error)}"
                )
                notebook_scan_errors.append(
                    NBDefenseError(
                        ErrorType.SCAN,
                        SecretsPlugin.name(),
                        f"Secrets scan for notebook {notebook.path} was skipped because of the following error: {str(error)}",
                    )
                )

        SecretsPlugin.redact(codebase, settings)

        return notebook_scan_errors

    @staticmethod
    def redact(codebase: Codebase, settings: SecretPluginSettings) -> None:  # type: ignore[override]
        for notebook in codebase.notebooks():
            for issue in notebook.issues.all_issues:
                if issue.code == IssueCode.SECRETS:
                    SecretsPlugin._redact(issue, settings)

    @staticmethod
    def _redact(issue: Issue, settings: SecretPluginSettings) -> None:
        if isinstance(issue, LineCellIssue):
            secret_value = issue.cell.lines[issue.line_index][
                issue.character_start_index : issue.character_end_index
            ]
            redacted_value = "******"
            redact_secret = str(settings.get("redact_secret")).lower()
            if redact_secret == RedactSecretEnum.PARTIAL:
                redacted_value = f"{secret_value[:2]}..{secret_value[-2:]}"
            elif redact_secret == RedactSecretEnum.HASH:
                redacted_value = hashlib.md5(secret_value.encode()).hexdigest()  # nosec
            elif redact_secret == RedactSecretEnum.ALL:
                pass
            else:
                raise UnknownSettingsValueError("redact_secret", redact_secret)

            issue.cell.scrubbed_lines[issue.line_index] = re.sub(
                re.escape(secret_value),
                redacted_value,
                issue.cell.scrubbed_lines[issue.line_index],
            )
        # TODO DataFrameCellIssue. Secret detection is not working within dataframe cells.

    @staticmethod
    def add_secret_detected_issue(issues: Issues, secret: Secret, path: Path) -> None:
        if secret.cell.cell_type != OutputCellType.DATAFRAME:
            character_start_index = 0
            character_end_index = 0

            cell_line_index = secret.cell.get_cell_line_index_for_file_line_number(
                secret.found_secret.line_number
            )
            if cell_line_index is None:
                raise RuntimeError(
                    "Could not convert file line number to cell line index"
                )

            if secret.found_secret.secret_value:
                character_start_index = secret.cell.lines[cell_line_index].find(
                    secret.found_secret.secret_value, None, None
                )
                character_end_index = character_start_index + len(
                    str(secret.found_secret.secret_value)
                )

            line_cell_issue = LineCellIssue(
                code=IssueCode.SECRETS,
                severity=Severity.CRITICAL,
                cell=secret.cell,
                line_index=cell_line_index,
                character_start_index=character_start_index,
                character_end_index=character_end_index,
                details=IssueBlock(
                    file_path=str(path), description=secret.found_secret.type
                ),
            )
            issues.add_issue(line_cell_issue)
        # TODO Add issues found in dataframes
