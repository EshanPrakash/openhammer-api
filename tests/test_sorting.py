"""
Test sorting functionality
"""
import requests

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TESTING SORTING FUNCTIONALITY")
print("=" * 70)

# Test sort by name ascending
print("\n1. Sort by name (ascending):")
r = requests.get(f"{BASE_URL}/units?faction_type=Chaos&limit=5&sort_by=name")
units = r.json()
print(f"   First 5 Chaos units alphabetically:")
for u in units:
    print(f"   - {u['name']}")

# Test sort by name descending
print("\n2. Sort by name (descending):")
r = requests.get(f"{BASE_URL}/units?faction_type=Chaos&limit=5&sort_by=-name")
units = r.json()
print(f"   Last 5 Chaos units alphabetically:")
for u in units:
    print(f"   - {u['name']}")

# Test sort by points ascending
print("\n3. Sort by points (ascending):")
r = requests.get(f"{BASE_URL}/units?limit=5&sort_by=points")
units = r.json()
print(f"   5 cheapest units:")
for u in units:
    pts = u['points']['base'] if u['points']['base'] else 'N/A'
    print(f"   - {u['name']}: {pts} pts")

# Test sort by points descending
print("\n4. Sort by points (descending):")
r = requests.get(f"{BASE_URL}/units?limit=5&sort_by=-points")
units = r.json()
print(f"   5 most expensive units:")
for u in units:
    pts = u['points']['base'] if u['points']['base'] else 'N/A'
    print(f"   - {u['name']}: {pts} pts")

# Test sort by faction
print("\n5. Sort by faction (ascending):")
r = requests.get(f"{BASE_URL}/units?has_invuln=true&limit=6&sort_by=faction")
units = r.json()
print(f"   Units with invuln saves by faction:")
for u in units:
    print(f"   - [{u['faction']}] {u['name']}")

print("\n" + "=" * 70)
print("SORTING TESTS COMPLETE!")
print("=" * 70)
