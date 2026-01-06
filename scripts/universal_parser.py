import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path

def parse_catalogue(filepath, faction_type=None):
    tree = ET.parse(filepath)
    root = tree.getroot()

    ns = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}

    # Extract faction from catalogue name
    catalogue_name = root.get('name', '')
    faction = extract_faction(catalogue_name)

    units = []

    shared_entries = root.find('.//bs:sharedSelectionEntries', ns)

    if shared_entries is not None:
        # Parse both type="unit" (squads) and type="model" (characters)
        # Only get direct children, not nested entries
        for unit in shared_entries.findall('bs:selectionEntry', ns):
            unit_type = unit.get('type')

            # Only process units and models
            if unit_type not in ['unit', 'model']:
                continue

            unit_data = {
                'name': unit.get('name'),
                'id': unit.get('id'),
                'type': unit_type,  # 'unit' or 'model'
                'faction': faction,
                'faction_type': faction_type,  # Imperium, Chaos, Xenos, or Unaligned
                'points': {
                    'base': None,
                    'variants': []  # For units with variable squad sizes
                },
                'composition': {
                    'min_models': None,
                    'max_models': None
                },
                'stats': {},
                'invuln_save': None,
                'transport': None,  # Transport capacity if applicable
                'weapons': {
                    'ranged': [],
                    'melee': []
                },
                'abilities': [],
                'special_rules': [],
                'keywords': []
            }
            
            # Get base points cost (find the first non-zero cost, or use first if all zero)
            costs = unit.findall('.//bs:cost[@name="pts"]', ns)
            if costs:
                # Try to find a non-zero cost first
                for cost in costs:
                    cost_value = int(float(cost.get('value', 0)))
                    if cost_value > 0:
                        unit_data['points']['base'] = cost_value
                        break
                # If all costs are 0, use the first one
                if unit_data['points']['base'] is None:
                    unit_data['points']['base'] = int(float(costs[0].get('value', 0)))
            
            # Get point modifiers (for variable squad sizes)
            for modifier in unit.findall('.//bs:modifier[@field="51b2-306e-1021-d207"]', ns):
                mod_value = modifier.get('value')
                condition = modifier.find('.//bs:condition[@childId="model"]', ns)
                
                if condition is not None and mod_value:
                    model_count = condition.get('value')
                    unit_data['points']['variants'].append({
                        'models': int(model_count),
                        'points': int(float(mod_value))
                    })
            
            # Sort variants by model count
            unit_data['points']['variants'].sort(key=lambda x: x['models'])
            
            # Get squad size constraints
            for constraint in unit.findall('.//bs:constraint[@field="selections"]', ns):
                constraint_type = constraint.get('type')
                value = constraint.get('value')
                
                if constraint_type == 'min' and value:
                    unit_data['composition']['min_models'] = int(float(value))
                elif constraint_type == 'max' and value:
                    unit_data['composition']['max_models'] = int(float(value))
            
            # Get unit stats
            for profile in unit.findall('.//bs:profile[@typeName="Unit"]', ns):
                for char in profile.findall('.//bs:characteristic', ns):
                    stat_name = char.get('name')
                    stat_value = char.text
                    unit_data['stats'][stat_name] = stat_value
            
            # Get transport capacity
            for profile in unit.findall('.//bs:profile[@typeName="Transport"]', ns):
                capacity_char = profile.find('.//bs:characteristic[@name="Capacity"]', ns)
                if capacity_char is not None and capacity_char.text:
                    unit_data['transport'] = clean_text(capacity_char.text)

            # Get invulnerable save (check both infoLinks and ability profiles)
            # Method 1: Check infoLinks (used by Adeptus Custodes, some Space Marines)
            for info_link in unit.findall('.//bs:infoLink', ns):
                link_name = info_link.get('name', '')
                if 'Invulnerable' in link_name:
                    # Try to get the actual invuln value by following the targetId
                    target_id = info_link.get('targetId')
                    if target_id:
                        # Find the target profile in the root
                        target_profile = root.find(f'.//bs:profile[@id="{target_id}"]', ns)
                        if target_profile:
                            desc_elem = target_profile.find('.//bs:characteristic[@name="Description"]', ns)
                            if desc_elem is not None and desc_elem.text:
                                description = desc_elem.text
                                # Extract the invuln value (e.g., "4+")
                                match = re.search(r'(\d\+)', description)
                                if match:
                                    unit_data['invuln_save'] = match.group(1)
                                else:
                                    unit_data['invuln_save'] = link_name
                            else:
                                unit_data['invuln_save'] = link_name
                        else:
                            unit_data['invuln_save'] = link_name
                    else:
                        unit_data['invuln_save'] = link_name
                    break

            # Method 2: Check ability profiles (used by Chaos Space Marines, some others)
            # Only do this if we didn't already find an invuln from infoLinks
            if not unit_data['invuln_save']:
                for ability in unit.findall('.//bs:profile[@typeName="Abilities"]', ns):
                    ability_name = ability.get('name', '')
                    desc_elem = ability.find('.//bs:characteristic[@name="Description"]', ns)
                    description = desc_elem.text if desc_elem is not None else ''

                    # Check if ability name OR description contains "invulnerable save"
                    if 'invulnerable save' in ability_name.lower() or \
                       (description and 'invulnerable save' in description.lower()):

                        # Skip if this ability is inside optional wargear (type="upgrade")
                        # We need to check if any parent selectionEntry has type="upgrade"
                        is_optional_wargear = False

                        # Walk up the tree to check for upgrade parent
                        for parent in unit.iter():
                            # Check if ability is a descendant of this parent
                            if ability in list(parent.iter()):
                                if parent.tag == '{http://www.battlescribe.net/schema/catalogueSchema}selectionEntry' and \
                                   parent.get('type') == 'upgrade':
                                    is_optional_wargear = True
                                    break

                        # Only set invuln_save if it's NOT optional wargear
                        if not is_optional_wargear:
                            # Try to extract the invuln value from description (e.g., "4+")
                            if description:
                                # Look for patterns like "4+", "5+", etc. in the description
                                match = re.search(r'(\d\+)', description)
                                if match:
                                    unit_data['invuln_save'] = match.group(1)
                                else:
                                    # If we can't extract the value, just note that it has one
                                    unit_data['invuln_save'] = "Invulnerable Save"
                            else:
                                unit_data['invuln_save'] = "Invulnerable Save"
                            break

            # Get special rules with modifiers
            processed_rules = set()  # Track to avoid duplicates
            for info_link in unit.findall('.//bs:infoLink[@type="rule"]', ns):
                rule_name = info_link.get('name', '')
                if not rule_name or 'Invulnerable' in rule_name:
                    continue

                # Check for modifiers that append values (like "5+" or "6"")
                modifier = info_link.find('.//bs:modifier[@type="append"][@field="name"]', ns)
                if modifier is not None:
                    modifier_value = modifier.get('value', '')
                    full_rule = f"{rule_name} {modifier_value}".strip()
                else:
                    full_rule = rule_name

                # Only add if not already processed (avoid duplicates)
                if full_rule not in processed_rules:
                    unit_data['special_rules'].append(full_rule)
                    processed_rules.add(full_rule)
            
            # Get all ranged weapons from the unit (including from nested model entries and entryLinks)
            seen_ranged = set()

            # First, get weapons from direct profiles
            for weapon in unit.findall('.//bs:profile[@typeName="Ranged Weapons"]', ns):
                weapon_data = {'name': weapon.get('name')}
                for char in weapon.findall('.//bs:characteristic', ns):
                    weapon_data[char.get('name')] = char.text

                weapon_key = weapon_data['name']
                if weapon_key not in seen_ranged:
                    unit_data['weapons']['ranged'].append(weapon_data)
                    seen_ranged.add(weapon_key)

            # Then, check entryLinks for referenced weapons
            for entry_link in unit.findall('.//bs:entryLink[@type="selectionEntry"]', ns):
                link_target_id = entry_link.get('targetId')
                if link_target_id:
                    # Find the referenced weapon in sharedSelectionEntries
                    weapon_entry = root.find(f'.//bs:selectionEntry[@id="{link_target_id}"][@type="upgrade"]', ns)
                    if weapon_entry:
                        for weapon in weapon_entry.findall('.//bs:profile[@typeName="Ranged Weapons"]', ns):
                            weapon_data = {'name': weapon.get('name')}
                            for char in weapon.findall('.//bs:characteristic', ns):
                                weapon_data[char.get('name')] = char.text

                            weapon_key = weapon_data['name']
                            if weapon_key not in seen_ranged:
                                unit_data['weapons']['ranged'].append(weapon_data)
                                seen_ranged.add(weapon_key)

            # Get all melee weapons from the unit (including from nested model entries and entryLinks)
            seen_melee = set()

            # First, get weapons from direct profiles
            for weapon in unit.findall('.//bs:profile[@typeName="Melee Weapons"]', ns):
                weapon_data = {'name': weapon.get('name')}
                for char in weapon.findall('.//bs:characteristic', ns):
                    weapon_data[char.get('name')] = char.text

                weapon_key = weapon_data['name']
                if weapon_key not in seen_melee:
                    unit_data['weapons']['melee'].append(weapon_data)
                    seen_melee.add(weapon_key)

            # Then, check entryLinks for referenced weapons
            for entry_link in unit.findall('.//bs:entryLink[@type="selectionEntry"]', ns):
                link_target_id = entry_link.get('targetId')
                if link_target_id:
                    # Find the referenced weapon in sharedSelectionEntries
                    weapon_entry = root.find(f'.//bs:selectionEntry[@id="{link_target_id}"][@type="upgrade"]', ns)
                    if weapon_entry:
                        for weapon in weapon_entry.findall('.//bs:profile[@typeName="Melee Weapons"]', ns):
                            weapon_data = {'name': weapon.get('name')}
                            for char in weapon.findall('.//bs:characteristic', ns):
                                weapon_data[char.get('name')] = char.text

                            weapon_key = weapon_data['name']
                            if weapon_key not in seen_melee:
                                unit_data['weapons']['melee'].append(weapon_data)
                                seen_melee.add(weapon_key)

            # Get abilities
            for ability in unit.findall('.//bs:profile[@typeName="Abilities"]', ns):
                desc_elem = ability.find('.//bs:characteristic[@name="Description"]', ns)
                description = desc_elem.text if desc_elem is not None else None
                ability_data = {
                    'name': ability.get('name'),
                    'description': clean_text(description) if description else None
                }
                unit_data['abilities'].append(ability_data)
            
            # Get keywords
            for category in unit.findall('.//bs:categoryLink', ns):
                keyword = category.get('name')
                if keyword:
                    unit_data['keywords'].append(keyword)
            
            # Only add if it has stats (is a real unit/model)
            if unit_data['stats']:
                units.append(unit_data)
    
    return units

def clean_text(text):
    """Clean up text formatting issues from BattleScribe XML"""
    if not text:
        return text

    # Replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')

    # Replace curly quotes with straight quotes
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    text = text.replace('"', '"')
    text = text.replace('"', '"')

    # Replace em dash and en dash with regular dash
    text = text.replace('—', '-')
    text = text.replace('–', '-')

    # Replace black square bullet with proper bullet or dash
    text = text.replace('■', '-')

    # Replace other common unicode bullets
    text = text.replace('●', '-')
    text = text.replace('•', '-')

    # Remove ^^ markers (used for emphasis/styling in BattleScribe)
    text = text.replace('^^', '')

    return text

def extract_faction(catalogue_name):
    """Extract faction name from catalogue name"""
    if ' - ' in catalogue_name:
        parts = catalogue_name.split(' - ')
        return parts[-1].strip()
    return catalogue_name.strip()

def get_output_filename(catalogue_file):
    """
    Generate consistent output filename, mapping Library files to their wrapper names
    """
    input_filename = Path(catalogue_file).stem

    # Map Library files to their standard faction names
    library_mappings = {
        'Library - Titans': 'Unaligned_-_Titanicus',  # Shared between Imperium and Chaos
        'Imperium - Astra Militarum - Library': 'Imperium_-_Astra_Militarum',
        'Imperium - Imperial Knights - Library': 'Imperium_-_Imperial_Knights',
        'Chaos - Chaos Daemons Library': 'Chaos_-_Chaos_Daemons',
        'Chaos - Chaos Knights Library': 'Chaos_-_Chaos_Knights',
        'Aeldari - Aeldari Library': 'Xenos_-_Aeldari',
        'Library - Tyranids': 'Xenos_-_Tyranids',
    }

    # Map Xenos factions to include Xenos prefix
    xenos_mappings = {
        'Genestealer Cults': 'Xenos_-_Genestealer_Cults',
        'Leagues of Votann': 'Xenos_-_Leagues_of_Votann',
        'Necrons': 'Xenos_-_Necrons',
        'Orks': 'Xenos_-_Orks',
        'T\'au Empire': 'Xenos_-_T\'au_Empire',
    }

    # Map Unaligned factions to include Unaligned prefix
    unaligned_mappings = {
        'Unaligned Forces': 'Unaligned_-_Unaligned_Forces',
    }

    # Check if this is a library file that needs mapping
    if input_filename in library_mappings:
        output_filename = library_mappings[input_filename] + '.json'
    elif input_filename in xenos_mappings:
        output_filename = xenos_mappings[input_filename] + '.json'
    elif input_filename in unaligned_mappings:
        output_filename = unaligned_mappings[input_filename] + '.json'
    else:
        # Standard naming: replace spaces with underscores
        output_filename = input_filename.replace(' ', '_') + '.json'

    return output_filename

def main():
    # List of catalogue files to process with their faction types
    # Format: (filepath, faction_type)
    catalogue_files = [
        # Imperium
        ('data/BSData/Imperium - Adepta Sororitas.cat', 'Imperium'),
        ('data/BSData/Imperium - Adeptus Custodes.cat', 'Imperium'),
        ('data/BSData/Imperium - Adeptus Mechanicus.cat', 'Imperium'),
        ('data/BSData/Imperium - Agents of the Imperium.cat', 'Imperium'),
        ('data/BSData/Imperium - Astra Militarum - Library.cat', 'Imperium'),
        ('data/BSData/Imperium - Black Templars.cat', 'Imperium'),
        ('data/BSData/Imperium - Blood Angels.cat', 'Imperium'),
        ('data/BSData/Imperium - Dark Angels.cat', 'Imperium'),
        ('data/BSData/Imperium - Deathwatch.cat', 'Imperium'),
        ('data/BSData/Imperium - Grey Knights.cat', 'Imperium'),
        ('data/BSData/Imperium - Imperial Fists.cat', 'Imperium'),
        ('data/BSData/Imperium - Imperial Knights - Library.cat', 'Imperium'),
        ('data/BSData/Imperium - Iron Hands.cat', 'Imperium'),
        ('data/BSData/Imperium - Raven Guard.cat', 'Imperium'),
        ('data/BSData/Imperium - Salamanders.cat', 'Imperium'),
        ('data/BSData/Imperium - Space Marines.cat', 'Imperium'),
        ('data/BSData/Imperium - Space Wolves.cat', 'Imperium'),
        ('data/BSData/Imperium - Ultramarines.cat', 'Imperium'),
        ('data/BSData/Imperium - White Scars.cat', 'Imperium'),
        # Chaos
        ('data/BSData/Chaos - Chaos Daemons Library.cat', 'Chaos'),
        ('data/BSData/Chaos - Chaos Knights Library.cat', 'Chaos'),
        ('data/BSData/Chaos - Chaos Space Marines.cat', 'Chaos'),
        ('data/BSData/Chaos - Death Guard.cat', 'Chaos'),
        ('data/BSData/Chaos - Emperor\'s Children.cat', 'Chaos'),
        ('data/BSData/Chaos - Thousand Sons.cat', 'Chaos'),
        ('data/BSData/Chaos - World Eaters.cat', 'Chaos'),
        # Xenos
        ('data/BSData/Aeldari - Aeldari Library.cat', 'Xenos'),  # Library has the units
        # Skip: 'data/BSData/Aeldari - Craftworlds.cat',  # Just references Library
        # Skip: 'data/BSData/Aeldari - Drukhari.cat',  # Just references Library
        # Skip: 'data/BSData/Aeldari - Ynnari.cat',  # Just references Library
        ('data/BSData/Genestealer Cults.cat', 'Xenos'),
        ('data/BSData/Leagues of Votann.cat', 'Xenos'),
        ('data/BSData/Library - Tyranids.cat', 'Xenos'),  # Library has the units
        # Skip: 'data/BSData/Tyranids.cat',  # Just references Library
        ('data/BSData/Necrons.cat', 'Xenos'),
        ('data/BSData/Orks.cat', 'Xenos'),
        ('data/BSData/T\'au Empire.cat', 'Xenos'),
        # Unaligned
        ('data/BSData/Library - Titans.cat', 'Unaligned'),
        ('data/BSData/Unaligned Forces.cat', 'Unaligned')
    ]

    # Create output directory
    Path('data/json').mkdir(parents=True, exist_ok=True)

    # Process each catalogue file
    for catalogue_file, faction_type in catalogue_files:
        print(f"Processing: {catalogue_file}")

        # Parse the catalogue with faction type
        units = parse_catalogue(catalogue_file, faction_type)

        # Generate output filename using consistent naming
        output_filename = get_output_filename(catalogue_file)
        output_path = f'data/json/{output_filename}'

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(units, f, indent=2, ensure_ascii=False)

        print(f"  → Saved {len(units)} units to {output_path}")

        # Print first unit as example
        if units:
            print("\nExample unit:")
            print(json.dumps(units[0], indent=2))

    print("\nDone!")

if __name__ == '__main__':
    main()