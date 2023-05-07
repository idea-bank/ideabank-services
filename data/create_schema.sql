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

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_account_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at();


CREATE OR REPLACE TRIGGER update_concept_updated_at
    BEFORE UPDATE ON concepts
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at();
