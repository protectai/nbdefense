import logging
from pathlib import Path
from typing import Any, Dict, List

from rich import print

from nbdefense.codebase import Codebase
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import IssueCode, LineCellIssue, Severity
from nbdefense.plugins.licenses.license_plugin import (
    LicensePlugin,
    UnapprovedLicenseIssueDetails,
)
from nbdefense.plugins.licenses.license_plugin_settings import LicensePluginSettings
from nbdefense.plugins.plugin import ScanTarget

logger = logging.getLogger(__name__)


class UnapprovedLicenseImportIssueDetails(UnapprovedLicenseIssueDetails):
    def __init__(
        self,
        module_name: str,
        package_name: str,
        package_version: str,
        unapproved_license: str,
        file_path: Path,
    ) -> None:
        super().__init__(package_name, package_version, unapproved_license, file_path)
        self.module_name = module_name
        if unapproved_license:
            self.description = f"Package '{self.package_name}', version '{self.package_version}' has unapproved license '{self.unapproved_license}'"
        else:
            self.description = f"No license found in package '{self.package_name}', version '{self.package_version}'."

    def to_json(self) -> Dict[str, Any]:
        package_data = {
            "module_name": self.module_name,
            "package_name": self.package_name,
            "package_version": self.package_version,
            "description": self.description,
            "file_path": str(self.file_path),
        }
        if self.unapproved_license:
            package_data["unapproved_license"] = self.unapproved_license
        return package_data


class LicenseNotebookPlugin(LicensePlugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def scan_target() -> ScanTarget:
        return ScanTarget.NOTEBOOKS

    @staticmethod
    def name() -> str:
        return "License Plugin for Notebooks"

    @staticmethod
    def scan(cb: Codebase, settings: LicensePluginSettings) -> List[NBDefenseError]:  # type: ignore[override]
        if cb.quiet:
            logger.setLevel(logging.CRITICAL)
        if not cb._site_packages_path:
            print(
                f"[yellow]Skipping {LicenseNotebookPlugin.name()} scan as it requires a site-packages path[/yellow]"
            )
            return [
                NBDefenseError(
                    ErrorType.SCAN,
                    LicenseNotebookPlugin.name(),
                    f"License scan was skipped because a site-packages path was not provided.",
                )
            ]
        scan_errors = []
        notebooks = cb.notebooks()
        for notebook in cb.notebooks():
            try:
                notebooks.set_description(f"Scanning notebook: {notebook.path}")  # type: ignore[attr-defined]
                packages_with_licenses = LicensePlugin.get_licenses(
                    notebook.dependencies_linked_to_env,
                    cb.temp_directory,
                    settings.get_licenses_for_notebooks_source(),
                )

                accepted_licenses = settings.get_accepted_licenses()
                for package in packages_with_licenses:
                    if not package.module_metadata:
                        logger.warning(
                            f"Could not associate {package.name} with module in notebook."
                        )
                        continue
                    unapproved_licenses = LicensePlugin.filter_for_unapproved_licenses(
                        package.licenses, accepted_licenses
                    )
                    if unapproved_licenses or not package.licenses:
                        character_start_index = package.module_metadata.cell.lines[
                            package.module_metadata.cell_line_index
                        ].find(package.module_metadata.name)
                        character_end_index = character_start_index + len(
                            package.module_metadata.name
                        )
                        for unapproved_license in unapproved_licenses:
                            error_code = (
                                IssueCode.UNAPPROVED_LICENSE_IMPORT
                                if package.licenses
                                else IssueCode.LICENSE_NOT_FOUND_NOTEBOOK
                            )
                            notebook.issues.add_issue(
                                LineCellIssue(
                                    error_code,
                                    Severity.MEDIUM,
                                    package.module_metadata.cell,
                                    package.module_metadata.cell_line_index,
                                    character_start_index,
                                    character_end_index,
                                    UnapprovedLicenseImportIssueDetails(
                                        package.module_metadata.name,
                                        package.name,
                                        package.version,
                                        unapproved_license,
                                        notebook.path,
                                    ),
                                )
                            )
            except Exception as error:
                logger.warning(
                    f"Unable to scan notebook {notebook.path} because of the following error: {str(error)}"
                )
                scan_errors.append(
                    NBDefenseError(
                        ErrorType.SCAN,
                        LicenseNotebookPlugin.name(),
                        f"License scan for notebook {notebook.path} was skipped because of the following error: {str(error)}",
                    )
                )
        return scan_errors
