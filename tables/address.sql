CREATE TABLE address (
    id             UUID PRIMARY KEY,
    created        TIMESTAMP NOT NULL,
    street         VARCHAR NOT NULL,
    lat            DOUBLE,
    lon            DOUBLE,
    aliases        VARCHAR[],
    city           VARCHAR NOT NULL,
    state          VARCHAR NOT NULL,
);