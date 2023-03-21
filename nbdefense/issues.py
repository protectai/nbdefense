"""
This module provides classes for managing the 
"""
import abc
from collections import Counter, defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from nbdefense.notebook import Cell, InputCell


class IssueCode(Enum):
    # We found an embedded secret
    SECRETS = 1

    # License not in accepted license list
    UNAPPROVED_LICENSE_DEP_FILE = 2
    UNAPPROVED_LICENSE_IMPORT = 3

    # Issue with Dependency File
    DEPENDENCY_FILE = 4

    # Could not find a license
    LICENSE_NOT_FOUND_DEP_FILE = 5
    LICENSE_NOT_FOUND_NOTEBOOK = 6

    PII_FOUND = 7

    VULNERABLE_DEPENDENCY_DEP_FILE = 8
    VULNERABLE_DEPENDENCY_IMPORT = 9


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    ANY = 5  # Any priority

    def __lt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value < other.value  # type: ignore[no-any-return]
        raise NotImplemented


class IssueLocation(Enum):
    INPUT = "input"
    OUTPUT = "output"


class IssueDetails(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_json(self) -> Dict[str, Any]:
        raise NotImplemented


class IssueBlock(IssueDetails):
    """
    A code block consists of cell number and the line start and end number
    within that cell block. If scanning a notebook cell number can represent
    each code cells. When scanning a code file, the cell block could remain constant
    for the whole file.
    """

    def __init__(
        self,
        file_path: Optional[str] = None,
        description: Optional[str] = None,
        json_fields: Optional[List[str]] = [],
        summary_field: Optional[Dict[Any, Any]] = None,
    ) -> None:
        """
        Refer to a notebook cell that was scanned by

        :param description: Optionally, a freeform field to include more information about the issue detected.
        :param code_snippet: Optionally, a list of code lines as string can be included.
        :param json_fields: Optionally, a list of fields to include in json output. An empty list will return all fields.
        :summary_field: Optionally, a dictionary to include more information about the issue if neccessary. Will only be included if issue description is not None.
        """
        self.description = description
        self.json_fields = json_fields
        self.summary_field = summary_field
        self.file_path = file_path

    def to_json(self) -> Dict[str, Any]:
        if self.json_fields:
            return {
                field_name: (getattr(self, field_name, ""))
                for field_name in self.json_fields
            }
        else:
            return {
                "description": self.description,
                "summary_field": self.summary_field,
            }


class Issue:
    """
    Defines properties of a issue
    """

    def __init__(
        self,
        code: IssueCode,
        severity: Severity,
        details: Optional[IssueDetails] = None,
    ) -> None:
        """
        Create a issue with given information

        :param code: Code of the issue from the issue code enum.
        :param severity: The severity level of the issue from Severity enum.
        :param details: Optionally add IssueDetails.
        """
        self.code = code
        self.severity = severity
        self.details = details

    def to_json(self) -> Dict[str, Any]:
        return {
            "code": self.code.name,
            "severity": self.severity.name,
            "details": self.details.to_json() if self.details else self.details,
        }


class CellIssue(Issue):
    def __init__(
        self,
        code: IssueCode,
        severity: Severity,
        cell: Cell,
        details: Optional[IssueDetails] = None,
    ) -> None:
        """
        Create an issue for a cell with given information

        :param code: Code of the issue from the issue code enum.
        :param severity: The severity level of the issue from Severity enum.
        :cell: A Cell from a parsed notebook.
        :param details: Optionally add IssueDetails.
        """
        super().__init__(code, severity, details)
        self.cell = cell
        self.location = (
            IssueLocation.INPUT if type(cell) == InputCell else IssueLocation.OUTPUT
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "code": self.code.name,
            "severity": self.severity.name,
            "cell": self.cell.to_json(),
            "location": self.location.name,
            "details": self.details.to_json() if self.details else self.details,
        }


class LineCellIssue(CellIssue):
    def __init__(
        self,
        code: IssueCode,
        severity: Severity,
        cell: Cell,
        line_index: int,
        character_start_index: int,
        character_end_index: int,
        details: Optional[IssueDetails] = None,
    ) -> None:
        """
        Create an issue for a line within a cell with given information

        :param code: Code of the issue from the issue code enum.
        :param severity: The severity level of the issue from Severity enum.
        :cell: A Cell from a parsed notebook.
        :line_index: The line index of the issue.
        :character_start_index: The starting index of the issue within a line.
        :character_end_index: The ending index of the issue within a line.
        :param details: Optionally add IssueDetails.
        """
        super().__init__(code, severity, cell, details)
        self.line_index = line_index
        self.character_start_index = character_start_index
        self.character_end_index = character_end_index

    def to_json(self) -> Dict[str, Any]:
        return {
            "code": self.code.name,
            "severity": self.severity.name,
            "cell": self.cell.to_json(),
            "line_index": self.line_index,
            "location": self.location.name,
            "character_start_index": self.character_start_index,
            "character_end_index": self.character_end_index,
            "details": self.details.to_json() if self.details else self.details,
        }


class DataframeCellIssue(CellIssue):
    def __init__(
        self,
        code: IssueCode,
        severity: Severity,
        cell: Cell,
        row_index: int,
        column_index: int,
        character_start_index: int,
        character_end_index: int,
        details: Optional[IssueDetails] = None,
    ) -> None:
        """
        Create an issue for a cell with given information

        :param code: Code of the issue from the issue code enum.
        :param severity: The severity level of the issue from Severity enum.
        :cell: A Cell from a parsed notebook.
        :row_index: The row index of the issue in a dataframe.
        :column_index: The column index of the issue in a dataframe.
        :character_start_index: The starting index of the issue within dataframe cell specified by row_index and column_index.
        :character_end_index: The ending index of the issue within within dataframe cell specified by row_index and column_index.
        :param details: Optionally add IssueDetails.
        """
        super().__init__(code, severity, cell, details)
        self.row_index = row_index
        self.column_index = column_index
        self.character_start_index = character_start_index
        self.character_end_index = character_end_index
        self.location = (
            IssueLocation.INPUT if type(cell) == InputCell else IssueLocation.OUTPUT
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "code": self.code.name,
            "severity": self.severity.name,
            "cell": self.cell.to_json(),
            "location": self.location.name,
            "row_index": self.row_index,
            "column_index": self.column_index,
            "character_start_index": self.character_start_index,
            "character_end_index": self.character_end_index,
            "details": self.details.to_json() if self.details else self.details,
        }


class AggregateIssue(CellIssue):
    def __init__(
        self,
        code: IssueCode,
        severity: Severity,
        cell: Cell,
        issues: List[CellIssue],
        details: Optional[IssueDetails] = None,
    ) -> None:
        super().__init__(code, severity, cell, details)
        self.issues = issues

    def to_json(self) -> Dict[str, Any]:
        return {
            **super().to_json(),
            "issues": [issue.to_json() for issue in self.issues],
        }


class Issues:
    def __init__(self, path: Path) -> None:
        """
        Collection of individual issues for a resource at given path.

        :param path: The path object to the resource.
        """
        self.path = path

        # View of issues w.r.t priority
        self.issues_by_severity: Dict[Severity, List[Issue]] = defaultdict(list)

        # Hold all issues, this might not be necessary?
        self.all_issues: List[Issue] = []

    def add_issue(self, issue: Issue) -> None:
        """
        Add a issue to list of issues for the given notebook.

        :param issue: A issue object
        """
        self.issues_by_severity[issue.severity].append(issue)
        self.all_issues.append(issue)

    def group_by_severity(self) -> Dict[str, List[Issue]]:
        """
        Group issues by severity.
        """
        issues: Dict[str, List[Issue]] = defaultdict(list)
        for issue in self.all_issues:
            issues[issue.severity.name].append(issue)
        return issues

    def group_by_code(self) -> Dict[str, List[Issue]]:
        """
        Group issues by code.
        """
        issues: Dict[str, List[Issue]] = defaultdict(list)
        for issue in self.all_issues:
            issues[issue.code.name].append(issue)
        return issues

    def to_json(self) -> List[Dict[str, Any]]:
        ret = []
        for issue in self.all_issues:
            ret.append(issue.to_json())
        return ret
