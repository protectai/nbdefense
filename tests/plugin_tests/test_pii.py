import pathlib
from typing import Any, Dict, List, Tuple

import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine

from nbdefense.codebase import Codebase
from nbdefense.notebook import InputCell, InputCellType
from nbdefense.plugins.pii import DEFAULT_LENGTH, PII, PIIPlugin
from nbdefense.plugins.plugin import ScanTarget
from tests.default_settings import DEFAULT_SETTINGS


class TestPII:
    @pytest.fixture(scope="session", autouse=True)
    def install_dependencies(self) -> None:
        settings = PIIPlugin.get_settings(
            plugin_class_name="nbdefense.plugins.PIIPlugin",
            is_enabled=True,
            settings=DEFAULT_SETTINGS,
        )
        PIIPlugin.handle_binary_dependencies(True, True, settings)

    @pytest.fixture
    def analyzer(self) -> AnalyzerEngine:
        settings = PIIPlugin.get_settings(
            plugin_class_name="nbdefense.plugins.PIIPlugin",
            is_enabled=True,
            settings=DEFAULT_SETTINGS,
        )
        loaded_nlp_engine = SpacyNlpEngine({"en": "en_core_web_trf"})
        pii_analyzer = AnalyzerEngine(nlp_engine=loaded_nlp_engine)
        return pii_analyzer

    @pytest.fixture
    def notebook_file(
        self, tmp_path: pathlib.Path, mock_notebook_as_json: str
    ) -> pathlib.Path:
        tmp_file = tmp_path.joinpath("temp.ipynb")
        with open(tmp_file, "w") as f:
            f.write(mock_notebook_as_json)

        return tmp_file

    @pytest.fixture
    def codebase(self, notebook_file: pathlib.Path, tmp_path: pathlib.Path) -> Codebase:
        return Codebase(notebook_file, False, True, False, tmp_path)

    @pytest.fixture
    def test_cases(self) -> List[str]:
        testcases = [
            "No PII",
            "Short text with single PII in each snippet",
            "Short text with multiple PIIs in one of the snippets",
            "Long text with single PII in each snippet",
            "Long text with multiple PIIs in some of the snippets",
            "PII at the start and end of the text",
        ]
        return testcases

    @pytest.fixture
    def expected_scan_results(
        self, test_cases: List[str]
    ) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
        pii_test_cases_expected_results = {}
        full_text_without_single_quotes = {}
        for test_case in test_cases:
            if test_case == "No PII":
                cell_type = InputCellType.SOURCE
                cell_content = "Hello there I am trying to make this a long string. It is some more more text to add to this string."
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)

                pii_sample_data.summary = {}
                pii_test_cases_expected_results[test_case] = pii_sample_data
                full_text_without_single_quotes[
                    test_case
                ] = "Hello there I am trying to make this a long string. It is some more more text to add to this string."

            elif test_case == "Short text with single PII in each snippet":
                cell_type = InputCellType.SOURCE
                cell_content = "Hello there I am trying to make this a long string. My name is 'John Doe'. It is some more more text to tell you that I live near a place called Houston."
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)

                pii_sample_data.summary = {"PERSON": 1, "LOCATION": 1}
                pii_test_cases_expected_results[test_case] = pii_sample_data
                full_text_without_single_quotes[
                    test_case
                ] = "Hello there I am trying to make this a long string. My name is  John Doe . It is some more more text to tell you that I live near a place called Houston."

            elif test_case == "Short text with multiple PIIs in one of the snippets":
                cell_type = InputCellType.SOURCE
                cell_content = "Hello there I am trying to make this a long string. My name is John Doe. There is one more person called 'Jane Dior'. They live near the cities of Houston and Texas."
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)

                pii_sample_data.summary = {"PERSON": 2, "LOCATION": 2}
                pii_test_cases_expected_results[test_case] = pii_sample_data
                full_text_without_single_quotes[
                    test_case
                ] = "Hello there I am trying to make this a long string. My name is John Doe. There is one more person called  Jane Dior . They live near the cities of Houston and Texas."

            elif test_case == "Long text with single PII in each snippet":
                cell_type = InputCellType.SOURCE
                cell_content = "Hello there I am trying to make this a long string. My name is John Doe. It is some more more text to tell you that I live near a place called Houston. They have lived for a million years. Some more years ago they left leaving an email address john.doe@email.com to contact them on and some belongings. They never came back. The place is still there. This is still a long text."
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)

                pii_sample_data.summary = {
                    "PERSON": 1,
                    "LOCATION": 1,
                    "EMAIL_ADDRESS": 1,
                }
                pii_test_cases_expected_results[test_case] = pii_sample_data

                full_text_without_single_quotes[
                    test_case
                ] = "Hello there I am trying to make this a long string. My name is John Doe. It is some more more text to tell you that I live near a place called Houston. They have lived for a million years. Some more years ago they left leaving an email address john.doe@email.com to contact them on and some belongings. They never came back. The place is still there. This is still a long text."

            elif test_case == "Long text with multiple PIIs in some of the snippets":
                cell_type = InputCellType.SOURCE
                cell_content = "Hello there I am trying to make this a long string. Their names are John Doe and Jane Eyre. It is some more more text to tell you that they live near a place called Houston. They have lived for a million years. Some more years ago they left leaving an email address john.doe@email.com to contact them on and some belongings. They never came back. The place is still there. This is still a long text."
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)

                pii_sample_data.summary = {
                    "PERSON": 2,
                    "LOCATION": 1,
                    "EMAIL_ADDRESS": 1,
                }
                pii_test_cases_expected_results[test_case] = pii_sample_data

                full_text_without_single_quotes[
                    test_case
                ] = "Hello there I am trying to make this a long string. Their names are John Doe and Jane Eyre. It is some more more text to tell you that they live near a place called Houston. They have lived for a million years. Some more years ago they left leaving an email address john.doe@email.com to contact them on and some belongings. They never came back. The place is still there. This is still a long text."

            elif test_case == "PII at the start and end of the text":
                cell_type = InputCellType.SOURCE
                cell_content = "John Doe is the person. It is some more more text to tell you that I live near a place called Houston."
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)
                pii_sample_data.summary = {"PERSON": 1, "LOCATION": 1}
                pii_test_cases_expected_results[test_case] = pii_sample_data

                full_text_without_single_quotes[
                    test_case
                ] = "John Doe is the person. It is some more more text to tell you that I live near a place called Houston."

            else:
                cell_type = InputCellType.SOURCE
                cell_content = ""
                input_cell = InputCell(0, cell_type, cell_content)
                pii_sample_data = PII(input_cell)
                pii_test_cases_expected_results[test_case] = pii_sample_data
                full_text_without_single_quotes[test_case] = ""
        return pii_test_cases_expected_results, full_text_without_single_quotes

    @pytest.fixture
    def pii_scan_results(
        self,
        analyzer: AnalyzerEngine,
        expected_scan_results: List[Dict[str, PII]],
    ) -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
        settings = PIIPlugin.get_settings(
            plugin_class_name="nbdefense.plugins.PIIPlugin",
            is_enabled=True,
            settings=DEFAULT_SETTINGS,
        )
        pii_test_cases_results = {}
        text_without_single_quotes = {}
        pii_test_cases_expected_results, _ = expected_scan_results

        for test_case in pii_test_cases_expected_results:
            pii_data = PII(pii_test_cases_expected_results[test_case].cell)
            text_lines = "\n".join(
                pii_test_cases_expected_results[test_case].cell.lines
            )
            text_without_single_quotes[test_case] = PIIPlugin.remove_single_quotes(
                text_lines
            )
            for line in pii_test_cases_expected_results[test_case].cell.lines:
                results = PIIPlugin.scan_for_pii(line, analyzer, settings.entities())
                if results:
                    pii_data.results.append(results)

            pii_data.summary = PIIPlugin.get_summary_pii(pii_data)

            pii_test_cases_results[test_case] = pii_data

        return pii_test_cases_results, text_without_single_quotes

    def test_plugin_attributes(self) -> None:
        assert PIIPlugin.scan_target() == ScanTarget.NOTEBOOKS
        assert PIIPlugin.name() == "PII Plugin"

    def test_get_text_chunks(self, expected_scan_results: List[Dict[str, Any]]) -> None:
        expected_results, _ = expected_scan_results
        for test_case in expected_results:
            text_lines = expected_results[test_case].cell.lines
            for line in text_lines:
                text_chunks = PIIPlugin.get_text_chunks(line)
                if len(line) < DEFAULT_LENGTH:
                    assert text_chunks == [line]
                else:
                    assert text_chunks == [
                        line[t - DEFAULT_LENGTH : t]
                        for t in range(
                            DEFAULT_LENGTH,
                            len(line) + DEFAULT_LENGTH,
                            DEFAULT_LENGTH,
                        )
                    ]

    def test_remove_single_quotes(
        self,
        expected_scan_results: List[Dict[str, Any]],
        pii_scan_results: List[Dict[str, Any]],
    ) -> None:
        _, text_without_single_quotes = pii_scan_results
        _, expected_text_without_single_quotes = expected_scan_results
        for test_case in text_without_single_quotes:
            assert (
                text_without_single_quotes[test_case]
                == expected_text_without_single_quotes[test_case]
            )

    def test_get_summary_pii(
        self,
        expected_scan_results: List[Dict[str, PII]],
        pii_scan_results: List[Dict[str, PII]],
    ) -> None:
        pii_results, _ = pii_scan_results
        expected_results, _ = expected_scan_results
        for test_case in expected_results:
            assert pii_results[test_case].summary == expected_results[test_case].summary

    def test_redact(self, codebase: Codebase) -> None:
        assert len(list(codebase.notebooks())) == 1

        settings = PIIPlugin.get_settings(
            plugin_class_name="nbdefense.plugins.PIIPlugin",
            is_enabled=True,
            settings=DEFAULT_SETTINGS,
        )
        PIIPlugin.scan(codebase, settings)

        redacted_notebook = list(codebase.notebooks())[0]

        expected_redacted_input_cell = [
            "#id jeff-dean-ner",
            "#caption An example of a sequence annotated with named entities",
            "#hide_input",
            "import pandas as pd",
            'sentence = "[PII] is a computer scientist at Google in California".split()',
            'sentence_labels = ["B-PER", "I-PER", "O", "O", "O", "O", "O", "B-ORG", "O", "B-LOC"]',
            'df = pd.DataFrame(data=[sentence, sentence_labels], index=["Tokens", "Tags"])',
            "df",
        ]

        expected_redacted_output_cell = '<table border="1" class="dataframe">\n  <thead>\n    <tr style="text-align: right;">\n      <th>Index</th>\n      <th>0</th>\n      <th>1</th>\n      <th>2</th>\n      <th>3</th>\n      <th>4</th>\n      <th>5</th>\n      <th>6</th>\n      <th>7</th>\n      <th>8</th>\n      <th>9</th>\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>Tokens</td>\n      <td>[PII]</td>\n      <td>[PII]</td>\n      <td>is</td>\n      <td>a</td>\n      <td>computer</td>\n      <td>scientist</td>\n      <td>at</td>\n      <td>Google</td>\n      <td>in</td>\n      <td>[PII]</td>\n    </tr>\n    <tr>\n      <td>Tags</td>\n      <td>B-PER</td>\n      <td>I-PER</td>\n      <td>O</td>\n      <td>O</td>\n      <td>O</td>\n      <td>O</td>\n      <td>O</td>\n      <td>B-ORG</td>\n      <td>O</td>\n      <td>B-LOC</td>\n    </tr>\n  </tbody>\n</table>'

        assert (
            redacted_notebook.input_cells[12].scrubbed_lines
            == expected_redacted_input_cell
        )

        assert str(redacted_notebook.output_cells[7]) == expected_redacted_output_cell
