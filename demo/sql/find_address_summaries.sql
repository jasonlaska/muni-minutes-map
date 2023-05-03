SELECT
    source.record_date,
    summary FROM summary
JOIN address ON address.id = summary.address_id
JOIN source ON summary.source_id = source.id
WHERE
    address.street ilike '%35 main%'
ORDER BY source.record_date;


# change output: ".mode MODE" https://duckdb.org/docs/api/cli.html