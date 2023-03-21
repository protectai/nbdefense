from __future__ import absolute_import

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import SpacyNlpEngine

from nbdefense.codebase import Codebase
from nbdefense.errors import ErrorType, NBDefenseError
from nbdefense.issues import (
    AggregateIssue,
    CellIssue,
    DataframeCellIssue,
    IssueBlock,
    IssueCode,
    Issues,
    LineCellIssue,
    Severity,
)
from nbdefense.notebook import Cell, DataFrameOutputCell, OutputCellType
from nbdefense.plugins.plugin import Plugin, ScanTarget
from nbdefense.settings import Settings
from nbdefense.notebook import Cell, OutputCellType

from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer import RecognizerResult

import re
import os
import pandas as pd


logger = logging.getLogger(__name__)

DEFAULT_LENGTH = 512  # spaCy's transformer model gives a warning if the length of the string is greater than 512.


class PIIPluginSettings(Settings):
    def __init__(
        self,
        plugin_class_name: str,
        is_enabled: bool = True,
        settings: Dict[str, Any] = {},
    ) -> None:
        super().__init__(plugin_class_name, is_enabled, settings)

    def entities(self) -> Dict[str, float]:
        pii_entities = {}
        confidence_threshold = self.get("confidence_threshold")
        settings_entities = self.get("entities")
        for entity in settings_entities:
            if settings_entities[entity]:
                pii_entities[entity] = confidence_threshold
        return pii_entities


class PII:
    def __init__(self, cell: Cell) -> None:
        self.cell = cell
        self.summary: Dict[str, int] = {}
        self.results: List[List[RecognizerResult]] = []
        self.all_line_issues_for_cell: List[CellIssue] = []

        """
        Create a PII object 

        :param cell: Notebook cell.
        :param summary: A dictionary for the type of PII and their respective counts.
        :param results: A list of PII analysis results that contains information on 'entity_type', character 'start', and 'end' of where PII is found, and confidence 'score'.
        :param all_line_issues_for_cell: A list of issues found in the cell.
        """


class PIIPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def scan_target() -> ScanTarget:
        return ScanTarget.NOTEBOOKS

    @staticmethod
    def name() -> str:
        return "PII Plugin"

    @staticmethod
    def get_settings(
        plugin_class_name: str, is_enabled: bool = True, settings: Dict[str, Any] = {}
    ) -> PIIPluginSettings:
        return PIIPluginSettings(plugin_class_name, is_enabled, settings)

    @staticmethod
    def redact(codebase: Codebase, settings: Optional[Settings] = None) -> None:
        for notebook in codebase.notebooks():
            for issue in notebook.issues.all_issues:
                if issue.code == IssueCode.PII_FOUND and isinstance(
                    issue, AggregateIssue
                ):
                    PIIPlugin._redact(issue)

    @staticmethod
    def get_redacted_text(all_issues_on_one_line: List[Any], text: str) -> str:
        redacted_value = "[PII]"
        redaction_dictionary = {}
        for single_issue in all_issues_on_one_line:
            text_to_redact = text[
                single_issue.character_start_index : single_issue.character_end_index
            ]
            text_to_substitute = redacted_value
            redaction_dictionary[text_to_redact] = text_to_substitute

        redacted_text = text
        for key, value in redaction_dictionary.items():
            redacted_text = re.sub(re.escape(key), value, redacted_text)

        return redacted_text

    @staticmethod
    def get_issues_in_same_dataframe_cell(
        all_issues: List[DataframeCellIssue],
    ) -> Dict[Tuple[int, int], Any]:
        issues_in_same_cell = {}

        for issue in all_issues:
            row_and_column = (issue.row_index, issue.column_index)
            if row_and_column not in issues_in_same_cell:
                issues_in_same_cell[row_and_column] = [
                    issue_index
                    for issue_index, issue in enumerate(all_issues)
                    if (issue.row_index, issue.column_index) == row_and_column
                ]

        return issues_in_same_cell

    @staticmethod
    def _redact(issue: AggregateIssue) -> None:
        all_issues = issue.issues

        if isinstance(issue.cell, DataFrameOutputCell):
            dataframe_to_redact = pd.read_html(issue.cell.html)[0]
            all_data_cells = issue.cell.data_cells

            filtered_dataframe_output_cells: List[DataframeCellIssue] = list(filter(lambda issue: isinstance(issue, DataframeCellIssue), all_issues))  # type: ignore[arg-type]

            issues_in_same_cell = PIIPlugin.get_issues_in_same_dataframe_cell(
                filtered_dataframe_output_cells
            )

            dataframe_cells_already_redacted = []

            for sub_issue in filtered_dataframe_output_cells:
                dataframe_cell_indices_with_issue = (
                    sub_issue.row_index,
                    sub_issue.column_index,
                )

                if (
                    dataframe_cell_indices_with_issue
                    not in dataframe_cells_already_redacted
                ):
                    dataframe_cells_already_redacted.append(
                        dataframe_cell_indices_with_issue
                    )

                    issue_indices_in_cell = issues_in_same_cell[
                        dataframe_cell_indices_with_issue
                    ]
                    issues_in_cell = [
                        all_issues[index] for index in issue_indices_in_cell
                    ]

                    text = all_data_cells[sub_issue.row_index][sub_issue.column_index]
                    redacted_text = PIIPlugin.get_redacted_text(issues_in_cell, text)
                    # The sub_issue.row_index and sub_issue.columnn_index are adjusted to match the row and column index of dataframe
                    dataframe_to_redact.iloc[
                        sub_issue.row_index - 1, sub_issue.column_index + 1
                    ] = redacted_text

            # Change column name from Unnamed:0 to Index
            dataframe_to_redact.rename(columns={"Unnamed: 0": "Index"}, inplace=True)
            issue.cell.scrubbed_lines = [dataframe_to_redact.to_html(index=False)]

        else:
            all_lines = issue.cell.lines
            redacted_cell_text: List[str] = []

            for line_index, line in enumerate(all_lines):
                issues_on_same_line = [
                    issue
                    for issue in all_issues
                    if hasattr(issue, "line_index") and issue.line_index == line_index
                ]
                if issues_on_same_line:
                    redacted_text = PIIPlugin.get_redacted_text(
                        issues_on_same_line, line
                    )
                else:
                    redacted_text = line

                redacted_cell_text.append(redacted_text)
            issue.cell.scrubbed_lines = redacted_cell_text

    @staticmethod
    def get_summary_pii(pii_scan_results: PII) -> Dict[str, int]:
        all_results = [l for sublist in pii_scan_results.results for l in sublist]

        summary_stats = {}
        for result in all_results:
            if result.entity_type not in summary_stats:
                entity = result.entity_type
                summary_stats[entity] = sum(
                    [1 for res in all_results if res.entity_type == entity]
                )

        non_zero_summary_stats = {
            entity: count for entity, count in summary_stats.items() if count != 0
        }
        return non_zero_summary_stats

    @staticmethod
    def remove_single_quotes(text: str) -> str:
        text_without_single_quotes = text.replace("'", " ")
        return text_without_single_quotes

    @staticmethod
    def scan_for_pii(
        text: str, analyzer: AnalyzerEngine, entities: Dict[str, float]
    ) -> List[RecognizerResult]:
        text_without_single_quotes = PIIPlugin.remove_single_quotes(text)
        results = analyzer.analyze(
            text=text_without_single_quotes,
            entities=list(entities.keys()),
            language="en",
        )
        if results:
            significant_results = [
                result
                for result in results
                if result.score >= entities[result.entity_type]
            ]
        else:
            significant_results = []

        return significant_results

    @staticmethod
    def get_text_chunks(full_text: str) -> List[str]:
        if len(full_text) > DEFAULT_LENGTH:
            text_chunks = [
                full_text[t - DEFAULT_LENGTH : t]
                for t in range(
                    DEFAULT_LENGTH,
                    len(full_text) + DEFAULT_LENGTH,
                    DEFAULT_LENGTH,
                )
            ]
        else:
            text_chunks = [full_text]

        return text_chunks

    @staticmethod
    def get_results_startandend_indices_adjusted(
        results: List[RecognizerResult], text_chunk_index: int
    ) -> List[RecognizerResult]:
        new_results = results
        for result in new_results:
            result.start = result.start + text_chunk_index * DEFAULT_LENGTH
            result.end = result.end + text_chunk_index * DEFAULT_LENGTH
        return new_results

    @staticmethod
    def scan_pii_in_text(
        cell: Cell, analyzer: AnalyzerEngine, settings_entities: Dict[str, float]
    ) -> PII:

        pii_scan_results = PII(cell)

        for line_index, line in enumerate(pii_scan_results.cell.lines):
            if line:
                text_chunks = PIIPlugin.get_text_chunks(line)
                for text_chunk_index, text in enumerate(text_chunks):
                    results = PIIPlugin.scan_for_pii(text, analyzer, settings_entities)
                    if results:
                        if text_chunk_index > 0:
                            results_adjusted = (
                                PIIPlugin.get_results_startandend_indices_adjusted(
                                    results, text_chunk_index
                                )
                            )
                            pii_scan_results.results.append(results_adjusted)

                        else:
                            pii_scan_results.results.append(results)

                        for result in results:
                            PIIPlugin.add_line_cell_issue(
                                result, pii_scan_results, line_index
                            )

        return pii_scan_results

    @staticmethod
    def scan_pii_in_dataframes(
        cell: DataFrameOutputCell, analyzer: AnalyzerEngine, entities: Dict[str, float]
    ) -> PII:

        pii_scan_results = PII(cell)

        for row_index, row in enumerate(cell.data_cells):
            if row:
                for column_index, column in enumerate(row):
                    results = PIIPlugin.scan_for_pii(column, analyzer, entities)
                    if results:
                        pii_scan_results.results.append(results)

                        for result in results:
                            PIIPlugin.add_dataframe_cell_issue(
                                result, pii_scan_results, row_index, column_index
                            )
        return pii_scan_results

    @staticmethod
    def add_line_cell_issue(
        result: RecognizerResult, pii_results: PII, line_number: int
    ) -> None:
        line_cell_issue = LineCellIssue(
            code=IssueCode.PII_FOUND,
            severity=Severity.HIGH,
            cell=pii_results.cell,
            line_index=line_number,
            character_start_index=result.start,
            character_end_index=result.end,
        )

        pii_results.all_line_issues_for_cell.append(line_cell_issue)

    @staticmethod
    def add_dataframe_cell_issue(
        result: RecognizerResult, pii_results: PII, row_index: int, column_index: int
    ) -> None:
        dataframe_cell_issue = DataframeCellIssue(
            code=IssueCode.PII_FOUND,
            severity=Severity.HIGH,
            cell=pii_results.cell,
            row_index=row_index,
            column_index=column_index,
            character_start_index=result.start,
            character_end_index=result.end,
        )

        pii_results.all_line_issues_for_cell.append(dataframe_cell_issue)

    @staticmethod
    def add_aggregate_cell_issue(issues: Issues, pii_results: PII) -> None:
        all_issues = pii_results.all_line_issues_for_cell
        pii_results.summary = PIIPlugin.get_summary_pii(pii_results)
        cell_issue = AggregateIssue(
            code=IssueCode.PII_FOUND,
            severity=max([issue.severity for issue in all_issues]),
            cell=pii_results.cell,
            issues=all_issues,
            details=IssueBlock(
                file_path=str(issues.path),
                description=f"A total of {sum(pii_results.summary.values())} PII found in cell number {pii_results.cell.cell_index}",
                summary_field=pii_results.summary,
            ),
        )
        issues.add_issue(cell_issue)

    @staticmethod
    def scan(codebase: Codebase, settings: PIIPluginSettings) -> List[NBDefenseError]:  # type: ignore[override]
        if codebase.quiet:
            logger.setLevel(logging.CRITICAL)
        os.environ[
            "TOKENIZERS_PARALLELISM"
        ] = "false"  # Disables huggingface/tokenizers warning

        settings_entities = settings.entities()
        if not settings_entities:
            logger.warning(f"Skipping PII scan because no entities are enabled")
            return [
                NBDefenseError(
                    ErrorType.SCAN,
                    PIIPlugin.name(),
                    "PII scans were skipped because no entities were enabled.",
                )
            ]

        analyzer = AnalyzerEngine(nlp_engine=SpacyNlpEngine({"en": "en_core_web_trf"}))

        notebooks = codebase.notebooks()

        notebook_scan_errors: List[NBDefenseError] = []

        for notebook in notebooks:
            try:
                notebooks.set_description(f"Scanning notebook: {notebook.path}")  # type: ignore[attr-defined]

                for cell in notebook.input_cells:
                    pii_results = PIIPlugin.scan_pii_in_text(
                        cell, analyzer, settings_entities
                    )
                    if len(pii_results.all_line_issues_for_cell) > 0:
                        PIIPlugin.add_aggregate_cell_issue(notebook.issues, pii_results)

                for cell in notebook.output_cells:
                    if (
                        cell.cell_type == OutputCellType.PLAINTEXT
                        or cell.cell_type == OutputCellType.STREAM
                    ):
                        pii_results = PIIPlugin.scan_pii_in_text(
                            cell, analyzer, settings_entities
                        )
                        if len(pii_results.all_line_issues_for_cell) > 0:
                            PIIPlugin.add_aggregate_cell_issue(
                                notebook.issues, pii_results
                            )

                    if isinstance(cell, DataFrameOutputCell):
                        pii_results = PIIPlugin.scan_pii_in_dataframes(
                            cell, analyzer, settings_entities
                        )

                        if len(pii_results.all_line_issues_for_cell) > 0:
                            PIIPlugin.add_aggregate_cell_issue(
                                notebook.issues, pii_results
                            )

                logger.warning(
                    f"PII found in {len(list(filter(lambda issue: issue.code == IssueCode.PII_FOUND, notebook.issues.all_issues)))} cell(s) in {notebook.path}"
                )

            except Exception as error:
                logger.warning(
                    f"Skipping PII scan for notebook {notebook.path} because of the following error: {str(error)}"
                )
                notebook_scan_errors.append(
                    NBDefenseError(
                        ErrorType.SCAN,
                        PIIPlugin.name(),
                        f"PII scan for notebook {notebook.path} was skipped because of the following error: {str(error)}",
                    )
                )

        PIIPlugin.redact(codebase)

        return notebook_scan_errors
