# NBDefense Documentation

## Local dev

1. Run `make install-dev` to install the pip dependencies to the current python environment
2. Run `make start-dev` to run a development server locally
3. Go to `http://127.0.0.1:8000/` to view the docs

## References

We are using the following libraries for our documentation:

- [MkDocs](https://www.mkdocs.org/)
  - This is the static site generator we're using
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
  - This is the theme we're using for MkDocs

## Project structure

Most of the structure is standard for a MkDocs project, but there some differences:

- The `.vscode` dir
  - This is to include the yaml conf for the `mkdocs.yml` file as well as other IDE settings
- The `package.json` file
  - This is for deploying to [Vercel](https://vercel.com/docs)
