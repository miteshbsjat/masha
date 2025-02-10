# MASHA

MASHup of Configuration Loading from several file types and run [yAsha](https://github.com/kblomqvist/yasha/tree/master/yasha) like Jinja2 template rendition with [Validation](https://github.com/miteshbsjat/cli_config_validator).

## Installation

You can install `masha` via pip. Ensure you have Python 3.10 or later installed on your system:

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

3. Install the package using setuptools:
   ```bash
   poetry shell
   poetry install
   poetry build
   pip3 install --force-reinstall dist/masha-0.0.0-py3-none-any.whl --user
   ```

## Usage

### Basic Usage

To use `masha`, you can run it from the command line with various options to load configuration files and render templates.

```sh
masha -v test/config-a.yaml -v test/config-b.yaml \
  -m test/model.py -c ConfigModel \
  -f masha/filters -t masha/tests \
  -o /tmp/demo.txt \
  test/input.txt.j2
```

### Advanced Usage

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


### Example Configuration File (`config.yaml`)

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

### Example Template File (`template.j2`)

Here is a simple Jinja2 template file:

```jinja
Welcome to {{ app.name }} version {{ app.version }}!

Database configuration:
- Host: {{ database.host }}
- Port: {{ database.port }}
- Username: {{ database.username }}
- Password: {{ database.password }}
```

### Output

Running the command with the above example files would produce an output file (`output.txt`) like this:

```
Welcome to MyApplication version 1.0.0!

Database configuration:
- Host: localhost
- Port: 5432
- Username: user
- Password: pass
```

## License

This project is licensed under the Apache License 2.0.

## Contributing

If you would like to contribute to this project, please check out our [contributing guidelines](CONTRIBUTING.md).

## Issues

For any issues or bug reports, please open an issue in our [issue tracker](https://github.com/miteshbsjat/masha/issues).
