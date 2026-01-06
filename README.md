# OpenHammer API

A comprehensive Warhammer 40,000 10th Edition data parser and REST API that converts BattleScribe XML catalogues into clean, structured JSON and serves it via a high-performance API.

## Table of Contents
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [API Overview](#api-overview)
- [Data Coverage](#data-coverage)
- [Parser Usage](#parser-usage)
- [API Endpoints](#api-endpoints)
- [JSON Structure](#json-structure)
- [Architecture](#architecture)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Parse Data (Optional - JSON files already included)

```bash
python scripts/universal_parser.py
```

### 3. Run the API

```bash
uvicorn api.main:app --reload
```

Or using Python directly:

```bash
python -m uvicorn api.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Endpoint Reference**: See [ENDPOINTS.md](docs/ENDPOINTS.md)

---

## Deployment

Deploy your own instance to the cloud:

**Quick Deploy to Render (Free Tier)**:
1. Push code to GitHub
2. Sign up at [Render](https://render.com)
3. Connect your repo → Render auto-detects `render.yaml`
4. Click "Apply" → Your API is live in ~3 minutes

For detailed deployment instructions, see **[DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

**Other platforms**: Railway, Fly.io, DigitalOcean, AWS, GCP all work. See deployment guide for details.

---

## API Overview

### What You Can Do

The OpenHammer API provides **35+ endpoints** for accessing Warhammer 40K unit data:

- **Search & Filter**: Find units by name, faction, points cost, keywords, abilities
- **Faction Analytics**: Get detailed stats, breakdowns, and insights for any faction
- **Weapon Lookup**: Search for weapons and find which units have them
- **Bulk Operations**: Lookup multiple units at once, export data, aggregate statistics
- **Keyword/Ability Search**: Find all units with specific keywords or special rules

### Performance

- **Load Time**: ~1 second on startup
- **Memory Usage**: ~10-15MB (all 1,285 units loaded in memory)
- **Response Time**: <10ms for most queries
- **Data**: 1,285 units across 35 factions

### Key Features

- **In-Memory Storage**: All data loaded at startup for lightning-fast queries
- **HTTP Caching**: Responses cached for 1 hour (Cache-Control headers)
- **Rate Limiting**: 100 requests/minute per IP (prevents abuse)
- **Auto-Generated Docs**: Interactive Swagger/OpenAPI documentation
- **Extensive Filtering**: 11+ query parameters for precise searches
- **Flexible Sorting**: Sort by name, points, or faction (ascending/descending)
- **Bulk Operations**: Batch lookups and aggregated statistics
- **Faction Analytics**: Detailed breakdowns by faction, faction type, and keyword
- **CORS Enabled**: Ready for frontend integration
- **Production Ready**: Deploy to Render, Railway, or any cloud platform

---

## Data Coverage

**Total Units: 1,285**
**Total Factions: 35**

- **Imperium**: 574 units (18 factions)
- **Chaos**: 301 units (7 factions)
- **Xenos**: 386 units (7 factions)
- **Unaligned**: 24 units (2 groups)

### Faction List

#### Imperium (18 factions)
Adepta Sororitas, Adeptus Custodes, Adeptus Mechanicus, Agents of the Imperium, Astra Militarum, Black Templars, Blood Angels, Dark Angels, Deathwatch, Grey Knights, Imperial Fists, Imperial Knights, Iron Hands, Raven Guard, Salamanders, Space Marines, Space Wolves, Ultramarines, White Scars

#### Chaos (7 factions)
Chaos Daemons, Chaos Knights, Chaos Space Marines, Death Guard, Emperor's Children, Thousand Sons, World Eaters

#### Xenos (7 factions)
Aeldari (Craftworlds, Drukhari, Ynnari), Genestealer Cults, Leagues of Votann, Necrons, Orks, Tyranids, T'au Empire

#### Unaligned (2 groups)
Titanicus (shared between Imperium and Chaos), Unaligned Forces

---

## Parser Usage

### Running the Parser

```bash
python scripts/universal_parser.py
```

This will:
1. Parse all catalogue files from `data/BSData/`
2. Extract unit data for all 35 factions
3. Generate JSON files in `data/json/`

### Parser Features

- **Dual invulnerable save detection**: Checks both infoLinks and ability profiles
- **Library catalogue support**: Properly handles factions that use Library files (Astra Militarum, Imperial Knights, Titans, etc.)
- **Consistent naming**: Automatically renames Library outputs to match wrapper catalogue names
- **Organizational prefixes**: Adds faction-type prefixes (Imperium_, Chaos_, Xenos_, Unaligned_) for easy organization
- **Cross-faction compatibility**: Handles shared catalogues like Titanicus

### Known Limitations

1. **Cross-catalogue references**: Some Space Marine chapter supplements (~50 units) have generic "Invulnerable Save" values because they reference parent catalogue profiles that the parser doesn't follow
2. **Variable cost units**: Some units (especially Legends) may have `null` or `0` points if they have variable costs
3. **Optional wargear**: The parser filters out invulnerable saves from optional wargear to show only base unit characteristics

---

## API Endpoints

For the complete endpoint reference with examples, see **[ENDPOINTS.md](ENDPOINTS.md)**.

### Quick Reference

**Statistics & Info**
- `GET /` - API information
- `GET /stats` - API statistics (total units, factions, breakdown)

**Factions** (7 endpoints)
- `GET /factions` - List all factions
- `GET /factions/{faction_name}/units` - Get faction units
- `GET /factions/{faction_name}/details` - Comprehensive faction details
- `GET /factions/{faction_name}/stats` - Statistical breakdown
- `GET /factions/{faction_name}/keywords` - Faction keywords with counts

**Units** (11 endpoints)
- `GET /units` - Search/filter units (10+ query parameters)
- `GET /units/{unit_id}` - Get specific unit
- `GET /units/search/name/{name}` - Search by name
- `GET /units/random` - Random unit
- `GET /units/expensive` - Most expensive units
- `GET /units/cheap` - Cheapest units
- `GET /units/count` - Count matching units
- `GET /units/compare` - Compare multiple units

**Weapons** (3 endpoints)
- `GET /weapons/stats` - Weapon statistics
- `GET /weapons/list` - List all weapons
- `GET /weapons/search/{name}` - Search weapons, find units

**Abilities & Keywords** (5 endpoints)
- `GET /abilities/search/{term}` - Search abilities
- `GET /abilities/keywords/list` - List all keywords
- `GET /abilities/keywords/search/{keyword}` - Find units by keyword
- `GET /abilities/special-rules/list` - List special rules
- `GET /abilities/special-rules/search/{rule}` - Find units by rule

**Bulk Operations** (7 endpoints)
- `GET /bulk/units/by-ids` - Bulk lookup by IDs
- `GET /bulk/units/by-names` - Bulk lookup by names
- `GET /bulk/stats/by-keyword` - Aggregate stats by keyword
- `GET /bulk/stats/by-faction-type` - Aggregate stats by faction type
- `GET /bulk/stats/by-faction` - Aggregate stats by faction
- `GET /bulk/export/all-units-summary` - Export all units summary

### Example Queries

```bash
# Get all Chaos units with invulnerable saves
curl 'http://localhost:8000/units?faction_type=Chaos&has_invuln=true'

# Get most expensive units across all factions
curl 'http://localhost:8000/units?sort_by=-points&limit=10'

# Get cheapest Imperium units
curl 'http://localhost:8000/units?faction_type=Imperium&sort_by=points&limit=20'

# Search for bolter weapons
curl 'http://localhost:8000/weapons/search/bolter'

# Get faction details for Necrons
curl 'http://localhost:8000/factions/Necrons/details'

# Get stats for all Infantry units
curl 'http://localhost:8000/bulk/stats/by-keyword?keyword=Infantry'

# Get comprehensive Imperium statistics
curl 'http://localhost:8000/bulk/stats/by-faction-type?faction_type=Imperium'
```

### Main Search Endpoint

`GET /units` supports 11+ filter and sorting parameters:

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
| `sort_by` | string | Sort by field (name/points/faction) | `sort_by=points` or `sort_by=-points` |

**Sorting**: Use `sort_by=field` for ascending order, `sort_by=-field` for descending order.

---

## JSON Structure

All faction data is stored in `data/json/` with consistent naming:
- `Imperium_-_[Faction_Name].json`
- `Chaos_-_[Faction_Name].json`
- `Xenos_-_[Faction_Name].json`
- `Unaligned_-_[Faction_Name].json`

### Unit Object Schema

Each JSON file contains an array of unit objects:

```json
{
  "name": "string",                    // Unit name
  "id": "string",                      // Unique BattleScribe ID
  "type": "string",                    // Type: "unit" or "model"
  "faction": "string",                 // Faction name (e.g., "Adeptus Custodes")
  "faction_type": "string",            // Faction type: "Imperium", "Chaos", "Xenos", or "Unaligned"
  "points": {
    "base": number,                    // Base points cost
    "variants": [                      // Optional cost variants
      {
        "name": "string",
        "cost": number
      }
    ]
  },
  "composition": {
    "min_models": number,              // Minimum squad size
    "max_models": number               // Maximum squad size
  },
  "stats": {
    "M": "string",                     // Movement (e.g., "6\"")
    "T": "string",                     // Toughness
    "SV": "string",                    // Save (e.g., "3+")
    "W": "string",                     // Wounds
    "LD": "string",                    // Leadership (e.g., "6+")
    "OC": "string"                     // Objective Control
  },
  "invuln_save": "string|null",        // Invulnerable save (e.g., "4+") or null
  "transport": "string|null",          // Transport capacity description or null
  "weapons": {
    "ranged": [                        // Array of ranged weapons
      {
        "name": "string",
        "Range": "string",             // Weapon range
        "A": "string",                 // Attacks
        "BS": "string",                // Ballistic Skill (e.g., "3+")
        "S": "string",                 // Strength
        "AP": "string",                // Armor Penetration (e.g., "-2")
        "D": "string",                 // Damage
        "Keywords": "string"           // Weapon keywords (e.g., "Rapid Fire 1")
      }
    ],
    "melee": [                         // Array of melee weapons
      {
        "name": "string",
        "Range": "Melee",
        "A": "string",
        "WS": "string",                // Weapon Skill (e.g., "3+")
        "S": "string",
        "AP": "string",
        "D": "string",
        "Keywords": "string"
      }
    ]
  },
  "abilities": [                       // Array of unit abilities
    {
      "name": "string",
      "description": "string"
    }
  ],
  "special_rules": [                   // Array of special rule names (strings)
    "string"
  ],
  "keywords": [                        // Array of unit keywords (strings)
    "string"
  ]
}
```

### Field Descriptions

#### Basic Information
- **name**: The unit's display name (e.g., "Intercessor Squad", "Custodian Guard")
- **id**: Unique identifier from BattleScribe catalogue
- **type**: Either "unit" (squad) or "model" (single model)
- **faction**: The specific faction this unit belongs to (e.g., "Adeptus Custodes", "Necrons", "Chaos Space Marines")
- **faction_type**: The broad faction category - one of: "Imperium", "Chaos", "Xenos", or "Unaligned"

#### Points and Composition
- **points.base**: Base points cost for the unit
- **points.variants**: Optional array for units with multiple cost options (e.g., different squad sizes)
- **composition.min_models**: Minimum number of models in the unit
- **composition.max_models**: Maximum number of models in the unit

#### Stats
Standard Warhammer 40K 10th Edition statline:
- **M**: Movement characteristic (includes unit, e.g., "6\"", "12\"")
- **T**: Toughness value
- **SV**: Armor save value (e.g., "3+", "4+")
- **W**: Wounds characteristic
- **LD**: Leadership value (e.g., "6+", "7+")
- **OC**: Objective Control value

#### Defenses
- **invuln_save**: Invulnerable save value if the unit has one (e.g., "4+", "5+"), otherwise `null`
- **transport**: Transport capacity description if the unit is a transport, otherwise `null`

#### Weapons
Both ranged and melee weapons follow a consistent structure:
- **name**: Weapon name
- **Range**: Weapon range (or "Melee" for melee weapons)
- **A**: Number of attacks
- **BS/WS**: Ballistic Skill (ranged) or Weapon Skill (melee)
- **S**: Strength value
- **AP**: Armor Penetration (negative value, e.g., "-2", "-3")
- **D**: Damage characteristic
- **Keywords**: Special weapon abilities (e.g., "Rapid Fire 2", "Devastating Wounds")

#### Abilities and Rules
- **abilities**: Array of detailed ability objects with name and full description
- **special_rules**: Array of special rule names (e.g., "Deep Strike", "Feel No Pain 5+", "Scout")
- **keywords**: Array of unit keywords used for game rules and interactions

---

## Architecture

### Technology Stack

- **FastAPI**: Modern Python web framework with automatic API documentation
- **Pydantic**: Data validation and serialization
- **Uvicorn**: High-performance ASGI server
- **lxml**: XML parsing for BattleScribe catalogues

### Data Flow

```
BattleScribe XML (.cat files)
         ↓
  Universal Parser (scripts/universal_parser.py)
         ↓
  JSON Files (data/json/*.json)
         ↓
  DataStore (api/data_loader.py) - In-Memory Storage
         ↓
  FastAPI Routes (api/routers/*.py)
         ↓
  REST API Endpoints
```

### Project Structure

```
openhammer-api/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and core endpoints
│   ├── models.py            # Pydantic data models
│   ├── data_loader.py       # In-memory data store
│   └── routers/
│       ├── units.py         # Unit-specific endpoints
│       ├── weapons.py       # Weapon endpoints
│       ├── abilities.py     # Ability/keyword endpoints
│       ├── factions.py      # Faction detail endpoints
│       └── bulk.py          # Bulk operations
├── data/
│   ├── BSData/              # BattleScribe source catalogues (.cat files)
│   └── json/                # Generated JSON outputs
│       ├── Imperium_-_*.json
│       ├── Chaos_-_*.json
│       ├── Xenos_-_*.json
│       └── Unaligned_-_*.json
├── scripts/
│   └── universal_parser.py  # XML to JSON parser
├── tests/                   # Test files
│   ├── test_api.py
│   ├── test_all_endpoints.py
│   └── test_sorting.py
├── docs/                    # Documentation
│   ├── ENDPOINTS.md
│   ├── DEPLOYMENT.md
│   └── PROJECT_STRUCTURE.md
├── requirements.txt
└── README.md                # This file
```

### In-Memory Storage

The API uses an in-memory data store for optimal performance:

- **DataStore Class**: Loads all JSON on startup, builds multiple indices
- **Indices**: By ID, faction, faction_type for O(1) lookups
- **Search**: Filters results in-memory with sub-10ms response times
- **Memory Footprint**: ~10-15MB for 1,285 units

### CORS Configuration

CORS is enabled for all origins by default. For production, update `api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing

### Run All Endpoint Tests

```bash
python tests/test_all_endpoints.py
```

### Run Bulk Operation Tests

```bash
python tests/test_bulk_endpoints.py
```

### Run Sorting Tests

```bash
python tests/test_sorting.py
```

### Interactive Testing

Visit http://localhost:8000/docs for interactive Swagger UI where you can:
- Browse all endpoints
- See request/response schemas
- Test API calls directly in the browser
- View example responses

---

## Data Source

All data is parsed from official BattleScribe catalogue files maintained by the community at:
https://github.com/BSData/wh40k-10e

---

## License

This is a data parsing tool for personal use. All Warhammer 40,000 content is property of Games Workshop.
