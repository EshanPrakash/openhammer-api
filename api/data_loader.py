"""
Data loader - loads all JSON files into memory on startup
"""
import json
from pathlib import Path
from typing import List, Dict
from api.models import Unit


class DataStore:
    """In-memory data store for all units"""

    def __init__(self):
        self.units: List[Unit] = []
        self.units_by_id: Dict[str, Unit] = {}
        self.units_by_faction: Dict[str, List[Unit]] = {}
        self.units_by_faction_type: Dict[str, List[Unit]] = {}
        self.factions: Dict[str, Dict] = {}

    def load_data(self, json_dir: str = "data/json"):
        """Load all unit data from JSON files"""
        json_path = Path(json_dir)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON directory not found: {json_dir}")

        # Load all JSON files
        for json_file in sorted(json_path.glob("*.json")):
            with open(json_file, 'r', encoding='utf-8') as f:
                units_data = json.load(f)

            # Parse each unit
            for unit_data in units_data:
                try:
                    unit = Unit(**unit_data)
                    self.units.append(unit)

                    # Index by ID
                    self.units_by_id[unit.id] = unit

                    # Index by faction
                    if unit.faction not in self.units_by_faction:
                        self.units_by_faction[unit.faction] = []
                    self.units_by_faction[unit.faction].append(unit)

                    # Index by faction type
                    if unit.faction_type not in self.units_by_faction_type:
                        self.units_by_faction_type[unit.faction_type] = []
                    self.units_by_faction_type[unit.faction_type].append(unit)

                    # Track faction info
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

        print(f"✓ Loaded {len(self.units)} units from {len(self.factions)} factions")

    def get_all_units(self) -> List[Unit]:
        """Get all units"""
        return self.units

    def get_unit_by_id(self, unit_id: str) -> Unit:
        """Get unit by ID"""
        return self.units_by_id.get(unit_id)

    def get_units_by_faction(self, faction: str) -> List[Unit]:
        """Get all units for a faction"""
        return self.units_by_faction.get(faction, [])

    def get_units_by_faction_type(self, faction_type: str) -> List[Unit]:
        """Get all units for a faction type"""
        return self.units_by_faction_type.get(faction_type, [])

    def get_factions(self) -> List[Dict]:
        """Get all factions"""
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
        """Search units with multiple filters"""
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


# Global data store instance
data_store = DataStore()
