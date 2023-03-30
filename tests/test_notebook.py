import pathlib
from typing import Dict, List, Optional

import pandas as pd

from nbdefense.notebook import (
    Cell,
    InputCell,
    InputCellType,
    Notebook,
    OutputCell,
    OutputCellType,
)


class TestNotebookParsing:
    def test_parsing(
        self, mock_notebook: Notebook, raw_notebook_cells: List[Dict[str, List[str]]]
    ) -> None:
        assert len(mock_notebook.input_cells) == len(raw_notebook_cells)
        assert (
            len(mock_notebook.output_cells) == 8
        )  # TODO replace the hard-coded output number

        for index, data in enumerate(raw_notebook_cells):
            cell = mock_notebook.input_cells[index]
            assert type(cell) == InputCell
            if "markdown" in data:
                assert cell.cell_type == InputCellType.MARKDOWN
                markdown_text = data["markdown"]
                assert "\n".join(markdown_text) == str(cell)
            else:
                assert cell.cell_type == InputCellType.SOURCE
                source_text = data["source"]
                assert "\n".join(source_text) == str(cell)

        index = 0
        for data in raw_notebook_cells:
            if "plaintext_output" in data:
                cell = mock_notebook.output_cells[index]
                assert type(cell) == OutputCell
                assert cell.cell_type == OutputCellType.PLAINTEXT
                assert "\n".join(data["plaintext_output"]) == str(cell)
                index = index + 1
            elif "stream_output" in data:
                cell = mock_notebook.output_cells[index]
                assert type(cell) == OutputCell
                assert cell.cell_type == OutputCellType.STREAM
                assert "\n".join(data["stream_output"]) == str(cell)
                index = index + 1
            elif "dataframe_output" in data:
                cell = mock_notebook.output_cells[index]
                assert cell.cell_type == OutputCellType.DATAFRAME
                df: pd.DataFrame = data["dataframe_output"]
                assert [
                    str(elem) for elem in list(df.columns.values)
                ] == cell.data_cells[  # type: ignore[attr-defined]
                    0
                ]
                idx = 0
                for _, row in df.iterrows():
                    assert [str(val) for val in list(row.values)] == cell.data_cells[  # type: ignore[attr-defined]
                        idx + 1
                    ]
                    idx = idx + 1

                index = index + 1

    def test_input_file_line_number_to_cell(
        self, tmp_path: pathlib.Path, mock_notebook: Notebook
    ) -> None:
        tmp_file = tmp_path.joinpath("input_test_file.py")
        with open(tmp_file, "w") as f:
            for cell in mock_notebook.input_cells:
                f.write(str(cell))
                f.write("\n")

        with open(tmp_file, "r") as f:
            for line_number, line in enumerate(f.readlines()):
                line_number = line_number + 1
                found_cell: Optional[
                    Cell
                ] = mock_notebook.get_input_file_line_number_to_cell(line_number)
                assert found_cell
                # Test for the file text is in the cell found at line number
                assert line[:-1] in found_cell.lines

                # Test for the file text at line index within the found cell
                cell_line_index = found_cell.get_cell_line_index_for_file_line_number(
                    line_number
                )
                assert cell_line_index is not None
                assert len(found_cell.lines) > cell_line_index
                assert found_cell.lines[cell_line_index] == line[:-1]

    def test_output_file_line_number_to_cell(
        self, tmp_path: pathlib.Path, mock_notebook: Notebook
    ) -> None:
        tmp_file = tmp_path.joinpath("output_test_file.txt")
        with open(tmp_file, "w") as f:
            for cell in mock_notebook.output_cells:
                f.write(str(cell))
                f.write("\n")

        with open(tmp_file, "r") as f:
            for line_number, line in enumerate(f.readlines()):
                line_number = line_number + 1
                found_cell = mock_notebook.get_output_file_line_number_to_cell(
                    line_number
                )

                # Test for the file text is in the cell found at line number
                assert found_cell
                assert line[:-1] in found_cell.lines

                # Test for the file text at line index within the found cell
                cell_line_index = found_cell.get_cell_line_index_for_file_line_number(
                    line_number
                )
                assert cell_line_index is not None
                assert found_cell.lines[cell_line_index] == line[:-1]
