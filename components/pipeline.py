import pprint
from dataclasses import dataclass

from components.processors.pdf2text import PDF2Text, TextPage
from components.processors.address import Address, AddressDetection
from components.processors.summarize import Summarize, Summary
from components.processors.geocode import Geocode, Coord
from components.dbwriter import DBWriter


PIPELINE_CONFIG = [
    {
        "processor": PDF2Text,
        "args": ["source"],
        "extract_args": [],
        "output": "pages",
        "load_from_cache": True,
    },
    {
        "processor": Address,
        "args": ["source"],
        "extract_args": ["pages"],
        "output": "addresses",
        "load_from_cache": True,
    },
    {
        "processor": Summarize,
        "args": ["source", "pages"],
        "extract_args": ["addresses"],
        "output": "summaries",
        "load_from_cache": True,
    },
    {
        "processor": Geocode,
        "args": ["source"],
        "extract_args": ["summaries"],
        "output": "coords",
        "load_from_cache": True,
    },
]


@dataclass
class ParsedStreet:
    street: str
    addresses: AddressDetection
    summaries: list[Summary]
    coords: Coord


@dataclass
class PipelineResult:
    source: dict
    pages: list[TextPage]
    parsed: list[ParsedStreet]


@dataclass
class PipelineStageResults:
    source: dict
    pages: list[TextPage]
    addresses: dict[AddressDetection]  # key is street
    summaries: dict[list[Summary]]  # key is "street"
    coords: dict[Coord]  # key is "street"


def pipeline(source, config=PIPELINE_CONFIG, verbose=False):
    result = PipelineStageResults(source, [], [], {}, {})
    for stage in config:
        args = tuple(
            getattr(result, k) if k in dir(result) else k for k in stage["args"]
        )
        extract_args = tuple(
            getattr(result, k) if k in dir(result) else k for k in stage["extract_args"]
        )
        processor = stage["processor"](*args)
        if processor.artifact_exists and stage["load_from_cache"]:
            setattr(result, stage["output"], processor.load())
        else:
            setattr(result, stage["output"], processor.extract(*extract_args))
            processor.save(overwrite=True)

        if not isinstance(processor, PDF2Text) and verbose:
            pprint.pprint(getattr(result, stage["output"]))

    return result


def reshape_to_pipeline_result(stage_results):
    result = PipelineResult(stage_results.source, stage_results.pages, [])
    for street in stage_results.summaries:
        result.parsed.append(
            ParsedStreet(
                street,
                stage_results.addresses[street],
                stage_results.summaries[street],
                stage_results.coords[street]
                if street in stage_results.coords
                else None,
            )
        )

    return result


def print_pipeline_results(result):
    print(f"filepath: {result.source['filepath']}")
    # print(f"pages: {result.pages}")
    for parsed in result.parsed:
        print(f"** street: {parsed.street} **")
        print(parsed.coords)
        print(parsed.addresses)
        pprint.pprint(parsed.summaries)

        print("\n\n")


def persist(source, result):
    ids = []
    writer = DBWriter()
    for parsed in result.parsed:
        ids.append(writer.insert(result.source, parsed))

    return ids
