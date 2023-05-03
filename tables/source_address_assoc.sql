CREATE TABLE source_address_assoc (
    id             UUID PRIMARY KEY,
    created        TIMESTAMP NOT NULL,
    source_id      UUID NOT NULL,
    address_id     UUID NOT NULL,
    FOREIGN KEY (source_id) REFERENCES source (id),
    FOREIGN KEY (address_id) REFERENCES address (id)
);