"""Pinned BibTeX parser — preserve exact bytes + structured semantic object."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from fcg_core.canonical_v2 import canonical_hash_v2
from fcg_core.identities import citation_semantic_id, content_id


@dataclass(frozen=True)
class BibTeXCustodyRecord:
    bib_key: str
    content_id: str
    semantic_id: str
    parser: str
    parser_version: str
    fields: dict[str, str]


def parse_bibtex_bytes(raw: bytes) -> list[BibTeXCustodyRecord]:
    """Parse BibTeX from exact bytes; never regex-only."""
    cid = content_id(raw)
    text = raw.decode("utf-8", errors="replace")
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    db = bibtexparser.loads(text, parser=parser)
    records: list[BibTeXCustodyRecord] = []
    for entry in db.entries:
        key = entry.get("ID") or entry.get("id") or ""
        authors_raw = entry.get("author", "")
        authors = [a.strip() for a in authors_raw.replace("\n", " ").split(" and ") if a.strip()]
        title = entry.get("title", "").strip("{} ")
        year_s = entry.get("year", "0")
        try:
            year = int(year_s[:4])
        except ValueError:
            year = 0
        doi = entry.get("doi")
        sid = citation_semantic_id(authors, title, year, doi)
        fields = {k: str(v) for k, v in entry.items()}
        records.append(
            BibTeXCustodyRecord(
                bib_key=key,
                content_id=cid,
                semantic_id=sid,
                parser="bibtexparser",
                parser_version="1.4.4",
                fields=fields,
            )
        )
    return records


def parse_bibtex_file(path: Path) -> tuple[str, list[BibTeXCustodyRecord]]:
    raw = path.read_bytes()
    return content_id(raw), parse_bibtex_bytes(raw)
