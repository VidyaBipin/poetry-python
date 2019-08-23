import json
import re

from cleo import argument
from cleo import option

from poetry.utils.helpers import (
    keyring_repository_password_del,
    keyring_repository_password_set,
)
from .command import Command


class ConfigCommand(Command):

    name = "config"
    description = "Sets/Gets config options."

    arguments = [
        argument("key", "Setting key.", optional=True),
        argument("value", "Setting value.", optional=True, multiple=True),
    ]

    options = [
        option("list", None, "List configuration settings."),
        option("unset", None, "Unset configuration setting."),
        option("local", None, "Set/Get from the project's local configuration."),
    ]

    help = """This command allows you to edit the poetry config settings and repositories.

To add a repository:

    <comment>poetry config repositories.foo https://bar.com/simple/</comment>

To remove a repository (repo is a short alias for repositories):

    <comment>poetry config --unset repo.foo</comment>"""

    @property
    def unique_config_values(self):
        from poetry.locations import CACHE_DIR
        from poetry.utils._compat import Path

        boolean_validator = lambda val: val in {"true", "false", "1", "0"}
        boolean_normalizer = lambda val: val in ["true", "1"]

        unique_config_values = {
            "cache-dir": (
                str,
                lambda val: str(Path(val)),
                str(Path(CACHE_DIR) / "virtualenvs"),
            ),
            "virtualenvs.create": (boolean_validator, boolean_normalizer, True),
            "virtualenvs.in-project": (boolean_validator, boolean_normalizer, False),
            "virtualenvs.path": (
                str,
                lambda val: str(Path(val)),
                str(Path(CACHE_DIR) / "virtualenvs"),
            ),
        }

        return unique_config_values

    def handle(self):
        from poetry.config.config import Config
        from poetry.config.config_source import ConfigSource
        from poetry.locations import CONFIG_DIR
        from poetry.utils._compat import Path
        from poetry.utils._compat import basestring
        from poetry.utils.toml_file import TomlFile

        config = Config()
        config_file = TomlFile(Path(CONFIG_DIR) / "config.toml")
        config_source = ConfigSource(config_file)
        config.merge(config_source.file.read())

        auth_config_file = TomlFile(Path(CONFIG_DIR) / "auth.toml")
        auth_config_source = ConfigSource(auth_config_file, auth_config=True)

        local_config_file = TomlFile(self.poetry.file.parent / "poetry.toml")
        if local_config_file.exists():
            config.merge(local_config_file.read())

        if self.option("local"):
            config_source = ConfigSource(local_config_file)

        if not config_file.exists():
            config_file.path.parent.mkdir(parents=True, exist_ok=True)
            config_file.touch(mode=0o0600)

        if self.option("list"):
            self._list_configuration(config.all(), config.raw())

            return 0

        setting_key = self.argument("key")
        if not setting_key:
            return 0

        if self.argument("value") and self.option("unset"):
            raise RuntimeError("You can not combine a setting value with --unset")

        # show the value if no value is provided
        if not self.argument("value") and not self.option("unset"):
            m = re.match(r"^repos?(?:itories)?(?:\.(.+))?", self.argument("key"))
            if m:
                if not m.group(1):
                    value = {}
                    if config.get("repositories") is not None:
                        value = config.get("repositories")
                else:
                    repo = config.get("repositories.{}".format(m.group(1)))
                    if repo is None:
                        raise ValueError(
                            "There is no {} repository defined".format(m.group(1))
                        )

                    value = repo

                self.line(str(value))
            else:
                values = self.unique_config_values
                if setting_key not in values:
                    raise ValueError("There is no {} setting.".format(setting_key))

                value = config.get(setting_key)

                if not isinstance(value, basestring):
                    value = json.dumps(value)

                self.line(value)

            return 0

        values = self.argument("value")

        unique_config_values = self.unique_config_values
        if setting_key in unique_config_values:
            if self.option("unset"):
                return config_source.remove_property(setting_key)

            return self._handle_single_value(
                config_source, setting_key, unique_config_values[setting_key], values
            )

        # handle repositories
        m = re.match(r"^repos?(?:itories)?(?:\.(.+))?", self.argument("key"))
        if m:
            if not m.group(1):
                raise ValueError("You cannot remove the [repositories] section")

            if self.option("unset"):
                repo = config.get("repositories.{}".format(m.group(1)))
                if repo is None:
                    raise ValueError(
                        "There is no {} repository defined".format(m.group(1))
                    )

                config_source.remove_property("repositories.{}".format(m.group(1)))

                return 0

            if len(values) == 1:
                url = values[0]

                config_source.add_property(
                    "repositories.{}.url".format(m.group(1)), url
                )

                return 0

            raise ValueError(
                "You must pass the url. "
                "Example: poetry config repositories.foo https://bar.com"
            )

        # handle auth
        m = re.match(r"^(http-basic|pypi-token)\.(.+)", self.argument("key"))
        if m:
            if self.option("unset"):
                keyring_repository_password_del(config, m.group(2))
                auth_config_source.remove_property(
                    "{}.{}".format(m.group(1), m.group(2))
                )

                return 0

            if m.group(1) == "http-basic":
                if len(values) == 1:
                    username = values[0]
                    # Only username, so we prompt for password
                    password = self.secret("Password:")
                elif len(values) != 2:
                    raise ValueError(
                        "Expected one or two arguments "
                        "(username, password), got {}".format(len(values))
                    )
                else:
                    username = values[0]
                    password = values[1]

                property_value = dict(username=username)
                try:
                    keyring_repository_password_set(m.group(2), username, password)
                except RuntimeError:
                    property_value.update(password=password)

                auth_config_source.add_property(
                    "{}.{}".format(m.group(1), m.group(2)), property_value
                )
            elif m.group(1) == "pypi-token":
                if len(values) != 1:
                    raise ValueError(
                        "Expected only one argument (token), got {}".format(len(values))
                    )

                token = values[0]

                auth_config_source.add_property(
                    "{}.{}".format(m.group(1), m.group(2)), token
                )

            return 0

        raise ValueError("Setting {} does not exist".format(self.argument("key")))

    def _handle_single_value(self, source, key, callbacks, values):
        validator, normalizer, _ = callbacks

        if len(values) > 1:
            raise RuntimeError("You can only pass one value.")

        value = values[0]
        if not validator(value):
            raise RuntimeError('"{}" is an invalid value for {}'.format(value, key))

        source.add_property(key, normalizer(value))

        return 0

    def _list_configuration(self, config, raw, k=""):
        from poetry.utils._compat import basestring

        orig_k = k
        for key, value in sorted(config.items()):
            raw_val = raw.get(key)

            if isinstance(value, dict):
                k += "{}.".format(key)
                self._list_configuration(value, raw_val, k=k)
                k = orig_k

                continue
            elif isinstance(value, list):
                value = [
                    json.dumps(val) if isinstance(val, list) else val for val in value
                ]

                value = "[{}]".format(", ".join(value))

            if k.startswith("repositories."):
                message = "<c1>{}</c1> = <c2>{}</c2>".format(
                    k + key, json.dumps(raw_val)
                )
            elif isinstance(raw_val, basestring) and raw_val != value:
                message = "<c1>{}</c1> = <c2>{}</c2>  # {}".format(
                    k + key, json.dumps(raw_val), value
                )
            else:
                message = "<c1>{}</c1> = <c2>{}</c2>".format(k + key, json.dumps(value))

            self.line(message)

    def _list_setting(self, contents, setting=None, k=None, default=None):
        values = self._get_setting(contents, setting, k, default)

        for value in values:
            self.line(
                "<comment>{}</comment> = <info>{}</info>".format(value[0], value[1])
            )

    def _get_setting(self, contents, setting=None, k=None, default=None):
        orig_k = k

        if setting and setting.split(".")[0] not in contents:
            value = json.dumps(default)

            return [((k or "") + setting, value)]
        else:
            values = []
            for key, value in contents.items():
                if setting and key != setting.split(".")[0]:
                    continue

                if isinstance(value, dict) or key == "repositories" and k is None:
                    if k is None:
                        k = ""

                    k += re.sub(r"^config\.", "", key + ".")
                    if setting and len(setting) > 1:
                        setting = ".".join(setting.split(".")[1:])

                    values += self._get_setting(
                        value, k=k, setting=setting, default=default
                    )
                    k = orig_k

                    continue

                if isinstance(value, list):
                    value = [
                        json.dumps(val) if isinstance(val, list) else val
                        for val in value
                    ]

                    value = "[{}]".format(", ".join(value))

                value = json.dumps(value)

                values.append(((k or "") + key, value))

            return values

    def _get_formatted_value(self, value):
        if isinstance(value, list):
            value = [json.dumps(val) if isinstance(val, list) else val for val in value]

            value = "[{}]".format(", ".join(value))

        return json.dumps(value)
