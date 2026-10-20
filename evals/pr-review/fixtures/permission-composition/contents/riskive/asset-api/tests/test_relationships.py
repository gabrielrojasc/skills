import pytest

LIST_URL = "/relationships/"
TYPES_URL = "/relationship-types/"


@pytest.mark.django_db
def test_list_requires_view_scope(api_client, user, scopes):
    scopes.set(user, [])
    assert api_client.get(LIST_URL).status_code == 403


@pytest.mark.django_db
def test_list_with_view_scope(api_client, user, scopes, relationship):
    scopes.set(user, ["entity:view_relationships"])
    response = api_client.get(LIST_URL)
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["results"]] == [relationship.pk]


@pytest.mark.django_db
def test_create_requires_manage_scope(api_client, user, scopes, parent, child, relationship_type):
    scopes.set(user, ["entity:view_relationships"])
    body = {"parent": parent.pk, "child": child.pk, "type": relationship_type.pk}
    assert api_client.post(LIST_URL, body).status_code == 403


@pytest.mark.django_db
def test_list_with_family_mapping_flag(api_client, user, scopes, flags, relationship):
    scopes.set(user, [])
    flags.enable(user.company, "relationships.family_mapping")
    assert api_client.get(LIST_URL).status_code == 200
    assert api_client.get(TYPES_URL).status_code == 200


@pytest.mark.django_db
def test_flag_does_not_grant_create(api_client, user, scopes, flags, parent, child, relationship_type):
    scopes.set(user, [])
    flags.enable(user.company, "relationships.family_mapping")
    body = {"parent": parent.pk, "child": child.pk, "type": relationship_type.pk}
    assert api_client.post(LIST_URL, body).status_code == 403
