from typing import Any, Dict, List, Optional

from rich import print
from rich.prompt import Confirm

from nbdefense.issues import Severity
from nbdefense.plugins.plugin import Plugin
from nbdefense.settings import Settings
from nbdefense.tools import Trivy


class CVEPluginSettings(Settings):
    def __init__(
        self, plugin_class_name: str, is_enabled: bool, overrides: Dict[str, Any]
    ) -> None:
        super().__init__(plugin_class_name, is_enabled, overrides)


class CVEPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def handle_binary_dependencies(
        quiet: bool, yes: bool, settings: Optional[Settings] = None
    ) -> bool:
        initialTrivyBinaryPath = settings.get("trivy_binary_path") if settings else ""
        trivy = Trivy(initialTrivyBinaryPath)
        if not quiet:
            print("Checking for trivy...")
            if not trivy.installed():
                print("trivy not found.")
                if yes:
                    trivy.install()
                else:
                    confirmation = Confirm.ask(
                        "[bold]Do you want to install trivy from https://github.com/aquasecurity/trivy?[/bold]",
                        default=True,
                        show_default=True,
                    )
                    if confirmation:
                        trivy.install()
                    else:
                        return False
            else:
                print("trivy found.")
        else:
            if not trivy.installed():
                trivy.install()
        return trivy.installed()

    @staticmethod
    def get_settings(
        plugin_class_name: str, is_enabled: bool = True, overrides: Dict[str, Any] = {}
    ) -> CVEPluginSettings:
        return CVEPluginSettings(plugin_class_name, is_enabled, overrides)

    @staticmethod
    def vulnerability_severity(vulnerability: Dict[str, Any]) -> Severity:
        if vulnerability["Severity"] == "CRITICAL":
            return Severity.CRITICAL
        if vulnerability["Severity"] == "HIGH":
            return Severity.HIGH
        if vulnerability["Severity"] == "MEDIUM":
            return Severity.MEDIUM
        if vulnerability["Severity"] == "LOW":
            return Severity.LOW
        return Severity.HIGH

    @staticmethod
    def extract_results(trivy_json: Dict[Any, Any]) -> List[Dict[str, Any]]:
        try:
            results = trivy_json.get("Results", [])
            vulnerabilities: List[Dict[str, Any]] = results[0].get(
                "Vulnerabilities", []
            )
            return vulnerabilities
        except IndexError:
            return []
