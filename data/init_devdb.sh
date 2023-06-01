#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    COPY Accounts(display_name, preferred_name, biography, password_hash, salt_value, created_at, updated_at)
    FROM '/docker-entrypoint-initdb.d/test_accounts.csv'
    DELIMITER '|';

    COPY Concepts(author, title, description, diagram, created_at, updated_at)
    FROM '/docker-entrypoint-initdb.d/test_concepts.csv'
    DELIMITER '|';

    COPY Concept_Links(ancestor, descendant)
    FROM '/docker-entrypoint-initdb.d/test_links.csv'
    DELIMITER '|';
EOSQL
