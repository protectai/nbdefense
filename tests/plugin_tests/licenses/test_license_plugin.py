from pathlib import Path
from typing import Dict, List

from nbdefense.codebase import PackageInfo
from nbdefense.plugins.licenses.license_plugin import LicensePlugin
from nbdefense.plugins.licenses.license_plugin_settings import LicensePluginSource
from tests.default_settings import DEFAULT_SETTINGS


class TestLicensePlugin:
    def test_get_licenses_none_found(
        self,
        tmp_path: Path,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
        mock_fetch_license_data_from_pypi: Dict[str, List[str]],
    ) -> None:
        test_package = PackageInfo(name="none", version="none")

        installed_packages = LicensePlugin.get_licenses(
            [test_package], tmp_path, LicensePluginSource.HYBRID
        )
        assert len(installed_packages) == 1
        assert installed_packages[0].name == test_package.name
        assert installed_packages[0].version == test_package.version
        assert not installed_packages[0].licenses

    def test_get_licenses_fall_back_to_api(
        self,
        tmp_path: Path,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
        mock_fetch_license_data_from_pypi: Dict[str, List[str]],
    ) -> None:
        package_info = PackageInfo(name="package_test_1", version="version")
        fallback_license = "Fallback To API License"
        mock_fetch_license_data_from_pypi["licenses"].append(fallback_license)
        installed_packages = LicensePlugin.get_licenses(
            [package_info], tmp_path, LicensePluginSource.HYBRID
        )
        assert len(installed_packages) == 1
        assert installed_packages[0].name == package_info.name
        assert installed_packages[0].version == package_info.version
        assert installed_packages[0].licenses == [fallback_license]

    def test_filter_for_unapproved_licenses(self) -> None:
        licenses = LicensePlugin.filter_for_unapproved_licenses(
            ["MIT", "UNAPPROVED"], ["MIT"]
        )
        assert len(licenses) == 1
        assert licenses[0] == "UNAPPROVED"

    def test_get_licenses_in_metadata(
        self,
        tmp_path: Path,
        mock_license_cache: None,
        mock_fetch_licenses_from_dist_info_path: Dict[str, List[str]],
    ) -> None:
        license = "GNU"
        package_info = PackageInfo(name="package_test_1", version="version")
        mock_fetch_licenses_from_dist_info_path["license_metadata"].append(license)
        installed_packages = LicensePlugin.get_licenses(
            [package_info], tmp_path, LicensePluginSource.HYBRID
        )
        assert len(installed_packages) == 1
        assert installed_packages[0].name == package_info.name
        assert installed_packages[0].version == package_info.version
        assert installed_packages[0].licenses == [license]

    def test_process_for_unnapproved_licenses(self) -> None:
        settings = LicensePlugin.get_settings(
            plugin_class_name="nbdefense.plugins.LicenseNotebookPlugin",
            settings=DEFAULT_SETTINGS,
        )
        unapproved_license = "APACHE_UNAPPROVED"
        unapproved_licenses = LicensePlugin.filter_for_unapproved_licenses(
            ["MIT", unapproved_license], settings.get_accepted_licenses()
        )
        assert unapproved_licenses == [unapproved_license]

    def test_parse_licenses_from_classifiers_single_license(self) -> None:
        classifiers_list = [
            "License :: OSI Approved",
            "License :: OSI Approved :: MIT",
            "Private :: Do Not Upload",
        ]
        licenses = LicensePlugin._parse_licenses_from_classifiers(classifiers_list)
        assert licenses == ["MIT"]

    def test_parse_licenses_from_classifiers_multiple_license(self) -> None:
        classifiers_list = [
            "License :: OSI Approved :: MIT",
            "License :: OSI Approved :: Apache 2",
        ]
        licenses = LicensePlugin._parse_licenses_from_classifiers(classifiers_list)
        assert licenses == ["MIT", "Apache 2"]

    def test_parse_licenses_from_classifiers_no_license(self) -> None:
        no_license_classifier = ["Private :: Do Not Upload"]
        licenses = LicensePlugin._parse_licenses_from_classifiers(no_license_classifier)
        assert licenses == []
