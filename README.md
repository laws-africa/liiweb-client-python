# liiweb-client-python

A python client for the LIIWeb Drupal JSON API.

## Installation

`pip install -e git+https://github.com/laws-africa/liiweb-client-python.git@master#egg=liiweb-client`

## Usage

```python
from liiweb import LIIWebClient

lii = LIIWebClient('https://example.com', 'username', 'password')
lii.list_legislation('za')
```

## License

MIT License
