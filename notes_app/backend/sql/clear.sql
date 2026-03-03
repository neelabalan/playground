-- Disable foreign key constraints
PRAGMA foreign_keys = OFF;

-- Begin a transaction
BEGIN TRANSACTION;

-- Drop tables (add your specific table names here)
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

-- Commit the transaction
COMMIT;

-- Re-enable foreign key constraints
PRAGMA foreign_keys = ON;
