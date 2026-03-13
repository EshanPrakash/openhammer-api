# OpenHammer API

REST API for Warhammer 40,000 10th Edition unit data. 1,285 units across 35 factions.

**Live API**: https://openhammer-api-production.up.railway.app

**Interactive Docs**: https://openhammer-api-production.up.railway.app/docs

## Table of Contents
- [Usage](#usage)
- [Quick Start (Local)](#quick-start-local)
- [API Overview](#api-overview)
- [Data Coverage](#data-coverage)
- [API Endpoints](#api-endpoints)
- [JSON Structure](#json-structure)

---

## Usage

The API is live at **https://openhammer-api-production.up.railway.app**

### Python
```python
import requests

# Get all factions
response = requests.get('https://openhammer-api-production.up.railway.app/factions')
factions = response.json()

# Search for Space Marine units
response = requests.get('https://openhammer-api-production.up.railway.app/units?name=Marine&limit=10')
units = response.json()

# Get random unit
response = requests.get('https://openhammer-api-production.up.railway.app/units/random')
random_unit = response.json()
```

### JavaScript
```javascript
// Get API statistics
fetch('https://openhammer-api-production.up.railway.app/stats')
  .then(res => res.json())
  .then(data => console.log(data));

// Search Necrons units
const response = await fetch('https://openhammer-api-production.up.railway.app/units?faction=Necrons');
const units = await response.json();
```

### curl
```bash
# Get all factions
curl https://openhammer-api-production.up.railway.app/factions

# Search for Terminator units
curl https://openhammer-api-production.up.railway.app/units?name=Terminator

# Get faction details
curl https://openhammer-api-production.up.railway.app/factions/Necrons/details
```

### Interactive Testing

Visit **https://openhammer-api-production.up.railway.app/docs** to:
- Browse all 29 endpoints
- Try requests directly in your browser
- See example responses
- View request/response schemas

---

## Quick Start (Local)

To run this API locally:

```bash
git clone https://github.com/EshanPrakash/openhammer-api.git
cd openhammer-api
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Visit http://localhost:8000/docs for interactive documentation.

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
- **Memory Usage**: ~10-15MB (all 1,285 units loaded in memory)
- **Response Time**: <10ms for most queries
- **Data**: 1,285 units across 35 factions

### Features

- In-memory storage with <10ms response times
- HTTP caching (1 hour)
- Rate limiting (100 req/min per IP)
- Interactive Swagger docs at `/docs`
- Sorting and filtering across 11+ parameters
- Bulk operations and faction analytics
- CORS enabled

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


## API Endpoints

### Quick Reference

**Statistics & Info**
- `GET /` - API information
- `GET /stats` - API statistics (total units, factions, breakdown)

**Factions** (5 endpoints)
- `GET /factions` - List all factions
- `GET /factions/{faction_name}/units` - Get faction units
- `GET /factions/{faction_name}/details` - Comprehensive faction details
- `GET /factions/{faction_name}/stats` - Statistical breakdown
- `GET /factions/{faction_name}/keywords` - Faction keywords with counts

**Units** (8 endpoints)
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

**Bulk Operations** (6 endpoints)
- `GET /bulk/units/by-ids` - Bulk lookup by IDs
- `GET /bulk/units/by-names` - Bulk lookup by names
- `GET /bulk/stats/by-keyword` - Aggregate stats by keyword
- `GET /bulk/stats/by-faction-type` - Aggregate stats by faction type
- `GET /bulk/stats/by-faction` - Aggregate stats by faction
- `GET /bulk/export/all-units-summary` - Export all units summary

### Example Queries

```bash
# Get all Chaos units with invulnerable saves
curl 'https://openhammer-api-production.up.railway.app/units?faction_type=Chaos&has_invuln=true'

# Get most expensive units across all factions
curl 'https://openhammer-api-production.up.railway.app/units?sort_by=-points&limit=10'

# Get cheapest Imperium units
curl 'https://openhammer-api-production.up.railway.app/units?faction_type=Imperium&sort_by=points&limit=20'

# Search for bolter weapons
curl 'https://openhammer-api-production.up.railway.app/weapons/search/bolter'

# Get faction details for Necrons
curl 'https://openhammer-api-production.up.railway.app/factions/Necrons/details'

# Get stats for all Infantry units
curl 'https://openhammer-api-production.up.railway.app/bulk/stats/by-keyword?keyword=Infantry'

# Get comprehensive Imperium statistics
curl 'https://openhammer-api-production.up.railway.app/bulk/stats/by-faction-type?faction_type=Imperium'
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

## License

MIT License - see LICENSE file.

All Warhammer 40,000 content is property of Games Workshop. 

Unit data sourced from [BSData/wh40k-10e](https://github.com/BSData/wh40k-10e).
