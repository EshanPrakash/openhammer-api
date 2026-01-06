"""
Units router - additional unit endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.data_loader import data_store
from api.models import Unit

router = APIRouter(prefix="/units", tags=["Units"])


@router.get("/search/name/{name}", response_model=List[Unit])
async def search_units_by_name(
    name: str,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search units by name (case-insensitive partial match)

    Example: /units/search/name/terminator
    """
    results = [u for u in data_store.units if name.lower() in u.name.lower()]
    return results[:limit]


@router.get("/random", response_model=Unit)
async def get_random_unit(faction_type: Optional[str] = None):
    """
    Get a random unit, optionally filtered by faction type

    Example: /units/random?faction_type=Chaos
    """
    import random

    units = data_store.units

    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]

    if not units:
        raise HTTPException(status_code=404, detail="No units found")

    return random.choice(units)


@router.get("/compare", response_model=List[Unit])
async def compare_units(ids: str = Query(..., description="Comma-separated unit IDs")):
    """
    Compare multiple units by their IDs

    Example: /units/compare?ids=abc-123,def-456,ghi-789
    """
    unit_ids = [id.strip() for id in ids.split(',')]
    units = []

    for unit_id in unit_ids:
        unit = data_store.get_unit_by_id(unit_id)
        if unit:
            units.append(unit)

    if not units:
        raise HTTPException(status_code=404, detail="No units found with provided IDs")

    return units


@router.get("/expensive", response_model=List[Unit])
async def get_most_expensive_units(
    limit: int = Query(10, ge=1, le=50),
    faction_type: Optional[str] = None
):
    """
    Get the most expensive units by points cost

    Example: /units/expensive?limit=10&faction_type=Imperium
    """
    units = data_store.units

    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]

    # Filter units with valid points
    units = [u for u in units if u.points.base is not None and u.points.base > 0]

    # Sort by points descending
    units.sort(key=lambda u: u.points.base, reverse=True)

    return units[:limit]


@router.get("/cheap", response_model=List[Unit])
async def get_cheapest_units(
    limit: int = Query(10, ge=1, le=50),
    faction_type: Optional[str] = None
):
    """
    Get the cheapest units by points cost

    Example: /units/cheap?limit=10&faction_type=Xenos
    """
    units = data_store.units

    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]

    # Filter units with valid points
    units = [u for u in units if u.points.base is not None and u.points.base > 0]

    # Sort by points ascending
    units.sort(key=lambda u: u.points.base)

    return units[:limit]


@router.get("/count", response_model=dict)
async def count_units(
    faction: Optional[str] = None,
    faction_type: Optional[str] = None,
    has_invuln: Optional[bool] = None,
    has_transport: Optional[bool] = None
):
    """
    Count units matching filters (without returning the data)

    Example: /units/count?faction_type=Chaos&has_invuln=true
    """
    results = data_store.search_units(
        faction=faction,
        faction_type=faction_type,
        has_invuln=has_invuln,
        has_transport=has_transport
    )

    return {
        "count": len(results),
        "filters": {
            "faction": faction,
            "faction_type": faction_type,
            "has_invuln": has_invuln,
            "has_transport": has_transport
        }
    }
