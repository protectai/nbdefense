# 👩‍💻 CONTRIBUTING

Welcome! We're glad to have you. If you would like to report a bug, request a new feature or enhancement, follow [this link](https://nbdefense.ai/contributing) for more help.

If you're looking for documentation on how to use NB Defense, you can find that [here](https://nbdefense.ai).

## ❗️ Requirements

1. Python

    NB Defense requires python version greater than `3.7.1` and less than `3.11`

2. Poetry

    The following install commands require [Poetry](https://python-poetry.org/). To install Poetry you can follow [this installation guide](https://python-poetry.org/docs/#installation). Poetry can also be installed with brew using the command `brew install poetry`.

## 💪 Developing with NB Defense

1. Clone the Repo

    ```bash
    git clone git@github.com:protectai/nbdefense.git
    ```

2. To install development dependencies to your environment and set up the cli for live updates, run the following command in the root of the `nbdefense` directory:

    ```bash
    $ make install-dev
    ```

3. You are now ready to start developing!

    Run a scan with the cli with the following command:

    ```bash
    nbdefense scan -s
    ```

## 📚 CLI Usage

### `nbdefense scan` command

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

### `nbdefense settings create` command

```
nbdefense settings create --help
Usage: nbdefense settings create [OPTIONS]

Create a settings file in the current working directory.

Options:
-f, --force          Overwrite existing settings file if it exists.
-l, --location FILE  The specific filepath to write the settings.toml file.
--help               Show this message and exit.
```
