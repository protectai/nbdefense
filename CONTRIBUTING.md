# 👩‍💻 CONTRIBUTING

Welcome! We're glad to have you. If you would like to report a bug, request a new feature or enhancement, follow [this link](https://nbdefense.ai/faq) for more help.

If you're looking for documentation on how to use NB Defense, you can find that [here](https://nbdefense.ai).

## ❗️ Requirements

1. Python

   NB Defense requires python version greater than `3.8` and less than `3.11`

2. Poetry

   The following install commands require [Poetry](https://python-poetry.org/). To install Poetry you can follow [this installation guide](https://python-poetry.org/docs/#installation). Poetry can also be installed with brew using the command `brew install poetry`.

## 💪 Developing with NB Defense

1. Clone the repo

   ```bash
   git clone git@github.com:protectai/nbdefense.git
   ```

2. To install development dependencies to your environment and set up the cli for live updates, run the following command in the root of the `nbdefense` directory:

   ```bash
   make install-dev
   ```

3. You are now ready to start developing!

   Run a scan with the cli with the following command:

   ```bash
   nbdefense scan -s
   ```

## 📝 Submitting Changes

Thanks for contributing! In order to open a PR into the NB Defense project, you'll have to follow these steps:

1. Fork the repo and clone your fork locally
2. Run `make install-dev` from the root of your forked repo to setup your environment
3. Make your changes
4. Submit a pull request

After these steps have been completed, someone on our team at Protect AI will review the code and help merge in your changes!
