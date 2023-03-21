import logging
import os
import pathlib
from typing import Any, Optional

import click
from tomlkit import parse

from nbdefense._version import __version__
from nbdefense.constants import AVAILABLE_REPORTING_MODULES, DEFAULT_SETTINGS
from nbdefense.nbdefense import NBDefense
from nbdefense.settings import SettingsUtils
from nbdefense.utils import serve_report_and_launch_url, write_output_file

logger = logging.getLogger("NBDefense")


def _enable_debug_logging(verbosity: int) -> None:
    verbose_levels = [None, logging.WARN, logging.INFO, logging.DEBUG]
    verbosity = min(verbosity, 3)
    logging.basicConfig(
        level=verbose_levels[verbosity], format="%(name)s - %(message)s"
    )


@click.group()
@click.pass_context
@click.version_option(__version__)
@click.option("-v", "--verbose", count=True)
def cli(ctx: click.Context, verbose: int) -> None:
    _enable_debug_logging(verbose)

    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
@click.argument("path", type=click.Path(exists=True), default=os.getcwd())
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    help="Scan all nested directories for .ipynb files.",
)
@click.option(
    "-s",
    "--serve",
    is_flag=True,
    help="Run an HTTP Server to view the report instead of persisting the report as an html file.",
)
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output.")
@click.option(
    "-d",
    "--dependency-file",
    type=click.Path(exists=True),
    help="Specify a requirements.txt file to scan for CVEs and license compatibility.",
)
@click.option(
    "-f",
    "--output-file",
    type=click.Path(dir_okay=False, writable=True),
    help="Specify an output filename for the report.",
)
@click.option(
    "-o",
    "--output-format",
    type=click.Choice(list(AVAILABLE_REPORTING_MODULES.keys())),
    help="The output format for the report.",
)
@click.option(
    "-y", "--yes", is_flag=True, help="Bypass all prompts with an affirmative response."
)
@click.option(
    "--settings-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Specify a settings file to use for the scan. Defaults to [PATH]/settings.toml.",
)
@click.option(
    "--no-progress-bars",
    is_flag=True,
    help="Hide progress bars, but keep other logging active.",
)
def scan(
    ctx: click.Context,
    path: str,
    recursive: bool,
    serve: bool,
    quiet: bool,
    dependency_file: str,
    output_file: str,
    output_format: str,
    yes: bool,
    settings_file: Optional[str],
    no_progress_bars: bool,
) -> None:
    """Scan [PATH] for .ipynb files for potential issues."""
    nbd = NBDefense()
    # Forcing html format if user doesn't specify report format
    internal_report_format = "html"
    if output_format:
        internal_report_format = output_format

    # --serve option cannot be run if output file or output format are specified.
    if serve:
        if output_file:
            raise click.BadOptionUsage(
                "--output-file",
                "-f / --output-file option cannot be used with --serve / -s",
            )
        if output_format:
            raise click.BadOptionUsage(
                "--output-format",
                "-o / --output-format option cannot be used with --serve / -s",
            )

    settings_file_path = pathlib.Path(
        settings_file if settings_file else f"{path}/settings.toml"
    )

    settings = DEFAULT_SETTINGS

    if settings_file_path and settings_file_path.is_file():
        with open(settings_file_path) as sf:
            settings = parse(sf.read()).unwrap()
            if not quiet:
                click.echo(f"Detected settings file. Using {settings_file_path}.")
    else:
        if not quiet:
            click.echo(
                f"No settings file detected at {settings_file_path}. Using defaults."
            )

    report = nbd.scan(
        root=path,
        recursive=recursive,
        quiet=quiet,
        requirements_file=dependency_file,
        report_format=internal_report_format,
        yes=yes,
        settings=settings,
        show_progress_bars=not no_progress_bars,
    )

    if serve:
        serve_report_and_launch_url(report)
    else:
        final_output_file = write_output_file(
            report, internal_report_format, output_file
        )
        if not quiet:
            logger.warning(f"Report file can be found here: {final_output_file}")


@cli.group(help="Commands related to NB Defense settings.")
def settings() -> None:
    pass


@settings.command(help="Create a settings file in the current working directory.")
@click.option(
    "-f", "--force", is_flag=True, help="Overwrite existing settings file if it exists."
)
@click.option(
    "-l",
    "--location",
    type=click.Path(dir_okay=False, writable=True),
    help="The specific filepath to write the settings.toml file.",
)
def create(force: bool, location: Optional[str]) -> None:
    working_dir = os.getcwd()
    settings_path = os.path.join(working_dir, "settings.toml")

    if location:
        settings_path = location

    try:
        open(settings_path)
        if force:
            with open(settings_path, "w") as settings_file:
                settings_file.write(SettingsUtils.get_default_settings_as_toml())
        else:
            logger.warning("settings.toml file detected. Exiting")
    except FileNotFoundError:
        with open(settings_path, "w") as settings_file:
            settings_file.write(SettingsUtils.get_default_settings_as_toml())


if __name__ == "__main__":
    cli()
