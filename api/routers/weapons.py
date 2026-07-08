"""
Weapons router - weapon-related endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.data_loader import data_store

router = APIRouter(prefix="/v1/{edition}/weapons", tags=["Weapons"])


@router.get("/list", response_model=List[str])
async def list_all_weapons(
    edition: str,
    weapon_type: str = Query(None, description="Filter by 'ranged' or 'melee'"),
    limit: int = Query(100, ge=1, le=500)
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    weapons = set()
    for unit in store.units:
        if weapon_type == "ranged" or weapon_type is None:
            for weapon in unit.weapons.ranged:
                weapons.add(weapon.name)
        if weapon_type == "melee" or weapon_type is None:
            for weapon in unit.weapons.melee:
                weapons.add(weapon.name)

    return sorted(list(weapons))[:limit]


@router.get("/search/{name}")
async def search_weapons(
    edition: str,
    name: str,
    weapon_type: str = Query(None, description="Filter by 'ranged' or 'melee'")
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    results = []
    for unit in store.units:
        matching_weapons = []
        if weapon_type == "ranged" or weapon_type is None:
            matching_weapons.extend([
                {"type": "ranged", "weapon": w.dict()}
                for w in unit.weapons.ranged
                if name.lower() in w.name.lower()
            ])
        if weapon_type == "melee" or weapon_type is None:
            matching_weapons.extend([
                {"type": "melee", "weapon": w.dict()}
                for w in unit.weapons.melee
                if name.lower() in w.name.lower()
            ])
        if matching_weapons:
            results.append({
                "unit_name": unit.name,
                "unit_id": unit.id,
                "faction": unit.faction,
                "faction_type": unit.faction_type,
                "weapons": matching_weapons
            })

    return {"search_term": name, "weapon_type": weapon_type, "units_found": len(results), "results": results}


@router.get("/stats")
async def weapon_stats(edition: str):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    total_ranged, total_melee = 0, 0
    unique_ranged, unique_melee = set(), set()

    for unit in store.units:
        for weapon in unit.weapons.ranged:
            total_ranged += 1
            unique_ranged.add(weapon.name)
        for weapon in unit.weapons.melee:
            total_melee += 1
            unique_melee.add(weapon.name)

    return {
        "total_weapon_entries": total_ranged + total_melee,
        "ranged": {"total_entries": total_ranged, "unique_weapons": len(unique_ranged)},
        "melee": {"total_entries": total_melee, "unique_weapons": len(unique_melee)}
    }
