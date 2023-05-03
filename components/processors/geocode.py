from geopy.geocoders import Nominatim
from dataclasses import dataclass, asdict

from .base import DocumentProcessor
from ..artifact import Artifact


PROCESSOR_NAME = "geocode"


@dataclass
class Coord:
    street: str
    lat: float
    lon: float


class Geocode(DocumentProcessor):
    def __init__(self, source):
        self._source = source
        self._errors = []
        self._coordinates = None
        self._artifact = Artifact(source, PROCESSOR_NAME)
        self._geolocator = Nominatim(user_agent="app")

    @property
    def errors(self):
        return self._errors

    @property
    def result(self):
        return self._coordinates

    @property
    def artifact_exists(self):
        return self._artifact.exists

    def extract(self, summaries):
        # Input:   {street: [Summary, ...], ...}, but just uses street keys
        # Returns: {street: Coord, ...}
        self._coordinates = dict()
        for street in summaries:
            location = self._geolocator.geocode(
                f"{street} {self._source['city']} {self._source['state']}", timeout=10
            )
            if not location:
                self._errors.append("GEOCODE_FAILED")

            else:
                self._coordinates[street] = Coord(
                    street, location.latitude, location.longitude
                )

        return self._coordinates

    def save(self, overwrite=False):
        return self._artifact.write(
            {k: asdict(v) for k, v in self._coordinates.items()}, overwrite=overwrite
        )

    def load(self):
        self._coordinates = {k: Coord(**v) for k, v in self._artifact.read().items()}
        return self._coordinates
