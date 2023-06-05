DROP TABLE IF EXISTS "likes";
DROP TABLE IF EXISTS "follows";
DROP TABLE IF EXISTS "concept_links";
DROP TABLE IF EXISTS "commets";
DROP TABLE IF EXISTS "concepts";
DROP TABLE IF EXISTS "accounts";

CREATE TABLE accounts (
	display_name VARCHAR(64) NOT NULL,
	preferred_name VARCHAR(255),
	biography VARCHAR,
	password_hash VARCHAR(64),
	salt_value VARCHAR(64),
	created_at TIMESTAMP WITHOUT TIME ZONE,
	updated_at TIMESTAMP WITHOUT TIME ZONE,
	PRIMARY KEY (display_name)
);



CREATE TABLE concepts (
	title VARCHAR(128) NOT NULL,
	author VARCHAR(64) NOT NULL,
	description VARCHAR,
	diagram JSON,
	created_at TIMESTAMP WITHOUT TIME ZONE,
	updated_at TIMESTAMP WITHOUT TIME ZONE,
	identifier VARCHAR GENERATED ALWAYS AS (author || '/' || title) STORED,
	PRIMARY KEY (title, author),
	FOREIGN KEY(author) REFERENCES accounts (display_name) ON DELETE SET DEFAULT ON UPDATE CASCADE,
	UNIQUE (identifier)
);



CREATE TABLE follows (
	follower VARCHAR(64) NOT NULL,
	followee VARCHAR(64) NOT NULL,
	PRIMARY KEY (follower, followee),
	FOREIGN KEY(follower) REFERENCES accounts (display_name) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(followee) REFERENCES accounts (display_name) ON DELETE CASCADE ON UPDATE CASCADE
);



CREATE TABLE concept_links (
	ancestor VARCHAR NOT NULL,
	descendant VARCHAR NOT NULL,
	PRIMARY KEY (ancestor, descendant),
	FOREIGN KEY(ancestor) REFERENCES concepts (identifier) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(descendant) REFERENCES concepts (identifier) ON DELETE CASCADE ON UPDATE CASCADE
);



CREATE TABLE likes (
	display_name VARCHAR(64) NOT NULL,
	concept_id VARCHAR NOT NULL,
	PRIMARY KEY (display_name, concept_id),
	FOREIGN KEY(display_name) REFERENCES accounts (display_name) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(concept_id) REFERENCES concepts (identifier) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE SEQUENCE comment_id_seq START WITH 1;

CREATE TABLE comments (
	comment_id INTEGER NOT NULL,
	comment_on VARCHAR,
	comment_by VARCHAR(64),
	free_text VARCHAR,
	parent INTEGER,
	created_at TIMESTAMP WITHOUT TIME ZONE,
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

COPY Likes(display_name, concept_id)
FROM '/docker-entrypoint-initdb.d/test_likes.csv'
DELIMITER '|';

COPY Follows(follower, followee)
FROM '/docker-entrypoint-initdb.d/test_follows.csv'
DELIMITER '|';
