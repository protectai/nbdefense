import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import print

from nbdefense.codebase import Codebase, PackageInfo
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import IssueBlock, IssueCode, LineCellIssue
from nbdefense.plugins.cve.cve_plugin import CVEPlugin
from nbdefense.plugins.plugin import ScanTarget
from nbdefense.settings import Settings
from nbdefense.tools import Trivy

logger = logging.getLogger(__name__)


class CVENotebookPlugin(CVEPlugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def scan_target() -> ScanTarget:
        return ScanTarget.NOTEBOOKS

    @staticmethod
    def name() -> str:
        return "CVE Plugin for Notebooks"

    @staticmethod
    def scan(
        codebase: Codebase, settings: Optional[Settings] = None
    ) -> List[NBDefenseError]:
        if codebase.quiet:
            logger.setLevel(logging.CRITICAL)
        if not codebase._site_packages_path:
            print(
                f"[yellow]Skipping {CVENotebookPlugin.name()} scan as it requires a site-packages path[/yellow]"
            )
            return [
                NBDefenseError(
                    ErrorType.SCAN,
                    CVENotebookPlugin.name(),
                    f"CVE scan was skipped because a site-packages path was not provided.",
                )
            ]

        initialTrivyBinaryPath = settings.get("trivy_binary_path") if settings else ""
        trivy = Trivy(initialTrivyBinaryPath)
        notebooks = codebase.notebooks()
        notebook_scan_errors: List[NBDefenseError] = []
        for notebook in notebooks:
            try:
                notebooks.set_description(f"Scanning notebook: {notebook.path}")  # type: ignore[attr-defined]
                # Find Vulnerabilities
                vulnerabilities = CVENotebookPlugin.get_vulnerabilities(
                    codebase, trivy, notebook.dependencies_linked_to_env
                )

                # Report Vulnerabilities
                if vulnerabilities:
                    print(
                        f"Scan found {len(vulnerabilities)} vulnerabilities in notebook {str(notebook.path)}"
                    )
                for vulnerability in vulnerabilities:
                    package_name = vulnerability.get("PkgName", None)
                    package_version = vulnerability.get("InstalledVersion", None)
                    package = CVENotebookPlugin.find_package_in_packages(
                        package_name,
                        package_version,
                        notebook.dependencies_linked_to_env,
                    )
                    if package and package.module_metadata:
                        character_start_index = package.module_metadata.cell.lines[
                            package.module_metadata.cell_line_index
                        ].find(package.module_metadata.name)
                        character_end_index = character_start_index + len(
                            package.module_metadata.name
                        )
                        notebook.issues.add_issue(
                            LineCellIssue(
                                IssueCode.VULNERABLE_DEPENDENCY_IMPORT,
                                CVEPlugin.vulnerability_severity(vulnerability),
                                package.module_metadata.cell,
                                package.module_metadata.cell_line_index,
                                character_start_index,
                                character_end_index,
                                IssueBlock(
                                    file_path=str(notebook.path),
                                    description=f"CVE found in package '{package_name}', version '{package_version}",
                                    summary_field={
                                        "CVE_ID": vulnerability.get(
                                            "VulnerabilityID", "Not Found"
                                        ),
                                        "INSTALLED_PACKAGE": package_name,
                                        "INSTALLED_VERSION": package_version,
                                        "FIXED_VERSION": vulnerability.get(
                                            "FixedVersion", "Not Found"
                                        ),
                                        "DESCRIPTION": vulnerability.get(
                                            "Title", "Description not found"
                                        ),
                                        "URL": vulnerability.get("PrimaryURL", None),
                                    },
                                ),
                            )
                        )
                    else:
                        error_message = f"Trivy returned a vulnerability for package '{package_name}=={package_version}', and we could not link it to a package installed in the environment."
                        logger.warning(error_message)
                        notebook_scan_errors.append(
                            NBDefenseError(
                                ErrorType.SCAN, CVENotebookPlugin.name(), error_message
                            )
                        )
            except Exception as error:
                logger.warning(
                    f"Skipping CVE scan for notebook {notebook.path} because of the following error: {str(error)}"
                )
                notebook_scan_errors.append(
                    NBDefenseError(
                        ErrorType.SCAN,
                        CVENotebookPlugin.name(),
                        f"CVE scan for notebook {notebook.path} was skipped because of the following error: {str(error)}",
                    )
                )
        return notebook_scan_errors

    @staticmethod
    def cleanup_file(path: Path) -> None:
        if os.path.isfile(path):
            os.remove(path)

    @staticmethod
    def get_vulnerabilities(
        codebase: Codebase, trivy: Trivy, packages: List[PackageInfo]
    ) -> List[Dict[Any, Any]]:
        requirements_file_lines = []
        for package in packages:
            requirements_file_lines.append(f"{package.name}=={package.version}\n")

        temp_file_path = codebase.temp_directory / "requirements.txt"
        CVENotebookPlugin.cleanup_file(temp_file_path)
        if os.path.isfile(temp_file_path):
            os.remove(temp_file_path)
        with open(temp_file_path, "w") as outfile:
            outfile.writelines(requirements_file_lines)

        _, stdout, _ = trivy.execute(str(temp_file_path))
        if stdout:
            stdoutstring = b"".join(stdout)
            vulnerabilities = CVENotebookPlugin.extract_results(
                json.loads(stdoutstring)
            )
            CVENotebookPlugin.cleanup_file(temp_file_path)
            return vulnerabilities
        return []

    @staticmethod
    def find_package_in_packages(
        package_name: Optional[str],
        package_version: Optional[str],
        packages: List[PackageInfo],
    ) -> Optional[PackageInfo]:
        if package_name and package_version:
            for package in packages:
                if package.name == package_name and package.version == package_version:
                    return package
        return None
