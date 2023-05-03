import pytesseract
from tqdm import tqdm
from pdf2image import convert_from_path
from dataclasses import dataclass, asdict

from .base import DocumentProcessor
from ..artifact import Artifact

POPPLER_PATH = "/usr/local/Cellar/poppler/23.01.0/bin"
PROCESSOR_NAME = "pdf2text"


@dataclass
class TextPage:
    page: int
    text: str
    headers: list[str]
    table: list
    source: dict


def _parse_tesseract_verbose(data):
    # Parse pytesseract.image_to_data output into table
    rows = data.split("\n")
    headers = rows[0].split("\t")
    table = []
    for row in rows[1:]:
        values = row.split("\t")
        if values[-1] != "":
            table.append(values)

    return headers, table


class PDF2Text(DocumentProcessor):
    def __init__(self, source, poppler_path=POPPLER_PATH):
        self._source = source
        self._poppler_path = poppler_path
        self._errors = []
        self._pages = None
        self._artifact = Artifact(source, PROCESSOR_NAME)

    @property
    def errors(self):
        return self._errors

    @property
    def result(self):
        return self._pages

    @property
    def artifact_exists(self):
        return self._artifact.exists

    def extract(self):
        # Returns: [TextPage, ...]
        self._pages = []
        images = convert_from_path(
            self._source["filepath"], poppler_path=self._poppler_path
        )
        for pp, image in enumerate(tqdm(images, desc=f"OCR {len(images)} images...")):
            text = pytesseract.image_to_string(image)
            headers, table = _parse_tesseract_verbose(pytesseract.image_to_data(image))
            self._pages.append(TextPage(pp, text, headers, table, self._source))

        return self._pages

    def save(self, overwrite=False):
        return self._artifact.write(
            [asdict(p) for p in self._pages], overwrite=overwrite
        )

    def load(self):
        self._pages = [TextPage(**p) for p in self._artifact.read()]
        return self._pages
