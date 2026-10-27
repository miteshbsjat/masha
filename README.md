# MASHA

MASHup of Configuration Loading from several file types and run [yAsha](https://github.com/kblomqvist/yasha/tree/master/yasha) like Jinja2 template rendition with [Validation](https://github.com/miteshbsjat/cli_config_validator).

## Motivation
* `MASHA` or `Magnificient yASHA`, is the name chosen, to show the amalgamation(`MASHa UP`) of my ideas and [`yasha` tool](https://github.com/kblomqvist/yasha). It has been inspired by these following magnificient tools or libraries:-
  * [`env-yaml-python`](https://github.com/iamKunal/env-yaml-python) helps in using ENV variable in the yaml configuration file.
  * [`j2yaml`](https://pypi.org/project/j2yaml/) looks good tool to be used for having templates inside `yaml` configuration files.
  * [`cli_config_validator`](https://github.com/miteshbsjat/cli_config_validator) configuration validation.
  * [`yasha`](https://github.com/kblomqvist/yasha) code generation tool based on jinja2 template rendition.


<table>
  <tr>
  <td><img src="docs/images/masha.jpg" width="135" height="100"></td>
<td>MASHA (name) is inspired from Cartoon Series <a href="https://en.wikipedia.org/wiki/Masha_and_the_Bear">Masha and Bear</a>. Like in this cartoon, a girl named `Masha` plays with the bear name `Mishka`, similarly, my daughter named `Diyanjali` plays with her father named `Mitesh` (i.e. me). :) <br />
The Masha logo is combination of Masha (the girl) and Yasha (the Katana Sword).
</td>
  </tr>
</table>

## Installation

You can install `masha` via pip. Ensure you have Python 3.13 or later installed on your system:

```sh
pip install masha
```

Alternatively, if you prefer to install from the source code (requires `poetry`), follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/miteshbsjat/masha.git
   ```

2. Navigate into the cloned directory:
   ```bash
   cd masha
   ```

3. Install the package using poetry:
   ```bash
   poetry shell
   poetry install
   poetry build
   pip3 install --force-reinstall dist/masha-0.0.7-py3-none-any.whl --user
   ```

## Best Practices Implemented

This project follows the Python and security practices documented in [CLAUDE.md](CLAUDE.md):

- **Logging**: Library modules use `logging.getLogger(__name__)`; only the CLI configures handlers, and logs go to `stderr`. Lazy `%s` interpolation throughout, no `print()`.
- **Error Handling**: Internal functions raise a custom exception hierarchy (`MashaBaseError` → `ConfigLoadError`, `ModelValidationError`, `TemplateRenderError`, `PluginLoadError`); the CLI turns them into a clean one-line error and exit code `1`.
- **Graceful Failures**: Users never see raw tracebacks; run with `--verbose` / `-V` to get DEBUG logs and tracebacks.
- **Type Hints**: Fully annotated, checked with `mypy --strict`.
- **Security**:
  - YAML is parsed with `yaml.safe_load` (no arbitrary object construction).
  - All Jinja2 rendering runs in a sandbox that *raises* on access to Python internals, blocking template injection through config values.
  - Autoescaping is enabled for `.html`/`.xml` templates only; code-generation outputs are emitted verbatim.
  - Resolved config values (which may contain secrets from env vars) are never logged — only keys, at DEBUG.
  - Rendering completes in memory before the output file is opened, so failures never leave truncated files.
  - Dependencies are scanned with `pip-audit`, code with `bandit` / ruff's `S` rules.

> **Note:** `--model-file`, `--template-filters-directory` and `--template-tests-directory` *import and execute* the given Python files. Only point them at code you trust.

## Development

```bash
poetry install
make format     # isort + black + ruff --fix
make check      # lint, mypy, bandit, pip-audit, pytest with coverage
```

## Usage

### masha help
```sh
$ masha --help
Usage: masha [OPTIONS] INPUT_FILE

  Validate merged configurations against a Pydantic model and render an input
  template.

Options:
  --version                       Show the version and exit.
  -v, --variables FILE            Path(s) to the various configuration files.
                                  [required]
  -m, --model-file FILE           Path to the Python file containing the
                                  Pydantic model class.
  -c, --class-model TEXT          Name of the Pydantic model class to validate
                                  against.
  -f, --template-filters-directory DIRECTORY
                                  Directory containing custom Jinja2 filter
                                  functions.
  -t, --template-tests-directory DIRECTORY
                                  Directory containing custom Jinja2 test
                                  functions.
  -o, --output FILE               Path to the output file where the rendered
                                  content will be written.  [required]
  -V, --verbose                   Enable debug logging (shows tracebacks on
                                  failure).
  --help                          Show this message and exit.
```

### Sample Usage

To use `masha`, you can run it from the command line with various options to load configuration files and render templates.

```sh
masha -v test/config-a.yaml -v test/config-b.yaml \
  -m test/model.py -c ConfigModel \
  -f masha/filters -t masha/tests \
  -o /tmp/demo.txt \
  test/input.txt.j2
```

### Basic Usage

#### Specifying Multiple Configurations

You can load multiple configuration files which will be merged together:

```bash
masha -v config1.yaml -v config2.json -o result.txt advanced_template.j2
```

#### Using Environment Variables

`masha` also supports environment variables to override or extend configurations:
in `env_example.j2` file `This came from env MY_VAR = ${MY_VAR:some_default_value}`

```bash
export MY_VAR="some_value"
masha -v default_config.yaml --output env_output.txt env_example.j2
```

output
```
This came from env MY_VAR = some_value
```


#### Example Configuration File (`config.yaml`)

Here is an example configuration file in YAML format:

```yaml
app:
  name: MyApplication
  version: 1.0.0

database:
  host: localhost
  port: 5432
  username: user
  password: pass
```

#### Example Template File (`template.j2`)

Here is a simple Jinja2 template file:

```jinja
Welcome to {{ app.name }} version {{ app.version }}!

Database configuration:
- Host: {{ database.host }}
- Port: {{ database.port }}
- Username: {{ database.username }}
- Password: {{ database.password }}
```

#### Output

Running the command with the above example files would produce an output file (`output.txt`) like this:

```
Welcome to MyApplication version 1.0.0!

Database configuration:
- Host: localhost
- Port: 5432
- Username: user
- Password: pass
```

### More Examples

More examples of `masha` usage are provided in [**examples.md**](docs/examples.md).

## License

This project is licensed under the Apache License 2.0.

## Contributing

If you would like to contribute to this project, please check out our [contributing guidelines](CONTRIBUTING.md).

## Issues

For any issues or bug reports, please open an issue in our [issue tracker](https://github.com/miteshbsjat/masha/issues).
