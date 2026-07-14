# OpenHammer API

REST API for Warhammer 40,000 unit data. Edition-namespaced — currently serving 10th Edition (1,380 units across 35 factions) and 11th Edition (1,368 units across 35 factions).

**Live API**: https://openhammer-api-production.up.railway.app

**Interactive Docs**: https://openhammer-api-production.up.railway.app/docs

## Table of Contents
- [Usage](#usage)
- [Quick Start (Local)](#quick-start-local)
- [Testing](#testing)
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
