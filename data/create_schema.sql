DROP TABLE IF EXISTS "concept_links";
DROP TABLE IF EXISTS "concepts";
DROP TABLE IF EXISTS "accounts";

CREATE TABLE accounts (
    display_name VARCHAR(64) PRIMARY KEY,
    preferred_name VARCHAR(255),
    biography TEXT,
    account_id CHAR(36) UNIQUE,
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
