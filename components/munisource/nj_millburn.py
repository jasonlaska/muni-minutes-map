import os
import json
from datetime import datetime
from tabulate import tabulate
import time
import contextlib
import urllib.parse
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By

from ..source import Source


DOCUMENTS_INDEX_URL = "https://twp.millburn.nj.us/agendacenter"
DOCUMENTS_ROOT = "https://twp.millburn.nj.us"

METADATA = {
    "city": "Millburn",
    "municipal": "Millburn Township",
    "state": "New Jersey",
    "state_abbrv": "NJ",
}

PAGE_SECTIONS = {
    "TOWNSHIP_COMMITTEE": {
        "section": "Township Committee",
        "keyword": "Township",
    },
    "ENVIRONMENTAL_COMMISSION": {
        "section": "Environmental Commission",
        "keyword": "Environmental",
    },
    "EXPLORE_MILLBURN_SHORTHILLS": {
        "section": "Explore Millburn-Short Hills Board of Trustees",
        "keyword": "Explore",
    },
    "FLOOD_MITIGATION": {
        "section": "Flood Mitigation Advisory Committee",
        "keyword": "Flood",
    },
    "HISTORIC_PRESERVATION": {
        "section": "Historic Preservation",
        "keyword": "Preservation",
    },
    "PEDESTRIAN_SAFETY": {
        "section": "Pedestrian Safety Advisory Board",
        "keyword": "Safety",
    },
    "PLANNING": {
        "section": "Planning Board",
        "keyword": "Planning",
    },
    "ZONING": {
        "section": "Zoning Board",
        "keyword": "Zoning",
    },
}
DOCTYPES = [
    "FLOOD_MITIGATION",
    "HISTORIC_PRESERVATION",
    "PEDESTRIAN_SAFETY",
    "PLANNING",
    "ZONING",
]  # doctypes we actually want to process later
YEARS_TO_PROCESS = [str(y) for y in range(2013, 2024)][::-1]


def get_sources(doctype, year):
    sources = []

    source = Source(
        METADATA["state_abbrv"],
        METADATA["city"],
        doctype,
        year,
    )
    for source_name in source.source_files:
        filepath = os.path.join(source.source_dir, source_name)
        sources.append(
            source.read_metadata(source_name)
            | METADATA
            | {"filepath": filepath, "doctype": doctype}
        )

    return sources


def year_table_to_doctype(label):
    for doctype, hints in PAGE_SECTIONS.items():
        if hints["keyword"].lower() in label.lower():
            return doctype


def year_table_to_year(label):
    for doctype, hints in PAGE_SECTIONS.items():
        if hints["section"].lower() in label.lower():
            return label[len(hints["section"].lower()) + 1 :]


def minutes_label_to_doctype(label):
    for doctype, hints in PAGE_SECTIONS.items():
        if hints["keyword"].lower() in label.lower():
            return doctype


def minutes_docid_to_year(doc_id):
    return doc_id.split("-")[0][-4:]


def minutes_docid_to_date_YYYYMMDD(doc_id):
    d = doc_id.split("-")[0]
    return f"{d[4:]}-{d[:2]}-{d[2:4]}"


@contextlib.contextmanager
def webdriver_session(url, wait_time=10):
    driver = webdriver.Chrome()
    driver.implicitly_wait(wait_time)
    driver.get(url)
    yield driver
    driver.close()


class NJMillburnCrawler(object):
    """
    Build a fresh index of all municipal documents urls.
    """

    def __init__(self, documents_index_url=DOCUMENTS_INDEX_URL):
        self._documents_index_url = documents_index_url
        self._minutes = None
        self._validation = None

        self._crawlfile = None
        self._validationfile = None

    @property
    def minutes(self):
        return self._minutes

    def save(self, overwrite=False):
        source = Source(METADATA["state_abbrv"], METADATA["city"], "crawler", "all")

        timestamp = str(datetime.now())

        self._crawlfile = f"nj-millburn-crawl-{timestamp}.json"
        crawlpath = os.path.join(source.source_dir, self._crawlfile)
        with open(crawlpath, "w") as f:
            f.write(json.dumps(self._minutes))

        self._validationfile = f"nj-millburn-validation-{timestamp}.txt"
        validationpath = os.path.join(source.source_dir, self._validationfile)
        with open(validationpath, "w") as f:
            f.write(self._validation)

        return timestamp

    def load(self, timestamp):
        source = Source(METADATA["state_abbrv"], METADATA["city"], "crawler", "all")

        self._crawlfile = f"nj-millburn-crawl-{timestamp}.json"
        crawlpath = os.path.join(source.source_dir, self._crawlfile)
        with open(crawlpath, "r") as f:
            self._minutes = json.loads(f.read())

        self._validationfile = f"nj-millburn-validation-{timestamp}.txt"
        validationpath = os.path.join(source.source_dir, self._validationfile)
        with open(validationpath, "r") as f:
            self._validation = f.read()

    def _year_table_index(self, driver):
        year_table = defaultdict(list)
        all_links = driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            # Initial three years are always presented on page
            parent_path = f".{''.join(['/parent::*'] * 2)}"
            try:
                ul = link.find_element(By.XPATH, parent_path)
            except:
                pass

            if ul.tag_name == "ul" and ul.get_attribute("class") == "years":
                year_table[ul.id].append((link, None))

            # Remaning years are available via popup
            parent_path = f".{''.join(['/parent::*'] * 8)}"
            try:
                ul = link.find_element(By.XPATH, parent_path)
            except:
                pass

            if ul.tag_name == "ul" and ul.get_attribute("class") == "years":
                parent_menu = None

                # "View More" parent popup -- to be clicked to reveal
                menu_path = f".{''.join(['/parent::*'] * 6)}/a"
                try:
                    a = link.find_element(By.XPATH, menu_path)
                except:
                    pass

                if "showMoreYears" in a.get_attribute("onclick"):
                    parent_menu = a

                year_table[ul.id].append((link, parent_menu))

        return year_table

    def _index_table(self, year_table):
        table = defaultdict(dict)
        for key, links in year_table.items():
            all_doctypes = set(
                [
                    year_table_to_doctype(link.get_dom_attribute("aria-label").lower())
                    for (link, parent_menu) in links
                ]
            )
            assert len(all_doctypes) == 1
            doctype = (all_doctypes).pop()
            table[doctype] = {
                year_table_to_year(link.get_dom_attribute("aria-label").lower()): {
                    "link": link,
                    "parent_menu": parent_menu,
                }
                for (link, parent_menu) in links
            }

        return table

    def _get_all_minutes(self, driver, filter_year):
        minutes = defaultdict(list)
        all_links = driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            try:
                url = link.get_dom_attribute("href")
            except Exception as err:
                print(err)
                continue

            if not url:
                continue

            if "minutes" in url.lower():
                doc_id = url.split("/")[-1][1:]
                try:
                    # this hack because aria-label doesnt work on this element
                    label = driver.find_element(By.ID, doc_id).text
                except Exception as err:
                    print(f"error finding id={doc_id} for label")
                    continue

                doctype = minutes_label_to_doctype(label)
                year = minutes_docid_to_year(doc_id)

                if year == filter_year:
                    minutes[doctype].append(
                        {
                            "id": doc_id,
                            "label": label,
                            "year": year,
                            "date": minutes_docid_to_date_YYYYMMDD(doc_id),
                            "url": urllib.parse.urljoin(DOCUMENTS_ROOT, url),
                        }
                    )

        return minutes

    def crawl(self, verbose=True):
        self._minutes = defaultdict(dict)
        for year in YEARS_TO_PROCESS:
            if verbose:
                print(f"Finding documents for the year: {year}")

            # Flaky: reload to process each year
            with webdriver_session(self._documents_index_url) as driver:
                # Flaky: rebuild index after every selection
                table = self._index_table(self._year_table_index(driver))

                # "Set page to year": click on year link year for all doctypes
                for doctype in PAGE_SECTIONS:
                    if year in table[doctype]:
                        try:
                            if table[doctype][year]["parent_menu"] is not None:
                                table[doctype][year]["parent_menu"].click()

                            table[doctype][year]["link"].click()
                        except Exception as err:
                            print(f"Unable to 'click' {doctype}, {year}, link")
                            print(
                                f"Has parent_menu: {table[doctype][year]['parent_menu'] is not None}"
                            )
                            print(err)

                # Get all minutes for current page view and year
                time.sleep(2)  # Flaky:  wait to load
                all_minutes = self._get_all_minutes(driver, year)
                for doctype in PAGE_SECTIONS:
                    if year in table[doctype] and doctype in all_minutes:
                        self._minutes[doctype][year] = all_minutes[doctype]

            self._validation = NJMillburnCrawler.show_minutes_table(
                YEARS_TO_PROCESS, self._minutes
            )
            if verbose:
                print(self._validation)

        return self._minutes

    @staticmethod
    def show_minutes_table(years, minutes):
        rows = []
        headers = ["year", "type", "# docs"]
        for year in years:
            rows.append([year] + [""] * 2)
            for doctype in minutes:
                if year in minutes[doctype]:
                    rows.append(
                        [
                            "",
                            doctype,
                            len(minutes[doctype][year]),
                        ]
                    )
        table = tabulate(rows, headers=headers)
        return table


class NJMillburnDownloader(object):
    """
    Download missing pdfs and metadata artifacts.
    """

    def __init__(self, crawl_timestamp):
        self.crawl_timestamp = crawl_timestamp
        self._crawler = None

        self._init()

    def _init(self):
        self._crawler = NJMillburnCrawler()
        self._crawler.load(self.crawl_timestamp)

    def download(self, overwrite=False):
        for doctype in DOCTYPES:
            for year, docs in self._crawler.minutes[doctype].items():
                source = Source(
                    METADATA["state_abbrv"],
                    METADATA["city"],
                    doctype,
                    year,
                )
                for doc in docs:
                    source.write(
                        doc["date"],
                        doc["url"],
                        METADATA | doc,
                        overwrite=overwrite,
                    )
