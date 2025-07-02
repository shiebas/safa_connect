#!/bin/bash

# Script to manually remove the 'level' column from the accounts_position table

echo "Creating a backup of the accounts_position table..."
python manage.py dbshell << EOF
.headers on
.mode insert
.output accounts_position_backup.sql
SELECT * FROM accounts_position;
.output stdout
EOF

echo "Creating temporary table without the 'level' column..."
python manage.py dbshell << EOF
-- Create new table without the 'level' column
CREATE TABLE accounts_position_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title VARCHAR(100) UNIQUE,
  description TEXT,
  employment_type VARCHAR(20),
  is_active BOOLEAN,
  created_by_id INTEGER,
  requires_approval BOOLEAN,
  created_at DATETIME,
  levels VARCHAR(100) DEFAULT 'NATIONAL,PROVINCE,REGION,LFA,CLUB',
  FOREIGN KEY (created_by_id) REFERENCES accounts_customuser(id)
);

-- Copy data from old table to new table
INSERT INTO accounts_position_new 
(id, title, description, employment_type, is_active, created_by_id, requires_approval, created_at, levels)
SELECT id, title, description, employment_type, is_active, created_by_id, requires_approval, created_at, levels
FROM accounts_position;

-- Drop old table
DROP TABLE accounts_position;

-- Rename new table
ALTER TABLE accounts_position_new RENAME TO accounts_position;

-- Verify table structure
PRAGMA table_info(accounts_position);
EOF

echo "Done! The 'level' column has been removed from the accounts_position table."
