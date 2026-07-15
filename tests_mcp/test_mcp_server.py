"""
Pytest suite for the OpenHammer MCP server.

Runs entirely in-process against the FastMCP instance via mcp.shared.memory's
in-memory client/server session - no live server, no network, same philosophy
as tests/test_api.py's use of FastAPI's TestClient.

Requires the mcp package, which only lives in venv-mcp/ (see requirements-mcp.txt),
not the main app's venv - so this suite is invoked separately from tests/test_api.py:

    source venv-mcp/bin/activate
    pip install -r requirements-mcp-dev.txt
    pytest -c pytest-mcp.ini

The MCP tools are thin wrappers around the same EditionStore/sort_units logic
tests/test_api.py already exercises thoroughly, so this suite focuses on the
MCP-specific plumbing (tool registration, argument passing, error surfacing,
return shapes) rather than re-deriving full confidence in the underlying
search/filter behavior. Like tests/test_api.py, it avoids hardcoding specific
unit/faction/weapon/ability names, since data/json/{edition}/ is regenerated
monthly - samples are fetched live instead.

Every test opens its own `async with mcp_session() as session:` rather than
receiving a live session from a yield-based fixture. The in-memory transport's
anyio task group requires __aenter__/__aexit__ to happen in the same asyncio
task, which pytest-asyncio can't guarantee for a session/function-scoped
generator fixture (setup and teardown are driven by separate calls, each
wrapped in its own Task) - opening it inline avoids that entirely, and it's
cheap enough (no real process/network) that per-test setup costs nothing
meaningful.
"""
import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from api.data_loader import data_store
from api.mcp_server import mcp

EDITIONS = ["10e", "11e"]
TOOL_NAMES = {
    "list_editions", "list_factions", "search_units", "get_unit",
    "compare_units", "random_unit", "faction_details", "search_weapons",
    "search_abilities_or_rules",
}


def unwrap(result):
    """Tool results come back as structuredContent (wrapped in {"result": ...}
    when the return type isn't itself an object, e.g. List[str]/List[dict]) or
    as plain text content (for bare `dict` returns, which FastMCP can't infer
    an output schema for)."""
    if result.isError:
        raise RuntimeError(result.content[0].text)
    sc = result.structuredContent
    if sc is not None:
        return sc["result"] if set(sc.keys()) == {"result"} else sc
    return json.loads(result.content[0].text)


async def call(session, tool_name, **kwargs):
    return unwrap(await session.call_tool(tool_name, kwargs))


@pytest.fixture
def mcp_session():
    """A callable that opens a fresh in-memory client/server session: use as
    `async with mcp_session() as session:` inside each test."""
    if not data_store.list_editions():
        data_store.load_all()
    return lambda: create_connected_server_and_client_session(mcp)


@pytest.fixture
def sample_unit(mcp_session):
    """One real unit per edition, fetched live so tests stay valid across data resyncs."""
    async def _fetch():
        async with mcp_session() as session:
            return {edition: (await call(session, "search_units", edition=edition, limit=1))[0] for edition in EDITIONS}
    return _fetch


@pytest.fixture
def sample_faction(mcp_session):
    async def _fetch():
        async with mcp_session() as session:
            return {edition: (await call(session, "list_factions", edition=edition))[0] for edition in EDITIONS}
    return _fetch


class TestToolRegistration:
    async def test_all_tools_present(self, mcp_session):
        async with mcp_session() as session:
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == TOOL_NAMES


class TestListEditions:
    async def test_lists_both_editions(self, mcp_session):
        async with mcp_session() as session:
            assert set(await call(session, "list_editions")) == set(EDITIONS)

    async def test_unknown_edition_raises(self, mcp_session):
        async with mcp_session() as session:
            with pytest.raises(RuntimeError, match="not found"):
                await call(session, "list_factions", edition="9e")


@pytest.mark.parametrize("edition", EDITIONS)
class TestListFactions:
    async def test_lists_35_factions(self, mcp_session, edition):
        async with mcp_session() as session:
            factions = await call(session, "list_factions", edition=edition)
            assert len(factions) == 35
            assert all(f["unit_count"] > 0 for f in factions)

    async def test_filter_by_faction_type(self, mcp_session, edition):
        async with mcp_session() as session:
            factions = await call(session, "list_factions", edition=edition, faction_type="Chaos")
            assert len(factions) == 7
            assert all(f["faction_type"] == "Chaos" for f in factions)


@pytest.mark.parametrize("edition", EDITIONS)
class TestSearchUnits:
    async def test_name_filter_is_partial_and_case_insensitive(self, mcp_session, sample_unit, edition):
        unit = (await sample_unit())[edition]
        needle = unit["name"][:4]
        async with mcp_session() as session:
            results = await call(session, "search_units", edition=edition, name=needle.upper(), limit=500)
        assert len(results) > 0
        assert all(needle.lower() in u["name"].lower() for u in results)

    async def test_faction_type_filter(self, mcp_session, edition):
        async with mcp_session() as session:
            results = await call(session, "search_units", edition=edition, faction_type="Xenos", limit=500)
        assert len(results) > 0
        assert all(u["faction_type"] == "Xenos" for u in results)

    async def test_points_range_filter(self, mcp_session, edition):
        async with mcp_session() as session:
            results = await call(session, "search_units", edition=edition, points_min=100, points_max=200, limit=500)
        assert len(results) > 0
        assert all(100 <= u["points"]["base"] <= 200 for u in results)

    async def test_limit_respected(self, mcp_session, edition):
        async with mcp_session() as session:
            results = await call(session, "search_units", edition=edition, limit=3)
        assert len(results) <= 3

    @pytest.mark.parametrize("sort_by,key,reverse", [
        ("name", lambda u: u["name"].lower(), False),
        ("-points", lambda u: u["points"]["base"] or 0, True),
        ("faction", lambda u: u["faction"].lower(), False),
    ])
    async def test_sort_by(self, mcp_session, edition, sort_by, key, reverse):
        async with mcp_session() as session:
            results = await call(session, "search_units", edition=edition, sort_by=sort_by, limit=500)
        values = [key(u) for u in results]
        assert values == sorted(values, reverse=reverse)


@pytest.mark.parametrize("edition", EDITIONS)
class TestGetUnit:
    async def test_get_by_id(self, mcp_session, sample_unit, edition):
        unit = (await sample_unit())[edition]
        async with mcp_session() as session:
            result = await call(session, "get_unit", edition=edition, unit_id=unit["id"])
        assert result["name"] == unit["name"]

    async def test_unknown_id_raises(self, mcp_session, edition):
        async with mcp_session() as session:
            with pytest.raises(RuntimeError, match="not found"):
                await call(session, "get_unit", edition=edition, unit_id="not-a-real-id")


@pytest.mark.parametrize("edition", EDITIONS)
class TestCompareUnits:
    async def test_skips_unknown_ids(self, mcp_session, sample_unit, edition):
        real_id = (await sample_unit())[edition]["id"]
        async with mcp_session() as session:
            results = await call(session, "compare_units", edition=edition, unit_ids=[real_id, "bogus-id"])
        assert len(results) == 1
        assert results[0]["id"] == real_id


@pytest.mark.parametrize("edition", EDITIONS)
class TestRandomUnit:
    async def test_returns_a_unit(self, mcp_session, edition):
        async with mcp_session() as session:
            result = await call(session, "random_unit", edition=edition)
        assert "id" in result

    async def test_faction_type_filter(self, mcp_session, edition):
        async with mcp_session() as session:
            result = await call(session, "random_unit", edition=edition, faction_type="Chaos")
        assert result["faction_type"] == "Chaos"


@pytest.mark.parametrize("edition", EDITIONS)
class TestFactionDetails:
    async def test_matches_faction_unit_count(self, mcp_session, sample_faction, edition):
        faction = (await sample_faction())[edition]
        async with mcp_session() as session:
            details = await call(session, "faction_details", edition=edition, faction_name=faction["name"])
        assert details["total_units"] == faction["unit_count"]
        assert details["units_with_invuln"] <= details["total_units"]
        assert isinstance(details["keywords"], list)

    async def test_unknown_faction_raises(self, mcp_session, edition):
        async with mcp_session() as session:
            with pytest.raises(RuntimeError, match="not found"):
                await call(session, "faction_details", edition=edition, faction_name="Not A Real Faction")


@pytest.mark.parametrize("edition", EDITIONS)
class TestSearchWeapons:
    async def test_finds_a_real_weapon(self, mcp_session, sample_unit, edition):
        unit = (await sample_unit())[edition]
        weapons = unit["weapons"]["ranged"] + unit["weapons"]["melee"]
        if not weapons:
            pytest.skip("sample unit has no weapons")
        async with mcp_session() as session:
            result = await call(session, "search_weapons", edition=edition, name=weapons[0]["name"])
        assert result["units_found"] > 0


@pytest.mark.parametrize("edition", EDITIONS)
class TestSearchAbilitiesOrRules:
    async def test_finds_a_real_ability(self, mcp_session, sample_unit, edition):
        unit = (await sample_unit())[edition]
        abilities = unit["abilities"]
        if not abilities:
            pytest.skip("sample unit has no abilities")
        term = abilities[0]["name"].split()[0]
        async with mcp_session() as session:
            result = await call(session, "search_abilities_or_rules", edition=edition, term=term, kind="ability")
        assert result["units_found"] > 0

    async def test_finds_a_real_rule(self, mcp_session, sample_unit, edition):
        unit = (await sample_unit())[edition]
        rules = unit["special_rules"]
        if not rules:
            pytest.skip("sample unit has no special rules")
        term = rules[0].split()[0]
        async with mcp_session() as session:
            result = await call(session, "search_abilities_or_rules", edition=edition, term=term, kind="rule")
        assert result["units_found"] > 0
