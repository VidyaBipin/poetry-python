import pytest
from requests import ConnectionError

from poetry.repositories import Pool
from poetry.repositories import Repository
from poetry.repositories.exceptions import PackageNotFound
from poetry.repositories.legacy_repository import LegacyRepository
from tests.repositories.test_pypi_repository import MockRepository


def test_pool_raises_package_not_found_when_no_package_is_found():
    pool = Pool()
    pool.add_repository(Repository())

    with pytest.raises(PackageNotFound):
        pool.package("foo", "1.0.0")


def test_pool():
    pool = Pool()

    assert 0 == len(pool.repositories)
    assert pool.default is None


def test_pool_with_initial_repositories():
    repo = Repository()
    pool = Pool([repo])

    assert 1 == len(pool.repositories)
    assert pool.default is None


def test_repository_no_repository():
    pool = Pool()

    with pytest.raises(ValueError):
        pool.repository("foo")


def test_repository_from_normal_pool():
    repo = LegacyRepository("foo", "https://foo.bar")
    pool = Pool()
    pool.add_repository(repo)

    assert pool.repository("foo") is repo


def test_repository_from_optional_pool():
    repo = LegacyRepository("foo", "https://foo.bar")
    pool = Pool()
    pool.add_repository(repo, optional=True)

    assert pool.repository("foo") is repo


def test_pool_raises_connection_error_when_offline():
    repo = LegacyRepository("foo", "https://foo.bar")
    pool = Pool()
    pool.add_repository(repo)

    with pytest.raises(ConnectionError):
        pool.package("foo", "1.0.0")


def test_pool_fallback_through_repos():
    repo = LegacyRepository("foo", "https://foo.bar")
    pool = Pool()
    pool.add_repository(repo, optional=True)
    pool.add_repository(MockRepository())

    package = pool.package("requests", "2.18.4")
    assert package.name == "requests"
