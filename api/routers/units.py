"""
Units router - additional unit endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.data_loader import data_store
from api.models import Unit

router = APIRouter(prefix="/v1/{edition}/units", tags=["Units"])


@router.get("/search/name/{name}", response_model=List[Unit])
async def search_units_by_name(edition: str, name: str, limit: int = Query(50, ge=1, le=200)):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")
    results = [u for u in store.units if name.lower() in u.name.lower()]
    return results[:limit]


@router.get("/random", response_model=Unit)
async def get_random_unit(edition: str, faction_type: Optional[str] = None):
    import random
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")
    units = store.units
    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]
    if not units:
        raise HTTPException(status_code=404, detail="No units found")
    return random.choice(units)


@router.get("/compare", response_model=List[Unit])
async def compare_units(edition: str, ids: str = Query(..., description="Comma-separated unit IDs")):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")
    unit_ids = [id.strip() for id in ids.split(',')]
    units = [store.get_unit_by_id(uid) for uid in unit_ids]
    units = [u for u in units if u]
    if not units:
        raise HTTPException(status_code=404, detail="No units found with provided IDs")
    return units


@router.get("/expensive", response_model=List[Unit])
async def get_most_expensive_units(
    edition: str,
    limit: int = Query(10, ge=1, le=50),
    faction_type: Optional[str] = None
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")
    units = store.units
    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]
    units = [u for u in units if u.points.base is not None and u.points.base > 0]
    units.sort(key=lambda u: u.points.base, reverse=True)
    return units[:limit]


@router.get("/cheap", response_model=List[Unit])
async def get_cheapest_units(
    edition: str,
    limit: int = Query(10, ge=1, le=50),
    faction_type: Optional[str] = None
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")
    units = store.units
    if faction_type:
        units = [u for u in units if u.faction_type == faction_type]
    units = [u for u in units if u.points.base is not None and u.points.base > 0]
    units.sort(key=lambda u: u.points.base)
    return units[:limit]


@router.get("/count")
async def count_units(
    edition: str,
    faction: Optional[str] = None,
    faction_type: Optional[str] = None,
    has_invuln: Optional[bool] = None,
    has_transport: Optional[bool] = None
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")
    results = store.search_units(
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
