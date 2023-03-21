from pathlib import Path
from typing import Any, List

import pytest

from nbdefense.codebase import Codebase
from nbdefense.plugins.cve.cve_dependency_file_plugin import CVEDependencyFilePlugin
from nbdefense.constants import DEFAULT_SETTINGS


class TestCVEDependencyFilePlugin:
    @pytest.fixture
    def codebase(self, tmp_path: Path) -> Codebase:
        return Codebase(
            Path("./tests/plugin_tests/cve/mock_files"),
            False,
            True,
            False,
            tmp_path,
            requirements_file=Path(
                "./tests/plugin_tests/cve/mock_files/requirements.txt"
            ),
        )

    def test_scan(
        self,
        install_trivy: None,
        codebase: Codebase,
    ) -> None:
        CVEDependencyFilePlugin.scan(
            codebase,
            CVEDependencyFilePlugin.get_settings(
                "nbdefense.plugins.CVEDependencyFilePlugin", True, DEFAULT_SETTINGS
            ),
        )
        self.verify_scan_results(codebase)

    @staticmethod
    def verify_scan_results(codebase: Codebase) -> None:
        issues = codebase.issues.to_json()
        assert len(issues) == 2

        cve = "CVE-2022-0845"
        cve_filter = lambda issue: issue["details"]["results"]["VulnerabilityID"] == cve
        cve_list: List[Any] = list(filter(cve_filter, issues))
        assert len(cve_list) == 1
        cve1: Any = cve_list[0]
        assert cve1["code"] == "VULNERABLE_DEPENDENCY_DEP_FILE"
        assert cve1["severity"] == "CRITICAL"
        assert (
            cve1["details"]["file_path"]
            == "tests/plugin_tests/cve/mock_files/requirements.txt"
        )
        assert cve1["details"]["results"]["PkgName"] == "pytorch-lightning"
        assert cve1["details"]["results"]["InstalledVersion"] == "1.5.10"
        assert cve1["details"]["results"]["FixedVersion"] == "1.6.0"

        cve = "CVE-2021-4118"
        cve2: Any = list(filter(cve_filter, issues))
        assert len(cve2) == 1
        cve2 = cve2[0]
        assert cve2["code"] == "VULNERABLE_DEPENDENCY_DEP_FILE"
        assert cve2["severity"] == "HIGH"
        assert (
            cve2["details"]["file_path"]
            == "tests/plugin_tests/cve/mock_files/requirements.txt"
        )
        assert cve2["details"]["results"]["PkgName"] == "pytorch-lightning"
        assert cve2["details"]["results"]["InstalledVersion"] == "1.5.10"
        assert cve2["details"]["results"]["FixedVersion"] == "1.6.0"
