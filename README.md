# NBDefense-private

## Poetry

The following install commands require [Poetry](https://python-poetry.org/). To install Poetry you can follow [this installation guide](https://python-poetry.org/docs/#installation). Poetry can also be installed with brew using the command `brew install poetry`.

Tips:

- You can add a dependency with the command `poetry add pendulum==0.0.0`. To specify a group use `poetry add pendulum==0.0.0 --group dev`
- You can remove a dependency with the command `poetry remove pendulum`

## Dev installation

Install the development dependencies to your environment and set up the cli for live updates with:

```bash
$ make install-dev
```

## Formatting

Run the formatter with:

```bash
$ make format
```

## Prod build

To build the cli for prod installs run the following:

```bash
$ make install
$ make build-prod
```

or if you want dynamic versioning with dunamai

```bash
$ make install-prod
$ make build-prod
```

# CLI Usage

## `nbdefense scan` command

```
nbdefense scan --help
Usage: nbdefense scan [OPTIONS] [PATH]

  Scan [PATH] for .ipynb files for potential issues.

Options:
  -r, --recursive                 Scan all nested directories for .ipynb
                                  files.
  -s, --serve                     Run an HTTP Server to view the report
                                  instead of persisting the report as an html
                                  file.
  -q, --quiet                     Suppress all output.
  -d, --dependency-file PATH      Specify a requirements.txt file to scan for
                                  CVEs and license compatibility.
  -f, --output-file FILE          Specify an output filename for the report.
  -o, --output-format [json|html]
                                  The output format for the report.
  -y, --yes                       Bypass all prompts with an affirmative
                                  response.
  --settings-file FILE            Specify a settings file to use for the scan.
                                  Defaults to [PATH]/settings.toml.
  --no-progress-bars              Hide progress bars, but keep other logging
                                  active.
  --help                          Show this message and exit.
```

## `nbdefense settings create` command

```
nbdefense settings create --help
Usage: nbdefense settings create [OPTIONS]

  Create a settings file in the current working directory.

Options:
  -f, --force          Overwrite existing settings file if it exists.
  -l, --location FILE  The specific filepath to write the settings.toml file.
  --help               Show this message and exit.
```
