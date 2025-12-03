#!/usr/bin/env python3
"""Fix the dump file to match the schema by removing battle_time and collected_at columns."""

import re

with open('clash_meta_dump.sql', 'r') as f:
    content = f.read()

# Fix the battles INSERT column list
content = content.replace(
    'INSERT INTO battles (battle_id, battle_time, battle_type, game_mode, arena_name, is_ladder, collected_at)',
    'INSERT INTO battles (battle_id, battle_type, game_mode, arena_name, is_ladder)'
)

# Fix the battles VALUES by removing 2nd and 7th values from each row
# Pattern: ('value1', 'value2', 'value3', 'value4', 'value5', value6, 'value7')
# We want to keep: value1, value3, value4, value5, value6

def fix_battle_row(match):
    """Remove 2nd and 7th values from a battles row."""
    full_match = match.group(0)
    # Match pattern: ('id', 'time', 'type', 'mode', 'arena', bool, 'collected')
    # We want to remove 'time' and 'collected'
    pattern = r"\('([^']+)', '[^']+', '([^']+)', '([^']+)', '([^']+)', (\d), '[^']+'\)"
    result = re.sub(pattern, r"('\1', '\2', '\3', '\4', \5)", full_match)
    return result

# Find all battles INSERT VALUES section
battles_pattern = r"INSERT INTO battles.*?VALUES\n(.*?);"
battles_match = re.search(battles_pattern, content, re.DOTALL)

if battles_match:
    values_section = battles_match.group(1)
    # Fix each row in the VALUES section
    fixed_values = re.sub(r"\('[^']+', '[^']+', '[^']+', '[^']+', '[^']+', \d, '[^']+'\)", fix_battle_row, values_section)
    content = content.replace(values_section, fixed_values)

with open('clash_meta_dump_fixed.sql', 'w') as f:
    f.write(content)

print("Fixed dump written to clash_meta_dump_fixed.sql")
