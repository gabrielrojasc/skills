from rest_framework.test import APIClient

from watchlists.models import Watchlist, WatchlistMember


def test_lists_only_members_of_the_users_organization(api_client, organization, other_organization):
    own = Watchlist.objects.create(organization=organization, name="Board")
    other = Watchlist.objects.create(organization=other_organization, name="Other")
    WatchlistMember.objects.create(watchlist=own, name="Ada Lovelace")
    WatchlistMember.objects.create(watchlist=other, name="Grace Hopper")

    response = api_client.get("/watchlist-members/")

    assert response.status_code == 200
    assert [m["name"] for m in response.data["results"]] == ["Ada Lovelace"]


def test_hides_another_organizations_member(api_client, other_organization):
    other = Watchlist.objects.create(organization=other_organization, name="Other")
    member = WatchlistMember.objects.create(watchlist=other, name="Grace Hopper")

    response = api_client.get(f"/watchlist-members/{member.id}/")

    assert response.status_code == 404


def test_requires_authentication(db):
    response = APIClient().get("/watchlist-members/")

    assert response.status_code == 403
