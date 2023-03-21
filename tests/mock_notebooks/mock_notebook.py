"""
Creates a mock v4 notebook using nbformat
"""
from enum import Enum
from typing import List, Optional

import pandas as pd
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output


class MockCellType(Enum):
    SOURCE = 1
    MARKDOWN = 2


class MockNotebook:
    def __init__(self) -> None:
        self.nb = new_notebook(cells=[])  # type: ignore[no-untyped-call]
        self.current_cell_index = -1

    def add_cell(
        self,
        cell_type: MockCellType,
        source: List[str],
        stream_output: Optional[List[str]] = None,
        data_frame: Optional[pd.DataFrame] = None,
        html_output: Optional[List[str]] = None,
        plaintext_output: Optional[List[str]] = None,
    ) -> None:
        """
        Add a cell to the mock notebook.
        The outputs are add to source cell only. if cell type is markdown all other outputs are ignored.
        The function will add all the outputs to the cell in the order of function arguments.
        DataFrames are added as both html and plain-text format.

        :param cell_type: Type of the cell to add.
        :param source: Source or markdown string(s)
        :param stream_output:
        :param data_frame: Dataframe is converted to html using df.to_html()
        :param html_output:
        :param plaintext_output:
        """
        joined_source = "\n".join(source)

        joined_stream_output: Optional[str] = None
        if stream_output:
            joined_stream_output = "\n".join(stream_output)

        joined_html_output: Optional[str] = None
        if html_output:
            joined_html_output = "\n".join(html_output)

        joined_plaintext_output: Optional[str] = None
        if plaintext_output:
            joined_plaintext_output = "\n".join(plaintext_output)

        if cell_type == MockCellType.MARKDOWN:
            self.nb.cells.append(new_markdown_cell(joined_source))  # type: ignore[no-untyped-call]
            return

        self.nb.cells.append(new_code_cell(source=joined_source))  # type: ignore[no-untyped-call]
        if joined_stream_output:
            self.nb.cells[-1].outputs.append(
                new_output(output_type="stream", text=joined_stream_output)  # type: ignore[no-untyped-call]
            )

        if data_frame is not None:
            self.nb.cells[-1].outputs.append(
                new_output(
                    output_type="execute_result",
                    data={
                        "text/html": data_frame.to_html(),
                        "text/plain": str(data_frame),
                    },
                )  # type: ignore[no-untyped-call]
            )

        if joined_html_output:
            self.nb.cells[-1].outputs.append(
                new_output(
                    output_type="execute_result", data={"text/html": joined_html_output}
                )  # type: ignore[no-untyped-call]
            )

        if joined_plaintext_output:
            self.nb.cells[-1].outputs.append(
                new_output(
                    output_type="execute_result",
                    data={"text/plain": joined_plaintext_output},
                )  # type: ignore[no-untyped-call]
            )

    @property
    def notebook_node(self) -> NotebookNode:
        return self.nb  # type: ignore[no-any-return]
