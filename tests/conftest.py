import pytest


@pytest.fixture(autouse=True)
def enable_db_access(db: None) -> None:
    """Enable database access for all tests."""


pytestmark = pytest.mark.django_db
