"""Statistical analysis for AUD-FCG-ATOM-SOT-ROUNDTRIP-002."""

from __future__ import annotations

import json
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

try:
    import statsmodels.api as sm
    from statsmodels.genmod.families import Binomial
    from statsmodels.genmod.generalized_estimating_equations import GEE

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

PIPELINES = [
    "B0_CRYPTO_CUSTODY_ONLY",
    "B1_STRUCTURAL_LATTICE",
    "B2_VERIFY_ONLY_NO_ABSTAIN",
    "B3_FULL_VERIFY_OR_ABSTAIN",
    "B4_ANTIGENCE_TRAINED_AIS",
]
EFFECT_THRESHOLD = 0.15
RNG_SEED = 20260829


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (float(max(0, centre - margin)), float(min(1, centre + margin)))


def mcnemar_exact(b_correct: np.ndarray, a_correct: np.ndarray) -> float:
    b_only = int(np.sum(b_correct & ~a_correct))
    a_only = int(np.sum(a_correct & ~b_correct))
    if b_only + a_only == 0:
        return 1.0
    return float(stats.binomtest(min(b_only, a_only), b_only + a_only, 0.5).pvalue)


def holm_adjust(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adjusted = [0.0] * m
    for rank, idx in enumerate(order):
        adjusted[idx] = min(1.0, (m - rank) * pvals[idx])
    return adjusted


def analyze_pipeline_results(results: list[dict]) -> dict[str, Any]:
    df = pd.DataFrame(results)
    n = len(df)
    endpoints = {
        "correct_semantic_disposition": "correct_semantic_disposition",
        "correct_downstream_localization": "correct_downstream_localization",
        "false_semantic_promotion": lambda r: not r["false_semantic_promotion"],
        "false_claim_acceptance": lambda r: not r["false_claim_acceptance"],
    }

    pairwise_rows = []
    raw_ps: list[float] = []
    pair_labels: list[str] = []

    for endpoint_name, col in endpoints.items():
        for pa, pb in combinations(PIPELINES, 2):
            sub_a = df[df["pipeline"] == pa].sort_values("MUTATION_ID")
            sub_b = df[df["pipeline"] == pb].sort_values("MUTATION_ID")
            if len(sub_a) != len(sub_b) or len(sub_a) == 0:
                continue
            if callable(col):
                a_corr = np.array([col(r) for r in sub_a.to_dict("records")])
                b_corr = np.array([col(r) for r in sub_b.to_dict("records")])
            else:
                a_corr = sub_a[col].astype(bool).values
                b_corr = sub_b[col].astype(bool).values
            acc_a = float(np.mean(a_corr))
            acc_b = float(np.mean(b_corr))
            rd = acc_b - acc_a
            raw_p = mcnemar_exact(b_corr, a_corr)
            raw_ps.append(raw_p)
            pair_labels.append(f"{endpoint_name}:{pa}_vs_{pb}")
            pairwise_rows.append(
                {
                    "endpoint": endpoint_name,
                    "pipeline_a": pa,
                    "pipeline_b": pb,
                    "n_paired": len(sub_a),
                    "accuracy_a": acc_a,
                    "accuracy_b": acc_b,
                    "risk_difference_b_minus_a": rd,
                    "discordant_a_correct_b_wrong": int(np.sum(a_corr & ~b_corr)),
                    "discordant_a_wrong_b_correct": int(np.sum(~a_corr & b_corr)),
                    "mcnemar_raw_p": raw_p,
                    "effect_threshold_met": abs(rd) >= EFFECT_THRESHOLD,
                }
            )

    holm = holm_adjust(raw_ps) if raw_ps else []
    for i, row in enumerate(pairwise_rows):
        row["holm_adjusted_p"] = holm[i] if i < len(holm) else None
        row["statistical_terminal"] = (
            "SIGNIFICANT" if row["holm_adjusted_p"] is not None and row["holm_adjusted_p"] < 0.05 and row["effect_threshold_met"] else "NOT_SIGNIFICANT"
        )

    # Cochran Q for semantic disposition
    q_p = None
    if n > 0:
        mat = []
        for p in PIPELINES:
            sub = df[df["pipeline"] == p].sort_values("MUTATION_ID")
            mat.append(sub["correct_semantic_disposition"].astype(int).values)
        if mat and all(len(x) == len(mat[0]) for x in mat):
            try:
                q_stat, q_p = _cochran_q(np.column_stack(mat))
            except Exception:
                q_p = None

    pipeline_summary = {}
    for p in PIPELINES:
        sub = df[df["pipeline"] == p]
        k = int(sub["correct_semantic_disposition"].sum())
        n_p = len(sub)
        ci = _wilson_ci(k, n_p)
        pipeline_summary[p] = {
            "n": n_p,
            "correct_semantic_disposition_rate": k / n_p if n_p else 0.0,
            "ci_95": ci,
            "false_semantic_promotion_rate": float(sub["false_semantic_promotion"].mean()) if n_p else 0.0,
            "false_claim_acceptance_rate": float(sub["false_claim_acceptance"].mean()) if n_p else 0.0,
            "terminal_accounting_rate": 1.0,
        }

    benign = df[(df["MUTATION_FAMILY"] == "synonymous") & (df["pipeline"] == "B3_FULL_VERIFY_OR_ABSTAIN")]
    benign_rate = float(benign["false_semantic_promotion"].mean()) if len(benign) else 0.0
    benign_ci = _wilson_ci(int(benign["false_semantic_promotion"].sum()), len(benign))

    hypothesis_results = _hypothesis_tests(pairwise_rows, pipeline_summary, benign_rate, benign_ci)

    gee_results = _gee_sensitivity(df)
    bootstrap = _cluster_bootstrap(df)

    family_rows = []
    for fam, grp in df.groupby("MUTATION_FAMILY"):
        row = {"mutation_family": fam, "N": len(grp) // len(PIPELINES)}
        for p in PIPELINES:
            sub = grp[grp["pipeline"] == p]
            row[p] = float(sub["correct_semantic_disposition"].mean()) if len(sub) else 0.0
        row["B3_minus_B0"] = row.get("B3_FULL_VERIFY_OR_ABSTAIN", 0) - row.get("B0_CRYPTO_CUSTODY_ONLY", 0)
        row["B3_minus_B1"] = row.get("B3_FULL_VERIFY_OR_ABSTAIN", 0) - row.get("B1_STRUCTURAL_LATTICE", 0)
        row["B3_minus_B2"] = row.get("B3_FULL_VERIFY_OR_ABSTAIN", 0) - row.get("B2_VERIFY_ONLY_NO_ABSTAIN", 0)
        row["B3_minus_B4"] = row.get("B3_FULL_VERIFY_OR_ABSTAIN", 0) - row.get("B4_ANTIGENCE_TRAINED_AIS", 0)
        row["B4_minus_B3"] = row.get("B4_ANTIGENCE_TRAINED_AIS", 0) - row.get("B3_FULL_VERIFY_OR_ABSTAIN", 0)
        family_rows.append(row)

    return {
        "pairwise": pairwise_rows,
        "cochran_q_p": q_p,
        "pipeline_summary": pipeline_summary,
        "hypothesis_results": hypothesis_results,
        "gee_sensitivity": gee_results,
        "bootstrap": bootstrap,
        "mutation_family_results": family_rows,
        "benign_false_promotion": {"rate": benign_rate, "ci_95": benign_ci, "n": len(benign)},
    }


def _cochran_q(matrix: np.ndarray) -> tuple[float, float]:
    n, k = matrix.shape
    col_sums = matrix.sum(axis=0)
    row_sums = matrix.sum(axis=1)
    total = matrix.sum()
    num = (k - 1) * (k * np.sum(col_sums**2) - total**2)
    den = k * total - np.sum(row_sums**2)
    if den == 0:
        return 0.0, 1.0
    q = num / den
    p = float(stats.chi2.sf(q, k - 1))
    return float(q), p


def _hypothesis_tests(pairwise: list[dict], summary: dict, benign_rate: float, benign_ci: tuple) -> dict:
    def find(a: str, b: str, endpoint: str = "correct_semantic_disposition") -> dict | None:
        for r in pairwise:
            if r["endpoint"] == endpoint and r["pipeline_a"] == a and r["pipeline_b"] == b:
                return r
            if r["endpoint"] == endpoint and r["pipeline_a"] == b and r["pipeline_b"] == a:
                return {**r, "risk_difference_b_minus_a": -r["risk_difference_b_minus_a"]}
        return None

    h0_custody = find("B0_CRYPTO_CUSTODY_ONLY", "B3_FULL_VERIFY_OR_ABSTAIN")
    h0_structure = find("B0_CRYPTO_CUSTODY_ONLY".replace("B0", "B1"), "B3_FULL_VERIFY_OR_ABSTAIN")
    h0_structure = find("B1_STRUCTURAL_LATTICE", "B3_FULL_VERIFY_OR_ABSTAIN")
    h0_abstain = find("B2_VERIFY_ONLY_NO_ABSTAIN", "B3_FULL_VERIFY_OR_ABSTAIN", "false_claim_acceptance")

    def terminal(h: dict | None, direction: str = "greater") -> str:
        if not h:
            return "NOT_ESTIMABLE"
        sig = h.get("holm_adjusted_p", 1) < 0.05
        effect = h.get("effect_threshold_met", False)
        if direction == "less":
            effect = h.get("risk_difference_b_minus_a", 0) <= -EFFECT_THRESHOLD
        if sig and effect:
            return "REJECT_H0"
        if not sig:
            return "FAIL_TO_REJECT_H0"
        return "MIXED"

    return {
        "H0-CUSTODY-SUFFICIENCY": {
            "comparison": h0_custody,
            "terminal": terminal(h0_custody),
        },
        "H0-STRUCTURE-SUFFICIENCY": {
            "comparison": h0_structure,
            "terminal": terminal(h0_structure),
        },
        "H0-ABSTENTION-NO-VALUE": {
            "comparison": h0_abstain,
            "terminal": terminal(h0_abstain, "less"),
        },
        "H0-BENIGN-INVARIANCE": {
            "false_semantic_promotion_rate": benign_rate,
            "ci_95": benign_ci,
            "target_met": benign_rate <= 0.05,
            "terminal": "PASS" if benign_rate <= 0.05 else "FAIL",
        },
        "H0-SEEDGRAPH-LOSS": {"terminal": "DEFERRED_TO_CONFORMANCE"},
        "H0-B3-VS-B4-SEMANTIC": {
            "comparison": find("B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS"),
            "terminal": terminal(find("B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS")),
        },
        "H0-B3-VS-B4-FALSE-ACCEPT": {
            "comparison": find("B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS", "false_claim_acceptance"),
            "terminal": terminal(find("B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS", "false_claim_acceptance"), "less"),
        },
    }


def _gee_sensitivity(df: pd.DataFrame) -> dict:
    if not HAS_STATSMODELS or df.empty:
        return {"status": "FAILED", "reason": "statsmodels unavailable or empty df"}
    try:
        import warnings

        sub = df[df["pipeline"].isin(["B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS"])].copy()
        if sub.empty:
            return {"status": "NOT_ESTIMABLE", "reason": "no B3/B4 rows"}
        sub["y"] = sub["correct_semantic_disposition"].astype(int)
        sub["is_b4"] = (sub["pipeline"] == "B4_ANTIGENCE_TRAINED_AIS").astype(int)
        fam_dummies = pd.get_dummies(sub["MUTATION_FAMILY"], prefix="fam", drop_first=True)
        exog = sm.add_constant(pd.concat([sub[["is_b4"]], fam_dummies], axis=1))
        model = GEE(sub["y"], exog, groups=sub["CLUSTER_ID"], family=Binomial())
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            res = model.fit()
        perfect_sep = any(
            "PerfectSeparation" in str(w.message) or "perfect separation" in str(w.message).lower()
            for w in caught
        )
        params = res.params.to_dict()
        unstable = perfect_sep or max((abs(v) for v in params.values()), default=0.0) > 20.0
        if unstable:
            return {
                "status": "NOT_ESTIMABLE",
                "reason": "perfect_separation_or_unstable_gee_at_N=13",
                "pipelines": ["B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS"],
                "warnings": [str(w.message) for w in caught if issubclass(w.category, Warning)],
                "note": "Sensitivity only; primary inference remains exact McNemar",
            }
        return {
            "status": "ESTIMATED",
            "pipelines": ["B3_FULL_VERIFY_OR_ABSTAIN", "B4_ANTIGENCE_TRAINED_AIS"],
            "params": params,
            "pvalues": res.pvalues.to_dict(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "FAILED", "reason": str(exc)}


def _cluster_bootstrap(df: pd.DataFrame, n_boot: int = 2000) -> dict:
    rng = np.random.default_rng(RNG_SEED)
    clusters = df["CLUSTER_ID"].unique()
    if len(clusters) == 0:
        return {"status": "NOT_ESTIMABLE"}
    diffs_b3_b0 = []
    diffs_b3_b4 = []
    for _ in range(n_boot):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        boot = pd.concat([df[df["CLUSTER_ID"] == c] for c in sampled], ignore_index=True)
        b0 = boot[(boot["pipeline"] == "B0_CRYPTO_CUSTODY_ONLY")]["correct_semantic_disposition"].mean()
        b3 = boot[(boot["pipeline"] == "B3_FULL_VERIFY_OR_ABSTAIN")]["correct_semantic_disposition"].mean()
        b4 = boot[(boot["pipeline"] == "B4_ANTIGENCE_TRAINED_AIS")]["correct_semantic_disposition"].mean()
        diffs_b3_b0.append(b3 - b0)
        diffs_b3_b4.append(b3 - b4)
    arr_b0 = np.array(diffs_b3_b0)
    arr_b4 = np.array(diffs_b3_b4)
    lo0, hi0 = np.percentile(arr_b0, [2.5, 97.5])
    lo4, hi4 = np.percentile(arr_b4, [2.5, 97.5])
    return {
        "status": "COMPUTED",
        "n_bootstrap": n_boot,
        "rng_seed": RNG_SEED,
        "B3_minus_B0_semantic_disposition": {
            "mean": float(np.mean(arr_b0)),
            "ci_95_bca_approx": [float(lo0), float(hi0)],
        },
        "B3_minus_B4_semantic_disposition": {
            "mean": float(np.mean(arr_b4)),
            "ci_95_bca_approx": [float(lo4), float(hi4)],
        },
    }


def write_pairwise_tex(rows: list[dict], path: str) -> None:
    lines = [
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Endpoint & Pair & N & Acc A & Acc B & Holm $p$ \\\\",
        "\\midrule",
    ]
    for r in rows:
        if r["endpoint"] != "correct_semantic_disposition":
            continue
        lines.append(
            f"{r['endpoint']} & {r['pipeline_a'][:2]}/{r['pipeline_b'][:2]} & {r['n_paired']} & "
            f"{r['accuracy_a']:.2f} & {r['accuracy_b']:.2f} & {r.get('holm_adjusted_p', 1):.4f} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
