from pathlib import Path
import sys
import json

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from biocustody.claims import claim_ceiling
from biocustody.fco import make_fco, verify_fco
from biocustody.opposition import rank_counter_perturbations
from biocustody.state import ReferenceStateModel


st.set_page_config(page_title="Bio-Delta-G", layout="wide")
st.title("Bio-Delta-G")
st.caption("Public Cell Painting profiles -> reference state -> restoration ranking -> custody receipt")


def real_result_path() -> Path | None:
    for path in [
        ROOT / "runs/kaggle_output/cpjump1_best_result.json",
        ROOT / "runs/kaggle/cpjump1_best_result.json",
        ROOT / "runs/local/cpjump1_benchmark_result.json",
    ]:
        if path.exists():
            return path
    return None


def render_real_result(path: Path) -> None:
    result = json.loads(path.read_text(encoding="utf-8"))
    benchmark = result["benchmark"]
    decision = result["state_decision"]
    ranking = pd.DataFrame(result["ranking"])

    st.subheader("CPJUMP1 phenotypic restoration benchmark")
    st.caption(str(path.relative_to(ROOT)))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Perturbation", benchmark["benchmark_gene"])
    c2.metric("State", decision["decision"])
    c3.metric("Distance D", f"{decision['distance2'] ** 0.5:.3f}")
    c4.metric("Claim ceiling", result["claim_ceiling"])

    points = []
    for row in result["plot_points"]["controls"]:
        points.append({"x": row["x"], "y": row["y"], "kind": "control", "label": "control", "score_size": 12.0})
    pert = result["plot_points"]["perturbation"]
    points.append({"x": pert["x"], "y": pert["y"], "kind": "perturbation", "label": pert["label"], "score_size": 80.0})
    for row in result["plot_points"]["candidates"]:
        points.append(
            {
                "x": row["x"],
                "y": row["y"],
                "kind": "candidate",
                "label": row["label"],
                "score_size": max(20.0, 45.0 + 80.0 * float(row["restoration_score"])),
            }
        )
    point_df = pd.DataFrame(points)
    st.scatter_chart(point_df, x="x", y="y", color="kind", size="score_size", use_container_width=True)

    show_cols = [
        col
        for col in [
            "candidate",
            "pert_iname",
            "target",
            "target_match",
            "target_list_match",
            "restoration_score",
            "candidate_distance",
            "distance_ratio",
            "pathway",
        ]
        if col in ranking.columns
    ]
    st.subheader("Candidate ranking")
    st.dataframe(ranking[show_cols], use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Evidence graph")
        st.json(result["evidence_graph"])
    with right:
        st.subheader("Custody receipt")
        st.write("FCO verifies:", bool(result["fco_verifies"]))
        st.write("Tampered receipt verifies:", bool(result["tamper_demo"]["verifies_after_tamper"]))
        st.code(result["fco"]["digest"], language="text")
        with st.expander("Receipt JSON"):
            st.code(json.dumps(result["fco"], indent=2), language="json")


def render_synthetic_fallback() -> None:
    st.subheader("Synthetic fallback")
    controls = pd.read_csv(ROOT / "data/synthetic/controls.csv")
    perturb = pd.read_csv(ROOT / "data/synthetic/perturbation.csv").iloc[0]
    cand_df = pd.read_csv(ROOT / "data/synthetic/candidates.csv")

    model = ReferenceStateModel(quantile=0.95, max_components=6).fit(controls.values)
    decision = model.decide(perturb.values)
    reference = controls.median(axis=0).values
    candidates = {
        row["candidate"]: row[controls.columns].to_numpy(dtype=float)
        for _, row in cand_df.iterrows()
    }
    ranking = rank_counter_perturbations(reference, perturb.values, candidates)
    top = ranking.iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Perturbation state", decision.decision)
    c2.metric("State distance D2", f"{decision.distance2:.2f}")
    c3.metric("Reference threshold D2", f"{decision.threshold2:.2f}")

    st.dataframe(ranking, use_container_width=True)

    ceiling = claim_ceiling(
        profile_observed=True,
        perturbation_detected=(decision.decision == "TRANSITION"),
        opposition_supported=(top.opposition_score > 0.5),
        target_evidence=st.checkbox("Target evidence verified", value=False),
    )
    source = {
        "public_data": True,
        "contains_phi": False,
        "access_restricted": False,
        "usage_rights_verified": True,
        "source": "synthetic demo",
    }
    fco = make_fco(
        "candidate_ranking",
        {"candidate": top.candidate, "opposition_score": float(top.opposition_score)},
        source,
        claim={"claim_ceiling": ceiling},
    )
    st.info(f"Claim ceiling: {ceiling}")
    st.code(json.dumps(fco.as_dict(), indent=2), language="json")
    st.write("Verification:", verify_fco(fco))


path = real_result_path()
if path:
    render_real_result(path)
else:
    render_synthetic_fallback()
