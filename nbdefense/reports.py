"""
This module handles generation of reports from codebase scan.
"""

import abc
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import jinja2

from nbdefense.codebase import Codebase
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import IssueCode
from nbdefense.plugins.plugin import Plugin, ScanTarget
from nbdefense.settings import Settings
from nbdefense.templating import Jinja2Templates
from nbdefense.utils import scrub_html

logger = logging.getLogger(__name__)


class Report(metaclass=abc.ABCMeta):
    """
    Abstract base class for different reporting modules.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def generate(
        codebase: Codebase,
        errors: List[NBDefenseError],
        plugin_list: List[Tuple[Plugin, Settings]],
    ) -> Optional[str]:
        """
        Generate report for the given codebase.
        Derived classes must provide implementation of this method.

        :param codebase: Instance of codebase.

        :param errors: Any errors that occurred during the scan.

        :param plugin_list: List of tuples with the plugin class and the associated settings for the run
        """
        raise NotImplemented


class JsonReport(Report):
    @staticmethod
    def generate(
        codebase: Codebase,
        errors: List[NBDefenseError],
        plugin_list: List[Tuple[Plugin, Settings]],
    ) -> str:
        report = {
            "root": str(codebase.path),
            "root_issues": codebase.issues.to_json(),
            "plugins": [
                {"name": plugin.name(), "settings": settings.to_json(True)}
                for ([plugin, settings]) in plugin_list
            ],
            "notebooks": [str(nb.path) for nb in codebase.notebooks()],
            "notebook_issues": [],
        }

        if errors:
            report["errors"] = [error.to_json() for error in errors]

        for notebook in codebase.notebooks():
            path = notebook.path
            report["notebook_issues"].append(  # type: ignore[attr-defined]
                {"path": str(path), "issues": notebook.issues.to_json()}
            )

        return json.dumps(report)


class HTMLReport(Report):
    @staticmethod
    def generate(
        codebase: Codebase,
        errors: List[NBDefenseError],
        plugin_list: List[Tuple[Plugin, Settings]],
    ) -> Optional[str]:
        # The HTML report is grouped by severity.
        # Todo: Group by severity is included in the issues object,
        # we need to abstract filename to fully migrate. I think
        # this will be easier to do once plugins have been fully refactored.
        issues_by_severity = codebase.issues.group_by_severity()

        # Get notebook issues
        # Todo: Once Notebook Plugins have been refactored to use issues object
        for notebook in codebase.notebooks():
            if not notebook.issues or not len(notebook.issues.all_issues):
                continue

            for issues in notebook.issues.all_issues:
                issues_by_severity[issues.severity.name].append(issues)

        # Get the timestamp
        now = datetime.now()
        date = now.strftime("%b %-d, %Y")
        time = now.strftime("%-I:%M %p")
        templates = Jinja2Templates()
        template = None
        try:
            template = templates.get_template("report.html")
        except jinja2.exceptions.TemplateNotFound as nf:
            logger.error(
                "The report.html template not found. Check the path to template directory."
            )
            return None

        # Calculate Checks Run and get settings
        total_checks_run = 0
        for [plugin, _] in plugin_list:
            scan_target = plugin.scan_target()
            if scan_target == ScanTarget.NOTEBOOKS:
                total_checks_run += len(list(codebase.notebooks()))
            elif scan_target == ScanTarget.DEPENDENCIES:
                total_checks_run += 1
            else:
                errors.append(
                    NBDefenseError(
                        ErrorType.REPORT,
                        plugin.name(),
                        f"The scan target '{scan_target}' has not been implemented",
                    )
                )

        artifacts_scanned: Dict[str, List[str]] = defaultdict(list)
        if codebase.requirements_file_path:
            artifacts_scanned["requirements"].append(
                str(codebase.requirements_file_path.resolve())
            )
        for notebook in codebase.notebooks():
            artifacts_scanned["notebooks"].append(str(notebook.path.resolve()))
        for package in codebase.requirements_file_dependencies:
            artifacts_scanned["packages"].append(f"{package.name}=={package.version}")

        # Calculate codebase root and basename, add separators if directory
        path = codebase.path.resolve()
        base = path.name
        if len(base.split(".ipynb")) < 2:
            base = f"{path.name}{os.sep}"

        def to_pretty_json(value: Any) -> str:
            return json.dumps(value, sort_keys=True, indent=4, separators=(",", ": "))

        template.environment.filters["to_pretty_json"] = to_pretty_json
        template.environment.filters["scrub_html"] = scrub_html

        output = template.render(
            {
                "issues_by_severity": issues_by_severity,
                "codebase_root": f"{path.parent}{os.sep}",
                "codebase_basename": base,
                "total_checks_run": total_checks_run,
                "date": date,
                "time": time,
                "artifacts_scanned": artifacts_scanned,
                "errors": errors,
                "issue_codes": IssueCode,
            }
        )

        return output
