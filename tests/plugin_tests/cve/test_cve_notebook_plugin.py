from pathlib import Path
from typing import Any, List

import pytest

from nbdefense.codebase import Codebase
from nbdefense.plugins.cve.cve_notebooks_plugin import CVENotebookPlugin
from nbdefense.constants import DEFAULT_SETTINGS


class TestCVENotebookPlugin:
    @pytest.fixture
    def codebase(self, mock_third_party_dependencies: None, tmp_path: Path) -> Codebase:
        return Codebase(
            Path("./tests/plugin_tests/cve/mock_files/test-cve.ipynb"),
            False,
            True,
            False,
            tmp_path,
            site_packages_path=Path("none"),
        )

    def test_scan(
        self,
        install_trivy: None,
        codebase: Codebase,
    ) -> None:
        CVENotebookPlugin.scan(
            codebase,
            CVENotebookPlugin.get_settings(
                "nbdefense.plugins.CVENotebookPlugin", True, DEFAULT_SETTINGS
            ),
        )
        self.verify_scan_results(codebase)

    @staticmethod
    def verify_scan_results(codebase: Codebase) -> None:
        notebooks = list(codebase.notebooks())
        assert len(notebooks) == 1
        issues = notebooks[0].issues.to_json()
        assert len(issues) == 2

        cve = "CVE-2022-0845"
        cve_filter = lambda issue: issue["details"]["summary_field"]["CVE_ID"] == cve
        cve_list: List[Any] = list(filter(cve_filter, issues))
        assert len(cve_list) == 1
        cve1: Any = cve_list[0]
        assert cve1["code"] == "VULNERABLE_DEPENDENCY_IMPORT"
        assert cve1["severity"] == "CRITICAL"
        assert cve1["cell"]["cell_index"] == 1
        assert cve1["line_index"] == 0
        assert cve1["location"] == "INPUT"
        assert cve1["character_start_index"] == 7
        assert cve1["character_end_index"] == 24
        assert (
            cve1["details"]["summary_field"]["INSTALLED_PACKAGE"] == "pytorch-lightning"
        )
        assert cve1["details"]["summary_field"]["INSTALLED_VERSION"] == "1.5.10"
        assert cve1["details"]["summary_field"]["FIXED_VERSION"] == "1.6.0"

        cve = "CVE-2021-4118"
        cve2: Any = list(filter(cve_filter, issues))
        assert len(cve2) == 1
        cve2 = cve2[0]
        assert cve2["code"] == "VULNERABLE_DEPENDENCY_IMPORT"
        assert cve2["severity"] == "HIGH"
        assert cve1["cell"]["cell_index"] == 1
        assert cve1["line_index"] == 0
        assert cve1["location"] == "INPUT"
        assert cve1["character_start_index"] == 7
        assert cve1["character_end_index"] == 24
        assert (
            cve2["details"]["summary_field"]["INSTALLED_PACKAGE"] == "pytorch-lightning"
        )
        assert cve2["details"]["summary_field"]["INSTALLED_VERSION"] == "1.5.10"
        assert cve2["details"]["summary_field"]["FIXED_VERSION"] == "1.6.0"
