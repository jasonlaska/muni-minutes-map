import os
import openai
import json
from tqdm import tqdm
from dataclasses import dataclass, asdict

from . import get_openai_key
from .base import DocumentProcessor
from ..artifact import Artifact


PROCESSOR_NAME = "summarize"

TAGS = [
    "INSTALLATION",
    "NEW_CONSTRUCTION",
    "AUXILIARY_UNIT",
    "EXTENSION",
    "ADJUSTMENT",
]
SYSTEM_NUDGE = (
    "You are a helpful document parsing tool that only responds in json objects."
)
PROMPT = """For the given property address, identify issue, resolution, and summary of decision.
Return the results as a json object like:

    {{
        "status": "<insert either APPROVED or DENIED or NO_STATUS>",
        "summary": "<insert short 3 sentence summary of the resolution with regard to the property>", or "", if missing
        "tags": ["<insert comma separated list, all that apply: {tags}>"]
    }}

Rules:
1. Think step by step for each result field
2. The result must be in valid json format

property address: {street}

document: {text}
"""
MAX_TOKENS = 1500
TEMPERATURE = 0


@dataclass
class Summary:
    street: str
    page: int
    status: str
    summary: str
    tags: list[str]


class Summarize(DocumentProcessor):
    def __init__(self, source, pages):
        self._source = source
        self._pages = pages
        self._errors = []
        self._summaries = None
        self._artifact = Artifact(source, PROCESSOR_NAME)

        openai.api_key = get_openai_key()

    @property
    def errors(self):
        return self._errors

    @property
    def result(self):
        return self._summary

    @property
    def artifact_exists(self):
        return self._artifact.exists

    def _parse_key_value_response(self, result):
        summary = dict()
        for line in result.split("\n"):
            if ":" not in line:
                self._errors.append("INVALID_KEY_VALUE")
                summary = None
                break

            key, value = line.split(":")
            value = value[1:]  # remove leading space
            if "[" in value:
                try:
                    value = json.loads(value)
                except:
                    self._errors.append("INVALID_TAG_LIST")

            summary[key] = value

        return summary

    def _summarize(self, text, street):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_NUDGE,
                },
                {
                    "role": "user",
                    "content": PROMPT.format(
                        tags=", ".join(TAGS), street=street, text=text
                    ),
                },
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        result = response["choices"][0]["message"]["content"]

        # try to parse summary json
        summary = None
        try:
            summary = json.loads(result)
        except:
            self._errors.append("INVALID_JSON")

        # hack: sometimes json fails, try one other thing
        if not summary:
            summary = self._parse_key_value_response(result)

        return summary

    def _extract_address_all(self, street, detection, n_consecutive_pages=2):
        street_summaries = []

        processed = []
        for pp in sorted(detection.pages):
            if pp in processed:
                continue

            # assemble a text blob of n_consecutive_pages
            text = ""
            for offset in range(n_consecutive_pages - 1):
                text += self._pages[pp + offset].text
                processed.append(pp + offset)

            # summarize
            summary = self._summarize(text, street)
            if summary:
                # street_summaries.append(summary | {"page": pp})
                street_summaries.append(Summary(street, pp, **summary))

        return street_summaries

    def extract(self, addresses):
        # Input:  {street: AddressDetection, ...}
        # Return: {street: [Summary, ...], ...}
        self._summaries = dict()
        for street, detection in tqdm(
            addresses.items(), desc="Summaries by address..."
        ):
            self._summaries[street] = self._extract_address_all(street, detection)

        return self._summaries

    def save(self, overwrite=False):
        # TODO: summaries are in a list
        return self._artifact.write(
            {k: [asdict(s) for s in v] for k, v in self._summaries.items()},
            overwrite=overwrite,
        )

    def load(self):
        self._summaries = {
            k: [Summary(**s) for s in v] for k, v in self._artifact.read().items()
        }
        return self._summaries
