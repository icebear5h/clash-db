#!/usr/bin/env python3
"""Fix the dump file to remove battle_time and collected_at columns from battles table."""

import re

with open('clash_meta_dump.sql', 'r') as f:
    lines = f.readlines()

output = []
in_battles = False

for line in lines:
    # Fix the column list
    if 'INSERT INTO battles (battle_id, battle_time' in line:
        line = line.replace(
            'INSERT INTO battles (battle_id, battle_time, battle_type, game_mode, arena_name, is_ladder, collected_at)',
            'INSERT INTO battles (battle_id, battle_type, game_mode, arena_name, is_ladder)'
        )
        in_battles = True
        output.append(line)
        continue

    # Fix the VALUES rows if we're in the battles section
    if in_battles:
        if line.strip() == ';':
            in_battles = False
            output.append(line)
            continue

        # Match pattern: ('id', 'datetime', 'type', 'mode', 'arena', 0/1, 'datetime'),
        # or ending with: ('id', 'datetime', 'type', 'mode', 'arena', 0/1, 'datetime');
        # Keep: id, type, mode, arena, is_ladder

        # Remove 2nd field (battle_time) and 7th field (collected_at)
        pattern = r"\('([^']+)', '[^']+', '([^']+)', '([^']+)', '([^']+)', ([0-1]), '[^']+'\)"
        replacement = r"('\1', '\2', '\3', '\4', \5)"
        line = re.sub(pattern, replacement, line)

    output.append(line)

with open('clash_meta_dump_fixed.sql', 'w') as f:
    f.writelines(output)

print("Fixed dump written to clash_meta_dump_fixed.sql")
