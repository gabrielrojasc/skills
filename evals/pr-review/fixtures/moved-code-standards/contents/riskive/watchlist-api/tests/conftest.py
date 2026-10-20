import pytest
from rest_framework.test import APIClient

from accounts.models import Organization, User


@pytest.fixture
def organization(db):
    return Organization.objects.create(name="Acme")


@pytest.fixture
def other_organization(db):
    return Organization.objects.create(name="Globex")


@pytest.fixture
def user(organization):
    return User.objects.create_user(username="analyst", organization=organization)


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client
