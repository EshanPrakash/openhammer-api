"""
Pytest suite for the OpenHammer API.

Runs entirely in-process against FastAPI's TestClient - no live server needed,
just `pytest` from the repo root. Each edition's data is loaded once (module
scope) the same way the real app loads it at startup (api/data_loader.py).

Tests avoid hardcoding specific unit/faction names or IDs where possible,
since data/json/{edition}/ is regenerated monthly by scripts/universal_parser.py
and specific units can be added, renamed, or removed by GW/BSData. Instead,
tests fetch a real sample via the API itself and assert on structural/contract
properties (status codes, shapes, filter behavior) rather than pinned values.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app

EDITIONS = ["10e", "11e"]
FACTION_TYPES = {"Imperium", "Chaos", "Xenos", "Unaligned"}


@pytest.fixture(scope="session")
def client():
    # The suite reuses one client for 100+ requests well within a minute, which would
    # otherwise trip the app's own 100/min rate limit; tests exercise business logic,
    # not rate limiting, so disable it here.
    app.state.limiter.enabled = False
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def sample_unit(client):
    """One real unit per edition, fetched live so tests stay valid across data resyncs."""
    units = {}
    for edition in EDITIONS:
        resp = client.get(f"/v1/{edition}/units", params={"limit": 1})
        units[edition] = resp.json()[0]
    return units


@pytest.fixture(scope="session")
def sample_faction(client):
    factions = {}
    for edition in EDITIONS:
        resp = client.get(f"/v1/{edition}/factions")
        factions[edition] = resp.json()[0]
    return factions


# --------------------------------------------------------------------------
# Root / unknown edition
# --------------------------------------------------------------------------

class TestRoot:
    def test_root_lists_both_editions(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert set(EDITIONS) <= set(resp.json()["editions"])

    def test_docs_available(self, client):
        assert client.get("/docs").status_code == 200


class TestUnknownEdition:
    @pytest.mark.parametrize("path", [
        "/v1/9e/stats",
        "/v1/9e/factions",
        "/v1/9e/units",
        "/v1/9e/units/does-not-exist",
        "/v1/9e/units/random",
        "/v1/9e/weapons/stats",
        "/v1/9e/abilities/keywords/list",
        "/v1/9e/bulk/units/by-ids",
    ])
    def test_returns_404(self, client, path):
        resp = client.get(path, params={"ids": "a"})
        assert resp.status_code == 404


# --------------------------------------------------------------------------
# Stats / edition parity
# --------------------------------------------------------------------------

@pytest.mark.parametrize("edition", EDITIONS)
class TestStats:
    def test_stats_shape(self, client, edition):
        data = client.get(f"/v1/{edition}/stats").json()
        assert data["total_units"] > 0
        assert data["total_factions"] == 35
        assert set(data["factions_by_type"]) == FACTION_TYPES
        assert sum(data["factions_by_type"].values()) == data["total_factions"]
        assert sum(data["units_by_faction_type"].values()) == data["total_units"]


class TestEditionParity:
    """Both editions should expose the same 35-faction structure, even though
    unit rosters differ (11e intentionally consolidates/changes some datasheets)."""

    def test_same_faction_names_across_editions(self, client):
        names = {
            edition: {f["name"] for f in client.get(f"/v1/{edition}/factions").json()}
            for edition in EDITIONS
        }
        assert names["10e"] == names["11e"]

    def test_same_faction_type_breakdown(self, client):
        breakdowns = {
            edition: client.get(f"/v1/{edition}/stats").json()["factions_by_type"]
            for edition in EDITIONS
        }
        assert breakdowns["10e"] == breakdowns["11e"]


# --------------------------------------------------------------------------
# Factions
# --------------------------------------------------------------------------

@pytest.mark.parametrize("edition", EDITIONS)
class TestFactions:
    def test_list_factions(self, client, edition):
        data = client.get(f"/v1/{edition}/factions").json()
        assert len(data) == 35
        assert all(f["unit_count"] > 0 for f in data)
        assert all(f["faction_type"] in FACTION_TYPES for f in data)

    def test_filter_by_faction_type(self, client, edition):
        data = client.get(f"/v1/{edition}/factions", params={"faction_type": "Chaos"}).json()
        assert len(data) == 7
        assert all(f["faction_type"] == "Chaos" for f in data)

    def test_faction_units(self, client, edition, sample_faction):
        name = sample_faction[edition]["name"]
        data = client.get(f"/v1/{edition}/factions/{name}/units").json()
        assert len(data) > 0
        assert all(u["faction"] == name for u in data)

    def test_faction_units_not_found(self, client, edition):
        resp = client.get(f"/v1/{edition}/factions/Not A Real Faction/units")
        assert resp.status_code == 404

    def test_faction_details(self, client, edition, sample_faction):
        name = sample_faction[edition]["name"]
        data = client.get(f"/v1/{edition}/factions/{name}/details").json()
        assert data["name"] == name
        assert data["total_units"] == sample_faction[edition]["unit_count"]
        assert data["stats"]["units_with_invuln"] <= data["total_units"]
        assert isinstance(data["keywords"], list)

    def test_faction_stats(self, client, edition, sample_faction):
        name = sample_faction[edition]["name"]
        data = client.get(f"/v1/{edition}/factions/{name}/stats").json()
        assert sum(data["points_distribution"].values()) <= sample_faction[edition]["unit_count"]
        assert 0 <= data["invulnerable_saves"]["percentage"] <= 100

    def test_faction_keywords(self, client, edition, sample_faction):
        name = sample_faction[edition]["name"]
        data = client.get(f"/v1/{edition}/factions/{name}/keywords").json()
        assert data["total_unique_keywords"] == len(data["keywords"])
        if data["keywords"]:
            counts = [k["unit_count"] for k in data["keywords"]]
            assert counts == sorted(counts, reverse=True)


# --------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------

@pytest.mark.parametrize("edition", EDITIONS)
class TestUnitSearch:
    def test_default_pagination(self, client, edition):
        data = client.get(f"/v1/{edition}/units").json()
        assert 0 < len(data) <= 100

    def test_limit_and_offset(self, client, edition):
        page1 = client.get(f"/v1/{edition}/units", params={"limit": 5, "offset": 0}).json()
        page2 = client.get(f"/v1/{edition}/units", params={"limit": 5, "offset": 5}).json()
        assert len(page1) == 5
        assert {u["id"] for u in page1}.isdisjoint({u["id"] for u in page2})

    def test_limit_bounds_rejected(self, client, edition):
        assert client.get(f"/v1/{edition}/units", params={"limit": 0}).status_code == 422
        assert client.get(f"/v1/{edition}/units", params={"limit": 501}).status_code == 422

    def test_name_filter_is_partial_and_case_insensitive(self, client, edition, sample_unit):
        needle = sample_unit[edition]["name"][:4]
        data = client.get(f"/v1/{edition}/units", params={"name": needle.upper(), "limit": 500}).json()
        assert len(data) > 0
        assert all(needle.lower() in u["name"].lower() for u in data)

    def test_faction_filter_exact(self, client, edition, sample_unit):
        faction = sample_unit[edition]["faction"]
        data = client.get(f"/v1/{edition}/units", params={"faction": faction, "limit": 500}).json()
        assert len(data) > 0
        assert all(u["faction"] == faction for u in data)

    def test_faction_type_filter(self, client, edition):
        data = client.get(f"/v1/{edition}/units", params={"faction_type": "Xenos", "limit": 500}).json()
        assert len(data) > 0
        assert all(u["faction_type"] == "Xenos" for u in data)

    def test_type_filter(self, client, edition):
        data = client.get(f"/v1/{edition}/units", params={"type": "model", "limit": 500}).json()
        assert len(data) > 0
        assert all(u["type"] == "model" for u in data)

    def test_has_invuln_filter(self, client, edition):
        data = client.get(f"/v1/{edition}/units", params={"has_invuln": True, "limit": 500}).json()
        assert len(data) > 0
        assert all(u["invuln_save"] is not None for u in data)

        data = client.get(f"/v1/{edition}/units", params={"has_invuln": False, "limit": 500}).json()
        assert all(u["invuln_save"] is None for u in data)

    def test_has_transport_filter(self, client, edition):
        data = client.get(f"/v1/{edition}/units", params={"has_transport": True, "limit": 500}).json()
        assert all(u["transport"] is not None for u in data)

    def test_points_range_filter(self, client, edition):
        data = client.get(
            f"/v1/{edition}/units", params={"points_min": 100, "points_max": 200, "limit": 500}
        ).json()
        assert len(data) > 0
        assert all(100 <= u["points"]["base"] <= 200 for u in data)

    def test_keyword_filter(self, client, edition):
        data = client.get(f"/v1/{edition}/units", params={"keyword": "Infantry", "limit": 500}).json()
        assert len(data) > 0
        assert all("Infantry" in u["keywords"] for u in data)

    @pytest.mark.parametrize("sort_by,key,reverse", [
        ("name", lambda u: u["name"].lower(), False),
        ("-name", lambda u: u["name"].lower(), True),
        ("points", lambda u: u["points"]["base"] or 0, False),
        ("-points", lambda u: u["points"]["base"] or 0, True),
        ("faction", lambda u: u["faction"].lower(), False),
    ])
    def test_sort_by(self, client, edition, sort_by, key, reverse):
        data = client.get(f"/v1/{edition}/units", params={"sort_by": sort_by, "limit": 500}).json()
        values = [key(u) for u in data]
        assert values == sorted(values, reverse=reverse)


@pytest.mark.parametrize("edition", EDITIONS)
class TestUnitLookup:
    def test_get_by_id(self, client, edition, sample_unit):
        unit = sample_unit[edition]
        resp = client.get(f"/v1/{edition}/units/{unit['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == unit["name"]

    def test_get_by_id_not_found(self, client, edition):
        resp = client.get(f"/v1/{edition}/units/not-a-real-id")
        assert resp.status_code == 404

    def test_search_by_name(self, client, edition, sample_unit):
        needle = sample_unit[edition]["name"][:4]
        data = client.get(f"/v1/{edition}/units/search/name/{needle}").json()
        assert len(data) > 0
        assert all(needle.lower() in u["name"].lower() for u in data)

    def test_random_unit(self, client, edition):
        resp = client.get(f"/v1/{edition}/units/random")
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_random_unit_with_faction_type(self, client, edition):
        data = client.get(f"/v1/{edition}/units/random", params={"faction_type": "Chaos"}).json()
        assert data["faction_type"] == "Chaos"

    def test_expensive_units_sorted_descending(self, client, edition):
        data = client.get(f"/v1/{edition}/units/expensive", params={"limit": 10}).json()
        points = [u["points"]["base"] for u in data]
        assert points == sorted(points, reverse=True)
        assert all(p > 0 for p in points)

    def test_cheap_units_sorted_ascending(self, client, edition):
        data = client.get(f"/v1/{edition}/units/cheap", params={"limit": 10}).json()
        points = [u["points"]["base"] for u in data]
        assert points == sorted(points)
        assert all(p > 0 for p in points)

    def test_count_matches_search(self, client, edition):
        # /units caps at limit=500 per request, but /units/count doesn't - paginate
        # through /units so this holds regardless of how large the filtered set is.
        count = client.get(f"/v1/{edition}/units/count", params={"faction_type": "Imperium"}).json()
        seen = []
        offset = 0
        while True:
            page = client.get(
                f"/v1/{edition}/units", params={"faction_type": "Imperium", "limit": 500, "offset": offset}
            ).json()
            if not page:
                break
            seen.extend(page)
            offset += 500
        assert count["count"] == len(seen)

    def test_compare_units(self, client, edition, sample_unit):
        real_id = sample_unit[edition]["id"]
        resp = client.get(f"/v1/{edition}/units/compare", params={"ids": f"{real_id},bogus-id"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == real_id

    def test_compare_units_all_invalid(self, client, edition):
        resp = client.get(f"/v1/{edition}/units/compare", params={"ids": "bogus-1,bogus-2"})
        assert resp.status_code == 404


# --------------------------------------------------------------------------
# Weapons
# --------------------------------------------------------------------------

@pytest.mark.parametrize("edition", EDITIONS)
class TestWeapons:
    def test_list_weapons(self, client, edition):
        data = client.get(f"/v1/{edition}/weapons/list").json()
        assert len(data) > 0
        assert data == sorted(data)

    def test_list_weapons_filtered_by_type(self, client, edition):
        # NOTE: there are ~2,300 unique weapon names combined (ranged+melee), but this endpoint
        # hard-caps at limit=500 - more than the endpoint's max, so a "melee results are a subset
        # of the unfiltered list" check can never hold at any valid limit (same class of cap-vs-
        # cardinality gap as /abilities/keywords/list). Only assert what's actually guaranteed:
        # the weapon_type param changes the result and each filtered set is internally sane.
        params = {"limit": 500}
        melee = set(client.get(f"/v1/{edition}/weapons/list", params={**params, "weapon_type": "melee"}).json())
        ranged = set(client.get(f"/v1/{edition}/weapons/list", params={**params, "weapon_type": "ranged"}).json())
        assert melee and ranged
        assert melee != ranged  # proves weapon_type actually changes the result, not a no-op

    def test_search_weapons(self, client, edition):
        weapon_name = client.get(f"/v1/{edition}/weapons/list").json()[0]
        data = client.get(f"/v1/{edition}/weapons/search/{weapon_name}").json()
        assert data["units_found"] > 0
        assert all(
            any(weapon_name.lower() in w["weapon"]["name"].lower() for w in r["weapons"])
            for r in data["results"]
        )

    def test_weapon_stats_totals_are_consistent(self, client, edition):
        data = client.get(f"/v1/{edition}/weapons/stats").json()
        assert data["total_weapon_entries"] == (
            data["ranged"]["total_entries"] + data["melee"]["total_entries"]
        )


# --------------------------------------------------------------------------
# Abilities / keywords / special rules
# --------------------------------------------------------------------------

@pytest.mark.parametrize("edition", EDITIONS)
class TestAbilities:
    def test_list_keywords(self, client, edition):
        # NOTE: keywords include each unit's own name (a real BattleScribe categoryLink,
        # not a data bug), so there are >1000 unique "keywords" total - far more than this
        # endpoint's hard max limit=500. Alphabetically-later common keywords like "Infantry"
        # are structurally unreachable through this endpoint at any limit. Only assert what
        # the endpoint can actually guarantee: a non-empty, sorted, limit-respecting slice.
        data = client.get(f"/v1/{edition}/abilities/keywords/list", params={"limit": 500}).json()
        assert 0 < len(data) <= 500
        assert data == sorted(data)

    def test_search_by_keyword(self, client, edition):
        data = client.get(f"/v1/{edition}/abilities/keywords/search/Infantry").json()
        assert data["units_found"] > 0
        assert all("infantry" in [kw.lower() for kw in u["matching_keywords"]] for u in data["results"])

    def test_list_special_rules(self, client, edition):
        data = client.get(f"/v1/{edition}/abilities/special-rules/list").json()
        assert len(data) > 0
        assert data == sorted(data)

    def test_search_special_rule(self, client, edition):
        rule = client.get(f"/v1/{edition}/abilities/special-rules/list").json()[0]
        data = client.get(f"/v1/{edition}/abilities/special-rules/search/{rule}").json()
        assert data["units_found"] > 0

    def test_search_abilities_by_term(self, client, edition):
        # units_found is the total match count; results is truncated to `limit` (default 50) -
        # request the max limit so the equality check below is meaningful rather than incidental.
        term = "strike"
        data = client.get(f"/v1/{edition}/abilities/search/{term}", params={"limit": 200}).json()
        assert data["units_found"] > 0
        assert data["units_found"] == len(data["results"])
        for unit_result in data["results"]:
            assert any(
                term in a["name"].lower() or (a["description"] and term in a["description"].lower())
                for a in unit_result["abilities"]
            )


# --------------------------------------------------------------------------
# Bulk operations
# --------------------------------------------------------------------------

@pytest.mark.parametrize("edition", EDITIONS)
class TestBulk:
    def test_bulk_by_ids_partial_match(self, client, edition, sample_unit):
        real_id = sample_unit[edition]["id"]
        data = client.get(f"/v1/{edition}/bulk/units/by-ids", params={"ids": f"{real_id},nope"}).json()
        assert data["found"] == 1
        assert data["not_found"] == ["nope"]

    def test_bulk_by_names_exact_match(self, client, edition, sample_unit):
        real_name = sample_unit[edition]["name"]
        data = client.get(
            f"/v1/{edition}/bulk/units/by-names", params={"names": f"{real_name},Nonexistent Unit XYZ"}
        ).json()
        assert data["found"] >= 1
        assert "Nonexistent Unit XYZ" in data["not_found"]

    def test_stats_by_keyword(self, client, edition):
        data = client.get(f"/v1/{edition}/bulk/stats/by-keyword", params={"keyword": "Infantry"}).json()
        assert data["unit_count"] > 0
        assert sum(data["faction_type_breakdown"].values()) == data["unit_count"]

    def test_stats_by_keyword_unknown_keyword(self, client, edition):
        data = client.get(
            f"/v1/{edition}/bulk/stats/by-keyword", params={"keyword": "NotARealKeywordXYZ"}
        ).json()
        assert data["unit_count"] == 0
        assert data["stats"] is None

    def test_stats_by_faction_type(self, client, edition):
        data = client.get(
            f"/v1/{edition}/bulk/stats/by-faction-type", params={"faction_type": "Chaos"}
        ).json()
        assert sum(data["faction_breakdown"].values()) == data["total_units"]

    def test_stats_by_faction(self, client, edition, sample_faction):
        name = sample_faction[edition]["name"]
        data = client.get(f"/v1/{edition}/bulk/stats/by-faction", params={"faction": name}).json()
        assert data["total_units"] == sample_faction[edition]["unit_count"]
        assert data["stats"]["cheapest_unit"] <= data["stats"]["most_expensive_unit"]

    def test_export_all_units_summary(self, client, edition):
        stats = client.get(f"/v1/{edition}/stats").json()
        data = client.get(f"/v1/{edition}/bulk/export/all-units-summary").json()
        assert data["total_units"] == stats["total_units"]
