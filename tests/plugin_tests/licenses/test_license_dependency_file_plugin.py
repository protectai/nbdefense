from pathlib import Path
from typing import Dict, List

import pytest

from nbdefense.codebase import Codebase
from nbdefense.plugins.licenses.licenses_dependency_file_plugin import (
    LicenseDependencyFilePlugin,
)
from tests.default_settings import DEFAULT_SETTINGS


class TestLicenseDependencyFilePlugin:
    @pytest.fixture
    def codebase(
        self, tmp_path: Path, create_license_requirements_file_path: Path
    ) -> Codebase:
        print(create_license_requirements_file_path)
        return Codebase(
            Path("./tests/plugin_tests/licenses/mock_files"),
            False,
            True,
            False,
            tmp_path,
            requirements_file=create_license_requirements_file_path,
        )

    def test_scan(
        self,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
        mock_fetch_license_data_from_pypi: Dict[str, List[str]],
        codebase: Codebase,
        create_license_requirements_file_path: Path,
    ) -> None:
        unapproved_licenses = ["BAD_LICENSE_1", "BAD_LICENSE_2"]
        mock_fetch_license_data_from_pypi["licenses"].append(unapproved_licenses[0])
        mock_fetch_license_data_from_pypi["licenses"].append(unapproved_licenses[1])
        LicenseDependencyFilePlugin.scan(
            codebase,
            LicenseDependencyFilePlugin.get_settings(
                plugin_class_name="nbdefense.plugins.LicenseDependencyFilePlugin",
                settings=DEFAULT_SETTINGS,
            ),
        )
        self.verify_scan_results(codebase, create_license_requirements_file_path)

    @staticmethod
    def verify_scan_results(codebase: Codebase, requirements_file_path: Path) -> None:
        issues = codebase.issues.to_json()
        assert len(issues) == 8
        for package_name_index in range(1, 5):
            package_name = f"test_package_{package_name_index}"
            package_version = None
            if package_name == "test_package_1":
                package_version = "23.2.1"
            elif package_name == "test_package_2":
                package_version = "2.28.1"
            elif package_name == "test_package_3":
                package_version = "1.8.0"
            elif package_name == "test_package_4":
                package_version = "1.16.0"

            issues_filter_by_package_name = list(
                filter(
                    lambda issue: (issue["details"]["package_name"] == package_name),
                    issues,
                )
            )
            assert len(issues_filter_by_package_name) == 2
            for package_index, _ in enumerate(issues_filter_by_package_name):
                assert {
                    "code": "UNAPPROVED_LICENSE_DEP_FILE",
                    "severity": "MEDIUM",
                    "details": {
                        "package_name": package_name,
                        "package_version": package_version,
                        "unapproved_license": f"BAD_LICENSE_{package_index+1}",
                        "file_path": str(requirements_file_path),
                    },
                } in issues_filter_by_package_name
