import pytest


@pytest.mark.parametrize(
    "fighter_name",
    [
        "Dustin Poirier",
        "Conor McGregor",
        "Sean O'Malley",
        "Jose Aldo",
        "Jon Jones",
    ],
)
def test_fighter_performance_known_fighters_return_200(client, fighter_name):
    response = client.get(f"/fighters/{fighter_name}/performance")
    assert response.status_code == 200
    body = response.json()

    assert body["fighter"] == fighter_name
    assert body["total_fights"] >= body["wins"] + body["losses"]
    assert sum(body["method_breakdown"].values()) == body["wins"]
    assert len(body["last_performances"]) <= 5


def test_fighter_performance_covers_entire_catalog(client):
    """Regression guard: every fighter in the catalog must resolve without error.

    Protects against the /fighters/{name}/performance endpoint silently
    failing for a subset of fighters (e.g. a stale or empty event_cards.csv).
    """
    fighters = client.get("/fighters").json()
    assert len(fighters) > 0

    failures = []
    for fighter in fighters:
        response = client.get(f"/fighters/{fighter['name']}/performance")
        if response.status_code != 200:
            failures.append((fighter["name"], response.status_code))

    assert not failures, f"{len(failures)} fighters failed /performance: {failures[:10]}"


def test_head_to_head_counts_real_meetings(client, two_fighter_names):
    fighter_a, fighter_b = two_fighter_names
    response = client.get("/head-to-head", params={"fighter_a": fighter_a, "fighter_b": fighter_b})
    assert response.status_code == 200
    body = response.json()

    assert body["fighter_a"] == fighter_a
    assert body["fighter_b"] == fighter_b
    total = body["fighter_a_wins"] + body["fighter_b_wins"] + body["no_contests"]
    assert total == len(body["meetings"])


def test_head_to_head_unknown_fighter_returns_404(client, two_fighter_names):
    _, fighter_b = two_fighter_names
    response = client.get("/head-to-head", params={"fighter_a": "Nobody Nonexistent", "fighter_b": fighter_b})
    assert response.status_code == 404


def test_fighter_performance_totals_are_consistent(client, two_fighter_names):
    fighter_a, _ = two_fighter_names
    response = client.get(f"/fighters/{fighter_a}/performance")
    assert response.status_code == 200
    body = response.json()

    assert body["fighter"] == fighter_a
    assert body["wins"] + body["losses"] <= body["total_fights"]
    assert sum(body["method_breakdown"].values()) == body["wins"]
    assert len(body["last_performances"]) <= 5


def test_fighter_performance_unknown_fighter_returns_404(client):
    response = client.get("/fighters/Nobody Nonexistent/performance")
    assert response.status_code == 404
