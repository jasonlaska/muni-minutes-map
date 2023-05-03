import duckdb
import uuid
from datetime import datetime


DB_FILEPATH = "property_activity.db"


Q_GET = """SELECT id
FROM {table}
WHERE {filters}
"""


def _fmt_row(row):
    return ",".join(
        [f"'{uuid.uuid4()}'::UUID", f"'{datetime.now()}'"]
        + [f"'{c}'" if isinstance(c, str) and c != "NULL" else str(c) for c in row]
    )


class DBWriter(object):
    def __init__(self, db_filepath=DB_FILEPATH):
        self._con = duckdb.connect(db_filepath)

    def _get_or_create(self, table, filtrows, row):
        filters = " AND ".join([f"{k}='{v}'" for k, v in filtrows.items()])
        record_id = self._con.sql(Q_GET.format(table=table, filters=filters)).fetchone()
        if not record_id:
            self._con.sql(f"INSERT INTO {table} VALUES ({_fmt_row(row)})")
            record_id = self._con.sql(
                Q_GET.format(table=table, filters=filters)
            ).fetchone()

        return record_id[0]

    def insert(self, source, parsed_street):
        # Source
        row = [
            source["doctype"],
            source["url"],
            source["date"],
            source["filepath"],
            source["municipal"],
            source["city"],
            source["state"],
        ]
        filtrows = {
            "url": source["url"],
            "local_path": source["filepath"],
        }
        source_id = self._get_or_create("source", filtrows, row)

        # Address
        row = [
            parsed_street.street.replace("'", ""),
            parsed_street.coords.lat if parsed_street.coords else "NULL",
            parsed_street.coords.lon if parsed_street.coords else "NULL",
            [a.replace("'", "") for a in parsed_street.addresses.aliases],
            source["city"],
            source["state"],
        ]
        filtrows = {
            "street": parsed_street.street.replace("'", ""),
            "city": source["city"],
        }
        address_id = self._get_or_create("address", filtrows, row)

        # Association
        row = [
            str(source_id),
            str(address_id),
        ]
        filtrows = {
            "source_id": source_id,
            "address_id": address_id,
        }
        association_id = self._get_or_create("source_address_assoc", filtrows, row)

        # Summaries
        summary_ids = []
        for summary in parsed_street.summaries:
            row = [
                str(source_id),
                str(address_id),
                summary.status,
                summary.page,
                summary.summary.replace("'", ""),
                summary.tags,
            ]
            filtrows = {
                "source_id": source_id,
                "address_id": address_id,
                "status": summary.status,
                "page": summary.page,
                "summary": summary.summary.replace("'", ""),
            }
            summary_id = self._get_or_create("summary", filtrows, row)
            summary_ids.append(summary_id)

        return {
            "source_id": source_id,
            "address_id": address_id,
            "association_id": association_id,
            "summary_ids": summary_ids,
        }
