import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class DependencyInfo:
    def __init__(
        self, name: str, version: str, dist_info_path: Path, dist_info_name: str
    ) -> None:
        self.name: str = name
        self.version: str = version
        self.dist_info_path: Path = dist_info_path
        self.dist_info_name: str = dist_info_name


class ThirdPartyDependencies:
    def __init__(self, site_packages_path: Path) -> None:
        self._site_packages_path: Path = site_packages_path
        self._dependencies_in_env: List[DependencyInfo] = []
        self._dependencies_by_module: Dict[str, DependencyInfo] = {}
        self._load()

    def _load(self) -> None:
        self._parse_dependencies_available_in_env()
        self._parse_modules_from_dependencies_available()

    @property
    def dependencies_in_env(self) -> List[DependencyInfo]:
        return self._dependencies_in_env

    @property
    def dependencies_by_module(self) -> Dict[str, DependencyInfo]:
        return self._dependencies_by_module

    def _parse_dependencies_available_in_env(self) -> None:
        for directory in self._site_packages_path.iterdir():
            directory_name = directory.name
            if directory_name.endswith(".dist-info"):
                # Parse package information from dist-info folder name
                package_details = directory_name.replace(".dist-info", "").split("-")
                if len(package_details) != 2:
                    raise NotImplementedError("Could not Parse Package Details")
                self._dependencies_in_env.append(
                    DependencyInfo(
                        name=package_details[0],
                        version=package_details[1],
                        dist_info_path=directory,
                        dist_info_name=directory_name,
                    )
                )

    def _parse_modules_from_dependencies_available(self) -> None:
        # Directories installed by a package that shouldn't be considered importable modules
        invalid_root_directories = [
            "_pytest",
            "/",
            "..",
            "__pycache__",
            "__pytest",
        ]
        for dependency in self._dependencies_in_env:
            # Parse Record File
            record_file: Path = dependency.dist_info_path / "RECORD"
            if record_file.exists():
                for file_line in open(record_file):
                    file_line = file_line.split(",")[0]
                    path = Path(file_line)
                    root_of_directory = path.parts[0].replace(".py", "")
                    module = self._site_packages_path / root_of_directory
                    if (
                        (module.is_dir() or root_of_directory.endswith(".py"))
                        and not root_of_directory.startswith("_")
                        and root_of_directory not in invalid_root_directories
                        and root_of_directory != dependency.dist_info_name
                        and root_of_directory not in self._dependencies_by_module.keys()
                    ):
                        self._dependencies_by_module[root_of_directory] = dependency
            else:
                logger.warning(
                    f"No RECORD file exists for {dependency.name}=={dependency.version}. Could not link dependency to modules."
                )
