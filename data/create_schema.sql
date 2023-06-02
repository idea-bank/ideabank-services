DROP TABLE IF EXISTS "concept_links";
DROP TABLE IF EXISTS "concepts";
DROP TABLE IF EXISTS "accounts";

CREATE TABLE accounts (
    display_name VARCHAR(64) PRIMARY KEY,
    preferred_name VARCHAR(255),
    biography TEXT,
    password_hash CHAR(64),
    salt_value CHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE concepts (
    title VARCHAR(128),
    author VARCHAR(64) DEFAULT '[Anonymous]',
    description TEXT,
    diagram JSON,
    identifier VARCHAR(255) GENERATED ALWAYS AS (author || '/' || title) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (identifier),
    PRIMARY KEY (author, title),
    CONSTRAINT fk_concept_author FOREIGN KEY (author) REFERENCES accounts(display_name)
        ON UPDATE CASCADE
        ON DELETE SET DEFAULT
);

CREATE TABLE concept_links (
    ancestor VARCHAR(255),
    descendant VARCHAR(255),
    PRIMARY KEY (ancestor, descendant),
    CONSTRAINT fk_ancestor_identifier FOREIGN KEY (ancestor) REFERENCES concepts(identifier)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_descendant_identifier FOREIGN KEY (descendant) REFERENCES concepts(identifier)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

COPY Accounts(display_name, preferred_name, biography, password_hash, salt_value, created_at, updated_at)
FROM '/docker-entrypoint-initdb.d/test_accounts.csv'
DELIMITER '|';

COPY Concepts(author, title, description, diagram, created_at, updated_at)
FROM '/docker-entrypoint-initdb.d/test_concepts.csv'
DELIMITER '|';

COPY Concept_Links(ancestor, descendant)
FROM '/docker-entrypoint-initdb.d/test_links.csv'
DELIMITER '|';
