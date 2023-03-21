from pathlib import Path
from typing import Any, Dict, List

import pytest

from nbdefense.codebase import Codebase
from nbdefense.plugins.licenses.licenses_notebooks_plugin import LicenseNotebookPlugin

MATPLOTLIB_LICENSE = "MPL License"
PYTORCH_LICENSE = "PD LICENSE"


class TestLicenseNotebookPlugin:
    @pytest.fixture
    def codebase(self, mock_third_party_dependencies: None, tmp_path: Path) -> Codebase:
        return Codebase(
            Path("./tests/plugin_tests/licenses/mock_files/test-license.ipynb"),
            False,
            True,
            False,
            tmp_path,
            site_packages_path=Path("none"),
        )

    def test_scan_local(
        self,
        codebase: Codebase,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
        mock_fetch_license_data_from_pypi: Dict[str, List[str]],
    ) -> None:
        issues = self.run_scan(
            codebase,
            mock_fetch_licenses_from_dist_info_path,
            mock_fetch_license_data_from_pypi,
            "local",
        )
        assert len(issues) == 1
        issue = issues[0]
        assert issue["code"] == "UNAPPROVED_LICENSE_IMPORT"
        assert issue["severity"] == "MEDIUM"
        assert issue["cell"]["cell_index"] == 0
        assert issue["line_index"] == 1
        assert issue["location"] == "INPUT"
        assert issue["character_start_index"] == 7
        assert issue["character_end_index"] == 21
        assert issue["details"]["module_name"] == "matplotlibXtns"
        assert issue["details"]["package_name"] == "matplotlibXtns"
        assert issue["details"]["package_version"] == "20.5"
        assert issue["details"]["unapproved_license"] == MATPLOTLIB_LICENSE

    def test_scan_hybrid(
        self,
        codebase: Codebase,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
        mock_fetch_license_data_from_pypi: Dict[str, List[str]],
    ) -> None:
        issues = self.run_scan(
            codebase,
            mock_fetch_licenses_from_dist_info_path,
            mock_fetch_license_data_from_pypi,
            "hybrid",
        )
        assert len(issues) == 2
        package = "matplotlibXtns"
        license_filter = lambda issue: issue["details"]["package_name"] == package
        issue1 = list(filter(license_filter, issues))[0]
        assert issue1["code"] == "UNAPPROVED_LICENSE_IMPORT"
        assert issue1["severity"] == "MEDIUM"
        assert issue1["cell"]["cell_index"] == 0
        assert issue1["line_index"] == 1
        assert issue1["location"] == "INPUT"
        assert issue1["character_start_index"] == 7
        assert issue1["character_end_index"] == 21
        assert issue1["details"]["module_name"] == "matplotlibXtns"
        assert issue1["details"]["package_version"] == "20.5"
        assert issue1["details"]["unapproved_license"] == MATPLOTLIB_LICENSE

        package = "pytorch-lightning"
        issue2 = list(filter(license_filter, issues))[0]
        assert issue2["code"] == "UNAPPROVED_LICENSE_IMPORT"
        assert issue2["severity"] == "MEDIUM"
        assert issue2["cell"]["cell_index"] == 1
        assert issue2["line_index"] == 0
        assert issue2["location"] == "INPUT"
        assert issue2["character_start_index"] == 7
        assert issue2["character_end_index"] == 24
        assert issue2["details"]["module_name"] == "pytorch_lightning"
        assert issue2["details"]["package_version"] == "1.5.10"
        assert issue2["details"]["unapproved_license"] == PYTORCH_LICENSE

    def test_scan_pypi(
        self,
        codebase: Codebase,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
        mock_fetch_license_data_from_pypi: Dict[str, List[str]],
    ) -> None:
        issues = self.run_scan(
            codebase,
            mock_fetch_licenses_from_dist_info_path,
            mock_fetch_license_data_from_pypi,
            "pypi",
        )

        assert len(issues) == 1
        issue = issues[0]
        assert issue["code"] == "UNAPPROVED_LICENSE_IMPORT"
        assert issue["severity"] == "MEDIUM"
        assert issue["cell"]["cell_index"] == 1
        assert issue["line_index"] == 0
        assert issue["location"] == "INPUT"
        assert issue["character_start_index"] == 7
        assert issue["character_end_index"] == 24
        assert issue["details"]["module_name"] == "pytorch_lightning"
        assert issue["details"]["package_version"] == "1.5.10"
        assert issue["details"]["unapproved_license"] == PYTORCH_LICENSE

    def run_scan(
        self,
        codebase: Codebase,
        mock_dist_info_path: Dict[str, List[Any]],
        mock_pypi: Dict[str, List[Any]],
        source_config: str,
    ) -> List[Dict[str, Any]]:
        mock_dist_info_path["classifiers"].append(MATPLOTLIB_LICENSE)
        mock_dist_info_path["package_names"].append("matplotlibXtns")
        mock_pypi["package_names"].append("pytorch-lightning")
        mock_pypi["licenses"].append(PYTORCH_LICENSE)
        LicenseNotebookPlugin.scan(
            codebase,
            LicenseNotebookPlugin.get_settings(
                "nbdefense.plugins.LicenseNotebookPlugin",
                True,
                {
                    "plugins": {
                        "nbdefense.plugins.LicenseNotebookPlugin": {
                            "enabled": True,
                            "accepted_licenses": [],
                            "licenses_for_notebooks_source": source_config,
                        }
                    }
                },
            ),
        )
        notebooks = list(codebase.notebooks())
        assert len(notebooks) == 1
        issues = notebooks[0].issues.to_json()
        return issues
