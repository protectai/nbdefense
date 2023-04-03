---
description: This section covers how to configure the settings for NBDefense.
---

# Scan Settings

Settings for scans can be adjusted for both the [JupyterLab extension](/scan-settings/jupyterlab-settings/) and the [CLI](/scan-settings/cli-settings/).

## Adjustable Settings

Each of the four NB Defense plugins (secrets, PII, licences, CVE) can be switched on or off. That is, if only the PII plugin is disabled and the remaining three plugins are enabled, the NB Defense scan will scan for the three enabled plugins but will not scan for PII.

In addition to enable/disable the available plugins for NB Defense scan, there is a global adjustable setting of `redact_secret` for presenting sensitive information in scan reports. Moreover, NB Defense also allows for individual settings for each of the four plugins. The global and individual plugin settings are described below:

### Global Settings

#### `redact_secret`

The `redact_secret` setting determines how sensitive information is presented in NB Defense scan reports. The possible values of `redact_secret` are `PARTIAL`, `ALL`, and `HASH`. `PARTIAL` will show only leading and trailing characters. `ALL` will shadow the full secret. `HASH` will replace the full secret with its hashed value (as shown in the table below as well).

| Redacted Secret Option | Redacted Secret |
| :--------------------- | :-------------- |
| PARTIAL                | 4aed\*\*\*\*78$ |
| ALL                    | ****\*\*\*****  |
| HASH                   | h3hb54i109k     |

### Secrets Plugin Settings

#### `secrets_plugins`

The `secrets_plugins` has the same modules as in the [detect-secrets](https://github.com/Yelp/detect-secrets) package. Each of the secret modules can be enable or disabled.

More details on which of the secret modules are enabled by default, and what they detect can be found on the [secrets scan details page](/supported-scans/detecting-secrets/#supported-detect-secrets-plugins).

### PII Plugin Settings

#### `confidence_threshold`

The `confidence_threshold` indicates the level of uncertainty allowed when flagging text as PII i.e., a confidence threshold set at `0.8` would only allow that text marked as PII when NB Defense's PII scan is at least `80%` confident that the text is PII. For any other text where the confidence of the NB Defense's PII scan is less than `80%` the text will not be marked as PII. The default value of `confidence_threshold` is set at `0.8` with a minimum allowed value of `0.0` and a maximum allowed value of `1.0`.

Also, NB Defense PII scan allows for separate setting of `confidence_threshold` for each of the PII entities. In this way, by adjusting the values of `confidence_threshold` for each PII entity separately, the users of NB Defense can set the uncertainty in PII scan results for each of the PII entities independently.

#### `entities`

The PII entities to be scanned for can be toggled on and off in the scan settings. A list of PII entities with their brief description can be found on the [PII scan details page](/supported-scans/detecting-PII/).

### License Plugin Settings

#### `accepted_licenses`

The licenses added to `accepted_licenses` setting will not be flagged in the NB Defense scan report. So, for example, if the following licenses are added to the `accepted_licences`, and they appear in the text, NB Defense License plugin will not flag it.

```
accepted_licenses = ["Apache License 2.0", "BSD-3-Clause",  "MIT License"]
```

### CVE Plugin Settings

There are no settings specific to the CVE plugin.
