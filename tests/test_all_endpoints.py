"""
Comprehensive API endpoint test script
"""
import requests

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, show_results=10):
    """Test an endpoint and display results"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"URL: {url}")
    print('='*70)

    try:
        r = requests.get(url)
        data = r.json()

        if isinstance(data, dict):
            for key, value in list(data.items())[:show_results]:
                if isinstance(value, (list, dict)) and len(str(value)) > 100:
                    print(f"  {key}: {type(value).__name__} (length: {len(value)})")
                else:
                    print(f"  {key}: {value}")
        elif isinstance(data, list):
            print(f"  Results: {len(data)} items")
            for item in data[:show_results]:
                if isinstance(item, dict) and 'name' in item:
                    print(f"    - {item.get('name', item.get('id', str(item)[:50]))}")
                else:
                    print(f"    - {str(item)[:80]}")
        else:
            print(f"  {data}")

        print(f"✓ SUCCESS")

    except Exception as e:
        print(f"✗ ERROR: {e}")


print("=" * 70)
print("OPENHAMMER API - COMPREHENSIVE ENDPOINT TEST")
print("=" * 70)

# Basic endpoints
test_endpoint("Root", f"{BASE_URL}/")
test_endpoint("API Stats", f"{BASE_URL}/stats")

# Faction endpoints
test_endpoint("All Factions", f"{BASE_URL}/factions")
test_endpoint("Imperium Factions", f"{BASE_URL}/factions?faction_type=Imperium")
test_endpoint("Faction Units - Necrons", f"{BASE_URL}/factions/Necrons/units?limit=5")

# Unit endpoints
test_endpoint("All Units (paginated)", f"{BASE_URL}/units?limit=5")
test_endpoint("Chaos Units", f"{BASE_URL}/units?faction_type=Chaos&limit=5")
test_endpoint("Units with Invuln", f"{BASE_URL}/units?has_invuln=true&limit=5")
test_endpoint("Points Range 100-200", f"{BASE_URL}/units?points_min=100&points_max=200&limit=5")
test_endpoint("Search by Name: Terminator", f"{BASE_URL}/units/search/name/terminator")

# New unit endpoints
test_endpoint("Random Chaos Unit", f"{BASE_URL}/units/random?faction_type=Chaos")
test_endpoint("Most Expensive Units", f"{BASE_URL}/units/expensive?limit=5")
test_endpoint("Cheapest Units", f"{BASE_URL}/units/cheap?limit=5")
test_endpoint("Unit Count - Xenos with Invuln", f"{BASE_URL}/units/count?faction_type=Xenos&has_invuln=true")

# Weapon endpoints
test_endpoint("Weapon Stats", f"{BASE_URL}/weapons/stats")
test_endpoint("List Ranged Weapons", f"{BASE_URL}/weapons/list?weapon_type=ranged&limit=10")
test_endpoint("Search Weapons: Bolter", f"{BASE_URL}/weapons/search/bolter?weapon_type=ranged", show_results=3)

# Ability endpoints
test_endpoint("Search Abilities: Deep Strike", f"{BASE_URL}/abilities/search/deep%20strike", show_results=3)
test_endpoint("List Keywords", f"{BASE_URL}/abilities/keywords/list?limit=20")
test_endpoint("Search Keyword: Infantry", f"{BASE_URL}/abilities/keywords/search/Infantry?faction_type=Imperium", show_results=5)
test_endpoint("List Special Rules", f"{BASE_URL}/abilities/special-rules/list?limit=15")
test_endpoint("Search Special Rule: Feel No Pain", f"{BASE_URL}/abilities/special-rules/search/Feel%20No%20Pain", show_results=5)

# Faction detail endpoints
test_endpoint("Faction Details - Necrons", f"{BASE_URL}/factions/Necrons/details", show_results=8)
test_endpoint("Faction Stats - Tyranids", f"{BASE_URL}/factions/Tyranids/stats", show_results=10)
test_endpoint("Faction Keywords - Custodes", f"{BASE_URL}/factions/Adeptus%20Custodes/keywords", show_results=15)

# Bulk endpoints
test_endpoint("Bulk Units by IDs", f"{BASE_URL}/bulk/units/by-ids?ids=7998-d0a-baa4-e8b3,a018-ca33-afd0-be83")
test_endpoint("Bulk Stats - Infantry", f"{BASE_URL}/bulk/stats/by-keyword?keyword=Infantry", show_results=10)
test_endpoint("Bulk Stats - Imperium", f"{BASE_URL}/bulk/stats/by-faction-type?faction_type=Imperium", show_results=12)
test_endpoint("Bulk Stats - Necrons Faction", f"{BASE_URL}/bulk/stats/by-faction?faction=Necrons", show_results=12)

print("\n" + "=" * 70)
print("ALL TESTS COMPLETE!")
print(f"Visit {BASE_URL}/docs for interactive API documentation")
print("=" * 70)
