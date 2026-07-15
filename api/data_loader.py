"""
Data loader - loads all JSON files into memory on startup
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from api.models import Unit


class EditionStore:
    """In-memory data store for a single edition"""

    def __init__(self):
        self.units: List[Unit] = []
        self.units_by_id: Dict[str, Unit] = {}
        self.units_by_faction: Dict[str, List[Unit]] = {}
        self.units_by_faction_type: Dict[str, List[Unit]] = {}
        self.factions: Dict[str, Dict] = {}

    def load(self, json_dir: Path):
        for json_file in sorted(json_dir.glob("*.json")):
            with open(json_file, 'r', encoding='utf-8') as f:
                units_data = json.load(f)

            for unit_data in units_data:
                try:
                    unit = Unit(**unit_data)
                    self.units.append(unit)
                    self.units_by_id[unit.id] = unit

                    if unit.faction not in self.units_by_faction:
                        self.units_by_faction[unit.faction] = []
                    self.units_by_faction[unit.faction].append(unit)

                    if unit.faction_type not in self.units_by_faction_type:
                        self.units_by_faction_type[unit.faction_type] = []
                    self.units_by_faction_type[unit.faction_type].append(unit)

                    if unit.faction not in self.factions:
                        self.factions[unit.faction] = {
                            "name": unit.faction,
                            "faction_type": unit.faction_type,
                            "unit_count": 0
                        }
                    self.factions[unit.faction]["unit_count"] += 1

                except Exception as e:
                    print(f"Error parsing unit in {json_file}: {e}")
                    continue

        print(f"[{json_dir.name}] Loaded {len(self.units)} units from {len(self.factions)} factions")

    def get_unit_by_id(self, unit_id: str) -> Optional[Unit]:
        return self.units_by_id.get(unit_id)

    def get_units_by_faction(self, faction: str) -> List[Unit]:
        return self.units_by_faction.get(faction, [])

    def get_units_by_faction_type(self, faction_type: str) -> List[Unit]:
        return self.units_by_faction_type.get(faction_type, [])

    def get_factions(self) -> List[Dict]:
        return list(self.factions.values())

    def search_units(
        self,
        name: str = None,
        faction: str = None,
        faction_type: str = None,
        unit_type: str = None,
        has_invuln: bool = None,
        has_transport: bool = None,
        keyword: str = None,
        points_min: int = None,
        points_max: int = None
    ) -> List[Unit]:
        results = self.units

        if name:
            results = [u for u in results if name.lower() in u.name.lower()]
        if faction:
            results = [u for u in results if u.faction == faction]
        if faction_type:
            results = [u for u in results if u.faction_type == faction_type]
        if unit_type:
            results = [u for u in results if u.type == unit_type]
        if has_invuln is not None:
            results = [u for u in results if (u.invuln_save is not None) == has_invuln]
        if has_transport is not None:
            results = [u for u in results if (u.transport is not None) == has_transport]
        if keyword:
            results = [u for u in results if keyword in u.keywords]
        if points_min is not None:
            results = [u for u in results if u.points.base and u.points.base >= points_min]
        if points_max is not None:
            results = [u for u in results if u.points.base and u.points.base <= points_max]

        return results


def sort_units(units: List[Unit], sort_by: str) -> List[Unit]:
    """Sort a unit list by 'name', 'points', or 'faction' (prefix with '-' for descending)."""
    reverse = sort_by.startswith('-')
    field = sort_by[1:] if reverse else sort_by

    if field == 'name':
        return sorted(units, key=lambda u: u.name.lower(), reverse=reverse)
    elif field == 'points':
        return sorted(units, key=lambda u: u.points.base or 0, reverse=reverse)
    elif field == 'faction':
        return sorted(units, key=lambda u: u.faction.lower(), reverse=reverse)
    return units


class DataStore:
    """Multi-edition in-memory data store"""

    def __init__(self):
        self._editions: Dict[str, EditionStore] = {}

    def load_all(self, base_dir: str = "data/json"):
        base_path = Path(base_dir)
        if not base_path.exists():
            raise FileNotFoundError(f"Data directory not found: {base_dir}")

        for edition_dir in sorted(base_path.iterdir()):
            if edition_dir.is_dir():
                store = EditionStore()
                store.load(edition_dir)
                self._editions[edition_dir.name] = store

        print(f"Loaded editions: {list(self._editions.keys())}")

    def get(self, edition: str) -> Optional[EditionStore]:
        return self._editions.get(edition)

    def list_editions(self) -> List[str]:
        return list(self._editions.keys())


data_store = DataStore()
