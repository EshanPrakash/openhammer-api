import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path

def parse_catalogue(filepath, faction_type=None, parent_catalogue=None):
    tree = ET.parse(filepath)
    root = tree.getroot()

    ns = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}

    # Extract faction from catalogue name
    catalogue_name = root.get('name', '')
    faction = extract_faction(catalogue_name)

    # Load parent catalogue if this is a Space Marine chapter supplement
    parent_root = None
    if parent_catalogue and Path(parent_catalogue).exists():
        parent_tree = ET.parse(parent_catalogue)
        parent_root = parent_tree.getroot()

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
                        # Find the target profile in the current file first
                        target_profile = root.find(f'.//bs:profile[@id="{target_id}"]', ns)

                        # If not found and we have a parent catalogue, check there
                        if not target_profile and parent_root is not None:
                            target_profile = parent_root.find(f'.//bs:profile[@id="{target_id}"]', ns)

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
            
            # Get keywords (direct categoryLinks only, not nested weapon/equipment ones)
            seen = set()
            for category in unit.findall('bs:categoryLinks/bs:categoryLink', ns):
                keyword = category.get('name')
                if keyword and keyword not in seen:
                    seen.add(keyword)
                    unit_data['keywords'].append(keyword)
            
            # Only add if it has stats (is a real unit/model)
            if unit_data['stats']:
                units.append(unit_data)

    return units

POINTS_FIELD_ID = '51b2-306e-1021-d207'  # Same BattleScribe points-field GUID in both 10e (XML) and 11e (JSON)

def _walk_entries(entry, ancestor_upgrade=False):
    """Recursively yield (sub_entry, is_upgrade) for entry and all nested
    selectionEntries/selectionEntryGroups, mirroring what XPath '//' recursive
    search gave the XML parser for free. is_upgrade is True if this entry or
    any ancestor has type == 'upgrade' (optional wargear)."""
    is_upgrade = ancestor_upgrade or (entry.get('type') == 'upgrade')
    yield entry, is_upgrade
    for child in entry.get('selectionEntries') or []:
        yield from _walk_entries(child, is_upgrade)
    for child in entry.get('selectionEntryGroups') or []:
        yield from _walk_entries(child, is_upgrade)

def _shared_roots(catalogue_root):
    """Top-level containers that can hold (possibly deeply nested) selectionEntries:
    both sharedSelectionEntries and sharedSelectionEntryGroups (e.g. shared weapon-option
    groups like 'Terminator Heavy Weapons' live under the latter)."""
    return (catalogue_root.get('sharedSelectionEntries') or []) + \
           (catalogue_root.get('sharedSelectionEntryGroups') or [])

def _find_profile_by_id(catalogue_root, profile_id):
    for entry in _shared_roots(catalogue_root):
        for sub_entry, _ in _walk_entries(entry):
            for profile in sub_entry.get('profiles') or []:
                if profile.get('id') == profile_id:
                    return profile
    for profile in catalogue_root.get('sharedProfiles') or []:
        if profile.get('id') == profile_id:
            return profile
    return None

def _find_upgrade_entry_by_id(catalogue_root, entry_id):
    for entry in _shared_roots(catalogue_root):
        for sub_entry, _ in _walk_entries(entry):
            if sub_entry.get('id') == entry_id and sub_entry.get('type') == 'upgrade':
                return sub_entry
    return None

def _char_text(characteristics, name):
    for char in characteristics or []:
        if char.get('name') == name:
            return char.get('$text')
    return None

def parse_catalogue_json(filepath, faction_type=None, parent_catalogue=None):
    """Parse a BSData BattleScribe-JSON catalogue (used by wh40k-11e).
    Produces the same unit_data schema as parse_catalogue() (XML/10e)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        root = json.load(f)['catalogue']

    catalogue_name = root.get('name', '')
    faction = extract_faction(catalogue_name)

    parent_root = None
    if parent_catalogue and Path(parent_catalogue).exists():
        with open(parent_catalogue, 'r', encoding='utf-8') as f:
            parent_root = json.load(f)['catalogue']

    units = []
    shared_entries = root.get('sharedSelectionEntries') or []

    for unit in shared_entries:
        unit_type = unit.get('type')
        if unit_type not in ['unit', 'model']:
            continue

        unit_data = {
            'name': unit.get('name'),
            'id': unit.get('id'),
            'type': unit_type,
            'faction': faction,
            'faction_type': faction_type,
            'points': {
                'base': None,
                'variants': []
            },
            'composition': {
                'min_models': None,
                'max_models': None
            },
            'stats': {},
            'invuln_save': None,
            'transport': None,
            'weapons': {
                'ranged': [],
                'melee': []
            },
            'abilities': [],
            'special_rules': [],
            'keywords': []
        }

        # Base points cost (find first non-zero cost, or use first if all zero), searched
        # recursively like the XML '//' did - some units (e.g. single-model entries) carry
        # their 'pts' cost on a nested selectionEntry rather than the top-level unit.
        costs = []
        for entry, _ in _walk_entries(unit):
            costs.extend(c for c in (entry.get('costs') or []) if c.get('name') == 'pts')
        if costs:
            non_zero = [c for c in costs if (c.get('value') or 0) > 0]
            chosen = non_zero[0] if non_zero else costs[0]
            unit_data['points']['base'] = int(chosen.get('value') or 0)

        # Point modifiers (variable squad sizes), searched recursively like the XML '//' did.
        # The condition that carries the model-count threshold is field == 'selections'; its
        # childId is sometimes the literal string 'model' (e.g. Orks) and sometimes a GUID
        # referencing the specific model selectionEntry (e.g. Space Marines) - only the
        # 'selections' field is consistent across factions, so match on that.
        for entry, _ in _walk_entries(unit):
            for modifier in entry.get('modifiers') or []:
                if modifier.get('field') != POINTS_FIELD_ID or modifier.get('type') != 'set':
                    continue
                for condition in modifier.get('conditions') or []:
                    if condition.get('field') == 'selections' and condition.get('value') is not None:
                        unit_data['points']['variants'].append({
                            'models': int(condition['value']),
                            'points': int(modifier.get('value') or 0)
                        })

        unit_data['points']['variants'].sort(key=lambda x: x['models'])

        # Squad size constraints
        for entry, _ in _walk_entries(unit):
            for constraint in entry.get('constraints') or []:
                if constraint.get('field') != 'selections':
                    continue
                value = constraint.get('value')
                if value is None:
                    continue
                if constraint.get('type') == 'min':
                    unit_data['composition']['min_models'] = int(value)
                elif constraint.get('type') == 'max':
                    unit_data['composition']['max_models'] = int(value)

        # Unit stats (and inline invuln save via 'InSv' characteristic, new in 11e)
        for entry, _ in _walk_entries(unit):
            for profile in entry.get('profiles') or []:
                if profile.get('typeName') != 'Unit':
                    continue
                for char in profile.get('characteristics') or []:
                    stat_name = char.get('name')
                    stat_value = char.get('$text')
                    if stat_name == 'Sv':
                        stat_name = 'SV'  # 11e uses 'Sv', 10e/the Stats model use 'SV'
                    if stat_name == 'InSv':
                        if stat_value:
                            unit_data['invuln_save'] = stat_value
                    else:
                        unit_data['stats'][stat_name] = stat_value

        # Transport capacity
        for entry, _ in _walk_entries(unit):
            for profile in entry.get('profiles') or []:
                if profile.get('typeName') != 'Transport':
                    continue
                capacity = _char_text(profile.get('characteristics'), 'Capacity')
                if capacity:
                    unit_data['transport'] = clean_text(capacity)

        # Invuln save fallback, Method 1: infoLinks, searched recursively like the XML '//'
        # did (ported from XML parser)
        if not unit_data['invuln_save']:
            done = False
            for entry, _ in _walk_entries(unit):
                if done:
                    break
                for info_link in entry.get('infoLinks') or []:
                    link_name = info_link.get('name', '')
                    if 'Invulnerable' not in link_name:
                        continue
                    target_id = info_link.get('targetId')
                    target_profile = None
                    if target_id:
                        target_profile = _find_profile_by_id(root, target_id)
                        if not target_profile and parent_root is not None:
                            target_profile = _find_profile_by_id(parent_root, target_id)
                    if target_profile:
                        description = _char_text(target_profile.get('characteristics'), 'Description')
                        if description:
                            match = re.search(r'(\d\+)', description)
                            unit_data['invuln_save'] = match.group(1) if match else link_name
                        else:
                            unit_data['invuln_save'] = link_name
                    else:
                        unit_data['invuln_save'] = link_name
                    done = True
                    break

        # Invuln save fallback, Method 2: ability profiles, skipping optional wargear (ported from XML parser)
        if not unit_data['invuln_save']:
            done = False
            for entry, is_upgrade in _walk_entries(unit):
                if done:
                    break
                for profile in entry.get('profiles') or []:
                    if profile.get('typeName') != 'Abilities':
                        continue
                    ability_name = profile.get('name', '')
                    description = _char_text(profile.get('characteristics'), 'Description')
                    if 'invulnerable save' in ability_name.lower() or \
                       (description and 'invulnerable save' in description.lower()):
                        if is_upgrade:
                            continue
                        if description:
                            match = re.search(r'(\d\+)', description)
                            unit_data['invuln_save'] = match.group(1) if match else "Invulnerable Save"
                        else:
                            unit_data['invuln_save'] = "Invulnerable Save"
                        done = True
                        break

        # Special rules with modifiers, searched recursively like the XML '//' did
        processed_rules = set()
        for entry, _ in _walk_entries(unit):
            for info_link in entry.get('infoLinks') or []:
                if info_link.get('type') != 'rule':
                    continue
                rule_name = info_link.get('name', '')
                if not rule_name or 'Invulnerable' in rule_name:
                    continue

                modifier_value = None
                for modifier in info_link.get('modifiers') or []:
                    if modifier.get('type') == 'append' and modifier.get('field') == 'name':
                        modifier_value = modifier.get('value', '')
                        break

                full_rule = f"{rule_name} {modifier_value}".strip() if modifier_value else rule_name
                if full_rule not in processed_rules:
                    unit_data['special_rules'].append(full_rule)
                    processed_rules.add(full_rule)

        # Ranged/melee weapons, including from nested entries and entryLinks
        seen_ranged, seen_melee = set(), set()

        def add_weapon_profile(profile, type_name):
            weapon_data = {'name': profile.get('name')}
            for char in profile.get('characteristics') or []:
                weapon_data[char.get('name')] = char.get('$text')
            if type_name == 'Ranged Weapons':
                if weapon_data['name'] not in seen_ranged:
                    unit_data['weapons']['ranged'].append(weapon_data)
                    seen_ranged.add(weapon_data['name'])
            else:
                if weapon_data['name'] not in seen_melee:
                    unit_data['weapons']['melee'].append(weapon_data)
                    seen_melee.add(weapon_data['name'])

        for entry, _ in _walk_entries(unit):
            for profile in entry.get('profiles') or []:
                type_name = profile.get('typeName')
                if type_name in ('Ranged Weapons', 'Melee Weapons'):
                    add_weapon_profile(profile, type_name)

            for entry_link in entry.get('entryLinks') or []:
                if entry_link.get('type') != 'selectionEntry':
                    continue
                target_id = entry_link.get('targetId')
                if not target_id:
                    continue
                weapon_entry = _find_upgrade_entry_by_id(root, target_id)
                if not weapon_entry and parent_root is not None:
                    weapon_entry = _find_upgrade_entry_by_id(parent_root, target_id)
                if not weapon_entry:
                    continue
                for sub_entry, _ in _walk_entries(weapon_entry):
                    for profile in sub_entry.get('profiles') or []:
                        type_name = profile.get('typeName')
                        if type_name in ('Ranged Weapons', 'Melee Weapons'):
                            add_weapon_profile(profile, type_name)

        # Abilities (typeName may be faction-flavored, e.g. 'Triarch Abilities')
        for entry, _ in _walk_entries(unit):
            for profile in entry.get('profiles') or []:
                type_name = profile.get('typeName') or ''
                if not type_name.endswith('Abilities'):
                    continue
                description = _char_text(profile.get('characteristics'), 'Description')
                unit_data['abilities'].append({
                    'name': profile.get('name'),
                    'description': clean_text(description) if description else None
                })

        # Keywords (direct categoryLinks only)
        seen_kw = set()
        for category in unit.get('categoryLinks') or []:
            keyword = category.get('name')
            if keyword and keyword not in seen_kw:
                seen_kw.add(keyword)
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
        faction = parts[-1].strip()
        if faction == 'Library':
            faction = parts[-2].strip()
        faction = re.sub(r'\s+Library$', '', faction)
        return faction
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
        'Tyranids': 'Xenos_-_Tyranids',  # 11e: Tyranids.json itself holds the roster (unlike 10e's Library file)
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
    # Format: (filepath, faction_type, optional_parent_catalogue)
    space_marines_parent = 'data/BSData-10e/Imperium - Space Marines.cat'

    catalogue_files = [
        # Imperium
        ('data/BSData-10e/Imperium - Adepta Sororitas.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Adeptus Custodes.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Adeptus Mechanicus.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Agents of the Imperium.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Astra Militarum - Library.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Black Templars.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Blood Angels.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Dark Angels.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Deathwatch.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Grey Knights.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Imperial Fists.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Imperial Knights - Library.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Iron Hands.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Raven Guard.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Salamanders.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Space Marines.cat', 'Imperium', None),
        ('data/BSData-10e/Imperium - Space Wolves.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - Ultramarines.cat', 'Imperium', space_marines_parent),
        ('data/BSData-10e/Imperium - White Scars.cat', 'Imperium', space_marines_parent),
        # Chaos
        ('data/BSData-10e/Chaos - Chaos Daemons Library.cat', 'Chaos', None),
        ('data/BSData-10e/Chaos - Chaos Knights Library.cat', 'Chaos', None),
        ('data/BSData-10e/Chaos - Chaos Space Marines.cat', 'Chaos', None),
        ('data/BSData-10e/Chaos - Death Guard.cat', 'Chaos', None),
        ('data/BSData-10e/Chaos - Emperor\'s Children.cat', 'Chaos', None),
        ('data/BSData-10e/Chaos - Thousand Sons.cat', 'Chaos', None),
        ('data/BSData-10e/Chaos - World Eaters.cat', 'Chaos', None),
        # Xenos
        ('data/BSData-10e/Aeldari - Aeldari Library.cat', 'Xenos', None),  # Library has the units
        # Skip: 'data/BSData-10e/Aeldari - Craftworlds.cat',  # Just references Library
        # Skip: 'data/BSData-10e/Aeldari - Drukhari.cat',  # Just references Library
        # Skip: 'data/BSData-10e/Aeldari - Ynnari.cat',  # Just references Library
        ('data/BSData-10e/Genestealer Cults.cat', 'Xenos', None),
        ('data/BSData-10e/Leagues of Votann.cat', 'Xenos', None),
        ('data/BSData-10e/Library - Tyranids.cat', 'Xenos', None),  # Library has the units
        # Skip: 'data/BSData-10e/Tyranids.cat',  # Just references Library
        ('data/BSData-10e/Necrons.cat', 'Xenos', None),
        ('data/BSData-10e/Orks.cat', 'Xenos', None),
        ('data/BSData-10e/T\'au Empire.cat', 'Xenos', None),
        # Unaligned
        ('data/BSData-10e/Library - Titans.cat', 'Unaligned', None),
        ('data/BSData-10e/Unaligned Forces.cat', 'Unaligned', None)
    ]

    # 11e catalogues are shipped as JSON by BSData/wh40k-11e, not XML .cat files.
    # For each faction, prefer whichever file actually holds the sharedSelectionEntries
    # (verified per-file; unlike 10e, 11e's plain "Tyranids.json" holds the roster while
    # "Library - Tyranids.json" doesn't - the reverse of the other Library/wrapper pairs).
    space_marines_parent_11e = 'data/BSData-11e/Imperium - Space Marines.json'

    catalogue_files_11e = [
        # Imperium
        ('data/BSData-11e/Imperium - Adepta Sororitas.json', 'Imperium', None),
        ('data/BSData-11e/Imperium - Adeptus Custodes.json', 'Imperium', None),
        ('data/BSData-11e/Imperium - Adeptus Mechanicus.json', 'Imperium', None),
        ('data/BSData-11e/Imperium - Agents of the Imperium.json', 'Imperium', None),
        ('data/BSData-11e/Imperium - Astra Militarum - Library.json', 'Imperium', None),
        # Skip: 'Imperium - Astra Militarum.json'  # Just references Library
        ('data/BSData-11e/Imperium - Black Templars.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Blood Angels.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Dark Angels.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Deathwatch.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Grey Knights.json', 'Imperium', None),
        ('data/BSData-11e/Imperium - Imperial Fists.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Imperial Knights - Library.json', 'Imperium', None),
        # Skip: 'Imperium - Imperial Knights.json'  # Just references Library
        ('data/BSData-11e/Imperium - Iron Hands.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Raven Guard.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Salamanders.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Space Marines.json', 'Imperium', None),
        ('data/BSData-11e/Imperium - Space Wolves.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - Ultramarines.json', 'Imperium', space_marines_parent_11e),
        ('data/BSData-11e/Imperium - White Scars.json', 'Imperium', space_marines_parent_11e),
        # Skip: 'Imperium - Adeptus Titanicus.json'  # Just references Library - Titans
        # Chaos
        ('data/BSData-11e/Chaos - Chaos Daemons Library.json', 'Chaos', None),
        # Skip: 'Chaos - Chaos Daemons.json'  # Just references Library
        ('data/BSData-11e/Chaos - Chaos Knights Library.json', 'Chaos', None),
        # Skip: 'Chaos - Chaos Knights.json'  # Just references Library
        ('data/BSData-11e/Chaos - Chaos Space Marines.json', 'Chaos', None),
        ('data/BSData-11e/Chaos - Death Guard.json', 'Chaos', None),
        ('data/BSData-11e/Chaos - Emperor\'s Children.json', 'Chaos', None),
        ('data/BSData-11e/Chaos - Thousand Sons.json', 'Chaos', None),
        ('data/BSData-11e/Chaos - World Eaters.json', 'Chaos', None),
        # Skip: 'Chaos - Titanicus Traitoris.json'  # Just references Library - Titans
        # Xenos
        ('data/BSData-11e/Aeldari - Aeldari Library.json', 'Xenos', None),  # Library has the units
        # Skip: 'Aeldari - Craftworlds.json'  # Just references Library
        # Skip: 'Aeldari - Drukhari.json'  # Just references Library
        ('data/BSData-11e/Genestealer Cults.json', 'Xenos', None),
        ('data/BSData-11e/Leagues of Votann.json', 'Xenos', None),
        ('data/BSData-11e/Tyranids.json', 'Xenos', None),  # Unlike 10e: this file has the units, not the Library
        # Skip: 'Library - Tyranids.json'  # Doesn't hold the full roster in 11e
        ('data/BSData-11e/Necrons.json', 'Xenos', None),
        ('data/BSData-11e/Orks.json', 'Xenos', None),
        ('data/BSData-11e/T\'au Empire.json', 'Xenos', None),
        # Unaligned
        ('data/BSData-11e/Library - Titans.json', 'Unaligned', None),
        ('data/BSData-11e/Unaligned Forces.json', 'Unaligned', None)
        # Skip: 'Library - Astartes Heresy Legends.json', 'Warhammer 40,000.json'  # Not per-faction rosters
    ]

    # Create output directories
    Path('data/json/10e').mkdir(parents=True, exist_ok=True)
    Path('data/json/11e').mkdir(parents=True, exist_ok=True)

    # Process each catalogue file: (parser function, file list, output dir)
    editions = [
        (parse_catalogue, catalogue_files, 'data/json/10e'),
        (parse_catalogue_json, catalogue_files_11e, 'data/json/11e'),
    ]

    for parse_fn, file_list, output_dir in editions:
        for catalogue_file, faction_type, parent_catalogue in file_list:
            print(f"Processing: {catalogue_file}")

            units = parse_fn(catalogue_file, faction_type, parent_catalogue)

            output_filename = get_output_filename(catalogue_file)
            output_path = f'{output_dir}/{output_filename}'

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(units, f, indent=2, ensure_ascii=False)

            print(f"  → Saved {len(units)} units to {output_path}")

            if units:
                print("\nExample unit:")
                print(json.dumps(units[0], indent=2))

    print("\nDone!")

if __name__ == '__main__':
    main()