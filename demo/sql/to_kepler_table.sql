COPY
    (
        SELECT
            a.lat,
            a.lon,
            FORMAT('{}, {}, {}', a.street, a.city, a.state) AS 'address',
            CAST(s.record_date AS datetime) AS record_date,
            s.doctype,
            status,
            summary,
            tags,
            page,
            s.url
        FROM summary
        JOIN address a ON a.id = address_id
        JOIN source s ON s.id = source_id
        WHERE summary.summary <> ''
        AND a.lat is not NULL
        AND a.lon is not NULL
    )
TO 'output.csv' WITH (HEADER 1, DELIMITER ',');