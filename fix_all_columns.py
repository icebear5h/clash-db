#!/usr/bin/env python3
"""Strip all extra columns from dump to match schema."""

import re

def parse_sql_values(line):
    """Parse SQL VALUES row into individual values, handling quoted strings."""
    values = []
    current = []
    in_quote = False
    i = 0

    # Remove opening ( and trailing ), or );
    line = line.strip()
    if line.startswith('('):
        line = line[1:]
    line = line.rstrip(',;\n')
    if line.endswith(')'):
        line = line[:-1]

    while i < len(line):
        char = line[i]

        if char == "'" and not in_quote:
            in_quote = True
            current.append(char)
        elif char == "'" and in_quote:
            # Check if it's an escaped quote
            if i + 1 < len(line) and line[i + 1] == "'":
                current.append("''")
                i += 1
            else:
                in_quote = False
                current.append(char)
        elif char == ',' and not in_quote:
            values.append(''.join(current).strip())
            current = []
        else:
            current.append(char)

        i += 1

    if current:
        values.append(''.join(current).strip())

    return values

with open('clash_meta_dump.sql', 'r') as f:
    lines = f.readlines()

output = []
current_table = None
table_columns_fixed = False

for line in lines:
    # Track which table we're in - check for specific INSERT patterns
    if 'INSERT INTO battles (battle_id, battle_time' in line:
        current_table = 'battles'
        line = line.replace(
            'INSERT INTO battles (battle_id, battle_time, battle_type, game_mode, arena_name, is_ladder, collected_at)',
            'INSERT INTO battles (battle_id, battle_type, game_mode, arena_name, is_ladder)'
        )
        output.append(line)
        table_columns_fixed = True
        continue

    elif 'INSERT INTO tournaments (tournament_tag, name' in line:
        current_table = 'tournaments'
        line = line.replace(
            'INSERT INTO tournaments (tournament_tag, name, description, status, tournament_type, capacity, max_capacity, level_cap, game_mode_name, created_time, started_time, first_place_prize, collected_at)',
            'INSERT INTO tournaments (tournament_tag, status, tournament_type, capacity, max_capacity, level_cap, game_mode_name, created_time, started_time, first_place_prize)'
        )
        output.append(line)
        table_columns_fixed = True
        continue

    elif 'INSERT INTO players (player_tag, name' in line:
        current_table = 'players'
        line = line.replace(
            'INSERT INTO players (player_tag, name, exp_level, current_trophies, best_trophies, location_id, last_seen)',
            'INSERT INTO players (player_tag)'
        )
        output.append(line)
        table_columns_fixed = True
        continue

    # Reset state if we hit a line that starts a new table or section
    elif line.strip().startswith('INSERT INTO') or line.strip().startswith('DELETE FROM') or line.strip().startswith('--'):
        current_table = None
        table_columns_fixed = False
        output.append(line)
        continue

    # Handle VALUES rows
    if current_table and table_columns_fixed:
        if line.strip() == ';':
            current_table = None
            table_columns_fixed = False
            output.append(line)
            continue

        if not line.strip() or line.strip().startswith('--'):
            output.append(line)
            continue

        # Parse and fix the values
        values = parse_sql_values(line)

        if current_table == 'battles' and len(values) >= 7:
            # Keep: id(0), type(2), mode(3), arena(4), ladder(5)
            new_values = [values[0], values[2], values[3], values[4], values[5]]
        elif current_table == 'tournaments' and len(values) >= 13:
            # Keep: tag(0), status(3), type(4), cap(5), max_cap(6), level(7), mode(8), created(9), started(10), prize(11)
            new_values = [values[0], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11]]
        elif current_table == 'players' and len(values) >= 7:
            # Keep: tag(0)
            new_values = [values[0]]
        else:
            output.append(line)
            continue

        # Rebuild line
        ends_with_semicolon = line.rstrip().endswith(');')
        new_line = '(' + ', '.join(new_values) + ')'
        if ends_with_semicolon:
            new_line += ';'
        else:
            new_line += ','
        output.append(new_line + '\n')
        continue

    output.append(line)

with open('clash_meta_dump_fixed.sql', 'w') as f:
    f.writelines(output)

print("Fixed all tables")
