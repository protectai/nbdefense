The settings for the NB Defense CLI can be configured using a [TOML](https://toml.io/en/) file.

### Creating a `settings.toml` file

You can create a `settings.toml` file using the following CLI command:

```bash
nbdefense settings create
```

Which creates the following `settings.toml` file:

??? abstract "settings.toml"

    ```toml
    # NB Defense settings file

    # Redact secrets
    # Possible values are `PARTIAL`, `ALL`, `HASH`

    # `PARTIAL` will show only leading and trailing characters.

    # `ALL` will shadow the full secret.

    # `HASH` will replace the full secret with its hashed value.
    redact_secret = "PARTIAL"
    trivy_binary_path = ""

    [plugins]
    [plugins."nbdefense.plugins.SecretsPlugin"]
    enabled = true

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "SoftlayerDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "StripeDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "SendGridDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "NpmDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "KeywordDetector"
    keyword_exclude = ""

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "IbmCosHmacDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "DiscordBotTokenDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "BasicAuthDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "AzureStorageKeyDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "ArtifactoryDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "AWSKeyDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "CloudantDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "GitHubTokenDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "IbmCloudIamDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "JwtTokenDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "MailchimpDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "PrivateKeyDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "SlackDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "SquareOAuthDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "TwilioKeyDetector"

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "Base64HighEntropyString"
    limit = 4.5

    [[plugins."nbdefense.plugins.SecretsPlugin".secrets_plugins]]
    name = "HexHighEntropyString"
    limit = 3.0

    [plugins."nbdefense.plugins.PIIPlugin"]
    enabled = true
    confidence_threshold = 0.8

    [plugins."nbdefense.plugins.PIIPlugin".entities]
    US_PASSPORT = true
    AU_MEDICARE = true
    AU_TFN = true
    AU_ACN = true
    AU_ABN = true
    UK_NHS = true
    US_SSN = true
    US_ITIN = true
    US_DRIVER_LICENSE = true
    US_BANK_NUMBER = true
    MEDICAL_LICENSE = true
    LOCATION = true
    PHONE_NUMBER = true
    NRP = true
    IP_ADDRESS = true
    EMAIL_ADDRESS = true
    IBAN_CODE = true
    CRYPTO = true
    CREDIT_CARD = true
    PERSON = true

    [plugins."nbdefense.plugins.LicenseDependencyFilePlugin"]
    enabled = true
    accepted_licenses = ["Apache License 2.0", "Apache Software License", "Apache 2.0", "Apache-2.0", "BSD", "BSD License", "BSD 3-Clause", "BSD-3-Clause", "GNU Library or Lesser General Public License (LGPL)", "Microsoft Public License", "MIT", "MIT License", "Python Software Foundation License", "ISC License (ISCL)", "MIT-0"]

    [plugins."nbdefense.plugins.CVEDependencyFilePlugin"]
    enabled = true
    ```

This settings file can be edited and subsequently used by the CLI. If the file is named `settings.toml` and located in the directory you are scanning, the settings file will be picked up by default. Otherwise the path to the desired settings file can be passed to the scan command with the following syntax:

```bash
nbdefense scan SCAN_PATH --settings-file SETTINGS_FILE_PATH
```

Replace `SCAN_PATH` with the directory or file you would like to scan and `SETTINGS_FILE_PATH` with the path to the settings file you would like to use.

### CLI Specific Settings

#### `trivy_binary_path`

The `trivy_binary_path` will override the [Trivy](https://aquasecurity.github.io/trivy/v0.38/) default installation/location. This is useful if you are installing the CLI in an environment where egress is limited or unavailable.
