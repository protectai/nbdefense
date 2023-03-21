import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich import print
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from nbdefense._version import __version__
from nbdefense.codebase import Codebase
from nbdefense.constants import (
    AVAILABLE_REPORTING_MODULES,
    DEFAULT_REPORTING_MODULE,
    DEFAULT_SETTINGS,
    SCANNING_PLUGINS,
    TEMPDIR,
)
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.plugins.plugin import Plugin, ScanTarget
from nbdefense.settings import Settings


class NBDefense:
    @staticmethod
    def generate_project_settings() -> None:
        pass

    @staticmethod
    def scan(
        root: str,
        recursive: bool,
        quiet: bool,
        requirements_file: Optional[str] = None,
        report_format: Optional[str] = None,
        yes: bool = False,
        temp_directory: Path = Path(TEMPDIR),
        plugins_to_load: List[str] = SCANNING_PLUGINS,
        settings: Dict[str, Any] = DEFAULT_SETTINGS,
        site_packages_path: Optional[str] = None,
        show_progress_bars: bool = False,
    ) -> Any:
        """
        Start a scan

        :param root: The starting point of the scan
        :param recursive: If true, recursively find all notebooks under root path
        :param quiet: Less logging if true
        :param requirements_file:
        :param yes: Automatically answer yes when installing dependencies
        :param temp_directory: Overrides temporary directory used by the scan
        :param license_key: Overrides license key read from the environment
        :param plugins_to_load: Overrides what plugins will be used during the scan.
        """

        if not quiet:
            click.echo(f"Starting scan on {root}")

        root_path = Path(root)
        if not root_path.exists():
            raise ValueError(f"Project root {root_path} does not exist")

        if not temp_directory.exists():
            os.makedirs(temp_directory, exist_ok=True)

        codebase_requirements_file = None
        if not requirements_file:
            # find requirements.txt file at top level
            # Todo: handle multiple requirements files
            reqs = list(root_path.glob("requirements.txt"))
            if len(reqs) == 1:
                codebase_requirements_file = reqs[0]
        if requirements_file:
            codebase_requirements_file = Path(requirements_file)

        # Make sure site packages exists
        converted_site_packages: Optional[Path]
        if site_packages_path:
            converted_site_packages = Path(site_packages_path)
            if (
                not converted_site_packages.exists()
                or not converted_site_packages.is_dir()
            ):
                converted_site_packages = None
        else:
            converted_site_packages = None

        codebase = Codebase(
            root_path,
            recursive,
            quiet,
            show_progress_bars,
            temp_directory,
            codebase_requirements_file,
            converted_site_packages,
        )
        plugin_errors: List[NBDefenseError] = []
        with logging_redirect_tqdm():
            plugin_names = plugins_to_load
            plugin_instances: Dict[str, Plugin] = {}
            for fully_qualified_cls in plugin_names:
                (modulename, classname) = fully_qualified_cls.rsplit(".", 1)
                imported_module = __import__(
                    modulename, globals(), locals(), [classname]
                )
                instance = getattr(imported_module, classname)
                # TODO Dynamically loading class like this is not showing that it is instance
                # of Plugin abstract class (isinstance(instance, Plugin) == False).
                # We need to handle this case. Either figure out why that is the case or
                # before calling `scan` check that the loaded plugin has the
                # scan method with correct signature.
                plugin_instances[fully_qualified_cls] = instance

            # check deps
            plugins_to_run: List[Tuple[Plugin, Settings]] = []
            for plugin_class, plugin in plugin_instances.items():
                is_enabled = settings["plugins"][plugin_class]["enabled"]

                plugin_settings_object = plugin.get_settings(
                    plugin_class, is_enabled, settings
                )
                if (
                    NBDefense._resolve_scan_type(plugin, codebase_requirements_file)
                    and NBDefense._resolve_binary_dependencies(
                        plugin,
                        plugin_errors,
                        yes,
                        quiet,
                        plugin_settings_object,
                    )
                    and plugin_settings_object.is_enabled
                ):
                    plugins_to_run.append((plugin, plugin_settings_object))

            if len(plugins_to_run) == len(plugin_instances) and not quiet:
                print("[green]✔ Dependencies downloaded and installed[/green]")

            plugin_tqdm = tqdm(
                plugins_to_run, disable=(quiet or not show_progress_bars)
            )
            for [plugin, plugin_settings] in plugin_tqdm:
                try:
                    plugin_tqdm.set_description(f"Scanning {root} with {plugin.name()}")
                    plugin_tqdm.refresh()
                    plugin_errors += plugin.scan(codebase, plugin_settings)
                except Exception as e:
                    if not quiet:
                        print(
                            f"[red]{plugin.name()} threw an error while scanning[/red]"
                        )
                    plugin_errors.append(
                        NBDefenseError(ErrorType.SCAN, plugin.name(), str(e))
                    )

        report = ""
        reporting_module = DEFAULT_REPORTING_MODULE or "nbdefense.reports.JsonReport"
        if report_format and report_format in AVAILABLE_REPORTING_MODULES.keys():
            reporting_module = AVAILABLE_REPORTING_MODULES[report_format]

        (modulename, classname) = reporting_module.rsplit(".", 1)
        imported_module = __import__(modulename, globals(), locals(), [classname])
        instance = getattr(imported_module, classname)
        if hasattr(instance, "generate"):
            report = instance.generate(
                codebase=codebase,
                errors=plugin_errors,
                plugin_list=plugins_to_run,
            )
        # TODO Log error message for invalid reporting module

        if not quiet:
            click.echo("Scan succeeded")

        return report

    @staticmethod
    def _resolve_scan_type(
        plugin: Plugin,
        requirements_file: Optional[Path] = None,
    ) -> bool:
        if not requirements_file and plugin.scan_target() == ScanTarget.DEPENDENCIES:
            print(
                f"[yellow]Skipping {plugin.name()} scan as it requires a dependency file[/yellow]"
            )
            return False
        return True

    @staticmethod
    def _resolve_binary_dependencies(
        plugin: Plugin,
        plugin_errors: List[NBDefenseError],
        yes: bool,
        quiet: bool,
        plugin_settings: Optional[Settings],
    ) -> bool:
        try:
            if not plugin.handle_binary_dependencies(quiet, yes, plugin_settings):
                print(
                    f"[yellow]Skipping {plugin.name()} scan as it is missing dependencies[/yellow]"
                )
                plugin_errors.append(
                    NBDefenseError(
                        ErrorType.DEPENDENCY_CHECK,
                        plugin.name(),
                        "Skipped by the user",
                    )
                )
                return False
        except Exception as e:
            if not quiet:
                print(
                    f"[red]Skipping {plugin.name()} scan as it threw an error while handling binary dependencies[/red]"
                )
            plugin_errors.append(
                NBDefenseError(ErrorType.DEPENDENCY_CHECK, plugin.name(), str(e))
            )
            return False
        return True
