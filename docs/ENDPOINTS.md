# OpenHammer API - Endpoint Reference

## Base URL
`http://localhost:8000`

## Quick Links
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📊 Statistics & Info

### `GET /`
Root endpoint with API info

### `GET /stats`
Get API statistics
```json
{
  "total_units": 1285,
  "total_factions": 34,
  "factions_by_type": {...},
  "units_by_faction_type": {...}
}
```

---

## 🏴 Faction Endpoints

### `GET /factions`
List all factions
- **Query params**: `faction_type` (Imperium, Chaos, Xenos, Unaligned)
- **Example**: `/factions?faction_type=Imperium`

### `GET /factions/{faction_name}/units`
Get all units for a specific faction
- **Query params**: `limit`, `offset`
- **Example**: `/factions/Necrons/units?limit=20`

### `GET /factions/{faction_name}/details`
Get comprehensive faction details
- **Returns**: Total units, unit breakdown, stats, all keywords, all special rules
- **Example**: `/factions/Necrons/details`

### `GET /factions/{faction_name}/stats`
Get statistical breakdown for a faction
- **Returns**: Points distribution, weapon counts, invuln percentage, ability counts
- **Example**: `/factions/Space%20Marines/stats`

### `GET /factions/{faction_name}/keywords`
Get all keywords used in a faction with unit counts
- **Returns**: Keywords sorted by frequency
- **Example**: `/factions/Tyranids/keywords`

---

## ⚔️ Unit Endpoints

### `GET /units`
**Main search endpoint** - List units with filtering and sorting
- **Query params**:
  - `limit` (1-500, default: 100)
  - `offset` (pagination)
  - `name` (partial match)
  - `faction` (exact match)
  - `faction_type` (Imperium/Chaos/Xenos/Unaligned)
  - `type` (unit or model)
  - `has_invuln` (true/false)
  - `has_transport` (true/false)
  - `keyword` (exact match)
  - `points_min` (integer)
  - `points_max` (integer)
  - `sort_by` (name, points, faction - prefix with `-` for descending)

**Examples**:
```bash
/units?faction_type=Chaos&has_invuln=true
/units?points_min=100&points_max=200
/units?name=terminator&faction_type=Imperium
/units?sort_by=points (cheapest first)
/units?sort_by=-points (most expensive first)
/units?faction_type=Xenos&sort_by=name
```

### `GET /units/{unit_id}`
Get specific unit by ID
- **Example**: `/units/9e42-7207-9c30-6122`

### `GET /units/search/name/{name}`
Search units by name (partial match)
- **Query params**: `limit`
- **Example**: `/units/search/name/custodian`

### `GET /units/random`
Get a random unit
- **Query params**: `faction_type`
- **Example**: `/units/random?faction_type=Chaos`

### `GET /units/expensive`
Get most expensive units by points
- **Query params**: `limit`, `faction_type`
- **Example**: `/units/expensive?limit=10&faction_type=Imperium`

### `GET /units/cheap`
Get cheapest units by points
- **Query params**: `limit`, `faction_type`
- **Example**: `/units/cheap?limit=10&faction_type=Xenos`

### `GET /units/count`
Count units matching filters (no data returned)
- **Query params**: `faction`, `faction_type`, `has_invuln`, `has_transport`
- **Example**: `/units/count?faction_type=Xenos&has_invuln=true`

### `GET /units/compare`
Compare multiple units by IDs
- **Query params**: `ids` (comma-separated)
- **Example**: `/units/compare?ids=abc-123,def-456,ghi-789`

---

## 🔫 Weapon Endpoints

### `GET /weapons/stats`
Get weapon statistics
```json
{
  "total_weapon_entries": 5661,
  "ranged": {"total_entries": 3625, "unique_weapons": 1411},
  "melee": {"total_entries": 2036, "unique_weapons": 840}
}
```

### `GET /weapons/list`
List all unique weapon names
- **Query params**: `weapon_type` (ranged/melee), `limit`
- **Example**: `/weapons/list?weapon_type=ranged&limit=50`

### `GET /weapons/search/{name}`
Search for weapons and get units that have them
- **Query params**: `weapon_type` (ranged/melee)
- **Example**: `/weapons/search/bolter?weapon_type=ranged`
- **Returns**: List of units with matching weapons

---

## ⚡ Ability & Keyword Endpoints

### `GET /abilities/search/{term}`
Search abilities by name or description
- **Query params**: `limit`
- **Example**: `/abilities/search/deep%20strike`
- **Returns**: Units with matching abilities

### `GET /abilities/keywords/list`
List all unique keywords
- **Query params**: `limit`
- **Example**: `/abilities/keywords/list?limit=100`

### `GET /abilities/keywords/search/{keyword}`
Find units with specific keyword
- **Query params**: `faction_type`
- **Example**: `/abilities/keywords/search/Infantry?faction_type=Imperium`
- **Returns**: Units with matching keyword

### `GET /abilities/special-rules/list`
List all unique special rules
- **Query params**: `limit`
- **Example**: `/abilities/special-rules/list?limit=100`

### `GET /abilities/special-rules/search/{rule}`
Find units with specific special rule
- **Query params**: `faction_type`
- **Example**: `/abilities/special-rules/search/Feel%20No%20Pain`
- **Returns**: Units with matching special rule

---

## 📦 Bulk Operations

### `GET /bulk/units/by-ids`
Bulk lookup units by IDs
- **Query params**: `ids` (comma-separated unit IDs)
- **Example**: `/bulk/units/by-ids?ids=abc-123,def-456,ghi-789`
- **Returns**: Requested count, found count, not_found list, units array

### `GET /bulk/units/by-names`
Bulk lookup units by names
- **Query params**: `names` (comma-separated unit names)
- **Example**: `/bulk/units/by-names?names=Intercessors,Terminators,Dreadnought`
- **Returns**: Requested count, found count, not_found list, units array

### `GET /bulk/stats/by-keyword`
Get aggregated stats for all units with a keyword
- **Query params**: `keyword`
- **Example**: `/bulk/stats/by-keyword?keyword=Infantry`
- **Returns**: Unit count, stats, faction breakdown, faction_type breakdown

### `GET /bulk/stats/by-faction-type`
Get comprehensive stats for a faction type
- **Query params**: `faction_type` (Imperium, Chaos, Xenos, Unaligned)
- **Example**: `/bulk/stats/by-faction-type?faction_type=Imperium`
- **Returns**: Total units, stats, points distribution, faction breakdown, top keywords

### `GET /bulk/stats/by-faction`
Get comprehensive stats for a specific faction
- **Query params**: `faction`
- **Example**: `/bulk/stats/by-faction?faction=Necrons`
- **Returns**: Total units, stats, points distribution, top keywords, top special rules

### `GET /bulk/export/all-units-summary`
Export summary of all units
- **Example**: `/bulk/export/all-units-summary`
- **Returns**: All units with id, name, faction, faction_type, type, points, invuln, transport, keywords

---

## 📝 Response Format

All unit responses follow this structure:
```json
{
  "name": "Custodian Guard",
  "id": "91b3-2e1c-e642-d213",
  "type": "unit",
  "faction": "Adeptus Custodes",
  "faction_type": "Imperium",
  "points": {
    "base": 160,
    "variants": [...]
  },
  "composition": {...},
  "stats": {...},
  "invuln_save": "4+",
  "transport": null,
  "weapons": {
    "ranged": [...],
    "melee": [...]
  },
  "abilities": [...],
  "special_rules": [...],
  "keywords": [...]
}
```

---

## 🚀 Usage Examples

### Find Cheap Chaos Units with Invuln
```bash
curl 'http://localhost:8000/units?faction_type=Chaos&has_invuln=true&points_max=100'
```

### Search for All Bolter Weapons
```bash
curl 'http://localhost:8000/weapons/search/bolter'
```

### Get Random Xenos Unit
```bash
curl 'http://localhost:8000/units/random?faction_type=Xenos'
```

### Find Infantry Units in Imperium
```bash
curl 'http://localhost:8000/abilities/keywords/search/Infantry?faction_type=Imperium'
```

### Count Transports
```bash
curl 'http://localhost:8000/units/count?has_transport=true'
```

---

## 💡 Tips

1. **Use the interactive docs**: Visit `/docs` to test endpoints in your browser
2. **URL encode spaces**: Use `%20` for spaces in search terms
3. **Pagination**: Use `limit` and `offset` for large results
4. **Combine filters**: Mix multiple query params for precise searches
5. **Case-insensitive**: Most searches are case-insensitive

---

## 📊 Data Stats

- **Total Units**: 1,285
- **Total Factions**: 34
- **Imperium**: 574 units (18 factions)
- **Chaos**: 301 units (7 factions)
- **Xenos**: 386 units (7 factions)
- **Unaligned**: 24 units (2 groups)
- **Unique Weapons**: 2,251 (1,411 ranged + 840 melee)
