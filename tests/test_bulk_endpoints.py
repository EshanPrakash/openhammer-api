"""
Test script for new bulk and faction detail endpoints
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
                    print(f"  {key}: {type(value).__name__} (length: {len(value) if isinstance(value, (list, dict)) else 'N/A'})")
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
print("OPENHAMMER API - NEW BULK & FACTION DETAIL ENDPOINTS TEST")
print("=" * 70)

# Faction detail endpoints
test_endpoint("Faction Details - Necrons", f"{BASE_URL}/factions/Necrons/details", show_results=8)
test_endpoint("Faction Details - Space Marines", f"{BASE_URL}/factions/Space%20Marines/details", show_results=8)
test_endpoint("Faction Stats - Tyranids", f"{BASE_URL}/factions/Tyranids/stats", show_results=12)
test_endpoint("Faction Keywords - Adeptus Custodes", f"{BASE_URL}/factions/Adeptus%20Custodes/keywords", show_results=15)

# Bulk unit lookups
test_endpoint("Bulk Units by IDs", f"{BASE_URL}/bulk/units/by-ids?ids=7998-d0a-baa4-e8b3,a018-ca33-afd0-be83")
test_endpoint("Bulk Units by Names", f"{BASE_URL}/bulk/units/by-names?names=Intercessors,Terminators")

# Bulk stats aggregations
test_endpoint("Bulk Stats by Keyword - Infantry", f"{BASE_URL}/bulk/stats/by-keyword?keyword=Infantry", show_results=12)
test_endpoint("Bulk Stats by Keyword - Vehicle", f"{BASE_URL}/bulk/stats/by-keyword?keyword=Vehicle", show_results=12)
test_endpoint("Bulk Stats by Faction Type - Imperium", f"{BASE_URL}/bulk/stats/by-faction-type?faction_type=Imperium", show_results=15)
test_endpoint("Bulk Stats by Faction Type - Xenos", f"{BASE_URL}/bulk/stats/by-faction-type?faction_type=Xenos", show_results=15)
test_endpoint("Bulk Stats by Faction - Necrons", f"{BASE_URL}/bulk/stats/by-faction?faction=Necrons", show_results=15)
test_endpoint("Bulk Stats by Faction - Death Guard", f"{BASE_URL}/bulk/stats/by-faction?faction=Death%20Guard", show_results=15)

# Export endpoint
test_endpoint("Export All Units Summary", f"{BASE_URL}/bulk/export/all-units-summary", show_results=5)

print("\n" + "=" * 70)
print("ALL NEW ENDPOINT TESTS COMPLETE!")
print(f"Visit {BASE_URL}/docs for interactive API documentation")
print("=" * 70)
