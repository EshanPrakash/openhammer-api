"""
Bulk operations router - batch lookups and aggregations
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict
from api.data_loader import data_store
from api.models import Unit

router = APIRouter(prefix="/bulk", tags=["Bulk Operations"])


@router.get("/units/by-ids")
async def bulk_get_units(
    ids: str = Query(..., description="Comma-separated unit IDs")
):
    """
    Bulk lookup units by IDs

    Example: /bulk/units/by-ids?ids=abc-123,def-456,ghi-789
    """
    unit_ids = [id.strip() for id in ids.split(',')]
    results = []
    not_found = []

    for unit_id in unit_ids:
        unit = data_store.get_unit_by_id(unit_id)
        if unit:
            results.append(unit)
        else:
            not_found.append(unit_id)

    return {
        "requested": len(unit_ids),
        "found": len(results),
        "not_found": not_found,
        "units": results
    }


@router.get("/units/by-names")
async def bulk_get_units_by_names(
    names: str = Query(..., description="Comma-separated unit names (exact match)")
):
    """
    Bulk lookup units by names

    Example: /bulk/units/by-names?names=Intercessors,Terminators,Dreadnought
    """
    unit_names = [name.strip() for name in names.split(',')]
    results = []
    not_found = []

    for name in unit_names:
        # Find all units with matching name
        matches = [u for u in data_store.units if u.name.lower() == name.lower()]
        if matches:
            results.extend(matches)
        else:
            not_found.append(name)

    return {
        "requested": len(unit_names),
        "found": len(results),
        "not_found": not_found,
        "units": results
    }


@router.get("/stats/by-keyword")
async def stats_by_keyword(
    keyword: str = Query(..., description="Keyword to aggregate stats for")
):
    """
    Get aggregated stats for all units with a keyword

    Example: /bulk/stats/by-keyword?keyword=Infantry
    """
    units = [u for u in data_store.units if keyword in u.keywords]

    if not units:
        return {
            "keyword": keyword,
            "unit_count": 0,
            "stats": None
        }

    # Aggregate stats
    total_points = sum(u.points.base for u in units if u.points.base)
    avg_points = total_points / len([u for u in units if u.points.base]) if units else 0

    faction_breakdown = {}
    for unit in units:
        faction_breakdown[unit.faction] = faction_breakdown.get(unit.faction, 0) + 1

    faction_type_breakdown = {}
    for unit in units:
        faction_type_breakdown[unit.faction_type] = faction_type_breakdown.get(unit.faction_type, 0) + 1

    return {
        "keyword": keyword,
        "unit_count": len(units),
        "stats": {
            "total_points_value": total_points,
            "average_points": round(avg_points, 2),
            "units_with_invuln": len([u for u in units if u.invuln_save]),
            "transports": len([u for u in units if u.transport])
        },
        "faction_breakdown": faction_breakdown,
        "faction_type_breakdown": faction_type_breakdown
    }


@router.get("/stats/by-faction-type")
async def stats_by_faction_type(
    faction_type: str = Query(..., description="Faction type (Imperium, Chaos, Xenos, Unaligned)")
):
    """
    Get aggregated stats for a faction type

    Example: /bulk/stats/by-faction-type?faction_type=Imperium
    """
    units = data_store.get_units_by_faction_type(faction_type)

    if not units:
        raise HTTPException(status_code=404, detail=f"Faction type '{faction_type}' not found")

    # Aggregate stats
    total_points = sum(u.points.base for u in units if u.points.base)
    avg_points = total_points / len([u for u in units if u.points.base]) if units else 0

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

    faction_breakdown = {}
    for unit in units:
        faction_breakdown[unit.faction] = faction_breakdown.get(unit.faction, 0) + 1

    # Top keywords
    keyword_counts = {}
    for unit in units:
        for keyword in unit.keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "faction_type": faction_type,
        "total_units": len(units),
        "stats": {
            "total_points_value": total_points,
            "average_points": round(avg_points, 2),
            "units_with_invuln": len([u for u in units if u.invuln_save]),
            "transports": len([u for u in units if u.transport])
        },
        "points_distribution": points_ranges,
        "faction_breakdown": faction_breakdown,
        "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords]
    }


@router.get("/stats/by-faction")
async def stats_by_faction(
    faction: str = Query(..., description="Faction name")
):
    """
    Get comprehensive aggregated stats for a faction

    Example: /bulk/stats/by-faction?faction=Necrons
    """
    units = data_store.get_units_by_faction(faction)

    if not units:
        raise HTTPException(status_code=404, detail=f"Faction '{faction}' not found")

    # Same aggregation as by-faction-type but for specific faction
    total_points = sum(u.points.base for u in units if u.points.base)
    avg_points = total_points / len([u for u in units if u.points.base]) if units else 0

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

    # Top keywords
    keyword_counts = {}
    for unit in units:
        for keyword in unit.keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    # Top special rules
    rule_counts = {}
    for unit in units:
        for rule in unit.special_rules:
            rule_counts[rule] = rule_counts.get(rule, 0) + 1

    top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "faction": faction,
        "faction_type": units[0].faction_type if units else None,
        "total_units": len(units),
        "stats": {
            "total_points_value": total_points,
            "average_points": round(avg_points, 2),
            "cheapest_unit": min((u.points.base for u in units if u.points.base), default=0),
            "most_expensive_unit": max((u.points.base for u in units if u.points.base), default=0),
            "units_with_invuln": len([u for u in units if u.invuln_save]),
            "transports": len([u for u in units if u.transport])
        },
        "points_distribution": points_ranges,
        "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
        "top_special_rules": [{"rule": k, "count": v} for k, v in top_rules]
    }


@router.get("/export/all-units-summary")
async def export_all_units_summary():
    """
    Get a summary of all units (name, faction, points, invuln)
    Useful for bulk exports or analysis

    Example: /bulk/export/all-units-summary
    """
    summary = []

    for unit in data_store.units:
        summary.append({
            "id": unit.id,
            "name": unit.name,
            "faction": unit.faction,
            "faction_type": unit.faction_type,
            "type": unit.type,
            "points": unit.points.base,
            "invuln_save": unit.invuln_save,
            "has_transport": unit.transport is not None,
            "keywords": unit.keywords
        })

    return {
        "total_units": len(summary),
        "units": summary
    }
