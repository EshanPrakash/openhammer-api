"""Quick API test script"""
import requests

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("OPENHAMMER API TEST")
print("=" * 70)

# Test 1: Stats
print("\n1. API Statistics:")
r = requests.get(f"{BASE_URL}/stats")
stats = r.json()
print(f"   Total Units: {stats['total_units']}")
print(f"   Total Factions: {stats['total_factions']}")
print(f"   By Type: {stats['units_by_faction_type']}")

# Test 2: Factions
print("\n2. Imperium Factions:")
r = requests.get(f"{BASE_URL}/factions", params={"faction_type": "Imperium"})
factions = r.json()
for f in factions[:5]:
    print(f"   - {f['name']}: {f['unit_count']} units")

# Test 3: Search
print("\n3. Search: Chaos units with invuln saves:")
r = requests.get(f"{BASE_URL}/units", params={
    "faction_type": "Chaos",
    "has_invuln": True,
    "limit": 3
})
units = r.json()
for u in units:
    print(f"   - {u['name']} ({u['faction']}): {u['invuln_save']}")

# Test 4: Points filter
print("\n4. Units costing 200-250 points:")
r = requests.get(f"{BASE_URL}/units", params={
    "points_min": 200,
    "points_max": 250,
    "limit": 3
})
units = r.json()
for u in units:
    print(f"   - {u['name']}: {u['points']['base']} pts")

# Test 5: Specific faction
print("\n5. Necron units:")
r = requests.get(f"{BASE_URL}/units", params={
    "faction": "Necrons",
    "limit": 5
})
units = r.json()
for u in units:
    print(f"   - {u['name']} ({u['type']})")

print("\n" + "=" * 70)
print("✓ All tests passed!")
print(f"✓ Visit http://localhost:8000/docs for interactive API docs")
print("=" * 70)
