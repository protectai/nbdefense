from typing import Dict, List, Union

import pandas as pd
import pytest
from nbformat import writes

from nbdefense.notebook import Notebook
from tests.mock_notebooks.mock_notebook import MockCellType, MockNotebook


@pytest.fixture
def dataframe() -> pd.DataFrame:
    data = {
        "numeric_column": list(range(1, 8)),
        "string_column": [f"test{i}" for i in range(1, 8)],
        "bool_column": [True for i in range(1, 8)],
    }

    return pd.DataFrame(data)


@pytest.fixture
def dataframe_with_secrets() -> pd.DataFrame:
    data = {
        "numeric_column": list(range(1, 3)),
        "secrets_column": [
            'aws_access_key_id="FGIAT45YKIPFLT4TXP9F"',
            'aws_secret_access_key="GKic7s/y/Hu5Jahq5Fx1NJaXnhgbFhF7EdOm1894"',
        ],
    }

    return pd.DataFrame(data)


@pytest.fixture
def dataframe_with_custom_index() -> pd.DataFrame:
    tokens = "Jeff Dean is a computer scientist at Google in California".split()
    labels = ["B-PER", "I-PER", "O", "O", "O", "O", "O", "B-ORG", "O", "B-LOC"]

    return pd.DataFrame(data=[tokens, labels], index=["Tokens", "Tags"])


@pytest.fixture
def raw_notebook_cells(
    dataframe: pd.DataFrame,
    dataframe_with_secrets: pd.DataFrame,
    dataframe_with_custom_index: pd.DataFrame,
) -> List[Dict[str, Union[List[str], pd.DataFrame]]]:
    cells: List[Dict[str, Union[List[str], pd.DataFrame]]] = [
        {
            "markdown": [
                "# Heading1",
                "## Heading 2",
            ]
        },
        {"source": ["import module1", "import module2"]},
        {
            "source": [
                "def sum():",
                "\tvar1 = 10",
                "\tvar2 = 20",
                "test3 = test1 + test2",
                "test3",
            ],
            "plaintext_output": ["30"],
        },
        {
            "source": [
                'text = "This is just a line of text\\n.This is another line of text"',
                "text",
            ],
            "plaintext_output": [
                "This is just a line of text\\n.This is another line of text"
            ],
        },
        {"markdown": ["### Heading 3", "some text here"]},
        {
            "source": ["pip install somepackage"],
            "stream_output": [
                "Installing 1",
                "Installing 2",
                "Installing 3",
            ],
        },
        {
            "source": [
                "import boto3",
                "client = boto3.client('s3',",
                '\taws_access_key_id="AKIAT45YKIPFLT4TXP6C",',
                '\taws_secret_access_key="W/ic7s/y/Hu5Jahq5Fx1NJaXnhgbFhF7EdOm18py")',
                "client.upload_file('sample_data.csv', 'mybucket', 'sample_data.csv')",
            ],
        },
        {
            "source": ["!cat /etc/secrets"],
            "stream_output": [
                'aws_access_key_id="AKIAT45YKIPFLT4TXP6C"',
                'aws_secret_access_key="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"',
            ],
        },
        {
            "source": ['df = pd.read_csv("myfile.csv")', "df.head()"],
            "dataframe_output": dataframe.head(),
        },
        {"source": ["a = 5"]},
        {
            "source": ["df.head()"],
            "dataframe_output": dataframe.head(),
        },
        {
            "source": ['df = pd.read_csv("secrets.csv")', "df.head()"],
            "dataframe_output": dataframe_with_secrets.head(),
        },
        {
            "source": [
                "#id jeff-dean-ner",
                "#caption An example of a sequence annotated with named entities",
                "#hide_input",
                "import pandas as pd",
                'sentence = "Jeff Dean is a computer scientist at Google in California".split()',
                'sentence_labels = ["B-PER", "I-PER", "O", "O", "O", "O", "O", "B-ORG", "O", "B-LOC"]',
                'df = pd.DataFrame(data=[sentence, sentence_labels], index=["Tokens", "Tags"])',
                "df",
            ],
            "dataframe_output": dataframe_with_custom_index,
        },
    ]

    return cells


@pytest.fixture
def mock_notebook_as_json(raw_notebook_cells: List[Dict[str, List[str]]]) -> str:
    mock_nb = MockNotebook()
    for cell in raw_notebook_cells:
        if "markdown" in cell:
            mock_nb.add_cell(cell_type=MockCellType.MARKDOWN, source=cell["markdown"])
        elif "source" in cell:
            if "plaintext_output" in cell:
                mock_nb.add_cell(
                    cell_type=MockCellType.SOURCE,
                    source=cell["source"],
                    plaintext_output=cell["plaintext_output"],
                )
            elif "stream_output" in cell:
                mock_nb.add_cell(
                    cell_type=MockCellType.SOURCE,
                    source=cell["source"],
                    stream_output=cell["stream_output"],
                )
            elif "dataframe_output" in cell:
                mock_nb.add_cell(
                    cell_type=MockCellType.SOURCE,
                    source=cell["source"],
                    data_frame=cell["dataframe_output"],
                )
            else:
                mock_nb.add_cell(cell_type=MockCellType.SOURCE, source=cell["source"])
    return writes(mock_nb.notebook_node)  # type: ignore[no-any-return,no-untyped-call]


@pytest.fixture
def mock_notebook(mock_notebook_as_json: str) -> Notebook:
    return Notebook(mock_notebook_as_json)
