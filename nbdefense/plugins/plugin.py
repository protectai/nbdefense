import abc
from enum import Enum
from typing import Any, Dict, List, Optional

from nbdefense.codebase import Codebase
from nbdefense.errors import NBDefenseError
from nbdefense.settings import Settings


class ScanTarget(Enum):
    NOTEBOOKS = 1
    DEPENDENCIES = 2


class Plugin(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        pass

    @staticmethod
    def handle_binary_dependencies(
        quiet: bool, yes: bool, settings: Optional[Settings] = None
    ) -> bool:
        """
        Implement this method if the plugin requires a binary dependency.
        It should perform the following actions:

        1. Check if the dependency is installed
        2. Prompt the user to install the dependency if it is not installed

        :param quiet: Whether or not to suppress output (Prompts should resolve with the default option)
        :param yes: When True, all user prompts should be assumed yes

        :returns:
            True if there are no dependencies or if they are all installed;
            False if the install failed or the user declines to install the dependency
        """
        return True

    @staticmethod
    @abc.abstractmethod
    def scan_target() -> ScanTarget:
        """
        Implement this method for all plugins.

        This method should return a scan target for each plugin.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def name() -> str:
        """
        Implement this method for all plugins.

        This method should return a readable name for each plugin.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_settings(
        plugin_class_name: str, is_enabled: bool = True, settings: Dict[str, Any] = {}
    ) -> Settings:
        """
        Implement this method for all plugins.

        This method should return a settings object for the plugin
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def scan(codebase: Codebase, settings: Settings) -> List[NBDefenseError]:
        """
        Implement this method for all plugins.

        This method should handle the main scan logic of that plugin.

        :param codebase: The codebase instance that holds issues at repo and notebook level.
        :param settings: The settings object for the plugin

        :returns: A list of the errors that occurred during the scan.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def redact(codebase: Codebase, settings: Optional[Settings] = None) -> None:
        """
        Implement this method for all plugins.

        This method should perform any necessary redaction on detected sensitive data.

        :param cb: The codebase instance that holds issues at repo and notebook level.
        """
        raise NotImplemented
