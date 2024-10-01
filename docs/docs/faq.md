---
hide:
  - navigation
---

Thank you for your interest in NB Defense. We want to make tools with the community that data scientist and engineers can use and enjoy. Welcome to the community!

## Common Questions

### Why should I use NB Defense as a data scientist?

We know that JupyterLab is where many data scientist experiement and prove out their ideas. The NB Defense [JupyterLab Extension](./getting-started/jupyter-lab-extension.md) and [CLI](./getting-started/cli.md) allows you to check for vulnerabilities and security issues before the code leaves your environment. You can use NB Defense to check for personally identifiable information, secrets, common exposures and vulnerabilites, and non permissive licenses with the click of the button. We wanted to create a way for data scientists to reduce exposure to security issues and save time later on, by integrating good security practices into the development process. 

### Can I run NB Defense in my CI pipeline?

Yes, you can run NB Defense in your CI pipline using the [NB Defense CLI](./getting-started/cli.md)! Use the CLI in your CI pipelines to scan repositories, or multiple notebooks at a time. 

### What is unique about NB Defense when many security tools offer similar functionality?


NB Defense allows you to scan Jupyter Notebooks. Currently most security tools do not support Notebook `.ipynb` formatted files. NB Defense fills this gap. We provide both a [JupyterLab Extension](./getting-started/jupyter-lab-extension.md) that you can use to scan notebooks within Jupyterlab environment, and a [CLI](./getting-started/cli.md) that you can use to scan groups of notebooks or repositories. Using both of these tools, you can scan your notebooks for personally identifiable information (PII), secrets, common exposures and vulnerabilities (CVEs), and non permissive licenses.

### Does NB Defense JupyterLab Extension run in my kernel?

No. We recommend installing NB Defense Jupyterlab extension outside of Kernel specific environment. NB Defense runs its code on the Jupyter Server instead of Notebook specific Kernel(s). We do use your active kernels python path to determine which third party dependencies are installed, so we can scan them for CVEs and licenses.

## Found A Bug? 🐞

Found an issue with the NB Defense CLI or JupyterLab Extension? Lets get that fixed. Let us know what you've found by opening an issue using the following links:

- [NB Defense Bug (SDK and CLI)](https://github.com/protectai/nbdefense/issues/new?labels=bug&template=bug_report.md&title=%5BA+Few+Words+Describing+the+Bug%5D)

- [NB Defense Jupyter Bug (JupyterLab Extension)](https://github.com/protectai/nbdefense-jupyter/issues/new?labels=bug&template=bug_report.md&title=%5BA+Few+Words+Describing+the+Bug%5D)

## Found An Issue With Our Documentation? 📄

We want to be clear, correct, and concise. Let us know where we can improve:

- [NB Defense Documentation Issue (SDK, CLI and JupyterLab Extension)](https://github.com/protectai/nbdefense/issues/new?labels=bug%2C+documentation&template=documentation-issue-report.md&title=%5BA+Few+Words+Describing+the+Issue%5D)

## Have An Idea For A New Feature? 💡

We'd love to hear about it. Tell us more by creating an issue below:

- [NB Defense Feature Request (SDK and CLI)](https://github.com/protectai/nbdefense/issues/new?labels=enhancement&template=feature_request.md&title=%5BA+Few+Words+Describing+the+Feature%5D)

- [NB Defense Jupyter Feature Request (JupyterLab Extension)](https://github.com/protectai/nbdefense/issues/new?labels=enhancement&template=feature_request.md&title=%5BA+Few+Words+Describing+the+Feature%5D)

## Have A Question? ❓

Feel free to ask questions using github discussions by following the links below:

- [NB Defense Discussions (SDK and CLI)](https://github.com/protectai/nbdefense/discussions)

- [NB Defense Jupyter Discussions (JupyterLab Extension)](https://github.com/protectai/nbdefense-jupyter/discussions)
