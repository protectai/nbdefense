import logging
from typing import List

from rich import print

from nbdefense.codebase import Codebase, DependencyIssue
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import Issue, IssueCode, Severity
from nbdefense.plugins.licenses.license_plugin import (
    LicensePlugin,
    UnapprovedLicenseIssueDetails,
)
from nbdefense.plugins.licenses.license_plugin_settings import (
    LicensePluginSettings,
    LicensePluginSource,
)
from nbdefense.plugins.plugin import ScanTarget

logger = logging.getLogger(__name__)


class LicenseDependencyFilePlugin(LicensePlugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def scan_target() -> ScanTarget:
        return ScanTarget.DEPENDENCIES

    @staticmethod
    def name() -> str:
        return "License Plugin for Dependency Files"

    @staticmethod
    def scan(cb: Codebase, settings: LicensePluginSettings) -> List[NBDefenseError]:  # type: ignore[override]
        if cb.quiet:
            logger.setLevel(logging.CRITICAL)

        if not cb.requirements_file_path:
            print(
                f"[yellow]Skipping {LicenseDependencyFilePlugin.name()} scan as it requires a dependency file. (Plugin should have been skipped)[/yellow]"
            )
            return [
                NBDefenseError(
                    ErrorType.SCAN,
                    LicenseDependencyFilePlugin.name(),
                    f"License scan was skipped because a dependency file was not provided.",
                )
            ]

        # Add issue if package is not installed in environment.
        packages = LicensePlugin.get_licenses(
            cb.requirements_file_dependencies,
            cb.temp_directory,
            LicensePluginSource.PYPI,
        )

        # Add issue unapproved packages
        accepted_licenses = settings.get_accepted_licenses()

        # Add errors that occur when scanning
        scan_errors = []
        for package in packages:
            try:
                unapproved_licenses = LicensePlugin.filter_for_unapproved_licenses(
                    package.licenses, accepted_licenses
                )
                if unapproved_licenses:
                    print(
                        f"Scan found {len(unapproved_licenses)} unapproved license(s): {unapproved_licenses} in package {package.name}."
                    )
                    for license in package.licenses:
                        cb.issues.add_issue(
                            Issue(
                                code=IssueCode.UNAPPROVED_LICENSE_DEP_FILE,
                                severity=Severity.MEDIUM,
                                details=UnapprovedLicenseIssueDetails(
                                    package_name=package.name,
                                    package_version=package.version,
                                    unapproved_license=license,
                                    file_path=cb.requirements_file_path,
                                ),
                            )
                        )
                elif not package.licenses:
                    print(f"Could not find license associated with {package.name}.")
                    cb.issues.add_issue(
                        Issue(
                            code=IssueCode.LICENSE_NOT_FOUND_DEP_FILE,
                            severity=Severity.MEDIUM,
                            details=DependencyIssue(
                                cb.requirements_file_path, package.name, package.version
                            ),
                        )
                    )
            except Exception as error:
                logger.warning(
                    f"Unable to scan package {package.name} because of the following error: {str(error)}"
                )
                scan_errors.append(
                    NBDefenseError(
                        ErrorType.SCAN,
                        LicenseDependencyFilePlugin.name(),
                        f"License scan for package {package.name} was skipped because of the following error: {str(error)}",
                    )
                )
        return scan_errors
