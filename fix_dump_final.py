#!/usr/bin/env python3
"""Fix the dump file to remove battle_time and collected_at columns from battles table."""

with open('clash_meta_dump.sql', 'r') as f:
    lines = f.readlines()

output = []
in_battles_insert = False

for i, line in enumerate(lines):
    # Fix the column list for battles INSERT
    if 'INSERT INTO battles (battle_id, battle_time' in line:
        line = line.replace(
            'INSERT INTO battles (battle_id, battle_time, battle_type, game_mode, arena_name, is_ladder, collected_at)',
            'INSERT INTO battles (battle_id, battle_type, game_mode, arena_name, is_ladder)'
        )
        in_battles_insert = True
        output.append(line)
        continue

    # Process battles VALUES rows
    if in_battles_insert and not line.strip().startswith('--') and line.strip():
        if line.strip() == ';':
            in_battles_insert = False
            output.append(line)
            continue

        # Parse each value carefully
        # Format: ('id', 'datetime', 'type', 'mode', 'arena', 0/1, 'datetime'),
        # Keep: id (0), type (2), mode (3), arena (4), is_ladder (5)

        original = line.rstrip()
        ends_with_semicolon = original.rstrip().endswith(';')

        # Remove trailing comma or semicolon
        working = original.rstrip(',;\n')

        # Remove opening parenthesis
        if working.startswith('('):
            working = working[1:]
        if working.endswith(')'):
            working = working[:-1]

        # Split by comma, but be careful with quotes
        values = []
        current = []
        in_quote = False
        escape_next = False

        for j, char in enumerate(working):
            if escape_next:
                current.append(char)
                escape_next = False
                continue

            if char == "'" and j + 1 < len(working) and working[j + 1] == "'":
                # This is an escaped quote ''
                current.append("''")
                escape_next = True
                continue

            if char == "'":
                in_quote = not in_quote
                current.append(char)
            elif char == ',' and not in_quote:
                values.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            values.append(''.join(current).strip())

        # Keep only indices 0, 2, 3, 4, 5
        if len(values) >= 7:
            kept_values = [values[0], values[2], values[3], values[4], values[5]]
            new_line = '(' + ', '.join(kept_values) + ')'

            if ends_with_semicolon:
                new_line += ';'
            else:
                new_line += ','

            output.append(new_line + '\n')
        else:
            # Keep original if parsing failed
            output.append(line)
        continue

    output.append(line)

with open('clash_meta_dump_fixed.sql', 'w') as f:
    f.writelines(output)

print("Fixed dump written to clash_meta_dump_fixed.sql")
