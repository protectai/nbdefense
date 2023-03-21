from enum import Enum
from typing import Any, Dict, Optional


class ErrorType(Enum):
    # Error occurred in the handle_binary_dependencies method
    DEPENDENCY_CHECK = "dependency check"
    # Error occurred in the scan method
    SCAN = "scan"
    # Error occurred in the report generation
    REPORT = "report generation"


class NBDefenseError:
    error_type: ErrorType
    plugin_name: str
    message: Optional[str]

    def __init__(
        self, error_type: ErrorType, plugin_name: str, message: Optional[str] = None
    ) -> None:
        self.error_type = error_type
        self.plugin_name = plugin_name
        self.message = message if message else "None"

    def __str__(self) -> str:
        return f"Error occurred in the {self.error_type.value} portion for the {self.plugin_name} plugin with the message: {self.message}"

    def to_json(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.name,
            "plugin_name": self.plugin_name,
            "message": self.message,
        }
