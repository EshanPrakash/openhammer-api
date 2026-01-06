"""
Factions router - detailed faction endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from api.data_loader import data_store
from api.models import Unit

router = APIRouter(prefix="/factions", tags=["Factions"])


@router.get("/{faction_name}/details")
async def get_faction_details(faction_name: str):
    """
    Get detailed faction information including stats

    Example: /factions/Necrons/details
    """
    units = data_store.get_units_by_faction(faction_name)

    if not units:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_name}' not found")

    # Calculate faction stats
    total_points = sum(u.points.base for u in units if u.points.base)
    avg_points = total_points / len([u for u in units if u.points.base]) if units else 0

    units_with_invuln = len([u for u in units if u.invuln_save])
    transports = len([u for u in units if u.transport])

    # Count by type
    unit_types = {}
    for unit in units:
        unit_types[unit.type] = unit_types.get(unit.type, 0) + 1

    # Get all unique keywords
    all_keywords = set()
    for unit in units:
        all_keywords.update(unit.keywords)

    # Get all unique special rules
    all_special_rules = set()
    for unit in units:
        all_special_rules.update(unit.special_rules)

    return {
        "name": faction_name,
        "faction_type": units[0].faction_type if units else None,
        "total_units": len(units),
        "unit_breakdown": unit_types,
        "stats": {
            "total_points_value": total_points,
            "average_points": round(avg_points, 2),
            "units_with_invuln": units_with_invuln,
            "transports": transports
        },
        "keywords": sorted(list(all_keywords)),
        "special_rules": sorted(list(all_special_rules))
    }


@router.get("/{faction_name}/stats")
async def get_faction_stats(faction_name: str):
    """
    Get statistical breakdown of a faction

    Example: /factions/Necrons/stats
    """
    units = data_store.get_units_by_faction(faction_name)

    if not units:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_name}' not found")

    # Points distribution
    points_ranges = {
        "0-50": 0,
        "51-100": 0,
        "101-150": 0,
        "151-200": 0,
        "201-300": 0,
        "301+": 0
    }

    for unit in units:
        pts = unit.points.base
        if pts:
            if pts <= 50:
                points_ranges["0-50"] += 1
            elif pts <= 100:
                points_ranges["51-100"] += 1
            elif pts <= 150:
                points_ranges["101-150"] += 1
            elif pts <= 200:
                points_ranges["151-200"] += 1
            elif pts <= 300:
                points_ranges["201-300"] += 1
            else:
                points_ranges["301+"] += 1

    # Weapon counts
    total_ranged = sum(len(u.weapons.ranged) for u in units)
    total_melee = sum(len(u.weapons.melee) for u in units)

    return {
        "faction": faction_name,
        "points_distribution": points_ranges,
        "weapons": {
            "total_ranged_weapons": total_ranged,
            "total_melee_weapons": total_melee,
            "avg_ranged_per_unit": round(total_ranged / len(units), 2) if units else 0,
            "avg_melee_per_unit": round(total_melee / len(units), 2) if units else 0
        },
        "invulnerable_saves": {
            "units_with_invuln": len([u for u in units if u.invuln_save]),
            "percentage": round(len([u for u in units if u.invuln_save]) / len(units) * 100, 1) if units else 0
        }
    }


@router.get("/{faction_name}/keywords")
async def get_faction_keywords(faction_name: str):
    """
    Get all keywords used in a faction with unit counts

    Example: /factions/Necrons/keywords
    """
    units = data_store.get_units_by_faction(faction_name)

    if not units:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_name}' not found")

    keyword_counts = {}
    for unit in units:
        for keyword in unit.keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    # Sort by count descending
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "faction": faction_name,
        "total_unique_keywords": len(keyword_counts),
        "keywords": [
            {"keyword": k, "unit_count": v}
            for k, v in sorted_keywords
        ]
    }
