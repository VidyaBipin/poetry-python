import json
import pytest
import shutil

from poetry.packages import Dependency
from poetry.repositories.pypi_repository import PyPiRepository
from poetry.utils._compat import PY35
from poetry.utils._compat import Path


class MockRepository(PyPiRepository):

    JSON_FIXTURES = Path(__file__).parent / "fixtures" / "pypi.org" / "json"
    DIST_FIXTURES = Path(__file__).parent / "fixtures" / "pypi.org" / "dists"

    def __init__(
        self, fallback=False, plat="Linux", is32bit=True, imp_name="py", pyver=(3, 7, 2)
    ):
        super(MockRepository, self).__init__(
            url="http://foo.bar", disable_cache=True, fallback=fallback
        )

        # Mock different hardware configurations
        self._sys_info = {
            "plat": plat.lower(),
            "is32bit": is32bit,
            "imp_name": imp_name,
            "pyver": pyver,
        }

    def _get(self, url):
        parts = url.split("/")[1:]
        name = parts[0]
        if len(parts) == 3:
            version = parts[1]
        else:
            version = None

        if not version:
            fixture = self.JSON_FIXTURES / (name + ".json")
        else:
            fixture = self.JSON_FIXTURES / name / (version + ".json")
            if not fixture.exists():
                fixture = self.JSON_FIXTURES / (name + ".json")

        if not fixture.exists():
            return

        with fixture.open(encoding="utf-8") as f:
            return json.loads(f.read())

    def _download(self, url, dest):
        filename = url.split("/")[-1]

        fixture = self.DIST_FIXTURES / filename

        shutil.copyfile(str(fixture), dest)


def test_find_packages():
    repo = MockRepository()
    packages = repo.find_packages("requests", "^2.18")

    assert len(packages) == 5


def test_find_packages_with_prereleases():
    repo = MockRepository()
    packages = repo.find_packages("toga", ">=0.3.0.dev2")

    assert len(packages) == 7


def test_find_packages_does_not_select_prereleases_if_not_allowed():
    repo = MockRepository()
    packages = repo.find_packages("pyyaml")

    assert len(packages) == 1


def test_package():
    repo = MockRepository()

    package = repo.package("requests", "2.18.4")

    assert package.name == "requests"
    assert len(package.requires) == 4
    assert len(package.extras["security"]) == 3
    assert len(package.extras["socks"]) == 2

    win_inet = package.extras["socks"][0]
    assert win_inet.name == "win-inet-pton"
    assert win_inet.python_versions == "~2.7 || ~2.6"
    assert str(win_inet.marker) == (
        'sys_platform == "win32" and (python_version == "2.7" '
        'or python_version == "2.6") and extra == "socks"'
    )


def test_fallback_on_downloading_packages():
    repo = MockRepository(fallback=True)

    package = repo.package("jupyter", "1.0.0")

    assert package.name == "jupyter"
    assert len(package.requires) == 6

    dependency_names = sorted([dep.name for dep in package.requires])
    assert dependency_names == [
        "ipykernel",
        "ipywidgets",
        "jupyter-console",
        "nbconvert",
        "notebook",
        "qtconsole",
    ]


# Mock platform specific wheels for testing
numpy_plat_spec_wheels = [
    (
        "numpy-1.16.2-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel."
        "macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
    ),
    "numpy-1.16.2-cp27-cp27m-manylinux1_i686.whl",
    "numpy-1.16.2-cp27-cp27m-manylinux1_x86_64.whl",
    "numpy-1.16.2-cp27-cp27mu-manylinux1_i686.whl",
    "numpy-1.16.2-cp27-cp27mu-manylinux1_x86_64.whl",
    "numpy-1.16.2-cp27-cp27m-win32.whl",
    "numpy-1.16.2-cp27-cp27m-win_amd64.whl",
    (
        "numpy-1.16.2-cp35-cp35m-macosx_10_6_intel.macosx_10_9_intel."
        "macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
    ),
    "numpy-1.16.2-cp35-cp35m-manylinux1_i686.whl",
    "numpy-1.16.2-cp35-cp35m-manylinux1_x86_64.whl",
    "numpy-1.16.2-cp35-cp35m-win32.whl",
    "numpy-1.16.2-cp35-cp35m-win_amd64.whl",
    (
        "numpy-1.16.2-cp36-cp36m-macosx_10_6_intel.macosx_10_9_intel."
        "macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
    ),
    "numpy-1.16.2-cp36-cp36m-manylinux1_i686.whl",
    "numpy-1.16.2-cp36-cp36m-manylinux1_x86_64.whl",
    "numpy-1.16.2-cp36-cp36m-win32.whl",
    "numpy-1.16.2-cp36-cp36m-win_amd64.whl",
    (
        "numpy-1.16.2-cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel."
        "macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
    ),
    "numpy-1.16.2-cp37-cp37m-manylinux1_i686.whl",
    "numpy-1.16.2-cp37-cp37m-manylinux1_x86_64.whl",
    "numpy-1.16.2-cp37-cp37m-win32.whl",
    "numpy-1.16.2-cp37-cp37m-win_amd64.whl",
]


@pytest.mark.parametrize(
    "plat,is32bit,imp_name,pyver,best_wheel",
    [
        (
            "Linux",
            False,
            "CPython",
            ("3", "7", "2"),
            "numpy-1.16.2-cp37-cp37m-manylinux1_x86_64.whl",
        ),
        (
            "Darwin",
            False,
            "CPython",
            ("2", "7", "3"),
            (
                "numpy-1.16.2-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel."
                "macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl"
            ),
        ),
        (
            "Windows",
            False,
            "CPython",
            ("3", "6", "2"),
            "numpy-1.16.2-cp36-cp36m-win_amd64.whl",
        ),
        (
            "Windows",
            True,
            "CPython",
            ("3", "5", "0a1"),
            "numpy-1.16.2-cp35-cp35m-win32.whl",
        ),
    ],
)
def test_fallback_selects_correct_platform_wheel(
    plat, is32bit, imp_name, pyver, best_wheel
):
    repo = MockRepository(
        fallback=True, plat=plat, is32bit=is32bit, imp_name=imp_name, pyver=pyver
    )
    assert best_wheel == repo._pick_platform_specific_wheel(numpy_plat_spec_wheels)


def test_fallback_inspects_sdist_first_if_no_matching_wheels_can_be_found():
    repo = MockRepository(fallback=True)

    package = repo.package("isort", "4.3.4")

    assert package.name == "isort"
    assert len(package.requires) == 1

    dep = package.requires[0]
    assert dep.name == "futures"
    assert dep.python_versions == "~2.7"


@pytest.mark.skipif(not PY35, reason="AST parsing does not work for Python <3.4")
def test_fallback_can_read_setup_to_get_dependencies():
    repo = MockRepository(fallback=True)

    package = repo.package("sqlalchemy", "1.2.12")

    assert package.name == "sqlalchemy"
    assert len(package.requires) == 0

    assert package.extras == {
        "mssql_pymssql": [Dependency("pymssql", "*")],
        "mssql_pyodbc": [Dependency("pyodbc", "*")],
        "mysql": [Dependency("mysqlclient", "*")],
        "oracle": [Dependency("cx_oracle", "*")],
        "postgresql": [Dependency("psycopg2", "*")],
        "postgresql_pg8000": [Dependency("pg8000", "*")],
        "postgresql_psycopg2binary": [Dependency("psycopg2-binary", "*")],
        "postgresql_psycopg2cffi": [Dependency("psycopg2cffi", "*")],
        "pymysql": [Dependency("pymysql", "*")],
    }


def test_pypi_repository_supports_reading_bz2_files():
    repo = MockRepository(fallback=True)

    package = repo.package("twisted", "18.9.0")

    assert package.name == "twisted"
    assert sorted(package.requires, key=lambda r: r.name) == [
        Dependency("attrs", ">=17.4.0"),
        Dependency("Automat", ">=0.3.0"),
        Dependency("constantly", ">=15.1"),
        Dependency("hyperlink", ">=17.1.1"),
        Dependency("incremental", ">=16.10.1"),
        Dependency("PyHamcrest", ">=1.9.0"),
        Dependency("zope.interface", ">=4.4.2"),
    ]

    expected_extras = {
        "all_non_platform": [
            Dependency("appdirs", ">=1.4.0"),
            Dependency("cryptography", ">=1.5"),
            Dependency("h2", ">=3.0,<4.0"),
            Dependency("idna", ">=0.6,!=2.3"),
            Dependency("priority", ">=1.1.0,<2.0"),
            Dependency("pyasn1", "*"),
            Dependency("pyopenssl", ">=16.0.0"),
            Dependency("pyserial", ">=3.0"),
            Dependency("service_identity", "*"),
            Dependency("soappy", "*"),
        ]
    }

    for name, deps in expected_extras.items():
        assert expected_extras[name] == sorted(
            package.extras[name], key=lambda r: r.name
        )
