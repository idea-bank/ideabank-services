DROP TABLE IF EXISTS "likes";
DROP TABLE IF EXISTS "follows";
DROP TABLE IF EXISTS "concept_links";
DROP TABLE IF EXISTS "commets";
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

CREATE TABLE follows (
	follower VARCHAR(64) NOT NULL,
	followee VARCHAR(64) NOT NULL,
	PRIMARY KEY (follower, followee),
	FOREIGN KEY(follower) REFERENCES accounts (display_name) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(followee) REFERENCES accounts (display_name) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE likes (
	display_name VARCHAR(64) NOT NULL,
	concept_id VARCHAR,
	PRIMARY KEY (display_name),
	FOREIGN KEY(display_name) REFERENCES accounts (display_name) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(concept_id) REFERENCES concepts (identifier) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE comments (
	comment_id INTEGER NOT NULL,
	comment_on VARCHAR,
	comment_by VARCHAR(64) DEFAULT '[Anonymous]',
	free_text VARCHAR,
	parent INTEGER,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (comment_id),
	FOREIGN KEY(comment_on) REFERENCES concepts (identifier) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(comment_by) REFERENCES accounts (display_name) ON DELETE SET DEFAULT ON UPDATE CASCADE,
	FOREIGN KEY(parent) REFERENCES comments (comment_id)
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
