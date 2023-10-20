# caul-proxy

Http Proxy via Python

### Installation

```sh
pip install pyinstaller
pyinstaller caul-proxy.spec
```

### Development

* Clone this repository
* Requirements:
    * Python 3.7+
* Create a virtual environment and install the dependencies

```sh
pip install -r requirements.txt
```

* Activate the virtual environment

```sh
python -m .venv
```

### Testing

```sh
pytest
```

### Documentation

The documentation is automatically generated from the content of the [docs directory](./docs) and from the docstrings
of the public signatures of the source code. The documentation is updated and published as a [Github project page
](https://pages.github.com/) automatically as part each release.
