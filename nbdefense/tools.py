"""
This module implements the tools to scan notebooks and repositories
"""
import abc
import os
from subprocess import PIPE, Popen, run  # nosec
from typing import Any, List, Optional, Tuple, Union

import click


class Tool(metaclass=abc.ABCMeta):
    """
    A base class for different type of tools used in the scanning.
    """

    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def execute(
        self, args: Optional[Union[str, List[Any]]] = None
    ) -> Tuple[Union[int, Any], Optional[List[bytes]], Optional[List[bytes]]]:
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(
        self,
        args: Optional[Union[str, List[Any]]] = None,
        ignore_output: Optional[bool] = True,
    ) -> Any:
        raise NotImplementedError


class CLITool(Tool):
    """
    Executes shell commands for running scans using 3rd party tools.
    """

    def __init__(self) -> None:
        self.basecmd = ["echo"]

    def execute(
        self, args: Optional[Union[str, List[Any]]] = None
    ) -> Tuple[Union[int, Any], Optional[List[bytes]], Optional[List[bytes]]]:
        cmd = self.basecmd
        if args:
            if isinstance(args, List):
                cmd = self.basecmd + args
            else:
                cmd = self.basecmd + [args]

        p = Popen(cmd, stdout=PIPE, stderr=PIPE)  # nosec

        stdout_lines = p.stdout.readlines() if p.stdout else None
        stderr_lines = p.stderr.readlines() if p.stderr else None

        return p.returncode, stdout_lines, stderr_lines

    def __call__(
        self,
        args: Optional[Union[str, List[Any]]] = None,
        ignore_output: Optional[bool] = True,
    ) -> Any:
        return self.execute(args)


class Trivy(CLITool):
    def __init__(self, initialTrivyBinaryPath: str = "") -> None:
        super().__init__()
        self.installPath = os.path.split(__file__)[0]
        self.trivyPath = (
            initialTrivyBinaryPath
            if initialTrivyBinaryPath
            else os.path.join(self.installPath, "trivy")
        )
        self.basecmd = [self.trivyPath, "fs", "--security-checks", "vuln", "-f", "json"]

    def installed(self) -> bool:
        return os.path.isfile(self.trivyPath)

    def install(self) -> None:
        click.echo(f"Installing trivy to {self.trivyPath}")
        p1 = Popen(
            [
                "curl",
                "-sfL",
                "https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh",
            ],
            stdout=PIPE,
        )  # nosec
        p2 = run(
            ["sh", "-s", "--", "-b", self.installPath, "v0.32.1"],
            stdin=p1.stdout,
            stdout=PIPE,
        )  # nosec


class DetectSecrets(CLITool):
    def __init__(self) -> None:
        super().__init__()
        self.basecmd = ["detect-secrets", "scan"]
