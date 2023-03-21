import pathlib

import pytest

from nbdefense.codebase import Codebase
from nbdefense.notebook import Notebook
from nbdefense.plugins.plugin import ScanTarget
from nbdefense.plugins.secrets import SecretPluginSettings, SecretsPlugin
from tests.default_settings import DEFAULT_SETTINGS


class TestSecrets:
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
    def settings(self) -> SecretPluginSettings:
        return SecretsPlugin.get_settings(
            plugin_class_name="nbdefense.plugins.SecretsPlugin",
            is_enabled=True,
            settings=DEFAULT_SETTINGS,
        )

    def test_plugin_attributes(self) -> None:
        assert SecretsPlugin.scan_target() == ScanTarget.NOTEBOOKS
        assert SecretsPlugin.name() == "Secrets Plugin"

    def test_scan(
        self,
        codebase: Codebase,
        mock_notebook: Notebook,
        settings: SecretPluginSettings,
    ) -> None:
        assert len(list(codebase.notebooks())) == 1

        SecretsPlugin.scan(codebase, settings)
        notebook = list(codebase.notebooks())[0]
        input_secret_cell = mock_notebook.input_cells[6]
        output_secret_cell = mock_notebook.output_cells[3]

        expected_scrubbed_input_cell_json = input_secret_cell.to_json()
        expected_scrubbed_input_cell_json["scrubbed_content"] = "\n".join(
            [
                "import boto3",
                "client = boto3.client('s3',",
                '\taws_access_key_id="AK..6C",',
                '\taws_secret_access_key="W/..py")',
                "client.upload_file('sample_data.csv', 'mybucket', 'sample_data.csv')",
            ]
        )

        expected_scrubbed_output_cell_json = output_secret_cell.to_json()
        expected_scrubbed_output_cell_json["scrubbed_content"] = "\n".join(
            [
                'aws_access_key_id="AK..6C"',
                'aws_secret_access_key="W/..py"',
            ]
        )

        # TODO: secrets coming out of detect_secrets are not in fixed order and on top of
        # that we have input and output cell with their own cell index. The test need to
        # check which issue we are asserting against. We might want to find a better logic to handle
        # this test.One idea is that instead of one notebook, we create multiple notebooks with secret
        # cells.

        found_issues = 0
        for issue in notebook.issues.all_issues:
            issue_json = issue.to_json()

            description = issue_json.get("details", {}).get("description", None)
            cell_index = issue_json.get("cell", {}).get("cell_index", None)
            line_index = issue_json.get("line_index", None)
            location = issue_json.get("location", None)

            if (
                description == "AWS Access Key"
                and cell_index == 6
                and line_index == 2
                and location == "INPUT"
            ):
                assert issue_json == {
                    "code": "SECRETS",
                    "severity": "CRITICAL",
                    "line_index": 2,
                    "cell": expected_scrubbed_input_cell_json,
                    "location": "INPUT",
                    "character_start_index": 20,
                    "character_end_index": 40,
                    "details": {
                        "description": "AWS Access Key",
                        "summary_field": None,
                    },
                }
                found_issues += 1
            elif (
                description == "AWS Access Key"
                and cell_index == 6
                and line_index == 3
                and location == "INPUT"
            ):
                assert issue_json == {
                    "code": "SECRETS",
                    "severity": "CRITICAL",
                    "line_index": 3,
                    "cell": expected_scrubbed_input_cell_json,
                    "location": "INPUT",
                    "character_start_index": 24,
                    "character_end_index": 64,
                    "details": {
                        "description": "AWS Access Key",
                        "summary_field": None,
                    },
                }
                found_issues += 1
            elif (
                description == "Secret Keyword"
                and cell_index == 6
                and location == "INPUT"
            ):
                assert issue_json == {
                    "code": "SECRETS",
                    "severity": "CRITICAL",
                    "line_index": 3,
                    "location": "INPUT",
                    "cell": expected_scrubbed_input_cell_json,
                    "character_start_index": 24,
                    "character_end_index": 64,
                    "details": {
                        "description": "Secret Keyword",
                        "summary_field": None,
                    },
                }
                found_issues += 1
            elif (
                description == "AWS Access Key"
                and cell_index == 7
                and line_index == 0
                and location == "OUTPUT"
            ):
                assert issue_json == {
                    "code": "SECRETS",
                    "severity": "CRITICAL",
                    "line_index": 0,
                    "location": "OUTPUT",
                    "cell": expected_scrubbed_output_cell_json,
                    "character_start_index": 19,
                    "character_end_index": 39,
                    "details": {
                        "description": "AWS Access Key",
                        "summary_field": None,
                    },
                }
                found_issues += 1

            elif (
                description == "AWS Access Key"
                and cell_index == 7
                and line_index == 1
                and location == "OUTPUT"
            ):
                assert issue_json == {
                    "code": "SECRETS",
                    "severity": "CRITICAL",
                    "line_index": 1,
                    "location": "OUTPUT",
                    "cell": expected_scrubbed_output_cell_json,
                    "character_start_index": 23,
                    "character_end_index": 63,
                    "details": {
                        "description": "AWS Access Key",
                        "summary_field": None,
                    },
                }
                found_issues += 1
            elif (
                description == "Secret Keyword"
                and cell_index == 7
                and location == "OUTPUT"
            ):
                assert issue_json == {
                    "code": "SECRETS",
                    "severity": "CRITICAL",
                    "line_index": 1,
                    "location": "OUTPUT",
                    "cell": expected_scrubbed_output_cell_json,
                    "character_start_index": 23,
                    "character_end_index": 63,
                    "details": {
                        "description": "Secret Keyword",
                        "summary_field": None,
                    },
                }
                found_issues += 1

        assert found_issues == 6
