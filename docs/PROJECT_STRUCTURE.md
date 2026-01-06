# Project Structure

This document describes the organization of the OpenHammer API project.

## Directory Layout

```
openhammer-api/
├── api/                          # API application code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app, core endpoints
│   ├── models.py                # Pydantic data models
│   ├── data_loader.py           # In-memory data store
│   └── routers/                 # Endpoint routers
│       ├── __init__.py
│       ├── units.py             # Unit endpoints
│       ├── weapons.py           # Weapon endpoints
│       ├── abilities.py         # Ability/keyword endpoints
│       ├── factions.py          # Faction detail endpoints
│       └── bulk.py              # Bulk operations
│
├── data/                         # Data files
│   ├── json/                    # Generated JSON data (committed)
│   │   ├── Imperium_-_*.json
│   │   ├── Chaos_-_*.json
│   │   ├── Xenos_-_*.json
│   │   └── Unaligned_-_*.json
│   └── BSData/                  # BattleScribe source (gitignored)
│       └── *.cat
│
├── scripts/                      # Utility scripts
│   ├── universal_parser.py      # XML to JSON parser
│   └── sync_BSData.py           # BSData sync script
│
├── tests/                        # Test files
│   ├── test_api.py              # Basic API tests
│   ├── test_all_endpoints.py   # Comprehensive endpoint tests
│   ├── test_bulk_endpoints.py  # Bulk operation tests
│   └── test_sorting.py          # Sorting functionality tests
│
├── docs/                         # Documentation
│   ├── ENDPOINTS.md             # Complete endpoint reference
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── PROJECT_STRUCTURE.md     # This file
│
├── README.md                     # Main project documentation
├── requirements.txt              # Python dependencies
├── render.yaml                   # Render deployment config
└── .gitignore                    # Git ignore rules
```

## Key Files

### Application Files

- **api/main.py**: FastAPI application, middleware, core endpoints
- **api/models.py**: Pydantic models for data validation
- **api/data_loader.py**: DataStore class for in-memory data
- **api/routers/*.py**: Organized endpoint routers by domain

### Data Files

- **data/json/*.json**: 35 JSON files containing unit data (1,285 units total)
- **data/BSData/*.cat**: BattleScribe XML source files (not in git)

### Scripts

- **scripts/universal_parser.py**: Parses BattleScribe XML to JSON
- **scripts/sync_BSData.py**: Updates BattleScribe data from GitHub

### Tests

All test files moved to `tests/` directory for cleaner organization:
- Run tests: `python tests/test_all_endpoints.py`

### Documentation

- **README.md**: Main project documentation
- **docs/ENDPOINTS.md**: Complete API endpoint reference
- **docs/DEPLOYMENT.md**: Deployment instructions for Render and other platforms
- **docs/PROJECT_STRUCTURE.md**: This file

## Development Workflow

### 1. Update Data
```bash
# Sync latest BattleScribe data
python scripts/sync_BSData.py

# Parse to JSON
python scripts/universal_parser.py
```

### 2. Run API Locally
```bash
uvicorn api.main:app --reload
```

### 3. Test
```bash
python tests/test_all_endpoints.py
python tests/test_sorting.py
```

### 4. Deploy
```bash
git add .
git commit -m "Update message"
git push origin main
# Render auto-deploys
```

## File Naming Conventions

- **Python files**: `lowercase_with_underscores.py`
- **JSON files**: `FactionType_-_Faction_Name.json`
- **Documentation**: `UPPERCASE.md`
- **Tests**: `test_*.py`

## Ignored Files

See `.gitignore` for full list:
- `venv/` - Virtual environment
- `data/BSData/` - Source XML files
- `__pycache__/` - Python cache
- `.env` - Environment variables
- `.DS_Store` - macOS files
