CREATE TABLE source (
    id             UUID PRIMARY KEY,
    created        TIMESTAMP NOT NULL,
    doctype        VARCHAR NOT NULL, -- enum?
    url            VARCHAR NOT NULL,
    record_date    DATE NOT NULL,
    local_path     VARCHAR NOT NULL,
    municipal      VARCHAR NOT NULL,
    city           VARCHAR NOT NULL,
    state          VARCHAR NOT NULL,
);