import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import lxml.etree  # nosec
import lxml.html  # nosec
import nbformat
import pandas as pd

logger = logging.getLogger(__name__)


class InputCellType(Enum):
    SOURCE = 1
    MARKDOWN = 2


class OutputCellType(Enum):
    STREAM = 1
    PLAINTEXT = 2
    DATAFRAME = 3


class Cell:
    """
    Generic cell type.
    """

    def __init__(self, cell_index: int, cell_type: Enum, content: str) -> None:
        """
        :param cell_index: Index of the notebook cell that contained this cell.
        :param cell_type: Type of the cell.
        :param content: newline separated contents of the cell.
        """
        self.cell_index = cell_index
        self.cell_type = cell_type
        self._file_line_number = 1
        self.lines: List[str] = []
        self.scrubbed_lines: List[str] = []
        if content:
            self.lines = content.split("\n")
            self.scrubbed_lines = self.lines[:]

    @property
    def file_line_number(self) -> int:
        return self._file_line_number

    @file_line_number.setter
    def file_line_number(self, line_number: int) -> None:
        self._file_line_number = line_number

    def get_cell_line_index_for_file_line_number(
        self, line_number: int
    ) -> Optional[int]:
        if (
            line_number >= self._file_line_number
            and line_number <= self._file_line_number + len(self.lines)
        ):
            return line_number - self._file_line_number

        return None

    def to_json(self) -> Dict[str, Any]:
        return {
            "cell_index": self.cell_index,
            "cell_type": self.cell_type.name,
            "scrubbed_content": "\n".join(self.scrubbed_lines),
        }

    def __str__(self) -> str:
        return "\n".join(self.scrubbed_lines)


class InputCell(Cell):
    """
    Input cell
    """

    def __init__(
        self, cell_index: int, input_cell_type: InputCellType, content: str
    ) -> None:
        """
        :param cell_index: Index of the notebook cell that contained this cell.
        :param cell_type: Type of the input cell.
        :param content: newline separated contents of the cell.
        """
        super().__init__(cell_index, input_cell_type, content)


class OutputCell(Cell):
    """
    Output cell
    """

    def __init__(
        self,
        cell_index: int,
        output_index: int,
        output_cell_type: OutputCellType,
        content: str,
    ) -> None:
        """
        :param cell_index: Index of the notebook cell that contained this cell.
        :param cell_type: Type of the cell.
        :param content: newline separated contents of the cell.
        """
        self.output_index = output_index

        super().__init__(cell_index, output_cell_type, content)

    def to_json(self) -> Dict[str, Any]:
        return {**super().to_json(), "output_index": self.output_index}


class DataFrameOutputCell(OutputCell):
    """
    Represent the full data frame within the parsed notebook.
    """

    def __init__(
        self,
        cell_index: int,
        output_index: int,
        html: str,
        data_cells: List[List[Any]],
        plain_text: str,
    ) -> None:
        """
        :param cell_index: Index of the notebook cell
        :param html: Raw html string
        :param data_cells: List of list representation of dataframe.
        :param plain_text: plain text representation of dataframe in the notebook.
        """
        super().__init__(cell_index, output_index, OutputCellType.DATAFRAME, plain_text)
        self.html = html
        self.data_cells = data_cells


class CellList:
    def __init__(self) -> None:
        self._cells: List[Cell] = []
        self._line_number_to_cell: Dict[int, Cell] = {}
        self._line_number: int = 1

    def append(self, cell: Cell) -> None:
        cell.file_line_number = self._line_number
        self._cells.append(cell)
        line_count = len(cell.lines)

        for _ in range(line_count):
            self._line_number_to_cell[self._line_number] = cell
            self._line_number += 1

    def extend(self, cells: List[Cell]) -> None:
        for cell in cells:
            self.append(cell)

    @property
    def cells(self) -> List[Cell]:
        return self._cells

    def get_cell_for_line_number(self, line_number: int) -> Optional[Cell]:
        return self._line_number_to_cell.get(line_number, None)


class Notebook:
    def __init__(self, content: str):
        self._input_cell_list: CellList = CellList()
        self._output_cell_list: CellList = CellList()

        self._parse(content)

    @property
    def input_cells(self) -> List[Cell]:
        return self._input_cell_list.cells

    @property
    def output_cells(self) -> List[Cell]:
        return self._output_cell_list.cells

    def get_input_file_line_number_to_cell(self, line_number: int) -> Optional[Cell]:
        return self._input_cell_list.get_cell_for_line_number(line_number)

    def get_output_file_line_number_to_cell(self, line_number: int) -> Optional[Cell]:
        return self._output_cell_list.get_cell_for_line_number(line_number)

    def _parse(self, content: str) -> None:
        validation_errors: Dict[str, Any] = {}
        nb = None

        try:
            nb = nbformat.reads(  # type: ignore[no-untyped-call]
                content, as_version=4.0, capture_validation_error=validation_errors
            )  # TODO handle multiple versions
        except nbformat.reader.NotJSONError as je:
            logging.warning(je)
            return

        if validation_errors and "ValidationError" in validation_errors:
            logger.warning(validation_errors["ValidationError"].message)

        # TODO: Do we really need to normalize?
        _, nb = nbformat.validator.normalize(nb)

        for cell_idx, cell in enumerate(nb.cells):
            if cell.cell_type == "code":
                self._input_cell_list.append(
                    InputCell(cell_idx, InputCellType.SOURCE, cell.source)
                )
            elif cell.cell_type == "markdown":
                self._input_cell_list.append(
                    InputCell(cell_idx, InputCellType.MARKDOWN, cell.source)
                )

            if "outputs" in cell:
                self._parse_outputs(cell_idx, cell.outputs)

    def _parse_outputs(self, cell_index: int, outputs: Dict[Any, Any]) -> None:
        for index, output in enumerate(outputs):
            if output.output_type == "stream" and output.text:
                self._output_cell_list.append(
                    OutputCell(cell_index, index, OutputCellType.STREAM, output.text)
                )

            if (
                output.output_type == "display_data"
                or output.output_type == "execute_result"
            ):
                if "data" in output:
                    output_cells = self._parse_mime(cell_index, index, output.data)
                    if output_cells:
                        self._output_cell_list.extend(output_cells)

    def _check_html_for_table(self, html_text: Optional[str] = None) -> bool:
        if not html_text:
            return False

        try:
            root = lxml.html.fromstring(html_text)
            if root is None:
                return False
            if root.xpath("//table"):
                return True
        except lxml.etree.ParseError as pe:
            logger.warning(pe)
        except lxml.etree.ParserError as pre:
            logger.warning(pre)

        return False

    def _parse_mime(
        self, cell_index: int, output_index: int, mime_dict: Dict[Any, Any]
    ) -> List[Cell]:
        cells: List[Cell] = []
        if "text/html" in mime_dict:
            data_cells = None
            if self._check_html_for_table(mime_dict["text/html"]):
                try:
                    df: List[pd.DataFrame] = pd.read_html(
                        mime_dict["text/html"], header=0, index_col=0
                    )
                    if df and df[0] is not None:
                        dataframe = df[0]  # TODO handle multiple parsed data frames.
                        data_cells = [list(dataframe.columns.values)]
                        for _, row in dataframe.iterrows():
                            data_cells.append([str(val) for val in list(row.values)])
                except ValueError as ve:
                    logger.warning(ve)

            if data_cells:
                cells.append(
                    DataFrameOutputCell(
                        cell_index,
                        output_index,
                        mime_dict["text/html"],
                        data_cells,
                        mime_dict["text/plain"] if "text/plain" in mime_dict else "",
                    )
                )
                # DataFrame has both html and text mime types, we delete one redundant representation.
                mime_dict.pop("text/plain")

        if "text/plain" in mime_dict:
            text = mime_dict["text/plain"]
            cells.append(
                OutputCell(cell_index, output_index, OutputCellType.PLAINTEXT, text)
            )

        return cells
