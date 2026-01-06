"""
Pydantic models for Warhammer 40K unit data
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class PointsVariant(BaseModel):
    """Points cost variant for different squad sizes"""
    models: int
    points: int


class Points(BaseModel):
    """Points cost information"""
    base: Optional[int] = None
    variants: List[PointsVariant] = []


class Composition(BaseModel):
    """Unit composition (squad size)"""
    min_models: Optional[int] = None
    max_models: Optional[int] = None


class Stats(BaseModel):
    """Unit statline"""
    M: Optional[str] = None  # Movement
    T: Optional[str] = None  # Toughness
    SV: Optional[str] = None  # Save
    W: Optional[str] = None  # Wounds
    LD: Optional[str] = None  # Leadership
    OC: Optional[str] = None  # Objective Control


class Weapon(BaseModel):
    """Weapon profile"""
    name: str
    Range: str
    A: str  # Attacks
    BS: Optional[str] = None  # Ballistic Skill (ranged)
    WS: Optional[str] = None  # Weapon Skill (melee)
    S: str  # Strength
    AP: str  # Armor Penetration
    D: str  # Damage
    Keywords: str


class Weapons(BaseModel):
    """Weapons collection"""
    ranged: List[Weapon] = []
    melee: List[Weapon] = []


class Ability(BaseModel):
    """Unit ability"""
    name: str
    description: Optional[str] = None


class Unit(BaseModel):
    """Complete unit data model"""
    name: str
    id: str
    type: str  # "unit" or "model"
    faction: str
    faction_type: str  # "Imperium", "Chaos", "Xenos", "Unaligned"
    points: Points
    composition: Composition
    stats: Stats
    invuln_save: Optional[str] = None
    transport: Optional[str] = None
    weapons: Weapons
    abilities: List[Ability] = []
    special_rules: List[str] = []
    keywords: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Custodian Guard",
                "id": "91b3-2e1c-e642-d213",
                "type": "unit",
                "faction": "Adeptus Custodes",
                "faction_type": "Imperium",
                "points": {
                    "base": 160,
                    "variants": [{"models": 5, "points": 200}]
                },
                "composition": {
                    "min_models": 3,
                    "max_models": 10
                },
                "stats": {
                    "M": "6\"",
                    "T": "6",
                    "SV": "2+",
                    "W": "4",
                    "LD": "6+",
                    "OC": "3"
                },
                "invuln_save": "4+",
                "transport": None,
                "weapons": {
                    "ranged": [],
                    "melee": []
                },
                "abilities": [],
                "special_rules": ["Deep Strike"],
                "keywords": ["Infantry", "Imperium"]
            }
        }


class FactionInfo(BaseModel):
    """Faction information"""
    name: str
    faction_type: str
    unit_count: int


class StatsResponse(BaseModel):
    """API statistics"""
    total_units: int
    total_factions: int
    factions_by_type: dict
    units_by_faction_type: dict
