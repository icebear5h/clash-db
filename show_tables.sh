#!/bin/bash
# Show database tables with row counts

DB_NAME="clash_royale"

echo "=========================================="
echo "Database: $DB_NAME"
echo "=========================================="
echo ""

mysql -u root -plittlegenius $DB_NAME -e "
SELECT
    TABLE_NAME as 'Table',
    TABLE_ROWS as 'Rows',
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '$DB_NAME'
ORDER BY TABLE_NAME;
" 2>&1 | grep -v "Warning"

echo ""
echo "=========================================="
echo "Table Structure"
echo "=========================================="
mysql -u root -plittlegenius $DB_NAME -e "SHOW TABLES;" 2>&1 | grep -v "Warning"
