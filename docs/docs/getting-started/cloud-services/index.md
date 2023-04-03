# JupyterLab Extension on Cloud Services

This page gives an overall account of installing NB Defense JupyterLab Extension (JLE) on different cloud platforms. Overall, the following four steps outline the installation of the JLE:

1.  Choose the conda environment in which JLE is to be installed.

    ```bash
    conda activate ENVIRONMENT_NAME
    ```

2.  Install the JLE using pip install command:

    ```bash
    pip install nbdefense_jupyter
    ```

3.  Enable the JLE using:

    ```bash
    jupyter server extension enable nbdefense_jupyter
    ```

4.  Restart the JupyterLab server with the platform specific restart command/sequence.

Please note that step 2 and step 3 will be the same on all cloud platforms, whereas step 1 and step 4 will change depending on the cloud platform.

Please follow the links for the following cloud platforms to learn more about their specific JLE installation steps:

[SageMaker Notebooks](/getting-started/cloud-services/sage-maker-notebook-instances){ .md-button .md-button--primary }

[SageMaker Studio Labs](/getting-started/cloud-services/sage-maker-studio-lab){ .md-button .md-button--primary }

[Azure Machine Learning Studio](/getting-started/cloud-services/azure-ml-notebooks){ .md-button .md-button--primary }

## Other Cloud Platforms?

If you are trying to install NB Defense JLE on a cloud platform for which the installation instructions are not listed, you are welcome to open a ticket, or a PR [here](https://github.com/protectai/nbdefense/issues).
