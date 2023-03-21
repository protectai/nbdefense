from enum import Enum
from typing import Any, Dict, List

from nbdefense.settings import Settings, UnknownSettingsError


class LicensePluginSource(Enum):
    HYBRID = "hybrid"  # Looks for licenses in local pip environment and uses the pypi api when a package is not installed locally
    PYPI = "pypi"  # Scans for licenses using PYPI api only
    LOCAL = "local"  # Scans for licenses in local pip environment only

    def to_json(self) -> str:
        return self.name


class LicensePluginSettings(Settings):
    def __init__(
        self, plugin_class_name: str, is_enabled: bool, settings: Dict[str, Any] = {}
    ) -> None:
        super().__init__(plugin_class_name, is_enabled, settings)

    def get_accepted_licenses(self) -> List[str]:
        accepted_licenses: List[str] = super().get("accepted_licenses")
        if isinstance(accepted_licenses, list):
            return accepted_licenses
        else:
            raise UnknownSettingsError("accepted_licenses")

    def get_licenses_for_notebooks_source(self) -> LicensePluginSource:
        source = super().get("licenses_for_notebooks_source")
        if source == "local":
            return LicensePluginSource.LOCAL
        elif source == "hybrid":
            return LicensePluginSource.HYBRID
        elif source == "pypi":
            return LicensePluginSource.PYPI
        else:
            raise UnknownSettingsError("licenses_for_notebooks_source")
