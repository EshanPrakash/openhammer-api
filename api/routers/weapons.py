"""
Weapons router - weapon-related endpoints
"""
from fastapi import APIRouter, Query
from typing import List, Dict
from api.data_loader import data_store

router = APIRouter(prefix="/weapons", tags=["Weapons"])


@router.get("/list", response_model=List[str])
async def list_all_weapons(
    weapon_type: str = Query(None, description="Filter by 'ranged' or 'melee'"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get list of all unique weapon names

    Example: /weapons/list?weapon_type=ranged
    """
    weapons = set()

    for unit in data_store.units:
        if weapon_type == "ranged" or weapon_type is None:
            for weapon in unit.weapons.ranged:
                weapons.add(weapon.name)

        if weapon_type == "melee" or weapon_type is None:
            for weapon in unit.weapons.melee:
                weapons.add(weapon.name)

    return sorted(list(weapons))[:limit]


@router.get("/search/{name}")
async def search_weapons(
    name: str,
    weapon_type: str = Query(None, description="Filter by 'ranged' or 'melee'")
):
    """
    Search for weapons by name and return all units that have it

    Example: /weapons/search/bolt?weapon_type=ranged
    """
    results = []

    for unit in data_store.units:
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

    return {
        "search_term": name,
        "weapon_type": weapon_type,
        "units_found": len(results),
        "results": results
    }


@router.get("/stats")
async def weapon_stats():
    """
    Get weapon statistics across all units

    Example: /weapons/stats
    """
    total_ranged = 0
    total_melee = 0
    unique_ranged = set()
    unique_melee = set()

    for unit in data_store.units:
        for weapon in unit.weapons.ranged:
            total_ranged += 1
            unique_ranged.add(weapon.name)

        for weapon in unit.weapons.melee:
            total_melee += 1
            unique_melee.add(weapon.name)

    return {
        "total_weapon_entries": total_ranged + total_melee,
        "ranged": {
            "total_entries": total_ranged,
            "unique_weapons": len(unique_ranged)
        },
        "melee": {
            "total_entries": total_melee,
            "unique_weapons": len(unique_melee)
        }
    }
