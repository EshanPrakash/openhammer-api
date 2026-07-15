# OpenHammer API

REST API for Warhammer 40,000 unit data — also available as an **MCP server**, so Claude (or any MCP client) can query it directly instead of you making manual HTTP calls. Edition-namespaced — currently serving 10th Edition (1,380 units across 35 factions) and 11th Edition (1,368 units across 35 factions).

**Live API**: https://openhammer-api-production.up.railway.app

**Interactive Docs**: https://openhammer-api-production.up.railway.app/docs

**Live MCP Server**: https://openhammer-mcp-production.up.railway.app/mcp

## Table of Contents
- [Usage](#usage)
- [Quick Start (Local)](#quick-start-local)
- [Testing](#testing)
- [MCP Server](#mcp-server)
- [API Overview](#api-overview)
- [Data Coverage](#data-coverage)
- [API Endpoints](#api-endpoints)
- [JSON Structure](#json-structure)

---

## Usage

All endpoints are namespaced by edition: `/v1/{edition}/resource`. The root endpoint lists all available editions.

The API is live at **https://openhammer-api-production.up.railway.app**

### Python
```python
import requests

BASE = 'https://openhammer-api-production.up.railway.app'
edition = '10e'

# Get all factions
factions = requests.get(f'{BASE}/v1/{edition}/factions').json()

# Search for Space Marine units
units = requests.get(f'{BASE}/v1/{edition}/units?name=Marine&limit=10').json()

# Get a random unit
random_unit = requests.get(f'{BASE}/v1/{edition}/units/random').json()
```

### JavaScript
```javascript
const BASE = 'https://openhammer-api-production.up.railway.app';
const edition = '10e';

// Get API statistics
const stats = await fetch(`${BASE}/v1/${edition}/stats`).then(r => r.json());

// Search Necrons units
const units = await fetch(`${BASE}/v1/${edition}/units?faction=Necrons`).then(r => r.json());
```

### curl
```bash
BASE="https://openhammer-api-production.up.railway.app"
EDITION="10e"

# Get all factions
curl "$BASE/v1/$EDITION/factions"

# Search for Terminator units
curl "$BASE/v1/$EDITION/units?name=Terminator"

# Get faction details
curl "$BASE/v1/$EDITION/factions/Necrons/details"
```

### Interactive Testing

Visit **https://openhammer-api-production.up.railway.app/docs** to:
- Browse all 29 endpoints
- Try requests directly in your browser
- See example responses
- View request/response schemas

---

## Quick Start (Local)

**With Python:**
```bash
git clone https://github.com/EshanPrakash/openhammer-api.git
cd openhammer-api
pip install -r requirements.txt
uvicorn api.main:app --reload
```

**With Docker:**
```bash
git clone https://github.com/EshanPrakash/openhammer-api.git
cd openhammer-api
docker build -t openhammer-api .
docker run -p 8000:8000 openhammer-api
```

Visit http://localhost:8000/docs for interactive documentation.

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run entirely in-process against both editions (no live server or network access needed) and cover search/filter/sort behavior, pagination, error cases, and edition parity across all 29 endpoints.

---

## MCP Server

`api/mcp_server.py` exposes the same unit/faction/weapon data as MCP tools, so an MCP client (Claude Code, Claude Desktop, claude.ai) can query it directly instead of making manual HTTP calls. Tools call the in-process data store directly rather than the REST API.

### Connect to the hosted server

The MCP server is live at **https://openhammer-mcp-production.up.railway.app/mcp** — no install needed.

```bash
claude mcp add --transport http openhammer https://openhammer-mcp-production.up.railway.app/mcp
```

Claude Desktop and claude.ai support the same URL as an HTTP/Streamable HTTP connector. This gives you 9 tools: `list_editions`, `list_factions`, `search_units`, `get_unit`, `compare_units`, `random_unit`, `faction_details`, `search_weapons`, `search_abilities_or_rules`.

### Run it yourself

Its dependencies are pinned separately in `requirements-mcp.txt`, since `mcp` needs newer starlette/anyio versions than the pinned `fastapi==0.104.1` in `requirements.txt` supports.

**With Python:**
```bash
python3 -m venv venv-mcp
source venv-mcp/bin/activate
pip install -r requirements-mcp.txt
python -m api.mcp_server
```

**With Docker:**
```bash
docker build -f Dockerfile.mcp -t openhammer-mcp .
docker run -p 8001:8001 openhammer-mcp
```

Both serve Streamable HTTP on port 8001 (or `$PORT`, if set) at `/mcp`.

### Testing

```bash
source venv-mcp/bin/activate
pip install -r requirements-mcp-dev.txt
pytest -c pytest-mcp.ini
```

Runs entirely in-process against the FastMCP instance via an in-memory client/server session (no live server, no network) and covers all 9 tools across both editions. Kept as a separate suite from `pytest` (which runs `tests/`) since it needs the `mcp` package.

---

## API Overview

### What You Can Do

The OpenHammer API provides **29 endpoints** for accessing Warhammer 40K unit data:

- **Search & Filter**: Find units by name, faction, points cost, keywords, abilities
- **Faction Analytics**: Get detailed stats, breakdowns, and insights for any faction
- **Weapon Lookup**: Search for weapons and find which units have them
- **Bulk Operations**: Lookup multiple units at once, export data, aggregate statistics
- **Keyword/Ability Search**: Find all units with specific keywords or special rules

### Performance

- **Load Time**: ~1 second on startup
- **Memory Usage**: ~10-15MB per edition (all units loaded in memory)
- **Response Time**: <10ms for most queries

### Features

- **MCP server** — query the data conversationally through Claude instead of writing HTTP calls (see [MCP Server](#mcp-server))
- Edition-namespaced URLs — add new editions without any code changes
- Automated monthly data sync via GitHub Actions (pulls latest BSData/wh40k-10e and BSData/wh40k-11e)
- In-memory storage with <10ms response times
- HTTP caching (1 hour)
- Rate limiting (100 req/min per IP)
- Interactive Swagger docs at `/docs`
- Sorting and filtering across 11+ parameters
- Bulk operations and faction analytics
- CORS enabled
- Dockerized for easy deployment

---

## Data Coverage

**Current editions:** `10e`, `11e`

Both editions cover the same 35 factions:

- **Imperium**: 19 factions
- **Chaos**: 7 factions
- **Xenos**: 7 factions
- **Unaligned**: 2 groups

### Faction List

#### Imperium (19 factions)
Adepta Sororitas, Adeptus Custodes, Adeptus Mechanicus, Agents of the Imperium, Astra Militarum, Black Templars, Blood Angels, Dark Angels, Deathwatch, Grey Knights, Imperial Fists, Imperial Knights, Iron Hands, Raven Guard, Salamanders, Space Marines, Space Wolves, Ultramarines, White Scars

#### Chaos (7 factions)
Daemons, Chaos Knights, Chaos Space Marines, Death Guard, Emperor's Children, Thousand Sons, World Eaters

#### Xenos (7 factions)
Aeldari, Genestealer Cults, Leagues of Votann, Necrons, Orks, Tyranids, T'au Empire

#### Unaligned (2 groups)
Titans, Unaligned Forces

### Edition Totals

| Edition | Units | Factions |
|---------|-------|----------|
| `10e` (10th Edition) | 1,380 | 35 |
| `11e` (11th Edition) | 1,368 | 35 |

---

## API Endpoints

### Quick Reference

**Root**
- `GET /` - API info and list of available editions

**Statistics & Info**
- `GET /v1/{edition}/stats` - Total units, factions, breakdown by type

**Factions** (5 endpoints)
- `GET /v1/{edition}/factions` - List all factions
- `GET /v1/{edition}/factions/{faction_name}/units` - Get faction units
- `GET /v1/{edition}/factions/{faction_name}/details` - Comprehensive faction details
- `GET /v1/{edition}/factions/{faction_name}/stats` - Statistical breakdown
- `GET /v1/{edition}/factions/{faction_name}/keywords` - Faction keywords with counts

**Units** (8 endpoints)
- `GET /v1/{edition}/units` - Search/filter units (11 query parameters)
- `GET /v1/{edition}/units/{unit_id}` - Get specific unit by ID
- `GET /v1/{edition}/units/search/name/{name}` - Search by name
- `GET /v1/{edition}/units/random` - Random unit
- `GET /v1/{edition}/units/expensive` - Most expensive units by points
- `GET /v1/{edition}/units/cheap` - Cheapest units by points
- `GET /v1/{edition}/units/count` - Count matching units without returning data
- `GET /v1/{edition}/units/compare` - Compare multiple units by ID

**Weapons** (3 endpoints)
- `GET /v1/{edition}/weapons/stats` - Weapon statistics
- `GET /v1/{edition}/weapons/list` - List all weapon names
- `GET /v1/{edition}/weapons/search/{name}` - Search weapons, find units that have them

**Abilities & Keywords** (5 endpoints)
- `GET /v1/{edition}/abilities/search/{term}` - Search abilities by name or description
- `GET /v1/{edition}/abilities/keywords/list` - List all keywords
- `GET /v1/{edition}/abilities/keywords/search/{keyword}` - Find units by keyword
- `GET /v1/{edition}/abilities/special-rules/list` - List all special rules
- `GET /v1/{edition}/abilities/special-rules/search/{rule}` - Find units by special rule

**Bulk Operations** (6 endpoints)
- `GET /v1/{edition}/bulk/units/by-ids` - Bulk lookup by IDs
- `GET /v1/{edition}/bulk/units/by-names` - Bulk lookup by names
- `GET /v1/{edition}/bulk/stats/by-keyword` - Aggregate stats by keyword
- `GET /v1/{edition}/bulk/stats/by-faction-type` - Aggregate stats by faction type
- `GET /v1/{edition}/bulk/stats/by-faction` - Aggregate stats by faction
- `GET /v1/{edition}/bulk/export/all-units-summary` - Export all units summary

### Example Queries

```bash
BASE="https://openhammer-api-production.up.railway.app"
EDITION="10e"

# Get all Chaos units with invulnerable saves
curl "$BASE/v1/$EDITION/units?faction_type=Chaos&has_invuln=true"

# Get most expensive units
curl "$BASE/v1/$EDITION/units?sort_by=-points&limit=10"

# Get cheapest Imperium units
curl "$BASE/v1/$EDITION/units?faction_type=Imperium&sort_by=points&limit=20"

# Search for bolter weapons
curl "$BASE/v1/$EDITION/weapons/search/bolter"

# Get faction details for Necrons
curl "$BASE/v1/$EDITION/factions/Necrons/details"

# Get stats for all Infantry units
curl "$BASE/v1/$EDITION/bulk/stats/by-keyword?keyword=Infantry"

# Get comprehensive Imperium statistics
curl "$BASE/v1/$EDITION/bulk/stats/by-faction-type?faction_type=Imperium"
```

### Main Search Endpoint

`GET /v1/{edition}/units` supports 11 filter and sorting parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `limit` | int | Max results (1-500, default: 100) | `limit=50` |
| `offset` | int | Skip results (pagination) | `offset=100` |
| `name` | string | Filter by name (partial match) | `name=guard` |
| `faction` | string | Filter by faction | `faction=Necrons` |
| `faction_type` | string | Filter by type | `faction_type=Imperium` |
| `type` | string | Filter by unit/model | `type=unit` |
| `has_invuln` | bool | Has invulnerable save | `has_invuln=true` |
| `has_transport` | bool | Is a transport | `has_transport=true` |
| `keyword` | string | Filter by keyword | `keyword=Infantry` |
| `points_min` | int | Minimum points cost | `points_min=100` |
| `points_max` | int | Maximum points cost | `points_max=200` |
| `sort_by` | string | Sort field (name/points/faction) | `sort_by=points` or `sort_by=-points` |

**Sorting**: `sort_by=field` for ascending, `sort_by=-field` for descending.

---

## JSON Structure

Data is stored in `data/json/{edition}/` with one JSON file per faction:
- `Imperium_-_[Faction_Name].json`
- `Chaos_-_[Faction_Name].json`
- `Xenos_-_[Faction_Name].json`
- `Unaligned_-_[Faction_Name].json`

Adding a new edition is as simple as adding a new subdirectory — the API picks it up automatically on startup.

### Unit Object Schema

```json
{
  "name": "string",
  "id": "string",
  "type": "string",
  "faction": "string",
  "faction_type": "string",
  "points": {
    "base": number,
    "variants": [{ "name": "string", "cost": number }]
  },
  "composition": {
    "min_models": number,
    "max_models": number
  },
  "stats": {
    "M": "string",
    "T": "string",
    "SV": "string",
    "W": "string",
    "LD": "string",
    "OC": "string"
  },
  "invuln_save": "string|null",
  "transport": "string|null",
  "weapons": {
    "ranged": [
      {
        "name": "string",
        "Range": "string",
        "A": "string",
        "BS": "string",
        "S": "string",
        "AP": "string",
        "D": "string",
        "Keywords": "string|null"
      }
    ],
    "melee": [
      {
        "name": "string",
        "Range": "Melee",
        "A": "string",
        "WS": "string",
        "S": "string",
        "AP": "string",
        "D": "string",
        "Keywords": "string|null"
      }
    ]
  },
  "abilities": [{ "name": "string", "description": "string" }],
  "special_rules": ["string"],
  "keywords": ["string"]
}
```

---

## License

MIT License - see LICENSE file.

All Warhammer 40,000 content is property of Games Workshop.

Unit data sourced from [BSData/wh40k-10e](https://github.com/BSData/wh40k-10e) and [BSData/wh40k-11e](https://github.com/BSData/wh40k-11e).
