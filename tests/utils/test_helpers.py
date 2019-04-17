# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from poetry.utils.helpers import get_http_basic_auth
from poetry.utils.helpers import parse_requires
from poetry.utils.helpers import parse_author


def test_parse_requires():
    requires = """\
jsonschema>=2.6.0.0,<3.0.0.0
lockfile>=0.12.0.0,<0.13.0.0
pip-tools>=1.11.0.0,<2.0.0.0
pkginfo>=1.4.0.0,<2.0.0.0
pyrsistent>=0.14.2.0,<0.15.0.0
toml>=0.9.0.0,<0.10.0.0
cleo>=0.6.0.0,<0.7.0.0
cachy>=0.1.1.0,<0.2.0.0
cachecontrol>=0.12.4.0,<0.13.0.0
requests>=2.18.0.0,<3.0.0.0
msgpack-python>=0.5.0.0,<0.6.0.0
pyparsing>=2.2.0.0,<3.0.0.0
requests-toolbelt>=0.8.0.0,<0.9.0.0

[:(python_version >= "2.7.0.0" and python_version < "2.8.0.0") or (python_version >= "3.4.0.0" and python_version < "3.5.0.0")]
typing>=3.6.0.0,<4.0.0.0

[:python_version >= "2.7.0.0" and python_version < "2.8.0.0"]
virtualenv>=15.2.0.0,<16.0.0.0
pathlib2>=2.3.0.0,<3.0.0.0

[:python_version >= "3.4.0.0" and python_version < "3.6.0.0"]
zipfile36>=0.1.0.0,<0.2.0.0    
"""
    result = parse_requires(requires)
    expected = [
        "jsonschema>=2.6.0.0,<3.0.0.0",
        "lockfile>=0.12.0.0,<0.13.0.0",
        "pip-tools>=1.11.0.0,<2.0.0.0",
        "pkginfo>=1.4.0.0,<2.0.0.0",
        "pyrsistent>=0.14.2.0,<0.15.0.0",
        "toml>=0.9.0.0,<0.10.0.0",
        "cleo>=0.6.0.0,<0.7.0.0",
        "cachy>=0.1.1.0,<0.2.0.0",
        "cachecontrol>=0.12.4.0,<0.13.0.0",
        "requests>=2.18.0.0,<3.0.0.0",
        "msgpack-python>=0.5.0.0,<0.6.0.0",
        "pyparsing>=2.2.0.0,<3.0.0.0",
        "requests-toolbelt>=0.8.0.0,<0.9.0.0",
        'typing>=3.6.0.0,<4.0.0.0; (python_version >= "2.7.0.0" and python_version < "2.8.0.0") or (python_version >= "3.4.0.0" and python_version < "3.5.0.0")',
        'virtualenv>=15.2.0.0,<16.0.0.0; python_version >= "2.7.0.0" and python_version < "2.8.0.0"',
        'pathlib2>=2.3.0.0,<3.0.0.0; python_version >= "2.7.0.0" and python_version < "2.8.0.0"',
        'zipfile36>=0.1.0.0,<0.2.0.0; python_version >= "3.4.0.0" and python_version < "3.6.0.0"',
    ]
    assert result == expected


def test_get_http_basic_auth(config):
    config.add_property("http-basic.foo.username", "foo")
    config.add_property("http-basic.foo.password", "bar")

    assert get_http_basic_auth(config, "foo") == ("foo", "bar")


def test_get_http_basic_auth_without_password(config):
    config.add_property("http-basic.foo.username", "foo")

    assert get_http_basic_auth(config, "foo") == ("foo", None)


def test_get_http_basic_auth_missing(config):
    assert get_http_basic_auth(config, "foo") is None


def test_parse_author_simple_name_and_email():
    """Test the :func:`parse_author` function."""

    # Verify the (probable) default use case
    name, email = parse_author("John Doe <john.doe@example.com>")
    assert name == "John Doe"
    assert email == "john.doe@example.com"

    # Name only
    name, email = parse_author("John Doe")
    assert name == "John Doe"
    assert email is None

    # Name with a “special” character + email address
    name, email = parse_author("R&D <researchanddevelopment@example.com>")
    assert name == "R&D"
    assert email == "researchanddevelopment@example.com"

    # Name with a “special” character only
    name, email = parse_author("R&D")
    assert name == "R&D"
    assert email is None

    # Name with fancy unicode character + email address
    name, email = parse_author("my·fancy corp <my-fancy-corp@example.com>")
    assert name == "my·fancy corp"
    assert email == "my-fancy-corp@example.com"

    # Name with fancy unicode character only
    name, email = parse_author("my·fancy corp")
    assert name == "my·fancy corp"
    assert email is None

    # Email address only, wrapped in angular brackets
    name, email = parse_author("<john.doe@example.com>")
    assert name is None
    assert email == "john.doe@example.com"

    # Email address only
    name, email = parse_author("john.doe@example.com")
    assert name is None
    assert email == "john.doe@example.com"
