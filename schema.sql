CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role INTEGER
);

CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    creator_id INTEGER REFERENCES users,
    title TEXT,
    description TEXT,
    instruction TEXT
);

CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes,
    ingredient TEXT
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    tag TEXT
);

CREATE TABLE recipetags (
    recipe_id INTEGER REFERENCES recipes,
    tag_id INTEGER REFERENCES tags
);

CREATE TABLE commments (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes,
    sender_id INTEGER REFERENCES users,
    comment TEXT
);

CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes,
    grade INTEGER
);