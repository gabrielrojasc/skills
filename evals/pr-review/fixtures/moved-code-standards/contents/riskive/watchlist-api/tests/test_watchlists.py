from watchlists.models import Watchlist


def test_lists_only_watchlists_of_the_users_organization(api_client, organization, other_organization):
    Watchlist.objects.create(organization=organization, name="Board")
    Watchlist.objects.create(organization=other_organization, name="Other")

    response = api_client.get("/watchlists/")

    assert response.status_code == 200
    assert [w["name"] for w in response.data["results"]] == ["Board"]
