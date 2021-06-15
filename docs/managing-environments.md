---
title: "Managing environments"
draft: false
type: docs
layout: "docs"

menu:
  docs:
    weight: 60
---

# Managing environments

Poetry makes project environment isolation one of its core features.

What this means is that it will always work isolated from your global Python installation.
To achieve this, it will first check if it's currently running inside a virtual environment.
If it is, it will use it directly without creating a new one. But if it's not, it will use
one that it has already created or create a brand new one for you.

By default, Poetry will use the Python used during installation to create the virtual environment
for the current project.

However, for various reasons, this Python version might not be compatible
with the `python` requirement of the project. In this case, Poetry will try
to find one that is and use it. If it's unable to do so then you will be prompted
to activate one explicitly, see [Switching environments](#switching-between-environments).

{{% note %}}
To easily switch between Python versions, it is recommended to
use [pyenv](https://github.com/pyenv/pyenv) or similar tools.

For instance, if your project is Python 2.7 only, a standard workflow
would be:

```bash
pyenv install 2.7.15
pyenv local 2.7.15  # Activate Python 2.7 for the current project
poetry install --use-env python2.7
```
{{% /note %}}

## Switching between environments

Sometimes this might not be feasible for your system, especially Windows where `pyenv`
is not available, or you simply prefer to have a more explicit control over your environment.
For this specific purpose, you can use the `env use` command to tell Poetry
which Python version to use for the current project.

```bash
poetry env use /full/path/to/python
```

If you have the python executable in your `PATH` you can use it:

```bash
poetry env use python3.7
```

You can even just use the minor Python version in this case:

```bash
poetry env use 3.7
```

If you want to disable the explicitly activated virtual environment, you can use the
special `system` Python version to retrieve the default behavior:

```bash
poetry env use system
```

# Multiple environments

You can use `poetry env use` to create multiple environments for your project with different interpreters. `poetry env use`
will store the information about the used currently used python version in `{cachedir}/virtualenvs/env.toml` by default.

Sometimes it might be feasible to run a poetry command like `poetry shell` or `poetry run` on an environment without
switching the default. For this purpose the global option `--use-env` exists.

Let's assume we already have an evironment for python3.7 and want to add another one for python3.8 without setting it
as the new default one:

```bash
poetry install --use-env python3.8
```

We can even open a new shell for this environment:

```bash
poetry shell --use-env python3.8
```

Or run a specific command:

```bash
poetry run --use-env python3.8 python --version
```

Just like `poetry env use` the `--use-env` parameter expects a full path to an executable, a python executable in `$PATH`
or minor Python version.

## Displaying the environment information

If you want to get basic information about the currently activated virtual environment,
you can use the `env info` command:

```bash
poetry env info
```

will output something similar to this:

```text
Virtual environment
Python:         3.7.1
Implementation: CPython
Path:           /path/to/poetry/cache/virtualenvs/test-O3eWbxRl-py3.7
Valid:          True

System
Platform: darwin
OS:       posix
Python:   /path/to/main/python
```

If you only want to know the path to the virtual environment, you can pass the `--path` option
to `env info`:

```bash
poetry env info --path
```

## Listing the environments associated with the project

You can also list all the virtual environments associated with the current project
with the `env list` command:

```bash
poetry env list
```

will output something like the following:

```text
test-O3eWbxRl-py2.7
test-O3eWbxRl-py3.6
test-O3eWbxRl-py3.7 (Activated)
```

## Deleting the environments

Finally, you can delete existing virtual environments by using `env remove`:

```bash
poetry env remove /full/path/to/python
poetry env remove python3.7
poetry env remove 3.7
poetry env remove test-O3eWbxRl-py3.7
```

If you remove the currently activated virtual environment, it will be automatically deactivated.
