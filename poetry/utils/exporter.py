import urllib.parse

from pathlib import Path
from typing import Optional
from typing import Sequence
from typing import Union

from cleo.io.io import IO

from poetry.poetry import Poetry
from poetry.utils._compat import decode


class Exporter(object):
    """
    Exporter class to export a lock file to alternative formats.
    """

    FORMAT_REQUIREMENTS_TXT = "requirements.txt"
    FORMAT_SETUP_PY = "setup.py"
    #: The names of the supported export formats.
    ACCEPTED_FORMATS = (FORMAT_REQUIREMENTS_TXT, FORMAT_SETUP_PY)
    ALLOWED_HASH_ALGORITHMS = ("sha256", "sha384", "sha512")

    def __init__(self, poetry: Poetry) -> None:
        self._poetry = poetry

    def export(
        self,
        fmt: str,
        cwd: Path,
        output: Union[IO, str],
        with_hashes: bool = True,
        dev: bool = False,
        extras: Optional[Union[bool, Sequence[str]]] = None,
        with_credentials: bool = False,
    ) -> None:
        if fmt not in self.ACCEPTED_FORMATS:
            raise ValueError("Invalid export format: {}".format(fmt))

        getattr(self, "_export_{}".format(fmt.replace(".", "_")))(
            cwd,
            output,
            with_hashes=with_hashes,
            dev=dev,
            extras=extras,
            with_credentials=with_credentials,
        )

    def _export_setup_py(
        self,
        cwd: Path,
        output: Union[IO, str],
        **_  # Cannot use any of the extra kwargs with the SdistBuilder
    ) -> None:
        from poetry.core.masonry.builders.sdist import SdistBuilder

        builder = SdistBuilder(self._poetry)
        content = builder.build_setup()

        self._output(content, cwd, output)

    def _export_requirements_txt(
        self,
        cwd: Path,
        output: Union[IO, str],
        with_hashes: bool = True,
        dev: bool = False,
        extras: Optional[Union[bool, Sequence[str]]] = None,
        with_credentials: bool = False,
    ) -> None:
        indexes = set()
        content = ""
        dependency_lines = set()

        for dependency_package in self._poetry.locker.get_project_dependency_packages(
            project_requires=self._poetry.package.all_requires, dev=dev, extras=extras
        ):
            line = ""

            dependency = dependency_package.dependency
            package = dependency_package.package

            if package.develop:
                line += "-e "

            requirement = dependency.to_pep_508(with_extras=False)
            is_direct_reference = (
                dependency.is_vcs()
                or dependency.is_url()
                or dependency.is_file()
                or dependency.is_directory()
            )

            if is_direct_reference:
                line = requirement
            else:
                line = "{}=={}".format(package.name, package.version)
                if ";" in requirement:
                    markers = requirement.split(";", 1)[1].strip()
                    if markers:
                        line += "; {}".format(markers)

            if not is_direct_reference and package.source_url:
                indexes.add(package.source_url)

            if package.files and with_hashes:
                hashes = []
                for f in package.files:
                    h = f["hash"]
                    algorithm = "sha256"
                    if ":" in h:
                        algorithm, h = h.split(":")

                        if algorithm not in self.ALLOWED_HASH_ALGORITHMS:
                            continue

                    hashes.append("{}:{}".format(algorithm, h))

                if hashes:
                    line += " \\\n"
                    for i, h in enumerate(hashes):
                        line += "    --hash={}{}".format(
                            h, " \\\n" if i < len(hashes) - 1 else ""
                        )
            dependency_lines.add(line)

        content += "\n".join(sorted(dependency_lines))
        content += "\n"

        if indexes:
            # If we have extra indexes, we add them to the beginning of the output
            indexes_header = ""
            for index in sorted(indexes):
                repositories = [
                    r
                    for r in self._poetry.pool.repositories
                    if r.url == index.rstrip("/")
                ]
                if not repositories:
                    continue
                repository = repositories[0]
                if (
                    self._poetry.pool.has_default()
                    and repository is self._poetry.pool.repositories[0]
                ):
                    url = (
                        repository.authenticated_url
                        if with_credentials
                        else repository.url
                    )
                    indexes_header = "--index-url {}\n".format(url)
                    continue

                url = (
                    repository.authenticated_url if with_credentials else repository.url
                )
                parsed_url = urllib.parse.urlsplit(url)
                if parsed_url.scheme == "http":
                    indexes_header += "--trusted-host {}\n".format(parsed_url.netloc)
                indexes_header += "--extra-index-url {}\n".format(url)

            content = indexes_header + "\n" + content

        self._output(content, cwd, output)

    def _output(self, content: str, cwd: Path, output: Union[IO, str]) -> None:
        decoded = decode(content)
        try:
            output.write(decoded)
        except AttributeError:
            filepath = cwd / output
            with filepath.open("w", encoding="utf-8") as f:
                f.write(decoded)
