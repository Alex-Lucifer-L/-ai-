# Database

This directory stores SQL database assets for the policy AI system.

Current target database: MySQL 8.x.

## Directory Structure

- `schema/`: Base table definitions and database objects.
- `migrations/`: Versioned database change scripts.
- `seeds/`: Initial or sample data scripts.
- `views/`: SQL view definitions.
- `procedures/`: Stored procedures, functions, and triggers.
- `backups/`: Local database dump files. Keep large or sensitive dumps out of Git.
- `docs/`: Database design notes, ER diagrams, and data dictionaries.

## Naming Convention

- Migration files: `YYYYMMDDHHMM_description.sql`
- Schema files: `table_name.sql`
- Seed files: `seed_description.sql`

## Current Scripts

- `migrations/202605211200_initial_schema.sql`: creates the initial database schema.
- `seeds/202605211210_seed_basic_reference_data.sql`: inserts policy categories and the Xiamen region hierarchy.
- `docs/data_dictionary.md`: explains table/entity mapping and core relationships.

## Quick Start

Create a database first, then run:

```bash
mysql -u <user> -p <database_name> < database/migrations/202605211200_initial_schema.sql
mysql -u <user> -p <database_name> < database/seeds/202605211210_seed_basic_reference_data.sql
```
