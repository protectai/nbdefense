from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests

from nbdefense.codebase import PackageInfo
from nbdefense.plugins.licenses.license_plugin import LicenseCache, LicensePlugin


@pytest.fixture
def mock_license_cache(monkeypatch: Any) -> None:
    def mock_init(self: Any, temp_directory: Path, filename: str) -> None:
        self._cache = {}
        self._cache_updated = False

    def mock_del(self: Any) -> None:
        pass

    monkeypatch.setattr(LicenseCache, "__init__", mock_init)
    monkeypatch.setattr(LicenseCache, "__del__", mock_del)


@pytest.fixture
def mock_fetch_licenses_from_dist_info_path(monkeypatch: Any) -> Dict[str, List[str]]:
    classifiers: List[str] = []
    license_metadata: List[str] = []
    package_names: List[str] = []

    def mock_parse_license_from_dist_info_path(package: PackageInfo) -> Any:
        if not package_names or package.name in package_names:
            if classifiers:
                return classifiers
            else:
                return license_metadata
        return []

    monkeypatch.setattr(
        LicensePlugin,
        "_parse_license_data_from_dist_info_path",
        mock_parse_license_from_dist_info_path,
    )
    return {
        "classifiers": classifiers,
        "license_metadata": license_metadata,
        "package_names": package_names,
    }


@pytest.fixture
def mock_fetch_license_data_from_pypi(monkeypatch: Any) -> Dict[str, List[str]]:
    licenses: List[str] = []
    package_names: List[str] = []

    def mock_function_response(
        _: requests.Session, package: PackageInfo
    ) -> PackageInfo:
        if not package_names or package.name in package_names:
            package.licenses = licenses
        else:
            package.licenses = []
        return package

    monkeypatch.setattr(
        LicensePlugin,
        "_fetch_license_data_from_pypi",
        mock_function_response,
    )
    return {
        "licenses": licenses,
        "package_names": package_names,
    }
