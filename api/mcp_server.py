"""
OpenHammer MCP server - exposes unit/faction/weapon data as MCP tools, so
an MCP client can query it directly instead of calling the REST API.

Runs as its own process from api/main.py and reuses the in-process
data_store rather than calling the REST API over HTTP. Deps are pinned
separately in requirements-mcp.txt - see that file for why.
"""
import os
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.data_loader import data_store

mcp = FastMCP("OpenHammer", host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))


@mcp.custom_route("/", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Plain 200 for platform healthchecks - the MCP protocol itself only lives at /mcp."""
    return JSONResponse({"status": "ok"})


def _get_store(edition: str):
    store = data_store.get(edition)
    if not store:
        raise ValueError(f"Edition '{edition}' not found. Available editions: {data_store.list_editions()}")
    return store


@mcp.tool()
def list_editions() -> List[str]:
    """List available Warhammer 40K rules editions (e.g. '10e', '11e')."""
    return data_store.list_editions()


@mcp.tool()
def list_factions(edition: str, faction_type: Optional[str] = None) -> List[dict]:
    """List factions for an edition, optionally filtered by faction_type
    (Imperium, Chaos, Xenos, or Unaligned)."""
    store = _get_store(edition)
    factions = store.get_factions()
    if faction_type:
        factions = [f for f in factions if f["faction_type"] == faction_type]
    return factions


@mcp.tool()
def search_units(
    edition: str,
    name: Optional[str] = None,
    faction: Optional[str] = None,
    faction_type: Optional[str] = None,
    unit_type: Optional[str] = None,
    has_invuln: Optional[bool] = None,
    has_transport: Optional[bool] = None,
    keyword: Optional[str] = None,
    points_min: Optional[int] = None,
    points_max: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 50,
) -> List[dict]:
    """Search/filter units. name is a partial, case-insensitive match;
    faction and faction_type are exact matches; unit_type is 'unit' or
    'model'; keyword is an exact keyword match (e.g. 'Infantry');
    points_min/points_max bound base points cost. sort_by is 'name',
    'points', or 'faction', prefixed with '-' for descending (e.g.
    '-points'). Capped at limit (default 50)."""
    store = _get_store(edition)
    results = store.search_units(
        name=name,
        faction=faction,
        faction_type=faction_type,
        unit_type=unit_type,
        has_invuln=has_invuln,
        has_transport=has_transport,
        keyword=keyword,
        points_min=points_min,
        points_max=points_max,
    )

    if sort_by:
        reverse = sort_by.startswith("-")
        field = sort_by[1:] if reverse else sort_by
        if field == "name":
            results = sorted(results, key=lambda u: u.name.lower(), reverse=reverse)
        elif field == "points":
            results = sorted(results, key=lambda u: u.points.base or 0, reverse=reverse)
        elif field == "faction":
            results = sorted(results, key=lambda u: u.faction.lower(), reverse=reverse)

    return [u.model_dump() for u in results[:limit]]


@mcp.tool()
def get_unit(edition: str, unit_id: str) -> dict:
    """Get a single unit's full details (stats, weapons, abilities, keywords,
    points) by exact unit ID."""
    store = _get_store(edition)
    unit = store.get_unit_by_id(unit_id)
    if not unit:
        raise ValueError(f"Unit with ID '{unit_id}' not found in edition '{edition}'")
    return unit.model_dump()


@mcp.tool()
def compare_units(edition: str, unit_ids: List[str]) -> List[dict]:
    """Fetch multiple units by ID for side-by-side comparison. Unknown
    IDs are skipped."""
    store = _get_store(edition)
    units = [store.get_unit_by_id(uid) for uid in unit_ids]
    return [u.model_dump() for u in units if u]


@mcp.tool()
def random_unit(edition: str, faction_type: Optional[str] = None) -> dict:
    """Get a random unit, optionally restricted to a faction_type
    (Imperium, Chaos, Xenos, or Unaligned)."""
    import random

    store = _get_store(edition)
    units = store.units
    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]
    if not units:
        raise ValueError(f"No units found for faction_type '{faction_type}'")
    return random.choice(units).model_dump()


@mcp.tool()
def faction_details(edition: str, faction_name: str) -> dict:
    """Get a faction's stat breakdown: unit/model counts, total and average
    points, invulnerable-save and transport counts, and every keyword and
    special rule used by the faction."""
    store = _get_store(edition)
    units = store.get_units_by_faction(faction_name)
    if not units:
        raise ValueError(f"Faction '{faction_name}' not found in edition '{edition}'")

    total_points = sum(u.points.base for u in units if u.points.base)
    priced = [u for u in units if u.points.base]
    unit_types = {}
    for u in units:
        unit_types[u.type] = unit_types.get(u.type, 0) + 1

    keywords, special_rules = set(), set()
    for u in units:
        keywords.update(u.keywords)
        special_rules.update(u.special_rules)

    return {
        "name": faction_name,
        "faction_type": units[0].faction_type,
        "total_units": len(units),
        "unit_breakdown": unit_types,
        "total_points_value": total_points,
        "average_points": round(total_points / len(priced), 2) if priced else 0,
        "units_with_invuln": len([u for u in units if u.invuln_save]),
        "transports": len([u for u in units if u.transport]),
        "keywords": sorted(keywords),
        "special_rules": sorted(special_rules),
    }


@mcp.tool()
def search_weapons(edition: str, name: str, weapon_type: Optional[str] = None) -> dict:
    """Search for a weapon by (partial, case-insensitive) name and find
    which units carry it. weapon_type filters to 'ranged' or 'melee'."""
    store = _get_store(edition)
    results = []
    for unit in store.units:
        matches = []
        if weapon_type in (None, "ranged"):
            matches += [{"type": "ranged", "weapon": w.model_dump()} for w in unit.weapons.ranged if name.lower() in w.name.lower()]
        if weapon_type in (None, "melee"):
            matches += [{"type": "melee", "weapon": w.model_dump()} for w in unit.weapons.melee if name.lower() in w.name.lower()]
        if matches:
            results.append({
                "unit_name": unit.name,
                "unit_id": unit.id,
                "faction": unit.faction,
                "weapons": matches,
            })
    return {"search_term": name, "units_found": len(results), "results": results}


@mcp.tool()
def search_abilities_or_rules(edition: str, term: str, kind: str = "ability") -> dict:
    """Search unit abilities or special rules by (partial, case-insensitive)
    term. kind is 'ability' (searches ability name + description) or 'rule'
    (searches special_rules)."""
    store = _get_store(edition)
    results = []
    if kind == "rule":
        for unit in store.units:
            matches = [r for r in unit.special_rules if term.lower() in r.lower()]
            if matches:
                results.append({"unit_name": unit.name, "unit_id": unit.id, "faction": unit.faction, "matching_rules": matches})
    else:
        for unit in store.units:
            matches = [
                a.model_dump() for a in unit.abilities
                if term.lower() in a.name.lower() or (a.description and term.lower() in a.description.lower())
            ]
            if matches:
                results.append({"unit_name": unit.name, "unit_id": unit.id, "faction": unit.faction, "matching_abilities": matches})
    return {"search_term": term, "kind": kind, "units_found": len(results), "results": results}


if __name__ == "__main__":
    print("Loading unit data...")
    data_store.load_all()
    print(f"Loaded editions: {data_store.list_editions()}")
    mcp.run(transport="streamable-http")
