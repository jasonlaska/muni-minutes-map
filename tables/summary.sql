CREATE TABLE summary (
    id             UUID PRIMARY KEY,
    created        TIMESTAMP NOT NULL,
    source_id      UUID NOT NULL,
    address_id     UUID NOT NULL,
    status         VARCHAR,
    page           VARCHAR,
    summary        VARCHAR,
    tags           VARCHAR[],
    FOREIGN KEY (source_id) REFERENCES source (id),
    FOREIGN KEY (address_id) REFERENCES address (id)
);