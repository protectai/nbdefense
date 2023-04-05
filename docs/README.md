# 📖 NBDefense Documentation

## ❗️ Requirements

1. Python

    NB Defense requires python version greater than `3.7.1` and less than `3.11`

2. Poetry

    The following install commands require [Poetry](https://python-poetry.org/). To install Poetry you can follow [this installation guide](https://python-poetry.org/docs/#installation). Poetry can also be installed with brew using the command `brew install poetry`.

## 💻 Local Install

1. Run `make install` to install the pip dependencies to the current python environment

2. Run `make start-dev` to run a development server locally

3. Go to `http://127.0.0.1:8000/` to view the docs

## 📚 References

We are using the following libraries for our documentation:

- [Live Documentation](https://nbdefense.ai)
  - This is where the production build is hosted
- [MkDocs](https://www.mkdocs.org/)
  - This is the static site generator we're using
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
  - This is the theme we're using for MkDocs
