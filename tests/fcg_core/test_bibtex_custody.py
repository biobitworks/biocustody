"""BibTeX custody regression — nested braces and escapes."""

from fcg_core.bibtex_custody import parse_bibtex_bytes


def test_nested_braces_in_title():
    raw = """
@article{chow1970,
  author = {Chow, C. K.},
  title = {{On} optimum {recognition} error and reject tradeoff},
  year = {1970},
  doi = {10.1109/TIT.1970.1054406}
}
""".strip().encode("utf-8")
    records = parse_bibtex_bytes(raw)
    assert len(records) == 1
    assert records[0].bib_key == "chow1970"
    assert "recognition" in records[0].fields.get("title", "")


def test_escaped_characters_preserved_in_bytes():
    raw = br'@misc{x, author={O\'Reilly}, title={100\% {Pure}}}' + b"\n"
    cid_records = parse_bibtex_bytes(raw)
    assert len(cid_records) == 1
