# MASHA

MASHup of Configuration Loading from several file types and run [yAsha](https://github.com/kblomqvist/yasha/tree/master/yasha) like Jinja2 template rendition with [Validation](https://github.com/miteshbsjat/cli_config_validator).

## Installation

```sh
pip install masha
```


## Usage

```sh
masha -v test/config-a.yaml -v test/config-b.yaml \
  -m test/model.py -c ConfigModel \
  -f masha/filters -t masha/tests \
  -o /tmp/demo.txt \
  test/input.txt.j2
```