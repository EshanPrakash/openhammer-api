"""
OpenHammer API - Warhammer 40K 10th Edition Data API
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

# Rate limiter - 100 requests per minute per IP
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Create FastAPI app
app = FastAPI(
    title="OpenHammer API",
    description="Warhammer 40,000 10th Edition unit data API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Cache middleware - adds caching headers to all responses
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Cache responses for 1 hour (3600 seconds)
        # Data is static so caching is safe
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response


# Enable CORS (allow requests from web browsers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add cache control middleware
app.add_middleware(CacheControlMiddleware)


@app.on_event("startup")
async def startup_event():
    """Load data when API starts"""
    print("Loading unit data...")
    data_store.load_data()
    print("API ready!")


# Include routers
app.include_router(units.router)
app.include_router(weapons.router)
app.include_router(abilities.router)
app.include_router(factions.router)
app.include_router(bulk.router)


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to OpenHammer API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "units": "/units",
            "factions": "/factions",
            "stats": "/stats"
        }
    }


@app.get("/stats", response_model=StatsResponse, tags=["Info"])
async def get_stats():
    """Get API statistics"""
    units_by_faction_type = {
        ft: len(units)
        for ft, units in data_store.units_by_faction_type.items()
    }

    factions_by_type = {}
    for faction_data in data_store.factions.values():
        ft = faction_data["faction_type"]
        if ft not in factions_by_type:
            factions_by_type[ft] = 0
        factions_by_type[ft] += 1

    return StatsResponse(
        total_units=len(data_store.units),
        total_factions=len(data_store.factions),
        factions_by_type=factions_by_type,
        units_by_faction_type=units_by_faction_type
    )


@app.get("/factions", response_model=List[FactionInfo], tags=["Factions"])
async def get_factions(
    faction_type: Optional[str] = Query(
        None,
        description="Filter by faction type (Imperium, Chaos, Xenos, Unaligned)"
    )
):
    """Get all factions, optionally filtered by type"""
    factions = data_store.get_factions()

    if faction_type:
        factions = [f for f in factions if f["faction_type"] == faction_type]

    return [FactionInfo(**f) for f in factions]


@app.get("/units", response_model=List[Unit], tags=["Units"])
async def get_units(
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
    """
    Get units with optional filtering, sorting, and pagination

    Examples:
    - /units?faction_type=Imperium
    - /units?faction=Necrons&has_invuln=true
    - /units?points_min=100&points_max=200
    - /units?name=guard&faction_type=Imperium
    - /units?sort_by=points (ascending)
    - /units?sort_by=-points (descending)
    """
    # Search with filters
    results = data_store.search_units(
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

    # Apply sorting
    if sort_by:
        reverse = False
        sort_field = sort_by

        # Check for descending order (- prefix)
        if sort_by.startswith('-'):
            reverse = True
            sort_field = sort_by[1:]

        # Sort by the specified field
        if sort_field == 'name':
            results = sorted(results, key=lambda u: u.name.lower(), reverse=reverse)
        elif sort_field == 'points':
            results = sorted(results, key=lambda u: u.points.base if u.points.base else 0, reverse=reverse)
        elif sort_field == 'faction':
            results = sorted(results, key=lambda u: u.faction.lower(), reverse=reverse)

    # Apply pagination
    total = len(results)
    results = results[offset:offset + limit]

    return results


@app.get("/units/{unit_id}", response_model=Unit, tags=["Units"])
async def get_unit_by_id(unit_id: str):
    """Get a specific unit by its ID"""
    unit = data_store.get_unit_by_id(unit_id)

    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit with ID '{unit_id}' not found")

    return unit


@app.get("/factions/{faction_name}/units", response_model=List[Unit], tags=["Factions"])
async def get_faction_units(
    faction_name: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all units for a specific faction"""
    units = data_store.get_units_by_faction(faction_name)

    if not units:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_name}' not found")

    # Apply pagination
    return units[offset:offset + limit]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
