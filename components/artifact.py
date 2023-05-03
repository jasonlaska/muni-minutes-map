import os
import json
from datetime import datetime


ARTIFACT_ROOT = "artifacts"


class Artifact(object):
    """
    Class for interacting with json processing artifacts.
    """

    def __init__(self, source, document_processor_name, root=ARTIFACT_ROOT):
        self.source = source
        self.document_processor_name = document_processor_name
        self._root = root
        self._artifact_dir = None
        self._filepath = None
        self.setup()

    def setup(self):
        self._artifact_dir = os.path.join(
            self._root,
            self.source["state_abbrv"],
            self.source["city"],
            self.source["doctype"],
            self.source["year"],
            f"{self.source['date']}-{self.source['id']}-artifacts",
        )
        os.makedirs(self._artifact_dir, exist_ok=True)
        self._filepath = os.path.join(
            self._artifact_dir, f"{self.document_processor_name}.json"
        )

    @property
    def filepath(self):
        return self._filepath

    @property
    def exists(self):
        return os.path.exists(self._filepath)

    def write(self, data, overwrite=False):
        if not overwrite and self.exists:
            return self._filepath

        with open(self._filepath, "w") as f:
            f.write(
                json.dumps(
                    {
                        "data": data,
                        "timestamp": str(datetime.now()),
                        "source": self.source,
                    }
                )
            )

        return self._filepath

    def read(self, metadata=False):
        with open(self._filepath, "r") as f:
            data = json.loads(f.read())

        if not metadata:
            return data["data"]

        return data

    def delete(self):
        os.path.delete(self._filepath)
