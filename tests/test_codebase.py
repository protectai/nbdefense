import pathlib

import pytest

from nbdefense.codebase import Codebase


class TestCodebase:
    @pytest.fixture
    def path_to_single_notebook(
        self, tmp_path: pathlib.Path, mock_notebook_as_json: str
    ) -> pathlib.Path:
        tmp_file = tmp_path.joinpath("temp.ipynb")
        with open(tmp_file, "w") as f:
            f.write(mock_notebook_as_json)

        return tmp_file

    @pytest.fixture
    def path_with_multiple_notebooks(
        self, tmp_path: pathlib.Path, mock_notebook_as_json: str
    ) -> pathlib.Path:
        paths = ["temp.ipynb", "dir2/temp2.ipynb", "dir3/temp3.ipynb"]
        for path in paths:
            tmp_file = tmp_path.joinpath(path)
            if "/" in path:
                subdir_path = tmp_path.joinpath(path.split("/")[0])
                subdir_path.mkdir(exist_ok=True)
            with open(tmp_file, "w") as f:
                f.write(mock_notebook_as_json)

        return tmp_path

    def test_codebase_single_notebook_file(
        self, path_to_single_notebook: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        # TODO: Add requirements.txt path as well.
        c = Codebase(
            path=path_to_single_notebook,
            recursive=False,
            quiet=True,
            temp_directory=tmp_path,
            requirements_file=None,
            show_progress_bars=False,
        )

        assert c.quiet == True
        assert len(list(c.notebooks())) == 1

    def test_codebase_multiple_notebook_path(
        self, path_with_multiple_notebooks: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        c = Codebase(
            path=path_with_multiple_notebooks,
            recursive=False,
            quiet=True,
            temp_directory=tmp_path,
            requirements_file=None,
            show_progress_bars=False,
        )

        assert len(list(c.notebooks())) == 1

        c = Codebase(
            path=path_with_multiple_notebooks,
            recursive=True,
            quiet=True,
            temp_directory=tmp_path,
            requirements_file=None,
            show_progress_bars=False,
        )

        assert len(list(c.notebooks())) == 3
