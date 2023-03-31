import abc
from typing import Any, Dict

import tomlkit

from nbdefense.constants import DEFAULT_SETTINGS


class Settings(abc.ABC):
    is_enabled: bool
    settings: Dict[str, Any]

    def __init__(
        self, plugin_class_name: str, is_enabled: bool, settings: Dict[str, Any]
    ) -> None:
        self.plugin_class_name = plugin_class_name
        self.is_enabled = is_enabled
        self.settings = settings

    def get(self, key: str) -> Any:
        # Global settings
        if key in self.settings:
            return self.settings.get(key)
        if (
            "plugins" in self.settings
            and self.plugin_class_name in self.settings["plugins"]
            and key in self.settings["plugins"][self.plugin_class_name]
        ):
            return self.settings["plugins"][self.plugin_class_name].get(key)

        raise UnknownSettingsError(key)

    def to_json(self, limit_to_plugin: bool = False) -> Any:
        return (
            self.settings["plugins"].get(self.plugin_class_name)
            if limit_to_plugin
            else self.settings
        )


class UnknownSettingsError(Exception):
    setting_accessed: str

    def __init__(self, setting_accessed: str, *args: object) -> None:
        self.setting_accessed = setting_accessed
        super().__init__(*args)

    def __str__(self) -> str:
        return f"Unknown setting: {self.setting_accessed}"


class UnknownSettingsValueError(UnknownSettingsError):
    setting_value: str

    def __init__(
        self, setting_accessed: str, setting_value: str, *args: object
    ) -> None:
        self.setting_value = setting_value
        super().__init__(setting_accessed, *args)

    def __str__(self) -> str:
        return f"Setting '{self.setting_accessed}' has unknown value: '{self.setting_value}'"


class SettingsUtils:
    @staticmethod
    def get_default_settings_as_toml() -> str:
        # TODO: Find a better way to add comments to the toml file
        toml_settings = tomlkit.dumps(DEFAULT_SETTINGS)

        # Remove notebook plugin settings
        toml_settings = toml_settings.split(
            '\n[plugins."nbdefense.plugins.LicenseNotebookPlugin"]'
        )[0]

        # Add settings file header
        toml_settings = f"# NB Defense settings file\n\n{toml_settings}"

        # Add redact_secret enum comment
        redact_secret_string = 'redact_secret = "PARTIAL"'  # nosec
        redact_secret_end_index = toml_settings.find(
            redact_secret_string
        )  # + len(redact_secret_string) - 1
        toml_settings_list = [
            toml_settings[:redact_secret_end_index],
            """# Redact secrets
# Possible values are `PARTIAL`, `ALL`, `HASH`

# `PARTIAL` will show only leading and trailing characters.

# `ALL` will shadow the full secret.

# `HASH` will replace the full secret with its hashed value.\n""",
            toml_settings[redact_secret_end_index:],
        ]
        toml_settings = "".join(toml_settings_list)

        return toml_settings
