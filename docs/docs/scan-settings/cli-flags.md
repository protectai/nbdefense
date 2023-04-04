There are various flags that can change the behavior of the CLI. Information about these flags can be found using the `nbdefense scan --help` command.

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
