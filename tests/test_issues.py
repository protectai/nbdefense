from pathlib import Path
from typing import Dict, List

import pytest

from nbdefense.issues import (
    AggregateIssue,
    CellIssue,
    DataframeCellIssue,
    Issue,
    IssueBlock,
    IssueCode,
    Issues,
    LineCellIssue,
    Severity,
)
from nbdefense.notebook import InputCell, InputCellType


class TestIssues:
    @pytest.fixture
    def input_cell(self) -> InputCell:
        return InputCell(1, InputCellType.SOURCE, "Cell Content")

    @pytest.fixture
    def multi_line_input_cell(self) -> InputCell:
        return InputCell(
            1,
            InputCellType.SOURCE,
            "Line text with an issue.\nLine text with more issues.\nA new line with an issue.",
        )

    @pytest.fixture
    def issue_block(self) -> IssueBlock:
        return IssueBlock(description="test")

    @pytest.fixture
    def issues(self, issue_block: IssueBlock, input_cell: InputCell) -> Issues:
        issues = Issues(Path("/path/to"))
        issues.add_issue(
            issue=CellIssue(
                code=IssueCode.SECRETS,
                severity=Severity.HIGH,
                cell=input_cell,
                details=issue_block,
            )
        )
        issues.add_issue(
            issue=DataframeCellIssue(
                code=IssueCode.UNAPPROVED_LICENSE_DEP_FILE,
                severity=Severity.LOW,
                cell=input_cell,
                column_index=1,
                row_index=2,
                character_start_index=2,
                character_end_index=3,
                details=issue_block,
            )
        )
        return issues

    def test_issue_block(self) -> None:
        description: str = "Test Description"
        summary_field: Dict[str, str] = {"key": "value1"}

        issue_block = IssueBlock(
            description=description,
            summary_field=summary_field,
        )

        assert issue_block.to_json() == {
            "description": description,
            "summary_field": summary_field,
        }

    def test_issue_block_json_fields(self) -> None:
        json_fields = ["description"]

        issue_data = {
            "description": "Test Description",
        }

        issue_block = IssueBlock(
            description=issue_data["description"],
            json_fields=json_fields,
            summary_field={"Key": "value"},
        )

        assert issue_block.to_json() == issue_data

    def test_issue(self, issue_block: IssueBlock) -> None:
        json_response = {
            "code": IssueCode.SECRETS.name,
            "severity": Severity.HIGH.name,
            "details": issue_block.to_json(),
        }

        issue = Issue(
            code=IssueCode.SECRETS, severity=Severity.HIGH, details=issue_block
        )

        assert issue.to_json() == json_response

    def test_cell_issue(self, issue_block: IssueBlock, input_cell: InputCell) -> None:
        json_response = {
            "code": IssueCode.SECRETS.name,
            "severity": Severity.HIGH.name,
            "location": "INPUT",
            "cell": input_cell.to_json(),
            "details": issue_block.to_json(),
        }

        issue = CellIssue(
            code=IssueCode.SECRETS,
            severity=Severity.HIGH,
            cell=input_cell,
            details=issue_block,
        )

        assert issue.to_json() == json_response

    def test_line_cell_issue(
        self, issue_block: IssueBlock, input_cell: InputCell
    ) -> None:
        line_index = 1
        character_start_index = 2
        character_end_index = 3

        json_response = {
            "code": IssueCode.SECRETS.name,
            "severity": Severity.HIGH.name,
            "details": issue_block.to_json(),
            "cell": input_cell.to_json(),
            "location": "INPUT",
            "line_index": line_index,
            "character_start_index": character_start_index,
            "character_end_index": character_end_index,
        }

        issue = LineCellIssue(
            code=IssueCode.SECRETS,
            severity=Severity.HIGH,
            cell=input_cell,
            line_index=line_index,
            character_start_index=character_start_index,
            character_end_index=character_end_index,
            details=issue_block,
        )

        assert issue.to_json() == json_response

    def test_data_frame_cell_issue(
        self, issue_block: IssueBlock, input_cell: InputCell
    ) -> None:
        column_index = 1
        row_index = 2
        character_start_index = 2
        character_end_index = 3

        json_response = {
            "code": IssueCode.SECRETS.name,
            "severity": Severity.HIGH.name,
            "cell": input_cell.to_json(),
            "details": issue_block.to_json(),
            "column_index": column_index,
            "row_index": row_index,
            "character_start_index": character_start_index,
            "character_end_index": character_end_index,
            "location": "INPUT",
        }

        issue = DataframeCellIssue(
            code=IssueCode.SECRETS,
            severity=Severity.HIGH,
            cell=input_cell,
            column_index=column_index,
            row_index=row_index,
            character_start_index=character_start_index,
            character_end_index=character_end_index,
            details=issue_block,
        )

        assert issue.to_json() == json_response

    def test_aggregate_issue(
        self, issue_block: IssueBlock, multi_line_input_cell: InputCell
    ) -> None:
        # Create some in-line issues.
        issues_lines_slices = [slice(2, 8), slice(4, 10), slice(3, 12)]

        issues: List[CellIssue] = []
        expected_scrubbed_cell_content = []
        for line_index, issue_slice in enumerate(issues_lines_slices):
            # Modify the cell scrubbed content for each issue.
            original_text = multi_line_input_cell.lines[line_index]
            multi_line_input_cell.scrubbed_lines[
                line_index
            ] = f"{original_text[0:issue_slice.start]}*{original_text[issue_slice.stop:]}"
            expected_scrubbed_cell_content.append(
                multi_line_input_cell.scrubbed_lines[line_index]
            )

            single_line_issue = LineCellIssue(
                code=IssueCode.SECRETS,
                severity=Severity.HIGH,
                cell=multi_line_input_cell,
                line_index=line_index,
                character_start_index=issue_slice.start,
                character_end_index=issue_slice.stop,
                details=issue_block,
            )

            issues.append(single_line_issue)

        summary_issue_block = IssueBlock(
            description="Found 3 issues in the cell",
            summary_field={"Simple Secret": "1", "Simple Secret 2": 2},
        )

        aggregate_issue = AggregateIssue(
            code=IssueCode.SECRETS,
            severity=max([issue.severity for issue in issues]),
            cell=multi_line_input_cell,
            issues=issues,
            details=summary_issue_block,
        )

        aggregate_json_response = {
            "cell": {
                "cell_index": multi_line_input_cell.cell_index,
                "cell_type": multi_line_input_cell.cell_type.name,
                "scrubbed_content": "\n".join(expected_scrubbed_cell_content),
            },
            "code": IssueCode.SECRETS.name,
            "severity": Severity.HIGH.name,
            "details": summary_issue_block.to_json(),
            "location": "INPUT",
            "issues": [issue.to_json() for issue in issues],
        }

        assert aggregate_issue.to_json() == aggregate_json_response

    def test_issues_group_by_severity(self, issues: Issues) -> None:
        issue_list = issues.group_by_severity()
        assert len(issue_list) == 2
        assert len(issue_list[Severity.HIGH.name]) == 1
        assert len(issue_list[Severity.LOW.name]) == 1
        assert issue_list[Severity.HIGH.name][0].severity == Severity.HIGH
        assert issue_list[Severity.LOW.name][0].severity == Severity.LOW

    def test_issues_group_by_code(self, issues: Issues) -> None:
        issue_list = issues.group_by_code()
        assert len(issue_list) == 2
        assert len(issue_list[IssueCode.SECRETS.name]) == 1
        assert len(issue_list[IssueCode.UNAPPROVED_LICENSE_DEP_FILE.name]) == 1
        assert issue_list[IssueCode.SECRETS.name][0].code == IssueCode.SECRETS
        assert (
            issue_list[IssueCode.UNAPPROVED_LICENSE_DEP_FILE.name][0].code
            == IssueCode.UNAPPROVED_LICENSE_DEP_FILE
        )

    def test_issues_to_json(self, issues: Issues) -> None:
        issues_list = issues.to_json()
        assert len(issues_list) == 2
