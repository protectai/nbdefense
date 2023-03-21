"""
This module loads Jinja2 templating engine. 
"""
from pathlib import Path
from typing import Any, Optional, Union

from jinja2 import Environment, FileSystemLoader, PackageLoader, Template


class Jinja2Templates:
    def __init__(
        self, directory: Optional[Union[str, Path]] = None, **env_options: Any
    ) -> None:
        """
        Initialize templating environment.
        """
        self.env = self._create_env(directory, **env_options)

    def _create_env(
        self, directory: Optional[Union[str, Path]] = None, **env_options: Any
    ) -> Environment:
        loader: Union[PackageLoader, FileSystemLoader] = PackageLoader(
            "nbdefense", "templates"
        )
        if directory:
            directory = Path(directory)
            if directory.exists():
                loader = FileSystemLoader(directory)

        env_options.setdefault("loader", loader)
        env_options.setdefault("autoescape", True)

        env = Environment(**env_options)  # nosec
        return env

    def get_template(self, name: str) -> Template:
        """
        Returns a template loaded via templating directory

        :param name: Name of the template e.g. report.html
        """
        return self.env.get_template(name)
