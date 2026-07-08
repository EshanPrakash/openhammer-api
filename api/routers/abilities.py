"""
Abilities router - ability and keyword search
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.data_loader import data_store

router = APIRouter(prefix="/v1/{edition}/abilities", tags=["Abilities"])


@router.get("/search/{term}")
async def search_abilities(edition: str, term: str, limit: int = Query(50, ge=1, le=200)):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    results = []
    for unit in store.units:
        matching_abilities = [
            ability for ability in unit.abilities
            if (term.lower() in ability.name.lower() or
                (ability.description and term.lower() in ability.description.lower()))
        ]
        if matching_abilities:
            results.append({
                "unit_name": unit.name,
                "unit_id": unit.id,
                "faction": unit.faction,
                "faction_type": unit.faction_type,
                "abilities": [a.dict() for a in matching_abilities]
            })

    return {"search_term": term, "units_found": len(results), "results": results[:limit]}


@router.get("/keywords/list", response_model=List[str])
async def list_all_keywords(edition: str, limit: int = Query(200, ge=1, le=500)):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    keywords = set()
    for unit in store.units:
        keywords.update(unit.keywords)
    return sorted(list(keywords))[:limit]


@router.get("/keywords/search/{keyword}")
async def search_by_keyword(
    edition: str,
    keyword: str,
    faction_type: str = Query(None, description="Filter by faction type")
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    results = []
    for unit in store.units:
        if any(keyword.lower() in kw.lower() for kw in unit.keywords):
            if faction_type is None or unit.faction_type == faction_type:
                results.append({
                    "name": unit.name,
                    "id": unit.id,
                    "faction": unit.faction,
                    "faction_type": unit.faction_type,
                    "points": unit.points.base,
                    "matching_keywords": [kw for kw in unit.keywords if keyword.lower() in kw.lower()]
                })

    return {"keyword": keyword, "faction_type": faction_type, "units_found": len(results), "results": results}


@router.get("/special-rules/list", response_model=List[str])
async def list_special_rules(edition: str, limit: int = Query(200, ge=1, le=500)):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    rules = set()
    for unit in store.units:
        rules.update(unit.special_rules)
    return sorted(list(rules))[:limit]


@router.get("/special-rules/search/{rule}")
async def search_by_special_rule(
    edition: str,
    rule: str,
    faction_type: str = Query(None, description="Filter by faction type")
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    results = []
    for unit in store.units:
        matching_rules = [r for r in unit.special_rules if rule.lower() in r.lower()]
        if matching_rules:
            if faction_type is None or unit.faction_type == faction_type:
                results.append({
                    "name": unit.name,
                    "id": unit.id,
                    "faction": unit.faction,
                    "faction_type": unit.faction_type,
                    "points": unit.points.base,
                    "matching_rules": matching_rules
                })

    return {"rule": rule, "faction_type": faction_type, "units_found": len(results), "results": results}
