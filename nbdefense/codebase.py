"""
This module provides classes for representing a codebase (e.g github repo) along
with related artifacts within the codebase like notebooks, requirements.txt file, 
and license files.
"""
import logging
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Iterable

import requirements
from tqdm import tqdm

from nbdefense.dependencies import DependencyInfo, ThirdPartyDependencies
from nbdefense.issues import Issue, IssueCode, IssueDetails, Issues, Severity
from nbdefense.notebook import Cell, Notebook

logger = logging.getLogger(__name__)


class DependencyIssue(IssueDetails):
    def __init__(
        self, file_path: Path, name: str, version: Optional[str] = None
    ) -> None:
        super().__init__()
        self.name = name
        self.version = version
        self.file_path = file_path

    def to_json(self) -> Dict[str, str]:
        package_data = {
            "package_name": self.name,
            "file_path": str(self.file_path),
        }
        if self.version:
            package_data["version"] = self.version
        return package_data


class ModuleMetadata:
    def __init__(self, name: str, cell: Cell, cell_line_index: int) -> None:
        """
        Create ModuleMetadata Object

        :param name: imported module name.
        :param cell: The cell where the module was imported.
        :param cell_line_index: The line index of the imported module in the cell.
        """
        self.name = name
        self.cell = cell
        self.cell_line_index = cell_line_index


class PackageInfo:
    def __init__(
        self,
        name: str,
        version: str,
        module_metadata: Optional[ModuleMetadata] = None,
        licenses: List[str] = [],
        dist_info_path: Optional[Path] = None,
    ) -> None:
        """
        Create PackageInfo Object

        :param name: package/distribution name.
        :param version: package/distribution version.
        :param module_metadata: Optionally add module metadata to link imported module to package.
        :param licenses: Optionally add licenses associated with package.
        :param dist_info_path: Optionally, add the path to the distribution info folder fo this package
        """
        self.name = name
        self.version = version
        self.module_metadata = module_metadata
        self.licenses = licenses
        self.dist_info_path = dist_info_path


class NotebookFile(Notebook):
    def __init__(
        self,
        path: Union[str, Path],
        dependencies_in_environment: Dict[str, DependencyInfo] = {},
    ):
        self.path = Path(path)
        self._dependencies_in_environment = dependencies_in_environment
        self._issues = Issues(self.path)
        self._import_regex = re.compile(r"^\s*(?:from|import)\s+\w+")
        self._imported_modules: List[ModuleMetadata] = []
        self._imported_modules_loaded: bool = False
        self._linked_dependencies: List[PackageInfo] = []
        self._linked_dependencies_loaded: bool = False
        super().__init__(self.path.read_text())

    @property
    def issues(self) -> Issues:
        return self._issues

    def _as_file(self, cells: List[Cell]) -> Path:
        temp_file = Path(tempfile.NamedTemporaryFile().name)
        with open(temp_file, "w") as f:
            for cell in cells:
                f.write(str(cell))
                f.write("\n")

        return temp_file

    def as_python_file(self) -> Path:
        return self._as_file(self.input_cells)

    def get_output_text_file(self) -> Path:
        return self._as_file(self.output_cells)

    @property
    def imported_modules_with_cell_and_cell_line(self) -> List[ModuleMetadata]:
        if not self._imported_modules_loaded:
            self._imported_modules_loaded = True
            for cell in self._input_cell_list.cells:
                for cell_line_index, line in enumerate(cell.lines):
                    for match in re.finditer(self._import_regex, line):
                        module_name = (
                            match.group(0)
                            .replace("import", "")
                            .replace("from", "")
                            .replace(" ", "")
                        )
                        self._imported_modules.append(
                            ModuleMetadata(
                                name=module_name,
                                cell=cell,
                                cell_line_index=cell_line_index,
                            )
                        )
        return self._imported_modules

    @property
    def dependencies_linked_to_env(self) -> List[PackageInfo]:
        if not self._linked_dependencies_loaded:
            self._linked_dependencies_loaded = True
            for module in self.imported_modules_with_cell_and_cell_line:
                if module.name in self._dependencies_in_environment:
                    package_data = self._dependencies_in_environment[module.name]
                    self._linked_dependencies.append(
                        PackageInfo(
                            name=package_data.name,
                            version=package_data.version,
                            module_metadata=ModuleMetadata(
                                name=module.name,
                                cell=module.cell,
                                cell_line_index=module.cell_line_index,
                            ),
                            dist_info_path=Path(package_data.dist_info_path),
                        )
                    )
        return self._linked_dependencies


class Codebase:
    """
    Refer to a codebase that could be a github repo
    """

    def __init__(
        self,
        path: Path,
        recursive: bool,
        quiet: bool,
        show_progress_bars: bool,
        temp_directory: Path,
        requirements_file: Optional[Path] = None,
        site_packages_path: Optional[Path] = None,
    ) -> None:
        self.path = path
        self._quiet = quiet
        self._show_progress_bars = show_progress_bars
        self._issues = Issues(self.path)
        self._notebooks: List[NotebookFile] = []
        self.temp_directory = temp_directory
        self._requirements_file_path = requirements_file
        self._requirement_files_loaded: bool = False
        self._requirements_file_dependencies: List[PackageInfo] = []
        self._site_packages_path = site_packages_path
        self._environment_dependencies_by_module: Dict[str, DependencyInfo] = {}

        self._load(recursive)

    def _load(self, recursive: bool) -> None:
        if self._site_packages_path:
            third_party_deps = ThirdPartyDependencies(self._site_packages_path)
            self._environment_dependencies_by_module = (
                third_party_deps.dependencies_by_module
            )

        if self.path.is_dir():
            notebook_search_str = f"{'**/' if recursive else ''}*.ipynb"
            for p in list(self.path.glob(notebook_search_str)):
                self._notebooks.append(
                    NotebookFile(p, self._environment_dependencies_by_module)
                )
        elif self.path.suffix == ".ipynb":
            self._notebooks.append(
                NotebookFile(self.path, self._environment_dependencies_by_module)
            )

    @property
    def issues(self) -> Issues:
        return self._issues

    @property
    def quiet(self) -> bool:
        return self._quiet

    @property
    def requirements_file_path(self) -> Optional[Path]:
        return self._requirements_file_path

    @property
    def requirements_file_dependencies(self) -> List[PackageInfo]:
        if not self._requirement_files_loaded:
            self._requirement_files_loaded = True
            if self._requirements_file_path:
                with open(self._requirements_file_path, "r") as fd:
                    for req in requirements.parse(fd):
                        if req.name:
                            if (
                                req.specs == []
                                or len(req.specs) != 1
                                or req.specs[0][0] != "=="
                            ):
                                logger.warning(
                                    f"Version is not pinned in requirements for package: {req.name}. Package will not be scanned."
                                )
                                self.issues.add_issue(
                                    Issue(
                                        IssueCode.DEPENDENCY_FILE,
                                        Severity.MEDIUM,
                                        DependencyIssue(
                                            self._requirements_file_path, req.name
                                        ),
                                    )
                                )
                            else:
                                self._requirements_file_dependencies.append(
                                    PackageInfo(name=req.name, version=req.specs[0][1])
                                )

        return self._requirements_file_dependencies

    def notebooks(self) -> Iterable[NotebookFile]:
        return tqdm(
            self._notebooks,
            desc="Notebooks",
            leave=False,
            unit="nb",
            dynamic_ncols=True,
            disable=(self._quiet or not self._show_progress_bars),
        )
