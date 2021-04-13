CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role INTEGER,
    visible INTEGER
);

CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    creator_id INTEGER REFERENCES users,
    created_at TIMESTAMP,
    title TEXT UNIQUE,
    description TEXT,
    instruction TEXT,
    visible INTEGER
);

CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes,
    ingredient TEXT,
    visible INTEGER
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    tag TEXT
);

CREATE TABLE recipetags (
    recipe_id INTEGER REFERENCES recipes,
    tag_id INTEGER REFERENCES tags,
    visible INTEGER
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes,
    sender_id INTEGER REFERENCES users,
    comment TEXT,
    sent_at TIMESTAMP,
    visible INTEGER
);

CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes,
    grade INTEGER,
    visible INTEGER
);