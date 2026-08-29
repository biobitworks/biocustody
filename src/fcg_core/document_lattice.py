"""Deterministic document lattice extraction for AUD-FCG-DOCUMENT-LATTICE-001."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fcg_core.canonical_v2 import canonical_hash_v2
from fcg_core.identities import content_id, occurrence_id, semantic_id, sentence_semantic_id

SOURCE_COMMIT = "4a372a5c459ad60cd23b850709011cbfd0e516b4"
RULESET_SHA = hashlib.sha256(b"document_lattice_extractor_v1").hexdigest()
CODE_SHA = hashlib.sha256(b"fcg_core.document_lattice").hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob_sha(repo: Path, commit: str, rel_path: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", f"{commit}:{rel_path}"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return out if len(out) == 40 else None
    except subprocess.CalledProcessError:
        return None


def git_tree_sha(repo: Path, commit: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{commit}^{{tree}}"], cwd=repo, text=True).strip()


@dataclass
class LatticeObject:
    object_id: str
    object_type: str
    content_id: str
    semantic_id: str
    occurrence_id: str
    parent_id: str | None
    ordinal: int
    source_file: str
    source_blob_sha: str | None
    source_span: dict[str, Any]
    source_commit: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base = {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "CONTENT_ID": self.content_id,
            "SEMANTIC_ID": self.semantic_id,
            "OCCURRENCE_ID": self.occurrence_id,
            "parent_id": self.parent_id,
            "ordinal": self.ordinal,
            "source_file": self.source_file,
            "source_blob_sha": self.source_blob_sha,
            "source_span": self.source_span,
            "source_commit": self.source_commit,
        }
        base.update(self.extra)
        return base


def _tid(prefix: str, semantic: str) -> str:
    return f"{prefix}-{semantic[:16]}"


def _occ(cid: str, locator: str) -> str:
    return occurrence_id("document_lattice.v1", cid, locator, "extractor:document_lattice", "provider:biocustody", {})


def extract_citations(text: str) -> list[str]:
    keys: list[str] = []
    for m in re.finditer(r"\\cite[t|p]?\{([^}]+)\}", text):
        keys.extend(k.strip() for k in m.group(1).split(","))
    return sorted(set(keys))


def split_sentences(text: str) -> list[str]:
    out: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+", text.strip()):
        part = re.sub(r"\s+", " ", part).strip()
        if len(part) >= 15:
            out.append(part)
    return out


def parse_bib_keys(bib_text: str) -> list[str]:
    return re.findall(r"@\w+\{([^,]+),", bib_text)


def build_lattice(manuscript_dir: Path, repo: Path) -> dict[str, Any]:
    main_tex = manuscript_dir / "main.tex"
    refs_bib = manuscript_dir / "references.bib"
    terminology = manuscript_dir / "sections" / "terminology.tex"
    checklist = manuscript_dir / "checklist.tex"

    rel_main = "paper/newinml2026/manuscript/main.tex"
    tex = main_tex.read_text(encoding="utf-8")
    bib = refs_bib.read_text(encoding="utf-8")
    main_blob = git_blob_sha(repo, SOURCE_COMMIT, rel_main) or sha256_file(main_tex)
    bib_blob = git_blob_sha(repo, SOURCE_COMMIT, "paper/newinml2026/manuscript/references.bib") or sha256_file(refs_bib)

    objects: dict[str, list[LatticeObject]] = {
        "documents": [],
        "sections": [],
        "paragraphs": [],
        "sentences": [],
        "spans": [],
        "citations": [],
        "reference_entries": [],
        "tables": [],
        "table_rows": [],
        "table_columns": [],
        "table_cells": [],
        "figures": [],
        "figure_panels": [],
        "figure_elements": [],
        "captions": [],
        "edges": [],
    }

    doc_cid = content_id(tex.encode("utf-8"))
    doc_sid = semantic_id("fco.document.v2", "1.0.0", {"title": "Verify-or-Abstain Evidence Pipelines", "commit": SOURCE_COMMIT})
    doc_oid = _tid("DOC", doc_sid)
    objects["documents"].append(
        LatticeObject(doc_oid, "Document", doc_cid, doc_sid, _occ(doc_cid, rel_main), None, 0, rel_main, main_blob, {"byte_start": 0, "byte_end": len(tex)}, SOURCE_COMMIT)
    )

    section_pattern = [
        ("abstract", r"\\begin\{abstract\}(.*?)\\end\{abstract\}"),
        ("Introduction", r"\\section\{Introduction\}(.*?)\\section\{"),
        ("Related Work and Terminology", r"\\section\{Related Work.*?\}(.*?)\\input\{sections/terminology\}"),
        ("Verify-or-Abstain Architecture", r"\\section\{Verify-or-Abstain Architecture\}(.*?)\\section\{"),
        ("Experimental Design", r"\\section\{Experimental Design\}(.*?)\\section\{"),
        ("Results", r"\\section\{Results\}(.*?)\\section\{"),
        ("Discussion and Limitations", r"\\section\{Discussion and Limitations\}(.*?)\\section\{"),
        ("Reproducibility and Provenance", r"\\section\{Reproducibility.*?\}(.*?)\\section\{"),
        ("Conclusion", r"\\section\{Conclusion\}(.*?)\\bibliographystyle"),
    ]

    sec_ord = 0
    para_global = 0
    sent_global = 0

    for sec_name, pattern in section_pattern:
        m = re.search(pattern, tex, re.S)
        body = m.group(1).strip() if m else ""
        sec_cid = content_id(body.encode("utf-8") if body else sec_name.encode())
        sec_sid = semantic_id("fco.section.v2", "1.0.0", {"name": sec_name, "document_id": doc_oid})
        sec_oid = _tid("SEC", sec_sid)
        sec_ord += 1
        objects["sections"].append(
            LatticeObject(sec_oid, "Section", sec_cid, sec_sid, _occ(sec_cid, f"{rel_main}#section:{sec_name}"), doc_oid, sec_ord, rel_main, main_blob, {"section": sec_name}, SOURCE_COMMIT)
        )
        objects["edges"].append({"edge_id": f"EDGE-{doc_oid}-{sec_oid}", "from": doc_oid, "to": sec_oid, "edge_type": "CONTAINS", "ordinal": sec_ord})

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip() and not p.strip().startswith("\\")]
        for p_ord, para in enumerate(paragraphs, start=1):
            para_global += 1
            pcid = content_id(para.encode("utf-8"))
            psid = semantic_id("fco.paragraph.v2", "1.0.0", {"section": sec_name, "ordinal": p_ord, "text_prefix": para[:80]})
            poid = _tid("PAR", psid)
            objects["paragraphs"].append(
                LatticeObject(poid, "Paragraph", pcid, psid, _occ(pcid, f"{sec_oid}:p{p_ord}"), sec_oid, p_ord, rel_main, main_blob, {"section": sec_name}, SOURCE_COMMIT)
            )
            objects["edges"].append({"edge_id": f"EDGE-{sec_oid}-{poid}", "from": sec_oid, "to": poid, "edge_type": "CONTAINS", "ordinal": p_ord})

            for s_ord, sent in enumerate(split_sentences(para), start=1):
                sent_global += 1
                scid = content_id(sent.encode("utf-8"))
                ssid = sentence_semantic_id(sent, "whitespace_normalized", 0, len(sent))
                soid = _tid("SEN", ssid)
                cite_keys = extract_citations(sent)
                objects["sentences"].append(
                    LatticeObject(
                        soid, "Sentence", scid, ssid, _occ(scid, f"{poid}:s{s_ord}"), poid, s_ord, rel_main, main_blob,
                        {"section": sec_name}, SOURCE_COMMIT,
                        extra={"exact_text": sent, "citation_keys": cite_keys, "claim_ceiling": "REPURPOSING_HYPOTHESIS"},
                    )
                )
                objects["edges"].append({"edge_id": f"EDGE-{poid}-{soid}", "from": poid, "to": soid, "edge_type": "CONTAINS", "ordinal": s_ord})
                for ck in cite_keys:
                    span_sid = semantic_id("fco.span.v2", "1.0.0", {"sentence_id": soid, "citation_key": ck})
                    span_oid = _tid("SPN", span_sid)
                    objects["spans"].append(
                        LatticeObject(span_oid, "Span", scid, span_sid, _occ(scid, f"{soid}:cite:{ck}"), soid, 0, rel_main, main_blob, {"citation_key": ck}, SOURCE_COMMIT, extra={"span_kind": "CitationCallsite"})
                    )
                    objects["edges"].append({"edge_id": f"EDGE-{soid}-{span_oid}", "from": soid, "to": span_oid, "edge_type": "CITES", "ordinal": 0, "citation_key": ck})

    # Reference section entries from bib
    for i, key in enumerate(parse_bib_keys(bib), start=1):
        entry_m = re.search(rf"@\w+\{{{re.escape(key)},(.*?)(?=\n@\w+\{{|\Z)", bib, re.S)
        entry_body = entry_m.group(0) if entry_m else key
        ecid = content_id(entry_body.encode("utf-8"))
        esid = semantic_id("fco.reference_entry.v2", "1.0.0", {"bib_key": key})
        eoid = _tid("REF", esid)
        objects["reference_entries"].append(
            LatticeObject(eoid, "ReferenceEntry", ecid, esid, _occ(ecid, f"references.bib:{key}"), doc_oid, i, "paper/newinml2026/manuscript/references.bib", bib_blob, {"bib_key": key}, SOURCE_COMMIT)
        )
        objects["edges"].append({"edge_id": f"EDGE-DOC-REF-{key}", "from": doc_oid, "to": eoid, "edge_type": "REFERENCES", "ordinal": i})

    # Table
    tab_m = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", tex, re.S)
    cap_m = re.search(r"\\caption\{Primary results.*?\}", tex, re.S)
    if tab_m:
        tab_text = tab_m.group(0)
        tcid = content_id(tab_text.encode())
        tsid = semantic_id("fco.table.v2", "1.0.0", {"label": "tab:results"})
        toid = _tid("TBL", tsid)
        results_sec = next((s.object_id for s in objects["sections"] if "Results" in s.extra.get("section", s.source_span.get("section", ""))), doc_oid)
        objects["tables"].append(
            LatticeObject(toid, "Table", tcid, tsid, _occ(tcid, "tab:results"), results_sec, 1, rel_main, main_blob, {"label": "tab:results"}, SOURCE_COMMIT, extra={"claim_ceiling": "REPURPOSING_HYPOTHESIS"})
        )
        if cap_m:
            cap_text = cap_m.group(0)
            ccid = content_id(cap_text.encode())
            csid = semantic_id("fco.caption.v2", "1.0.0", {"target": toid, "text": cap_text})
            coid = _tid("CAP", csid)
            objects["captions"].append(
                LatticeObject(coid, "TableCaption", ccid, csid, _occ(ccid, "tab:results:caption"), toid, 1, rel_main, main_blob, {}, SOURCE_COMMIT, extra={"exact_text": cap_text, "propositional": True})
            )
        lines = [ln.strip() for ln in tab_text.split("\\\\") if "&" in ln and "Experiment" not in ln and "toprule" not in ln and "midrule" not in ln and "bottomrule" not in ln]
        cols = ["Experiment", "Unit", "Guard", "Condition", "N", "Ceiling"]
        for ci, col in enumerate(cols, start=1):
            col_sid = semantic_id("fco.table_column.v2", "1.0.0", {"table_id": toid, "name": col})
            col_oid = _tid("TCOL", col_sid)
            objects["table_columns"].append(
                LatticeObject(col_oid, "TableColumn", tcid, col_sid, _occ(tcid, f"{toid}:col:{col}"), toid, ci, rel_main, main_blob, {"column": col}, SOURCE_COMMIT)
            )
        for ri, line in enumerate(lines, start=1):
            cells = [c.strip() for c in line.split("&")]
            row_sid = semantic_id("fco.table_row.v2", "1.0.0", {"table_id": toid, "row_index": ri, "context": line[:60]})
            row_oid = _tid("TROW", row_sid)
            objects["table_rows"].append(
                LatticeObject(row_oid, "TableRow", tcid, row_sid, _occ(tcid, f"{toid}:row:{ri}"), toid, ri, rel_main, main_blob, {"row_context": line}, SOURCE_COMMIT)
            )
            for ci, (col, val) in enumerate(zip(cols, cells + [""] * (len(cols) - len(cells))), start=1):
                cell_sid = semantic_id("fco.table_cell.v2", "1.0.0", {"table_id": toid, "row": ri, "column": col, "value": val})
                cell_oid = _tid("TCEL", cell_sid)
                cell_class = "PROPOSITIONAL" if col in {"Experiment", "N", "Ceiling"} else "STRUCTURAL"
                objects["table_cells"].append(
                    LatticeObject(
                        cell_oid, "TableCell", content_id(val.encode()), cell_sid, _occ(content_id(val.encode()), f"{row_oid}:{col}"),
                        row_oid, ci, rel_main, main_blob, {"row": ri, "column": col}, SOURCE_COMMIT,
                        extra={
                            "row_context": line,
                            "column_context": col,
                            "exact_value": val,
                            "display_value": val,
                            "cell_class": cell_class,
                            "proof_state": "PENDING",
                            "claim_ceiling": "REPURPOSING_HYPOTHESIS" if cell_class == "PROPOSITIONAL" else "STRUCTURAL",
                            "AOK_IDS": [],
                            "SOT_IDS": [],
                        },
                    )
                )

    # Figure (conceptual fbox)
    fig_m = re.search(r"\\begin\{figure\}.*?\\end\{figure\}", tex, re.S)
    if fig_m:
        fig_text = fig_m.group(0)
        fcid = content_id(fig_text.encode())
        fsid = semantic_id("fco.figure.v2", "1.0.0", {"label": "fig:pipeline", "kind": "conceptual_fbox"})
        foid = _tid("FIG", fsid)
        arch_sec = next((s.object_id for s in objects["sections"] if "Architecture" in str(s.source_span)), doc_oid)
        objects["figures"].append(
            LatticeObject(
                foid, "Figure", fcid, fsid, _occ(fcid, "fig:pipeline"), arch_sec, 1, rel_main, main_blob, {"label": "fig:pipeline"}, SOURCE_COMMIT,
                extra={"figure_class": "CONCEPTUAL", "rendered_artifact_sha": None, "generator_code_sha": CODE_SHA},
            )
        )
        cap_f = re.search(r"\\caption\{(.*?)\}", fig_text, re.S)
        if cap_f:
            cap_t = cap_f.group(1).strip()
            csid = semantic_id("fco.caption.v2", "1.0.0", {"target": foid, "text": cap_t})
            coid = _tid("FCAP", csid)
            objects["captions"].append(
                LatticeObject(coid, "FigureCaption", content_id(cap_t.encode()), csid, _occ(content_id(cap_t.encode()), "fig:pipeline:caption"), foid, 1, rel_main, main_blob, {}, SOURCE_COMMIT, extra={"exact_text": cap_t, "propositional": True, "element_class": "PROPOSITIONAL"})
            )
        panel_sid = semantic_id("fco.figure_panel.v2", "1.0.0", {"figure_id": foid, "panel": "main"})
        panel_oid = _tid("FPNL", panel_sid)
        objects["figure_panels"].append(
            LatticeObject(panel_oid, "FigurePanel", fcid, panel_sid, _occ(fcid, "fig:pipeline:panel"), foid, 1, rel_main, main_blob, {}, SOURCE_COMMIT)
        )
        for label in ["Source", "Normalize / Validate", "Admit", "Abstain", "Derived artifact", "Claim (ceiling)", "FCG custody"]:
            el_sid = semantic_id("fco.visual_element.v2", "1.0.0", {"figure_id": foid, "label": label})
            el_oid = _tid("VEL", el_sid)
            el_class = "PROPOSITIONAL" if label in {"Admit", "Abstain", "Claim (ceiling)"} else "STRUCTURAL"
            objects["figure_elements"].append(
                LatticeObject(
                    el_oid, "VisualElement", content_id(label.encode()), el_sid, _occ(content_id(label.encode()), f"fig:pipeline:{label}"),
                    panel_oid, 0, rel_main, main_blob, {"label": label}, SOURCE_COMMIT,
                    extra={"element_class": el_class, "decorative": el_class == "STRUCTURAL", "AOK_IDS": [], "SOT_IDS": []},
                )
            )

    # Included files in manifest
    included = []
    for inc in ["sections/terminology.tex", "checklist.tex"]:
        p = manuscript_dir / inc
        if p.is_file():
            included.append({"path": f"paper/newinml2026/manuscript/{inc}", "blob_sha": git_blob_sha(repo, SOURCE_COMMIT, f"paper/newinml2026/manuscript/{inc}") or sha256_file(p)})

    manifest = {
        "source_commit": SOURCE_COMMIT,
        "tree_sha": git_tree_sha(repo, SOURCE_COMMIT),
        "main_tex_blob_sha": main_blob,
        "references_bib_blob_sha": bib_blob,
        "included_files": included,
        "sealed_pdf_mutation": "FORBIDDEN",
    }
    return {"manifest": manifest, "objects": objects}


def project_seedgraph_envelope(obj: dict[str, Any]) -> dict[str, Any]:
    """Deterministic POST-INGEST projection envelope (isolated; no live Neo4j)."""
    return {
        "seedgraph_object_type": obj["object_type"],
        "object_id": obj["object_id"],
        "CONTENT_ID": obj["CONTENT_ID"],
        "SEMANTIC_ID": obj["SEMANTIC_ID"],
        "parent_id": obj.get("parent_id"),
        "ordinal": obj.get("ordinal"),
        "source_commit": obj.get("source_commit"),
    }
