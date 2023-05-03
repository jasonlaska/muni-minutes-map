import os
import json
from datetime import datetime
import requests


SOURCE_ROOT = "sources"


class Source(object):
    """
    Class for interacting with source artifacts.
    """

    def __init__(self, state_abbrv, city, doctype, year, root=SOURCE_ROOT):
        self.state_abbrv = state_abbrv
        self.city = city
        self.doctype = doctype
        self.year = year
        self._root = root
        self._source_dir = None
        self.setup()

    def setup(self):
        self._source_dir = os.path.join(
            self._root, self.state_abbrv, self.city, self.doctype, self.year
        )
        os.makedirs(self._source_dir, exist_ok=True)

    @property
    def source_dir(self):
        return self._source_dir

    @property
    def source_files(self):
        return [f for f in os.listdir(self._source_dir) if f.endswith("pdf")]

    def write(self, date, url, metadata, overwrite=False):
        source_path = os.path.join(self._source_dir, f"{date}-minutes.pdf")
        metadata_path = os.path.join(self._source_dir, f"{date}-minutes_metadata.json")

        if (
            not overwrite
            and os.path.exists(source_path)
            and os.path.exists(metadata_path)
        ):
            return self

        r = requests.get(url)
        if r.content:
            with open(source_path, "wb") as f:
                f.write(r.content)

            with open(metadata_path, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "metadata": metadata,
                            "timestamp": str(datetime.now()),
                            "source_path": source_path,
                        }
                    )
                )

        return self

    def read_metadata(self, source_name, artifact_data=False):
        date = source_name[:10]
        metadata_path = os.path.join(self._source_dir, f"{date}-minutes_metadata.json")
        with open(metadata_path, "r") as f:
            metadata = json.loads(f.read())

        if not artifact_data:
            return metadata["metadata"]

        return metadata
