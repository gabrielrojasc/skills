import pytest
from rest_framework.test import APIClient

from accounts.factories import CompanyFactory, UserFactory
from assets.factories import AssetFactory
from relationships.models import Relationship, RelationshipType


@pytest.fixture
def user():
    return UserFactory(company=CompanyFactory())


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def scopes(monkeypatch):
    granted = {}
    monkeypatch.setattr("core.opa_client.scopes_for", lambda user: set(granted.get(user.pk, [])))

    class Scopes:
        def set(self, user, values):
            granted[user.pk] = values

    return Scopes()


@pytest.fixture
def flags(monkeypatch):
    enabled = set()
    monkeypatch.setattr("core.flags.is_feature_enabled", lambda request, flag: (request.user.company_id, flag) in enabled)
    monkeypatch.setattr("relationships.services.is_feature_enabled", lambda request, flag: (request.user.company_id, flag) in enabled)

    class Flags:
        def enable(self, company, flag):
            enabled.add((company.pk, flag))

    return Flags()


@pytest.fixture
def relationship_type():
    return RelationshipType.objects.create(name="subsidiary")


@pytest.fixture
def parent(user):
    return AssetFactory(company=user.company)


@pytest.fixture
def child(user):
    return AssetFactory(company=user.company)


@pytest.fixture
def relationship(user, parent, child, relationship_type):
    return Relationship.objects.create(company=user.company, parent=parent, child=child, type=relationship_type)
