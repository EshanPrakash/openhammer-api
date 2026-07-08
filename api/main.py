"""
OpenHammer API - Warhammer 40K Data API
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.data_loader import data_store
from api.models import Unit, FactionInfo, StatsResponse
from api.routers import units, weapons, abilities, factions, bulk

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title="OpenHammer API",
    description="Warhammer 40,000 unit data API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path in ("/openapi.json", "/docs", "/redoc"):
            response.headers["Cache-Control"] = "no-store"
        else:
            response.headers["Cache-Control"] = "public, max-age=3600"
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CacheControlMiddleware)


@app.on_event("startup")
async def startup_event():
    print("Loading unit data...")
    data_store.load_all()
    print("API ready!")


app.include_router(units.router)
app.include_router(weapons.router)
app.include_router(abilities.router)
app.include_router(factions.router)
app.include_router(bulk.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to OpenHammer API",
        "version": "1.0.0",
        "docs": "/docs",
        "editions": data_store.list_editions(),
        "endpoints": {
            "units": "/v1/{edition}/units",
            "factions": "/v1/{edition}/factions",
            "stats": "/v1/{edition}/stats",
            "docs": "/docs"
        }
    }


@app.get("/v1/{edition}/stats", response_model=StatsResponse, tags=["Info"])
async def get_stats(edition: str):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    units_by_faction_type = {
        ft: len(units)
        for ft, units in store.units_by_faction_type.items()
    }

    factions_by_type = {}
    for faction_data in store.factions.values():
        ft = faction_data["faction_type"]
        if ft not in factions_by_type:
            factions_by_type[ft] = 0
        factions_by_type[ft] += 1

    return StatsResponse(
        total_units=len(store.units),
        total_factions=len(store.factions),
        factions_by_type=factions_by_type,
        units_by_faction_type=units_by_faction_type
    )


@app.get("/v1/{edition}/factions", response_model=List[FactionInfo], tags=["Factions"])
async def get_factions(
    edition: str,
    faction_type: Optional[str] = Query(
        None,
        description="Filter by faction type (Imperium, Chaos, Xenos, Unaligned)"
    )
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    factions = store.get_factions()
    if faction_type:
        factions = [f for f in factions if f["faction_type"] == faction_type]

    return [FactionInfo(**f) for f in factions]


@app.get("/v1/{edition}/units", response_model=List[Unit], tags=["Units"])
async def get_units(
    edition: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Number of units to skip"),
    name: Optional[str] = Query(None, description="Filter by unit name (partial match)"),
    faction: Optional[str] = Query(None, description="Filter by faction name"),
    faction_type: Optional[str] = Query(None, description="Filter by faction type (Imperium, Chaos, Xenos, Unaligned)"),
    type: Optional[str] = Query(None, description="Filter by type (unit or model)"),
    has_invuln: Optional[bool] = Query(None, description="Filter by invulnerable save"),
    has_transport: Optional[bool] = Query(None, description="Filter transports only"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    points_min: Optional[int] = Query(None, ge=0, description="Minimum points cost"),
    points_max: Optional[int] = Query(None, ge=0, description="Maximum points cost"),
    sort_by: Optional[str] = Query(None, description="Sort by: name, points, faction (add - prefix for descending, e.g., -points)"),
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    results = store.search_units(
        name=name,
        faction=faction,
        faction_type=faction_type,
        unit_type=type,
        has_invuln=has_invuln,
        has_transport=has_transport,
        keyword=keyword,
        points_min=points_min,
        points_max=points_max
    )

    if sort_by:
        reverse = False
        sort_field = sort_by
        if sort_by.startswith('-'):
            reverse = True
            sort_field = sort_by[1:]

        if sort_field == 'name':
            results = sorted(results, key=lambda u: u.name.lower(), reverse=reverse)
        elif sort_field == 'points':
            results = sorted(results, key=lambda u: u.points.base if u.points.base else 0, reverse=reverse)
        elif sort_field == 'faction':
            results = sorted(results, key=lambda u: u.faction.lower(), reverse=reverse)

    total = len(results)
    results = results[offset:offset + limit]

    return results


@app.get("/v1/{edition}/units/{unit_id}", response_model=Unit, tags=["Units"])
async def get_unit_by_id(edition: str, unit_id: str):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    unit = store.get_unit_by_id(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit with ID '{unit_id}' not found")

    return unit


@app.get("/v1/{edition}/factions/{faction_name}/units", response_model=List[Unit], tags=["Factions"])
async def get_faction_units(
    edition: str,
    faction_name: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    store = data_store.get(edition)
    if not store:
        raise HTTPException(status_code=404, detail=f"Edition '{edition}' not found")

    units = store.get_units_by_faction(faction_name)
    if not units:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_name}' not found")

    return units[offset:offset + limit]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
