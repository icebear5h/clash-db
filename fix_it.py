#!/usr/bin/env python3
import re

with open('clash_meta_dump.sql', 'r') as f:
    content = f.read()

# Fix column list
content = content.replace(
    'INSERT INTO battles (battle_id, battle_time, battle_type, game_mode, arena_name, is_ladder, collected_at)',
    'INSERT INTO battles (battle_id, battle_type, game_mode, arena_name, is_ladder)'
)

# Fix each row - remove 2nd and 7th value
# Pattern matches: ('val1', 'val2', 'val3', 'val4', 'val5', num, 'val7')
# We want: ('val1', 'val3', 'val4', 'val5', num)

def fix_row(match):
    id_val = match.group(1)
    type_val = match.group(2)
    mode_val = match.group(3)
    arena_val = match.group(4)
    ladder_val = match.group(5)
    ending = match.group(6)

    return f"('{id_val}', '{type_val}', '{mode_val}', '{arena_val}', {ladder_val}){ending}"

# This regex carefully handles the escaped quotes in arena names
pattern = r"\('([^']+)', '[^']+', '([^']+)', '([^']+)', '((?:[^']|'')+)', (\d), '[^']+'\)(,|;)"
content = re.sub(pattern, fix_row, content)

with open('clash_meta_dump_fixed.sql', 'w') as f:
    f.write(content)

print("Done")
