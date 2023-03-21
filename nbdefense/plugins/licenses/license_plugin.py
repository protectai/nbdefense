import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from requests.adapters import HTTPAdapter, Retry

from nbdefense.codebase import PackageInfo
from nbdefense.issues import IssueDetails
from nbdefense.plugins.licenses.license_plugin_settings import (
    LicensePluginSettings,
    LicensePluginSource,
)
from nbdefense.plugins.plugin import Plugin

logger = logging.getLogger(__name__)


class LicenseCache:
    def __init__(self, temp_directory: Path, filename: str) -> None:
        self._license_cache_path = temp_directory.joinpath(filename)
        self._cache_updated = False
        self._cache: Dict[str, List[str]] = {}
        self._onload()

    def __del__(self) -> None:
        if self._cache_updated:
            with open(self._license_cache_path, "w") as outfile:
                json.dump(self._cache, outfile)

    def _onload(self) -> None:
        if self._license_cache_path.exists():
            with open(self._license_cache_path) as f:
                try:
                    self._cache = json.load(f)
                    return
                except json.decoder.JSONDecodeError:
                    # Cache will be overwritten on save
                    logger.warning(
                        f"Could not decode license cache file. License cache will be overwritten."
                    )
                    pass
        self._cache = {}

    def add(self, package_name: str, package_version: str, licenses: List[str]) -> None:
        self._cache_updated = True
        self._cache[package_name + package_version] = licenses

    def get(self, package_name: str, package_version: str) -> List[str]:
        result: List[str] = self._cache.get(package_name + package_version, [])
        return result


class UnapprovedLicenseIssueDetails(IssueDetails):
    def __init__(
        self,
        package_name: str,
        package_version: str,
        unapproved_license: str,
        file_path: Path,
    ) -> None:
        super().__init__()
        self.package_name = package_name
        self.package_version = package_version
        self.unapproved_license = unapproved_license
        self.file_path = file_path

    def to_json(self) -> Dict[str, Any]:
        """
        Return Values:
        unapproved_license: a license that is not in the ACCEPTED_LICENSES list.
        package_name: packages that include the unapproved license.
        package_version: version of the package with unapproved license
        file_path: dependency file where package was found
        """
        return {
            "package_name": self.package_name,
            "package_version": self.package_version,
            "unapproved_license": self.unapproved_license,
            "file_path": str(self.file_path),
        }


class LicensePlugin(Plugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def get_settings(
        plugin_class_name: str, is_enabled: bool = True, settings: Dict[str, Any] = {}
    ) -> LicensePluginSettings:
        return LicensePluginSettings(plugin_class_name, is_enabled, settings)

    @staticmethod
    def get_licenses(
        packages: List[PackageInfo],
        temp_directory: Path,
        source: LicensePluginSource,
    ) -> List[PackageInfo]:
        """
        Processes packages and returns a list of packages with found licenses attached.
        """
        cache = LicenseCache(temp_directory, filename="license-cache.json")
        (
            packages_with_licenses,
            packages_for_pypi,
        ) = LicensePlugin._process_packages(cache, source, packages)
        if packages_for_pypi:
            LicensePlugin._process_packages_for_pypi(
                cache,
                packages_for_pypi,
                packages_with_licenses,
            )
        return packages_with_licenses

    @staticmethod
    def filter_for_unapproved_licenses(
        licenses: List[str], accepted_licenses: List[str]
    ) -> List[str]:
        return list(filter(lambda x: x not in accepted_licenses, licenses))

    @staticmethod
    def _process_packages(
        cache: LicenseCache,
        source: LicensePluginSource,
        packages: List[PackageInfo],
    ) -> Tuple[List[PackageInfo], List[PackageInfo]]:
        """
        cache: License cache object
        source: Where license data should be gathered from
        packages: Packages to be processed
        returns, packages_with_licenses: A list of packages with licenses attached if license was added
        returns, packages_for_pypi: A list of packages with licenses attached if license was added
        """
        packages_with_licenses: List[PackageInfo] = []
        packages_for_pypi: List[PackageInfo] = []
        for package in packages:
            licenses = cache.get(package.name, package.version)
            if licenses:
                package.licenses = licenses
                packages_with_licenses.append(package)
            else:
                LicensePlugin._process_package(
                    source,
                    cache,
                    package,
                    packages_with_licenses,
                    packages_for_pypi,
                )
        return packages_with_licenses, packages_for_pypi

    @staticmethod
    def _process_package(
        source: LicensePluginSource,
        cache: LicenseCache,
        package: PackageInfo,
        packages_with_licenses: List[PackageInfo],
        packages_for_pypi: List[PackageInfo],
    ) -> None:
        """
        Processes a package and adds it to packages with licenses
        or packages_for_pypi depending
        on whether license data was found locally,
        and the source configuration.
        """
        licenses: List[str] = []
        if source == LicensePluginSource.LOCAL or source == LicensePluginSource.HYBRID:
            licenses = LicensePlugin._parse_license_data_from_dist_info_path(package)

        if source == LicensePluginSource.PYPI or (
            source == LicensePluginSource.HYBRID and not licenses
        ):
            if not licenses:
                packages_for_pypi.append(package)
                return
        package.licenses = licenses
        cache.add(package.name, package.version, package.licenses)
        packages_with_licenses.append(package)

    @staticmethod
    def _process_packages_for_pypi(
        cache: LicenseCache,
        packages_for_pypi: List[PackageInfo],
        packages_with_licenses: List[PackageInfo],
    ) -> None:
        """
        Adds package in package_for_pypi to packages_with_licenses if
        license is found from the PYPI API. If license for a package is not
        found it is added to packages_with_errors.
        """
        packages_with_licenses_added = asyncio.run(
            LicensePlugin._fetch_license_data_from_pypi_async(packages_for_pypi)
        )
        for package in packages_with_licenses_added:
            cache.add(package.name, package.version, package.licenses)
            packages_with_licenses.append(package)

    @staticmethod
    def _parse_license_data_from_dist_info_path(package: PackageInfo) -> List[str]:
        """
        Parses the METADATA file associated with package if
        package has a dist_info_path for package is not none.
        Returns a list of licenses gathered from classifiers if found,
        and license metadata if no classifiers found.
        """
        CLASSIFIER_IDENTIFIER = "Classifier: License ::"
        LICENSE_METADATA_IDENTIFIER = "License:"
        classifier_licenses: List[str] = []
        metadata_licenses: List[str] = []
        if package.dist_info_path and package.dist_info_path.is_dir():
            metadata_path = package.dist_info_path / "METADATA"
            if metadata_path.is_file():
                with open(metadata_path, "r") as metadata_file:
                    for line in metadata_file.readlines():
                        if line.startswith(LICENSE_METADATA_IDENTIFIER):
                            metadata_licenses.append(
                                line.replace(LICENSE_METADATA_IDENTIFIER, "").strip()
                            )
                        elif line.startswith(CLASSIFIER_IDENTIFIER):
                            classifier_licenses.append(
                                line.replace(CLASSIFIER_IDENTIFIER, "")
                                .replace("OSI Approved ::", "")
                                .strip()
                            )
        if classifier_licenses:
            return classifier_licenses
        else:
            return metadata_licenses

    @staticmethod
    async def _fetch_license_data_from_pypi_async(
        packages: List[PackageInfo],
    ) -> List[PackageInfo]:
        with ThreadPoolExecutor(max_workers=10) as executor:
            with requests.Session() as session:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(
                        executor,
                        LicensePlugin._fetch_license_data_from_pypi,
                        *(session, package),
                    )
                    for package in packages
                ]
                return await asyncio.gather(*tasks)

    @staticmethod
    def _fetch_license_data_from_pypi(
        session: requests.Session, package: PackageInfo
    ) -> PackageInfo:
        licenses = []
        url = f"https://pypi.org/pypi/{package.name}/{package.version}/json"
        retries = Retry(total=2, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        response = session.get(url)
        response.content
        if response.status_code != 200:
            logger.warning(
                f"When trying to gather license data a call to PYPI failed with status code {response.status_code}. Failed on package: {package.name} URL: {url}"
            )
        else:
            package_metadata: Dict[str, Any] = json.loads(response.content)
            licenses = LicensePlugin._parse_licenses_from_pypi_metadata(
                package_metadata
            )
        package.licenses = licenses
        return package

    @staticmethod
    def _parse_licenses_from_pypi_metadata(
        package_metadata: Dict[str, Any]
    ) -> List[str]:
        package_info = package_metadata.get("info", {})
        classifiers = package_info.get("classifiers", [])
        licenses: List[str] = LicensePlugin._parse_licenses_from_classifiers(
            classifiers
        )
        if not licenses:
            license = package_info.get("license")
            if license and license != "UNKNOWN":
                return [license]
        return licenses

    @staticmethod
    def _parse_licenses_from_classifiers(classifiers: List[str]) -> List[str]:
        licenses = []
        for classifier in classifiers:
            if classifier.startswith("License"):
                license = classifier.split(" :: ")[-1]
                if license != "OSI Approved":
                    licenses.append(license)
        return licenses
