import os
from pathlib import Path
from typing import Any

import pytest

from nbdefense.dependencies import DependencyInfo, ThirdPartyDependencies
from nbdefense.plugins.cve.cve_plugin import CVEPlugin


@pytest.fixture(scope="session")
def create_cve_requirements_file_path() -> Path:
    current_directory = Path(os.path.dirname(os.path.realpath(__file__)))
    requirements_directory = current_directory / "mock_files"
    requirements_file_path = requirements_directory / "requirements.txt"
    with open(requirements_file_path, "w") as f:
        f.writelines(
            ["pytorch-lightning==1.5.10\n", "pandas==1.5.0\n", "matplotlibXtns==20.5\n"]
        )
    return requirements_file_path


@pytest.fixture
def mock_third_party_dependencies(monkeypatch: Any) -> None:
    dependencies = [
        DependencyInfo(
            name="pytorch-lightning",
            version="1.5.10",
            dist_info_path=Path("none"),
            dist_info_name="none",
        ),
        DependencyInfo(
            name="pandas",
            version="1.5.0",
            dist_info_path=Path("none"),
            dist_info_name="none",
        ),
        DependencyInfo(
            name="matplotlibXtns",
            version="20.5",
            dist_info_path=Path("none"),
            dist_info_name="none",
        ),
    ]

    def mock_parse_dependencies_available_in_env(self: Any) -> None:
        self._dependencies_in_env = dependencies

    def mock_parse_modules_from_dependencies_available(self: Any) -> None:
        self._dependencies_by_module["pytorch_lightning"] = dependencies[0]
        self._dependencies_by_module["pandas"] = dependencies[1]
        self._dependencies_by_module["matplotlibXtns"] = dependencies[2]

    monkeypatch.setattr(
        ThirdPartyDependencies,
        "_parse_dependencies_available_in_env",
        mock_parse_dependencies_available_in_env,
    )
    monkeypatch.setattr(
        ThirdPartyDependencies,
        "_parse_modules_from_dependencies_available",
        mock_parse_modules_from_dependencies_available,
    )


@pytest.fixture
def install_trivy() -> None:
    CVEPlugin.handle_binary_dependencies(True, True)
