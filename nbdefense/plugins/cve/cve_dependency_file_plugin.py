import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import print

from nbdefense.codebase import Codebase
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import Issue, IssueCode, IssueDetails
from nbdefense.plugins.cve.cve_plugin import CVEPlugin
from nbdefense.plugins.plugin import ScanTarget
from nbdefense.settings import Settings
from nbdefense.tools import Trivy

logger = logging.getLogger(__name__)


class DependencyIssueDetails(IssueDetails):
    def __init__(self, vulnerability: Dict[str, Any], file_path: Path) -> None:
        self.vulnerability = vulnerability
        self.file_path = file_path

    def to_json(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "results": self.vulnerability,
        }


class CVEDependencyFilePlugin(CVEPlugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def scan_target() -> ScanTarget:
        return ScanTarget.DEPENDENCIES

    @staticmethod
    def name() -> str:
        return "CVE Plugin for Dependency Files"

    @staticmethod
    def scan(
        codebase: Codebase, settings: Optional[Settings] = None
    ) -> List[NBDefenseError]:
        if codebase.quiet:
            logger.setLevel(logging.CRITICAL)
        if not codebase.requirements_file_path:
            print(
                f"[yellow]Skipping {CVEDependencyFilePlugin.name()} scan as it requires a dependency file. (Plugin should have been skipped)[/yellow]"
            )
            return [
                NBDefenseError(
                    ErrorType.SCAN,
                    CVEDependencyFilePlugin.name(),
                    f"CVE scan was skipped because a dependency file was not provided.",
                )
            ]

        initialTrivyBinaryPath = settings.get("trivy_binary_path") if settings else ""
        trivy = Trivy(initialTrivyBinaryPath)
        _, stdout, _ = trivy.execute(str(codebase.requirements_file_path))
        if stdout:
            stdoutstring = b"".join(stdout)
            vulnerabilities = CVEPlugin.extract_results(json.loads(stdoutstring))
            if vulnerabilities:
                logger.warning(f"Scan found {len(vulnerabilities)} vulnerabilities")
            for vulnerability in vulnerabilities:
                codebase.issues.add_issue(
                    Issue(
                        code=IssueCode.VULNERABLE_DEPENDENCY_DEP_FILE,
                        severity=CVEPlugin.vulnerability_severity(vulnerability),
                        details=DependencyIssueDetails(
                            vulnerability=vulnerability,
                            file_path=codebase.requirements_file_path,
                        ),
                    )
                )
        else:
            print("Scan found no vulnerabilities")
        return []
