# Getting Started

NB Defense is an open source tool for detecting security issues in Jupyter Notebooks. These issues can range from detecting leaked PII in your notebook output to detecting vulnerable versions of installed dependencies. There are currently two tools that you can use to scan your notebooks with NB Defense.

## Choose the tool for you

### [The JupyterLab Extension](jupyter-lab-extension.md)

Using the JupyterLab Extension is ideal for correcting issues directly within the JupyterLab environment. You can quickly scan and re-scan a single notebook in order to correct any potential security issues within your environment.

<video autoplay loop muted src="/imgs/jupyter-extension-example.mp4">
    Jupyter Extension Example
</video>

[Try it out!](jupyter-lab-extension.md){ .md-button .md-button--primary }

### [The CLI](cli.md)

The CLI is a better option if you have a lot of notebooks that you would like to scan simultaneously or if you would like to automatically scan notebooks that are going into a central repository. It can also help you set a baseline for correcting individual notebooks with the JupyterLab Extension at a later time.

![CLI help message](/imgs/cli-help-message.png)

[Try it out!](cli.md){ .md-button .md-button--primary }
