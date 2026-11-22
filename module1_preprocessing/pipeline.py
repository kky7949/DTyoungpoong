"""Clean the supplied RAW file and produce auditable development-only exports.

Run from the repository root with ``python -m module1_preprocessing.pipeline``.
The cleaned development CSV retains missing values and is the CV input.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted

from .features import feature_matrix, feature_names
from .schema import (
    BASE, CHEM, DEFAULT_RAW_PATH, LIMITS, PLOT_LABELS, PROCESS, RAW_COLUMNS,
    RAW_SHEET, ROOT, TARGETS, UNITS,
)


def load_raw_data(path=None):
    """Read original values from the packaged XLSX or an equivalent UTF-8 CSV.

    No date parsing is performed. The original analysis-date text is metadata.
    """
    source = Path(path) if path is not None else DEFAULT_RAW_PATH
    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source, encoding="utf-8-sig", dtype={"배치ID": str, "분석일자": str})
    elif source.suffix.lower() in (".xlsx", ".xlsm"):
        frame = pd.read_excel(source, sheet_name=RAW_SHEET)
    else:
        raise ValueError("Input must be the supplied .xlsx workbook or an equivalent .csv file.")
    missing = [column for column in RAW_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required source columns: {missing}")
    if frame.empty:
        raise ValueError("The source contains no data rows.")
    return frame


def _clean_frame(raw):
    frame = raw.copy()
    frame["배치ID"] = frame["배치ID"].astype(str).str.strip()
    frame["원료등급"] = (
        frame["원료등급"].astype(str).str.strip().str.upper().str.replace("급", "", regex=False)
    )
    duplicate_mask = frame.duplicated("배치ID", keep="first")
    duplicates = frame.loc[duplicate_mask, "배치ID"].tolist()
    frame = frame.loc[~duplicate_mask].copy()
    suffix = pd.to_numeric(frame["배치ID"].str.extract(r"-(\d+)$")[0], errors="raise")
    if suffix.isna().any():
        raise ValueError("Every batch ID must end with a hyphen and a numeric batch suffix.")
    frame = frame.assign(_batch_order=suffix).sort_values("_batch_order", kind="mergesort")
    frame = frame.drop(columns="_batch_order").reset_index(drop=True)
    if not frame["원료등급"].isin(["A", "B", "C"]).all():
        raise ValueError("Raw-material grade must normalize to A, B, or C.")
    counts = []
    for column in BASE:
        original = frame[column]
        numeric = pd.to_numeric(original, errors="coerce")
        low, high = LIMITS[column]
        invalid_range = numeric.notna() & ~numeric.between(low, high)
        counts.append({
            "feature": column, "label": PLOT_LABELS[column], "unit": UNITS[column],
            "source_empty_after_dedup": int(original.isna().sum()),
            "numeric_coercion_to_missing": int((original.notna() & numeric.isna()).sum()),
            "out_of_range_to_missing": int(invalid_range.sum()),
        })
        frame[column] = numeric.mask(~numeric.between(low, high)).astype(float)
    for column in TARGETS.values():
        target = pd.to_numeric(frame[column], errors="raise")
        if target.isna().any() or not target.between(0, 100).all():
            raise ValueError(f"Target {column} must be observed and within 0–100%; targets are never imputed.")
        frame[column] = target.astype(float)
    return frame, {"duplicates_removed": duplicates, "input_quality": counts}


def load_clean_data(path=None):
    """Normalize, retain first duplicate, order by batch suffix, and mask inputs.

    Missing inputs remain missing. The first 85% of this result is the development
    segment. Batch order is an explicit proxy, not verified calendar chronology.
    """
    return _clean_frame(load_raw_data(path))[0]


class FoldPreprocessor(BaseEstimator, TransformerMixin):
    """Fit grade/global medians using only the rows passed to ``fit``.

    Chemistry uses its grade median when that grade has at least five observed
    values for that variable, falling back to the global training median.
    The four process inputs use global training medians. ``y`` is ignored.
    """

    def __init__(self, feature_mode="A17"):
        self.feature_mode = feature_mode

    def fit(self, X, y=None):
        feature_names(self.feature_mode)
        X = X.copy()
        self.global_median_ = X[list(BASE)].median()
        self.grade_median_ = X.groupby("원료등급")[list(CHEM)].median()
        self.grade_count_ = X.groupby("원료등급")[list(CHEM)].count()
        if self.global_median_.isna().any() or not np.isfinite(self.global_median_).all():
            raise ValueError("A training input has no finite observed values; its median cannot be fitted.")
        self.n_features_in_ = len(BASE) + 1
        return self

    def transform(self, X):
        check_is_fitted(self, ["global_median_", "grade_median_", "grade_count_"])
        X = X.copy()
        for column in CHEM:
            fallback = self.global_median_[column]
            for grade in ("A", "B", "C"):
                missing = X["원료등급"].eq(grade) & X[column].isna()
                count = self.grade_count_.loc[grade, column] if grade in self.grade_count_.index else 0
                value = self.grade_median_.loc[grade, column] if count >= 5 else fallback
                X.loc[missing, column] = value if pd.notna(value) else fallback
            X[column] = X[column].fillna(fallback)
        for column in PROCESS:
            X[column] = X[column].fillna(self.global_median_[column])
        return feature_matrix(X.loc[:, list(BASE)], self.feature_mode)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(feature_names(self.feature_mode), dtype=object)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _write_json(path, value):
    path.write_text(json.dumps(_json_safe(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _quality_outputs(development, quality, destination):
    """Descriptive development-only EDA; no record is deleted by the IQR rule."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination.mkdir(parents=True, exist_ok=True)
    paths = {}

    def csv(key, table):
        path = destination / f"{key}.csv"
        table.to_csv(path, index=False, encoding="utf-8-sig")
        paths[key] = str(path)

    csv("missing_counts", quality)
    numeric_columns = list(BASE) + list(TARGETS.values())
    summary = development[numeric_columns].describe().T.rename_axis("feature").reset_index()
    summary.insert(1, "unit", summary["feature"].map(UNITS))
    csv("development_summary", summary)

    candidates, rules = [], []
    for column in numeric_columns:
        observed = development[column].dropna()
        q1, q3 = observed.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        rules.append({"feature": column, "unit": UNITS[column], "observed_n": len(observed),
                      "q1": q1, "q3": q3, "iqr": iqr, "lower_fence": lower, "upper_fence": upper})
        flagged = development[column].notna() & ~development[column].between(lower, upper)
        for _, row in development.loc[flagged, ["배치ID", column]].iterrows():
            candidates.append({"batch_id": row["배치ID"], "split": "development", "feature": column,
                               "unit": UNITS[column], "value": row[column], "lower_fence": lower,
                               "upper_fence": upper, "action": "retain_for_review"})
    candidate_columns = ["batch_id", "split", "feature", "unit", "value", "lower_fence", "upper_fence", "action"]
    csv("outlier_candidates", pd.DataFrame(candidates, columns=candidate_columns))
    csv("outlier_rules", pd.DataFrame(rules))

    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(11, 6.2), layout="constrained")
        position = np.arange(len(BASE))
        ax.barh(position - .18, quality["development_missing"], height=.34, color="#236A83", label="Development (357 rows)")
        ax.barh(position + .18, quality["holdout_missing"], height=.34, color="#D9A441", label="Reserved segment (63 rows)")
        ax.set_yticks(position, quality["label"])
        ax.invert_yaxis()
        ax.set_xlabel("Missing cells after numeric/range cleaning")
        ax.set_title("Input missingness before imputation")
        fig.legend(loc="outside lower center", ncol=2, frameon=False)
        ax.grid(axis="x", alpha=.18)
        path = destination / "missing_counts.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths["missing_counts_plot"] = str(path)

        fig, axes = plt.subplots(4, 4, figsize=(14, 11.5), layout="constrained")
        for ax, column in zip(axes.flat, numeric_columns):
            observed = development[column].dropna()
            ax.hist(observed, bins=18, color="#236A83", edgecolor="white", linewidth=.5)
            ax.set_title(PLOT_LABELS[column], fontsize=10)
            ax.set_ylabel("Observed rows", fontsize=9)
            ax.text(.98, .95, f"n={len(observed)}", ha="right", va="top", transform=ax.transAxes, fontsize=9)
            ax.tick_params(labelsize=8)
        for ax in list(axes.flat)[len(numeric_columns):]:
            ax.set_visible(False)
        fig.suptitle("Development distributions | observed values only (357 batches)", fontsize=16)
        path = destination / "development_distributions.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths["development_distributions_plot"] = str(path)

        corr = development[numeric_columns].corr(min_periods=2)
        csv("development_correlation", corr.rename_axis("feature").reset_index())
        pair_n = development[numeric_columns].notna().astype(int).T @ development[numeric_columns].notna().astype(int)
        csv("correlation_pair_counts", pair_n.rename_axis("feature").reset_index())
        fig, ax = plt.subplots(figsize=(12.3, 10.5), layout="constrained")
        im = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
        short = ["Ni", "Co", "Li", "Mn", "Cu", "Fe", "Al", "Feed", "Acid", "Temp", "Time", "Ni rec.", "Co rec."]
        ax.set_xticks(range(len(short)), short, rotation=45, ha="right")
        ax.set_yticks(range(len(short)), short)
        for row in range(len(short)):
            for col in range(len(short)):
                value = corr.iloc[row, col]
                ax.text(col, row, f"{value:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if abs(value) > .6 else "#202020")
        ax.set_title("Development Pearson correlation\nPairwise observed values; association is not causation", pad=18)
        fig.colorbar(im, ax=ax, fraction=.045, pad=.04, label="Pearson r")
        path = destination / "development_correlation.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths["development_correlation_plot"] = str(path)
    return paths, len(candidates)


def run_preprocessing(data_path=None, output_dir=None):
    """Export clean splits, fitted development snapshots, state, and quality files.

    No fitting uses the reserved segment. Imputed/standardized development files
    describe one full-development fit and must not be supplied to cross-validation.
    """
    source = Path(data_path) if data_path is not None else DEFAULT_RAW_PATH
    destination = Path(output_dir) if output_dir is not None else ROOT / "data" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    raw = load_raw_data(source)
    cleaned, cleaning = _clean_frame(raw)
    split = int(len(cleaned) * .85)
    if split < 1 or split == len(cleaned):
        raise ValueError("Need enough cleaned rows for nonempty development and reserved segments.")
    development, holdout = cleaned.iloc[:split].copy(), cleaned.iloc[split:].copy()
    preprocessor = FoldPreprocessor("A17").fit(development)
    expanded = preprocessor.transform(development)
    imputed = development.copy()
    imputed.loc[:, list(BASE)] = expanded[:, :len(BASE)]
    scaler = StandardScaler().fit(expanded)
    standardized = scaler.transform(expanded)
    files = {}

    def csv(key, filename, table):
        path = destination / filename
        table.to_csv(path, index=False, encoding="utf-8-sig")
        files[key] = str(path)

    # Canonical names retain the published dataset counts; the audit records the
    # actual counts for an explicitly supplied replacement dataset.
    csv("cleaned", "cleaned420.csv", cleaned)
    csv("development", "development357.csv", development)
    csv("holdout", "holdout63.csv", holdout)
    csv("development_imputed", "development_imputed.csv", imputed)
    csv("development_features17", "development_features17.csv", pd.DataFrame(expanded, columns=feature_names("A17")))
    csv("development_standardized17", "development_standardized17.csv", pd.DataFrame(standardized, columns=feature_names("A17")))

    quality = pd.DataFrame(cleaning["input_quality"])
    for name, frame in (("raw_missing", raw), ("cleaned_missing", cleaned),
                        ("development_missing", development), ("holdout_missing", holdout)):
        quality[name] = [int(frame[column].isna().sum()) for column in BASE]
    quality["development_imputed"] = quality["development_missing"]
    quality_files, candidate_count = _quality_outputs(development, quality, destination / "quality")
    files.update(quality_files)

    state = {
        "fit_scope": "development only", "fit_rows": len(development),
        "fit_first_batch": development.iloc[0]["배치ID"], "fit_last_batch": development.iloc[-1]["배치ID"],
        "feature_mode": "A17", "base_feature_names": list(BASE), "minimum_grade_observed_count": 5,
        "global_median": preprocessor.global_median_.to_dict(),
        "grade_median": preprocessor.grade_median_.to_dict(orient="index"),
        "grade_count": preprocessor.grade_count_.to_dict(orient="index"),
        "imputed_cells_by_feature": dict(zip(BASE, quality["development_missing"].astype(int))),
        "target_imputation": False,
    }
    path = destination / "imputer_state.json"
    _write_json(path, state)
    files["imputer_state"] = str(path)
    path = destination / "scaler_state.json"
    _write_json(path, {"fit_scope": "development only", "fit_rows": len(development),
                      "feature_mode": "A17", "feature_names": feature_names("A17"),
                      "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                      "variance": scaler.var_.tolist(), "variance_ddof": 0})
    files["scaler_state"] = str(path)

    audit = {
        "source_filename": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_sheet": RAW_SHEET if source.suffix.lower() != ".csv" else None,
        "rows": {"raw": len(raw), "duplicates_removed": len(cleaning["duplicates_removed"]),
                 "cleaned": len(cleaned), "development": len(development), "holdout": len(holdout),
                 "development_complete_observed": int(development[list(BASE)].notna().all(axis=1).sum())},
        "columns": {"source": len(raw.columns), "base_inputs": len(BASE), "targets": len(TARGETS), "expanded": 17},
        "split": {"rule": "first floor(0.85*n) rows by numeric batch suffix", "development_first": development.iloc[0]["배치ID"],
                  "development_last": development.iloc[-1]["배치ID"], "holdout_first": holdout.iloc[0]["배치ID"],
                  "holdout_last": holdout.iloc[-1]["배치ID"], "calendar_chronology_verified": False},
        "duplicate_policy": "Normalize batch whitespace, retain first source occurrence, stable numeric-suffix sort",
        "removed_duplicate_batch_ids": cleaning["duplicates_removed"],
        "date_policy": "Preserve original analysis-date metadata without parsing; do not use for ordering or modeling",
        "limits": LIMITS, "input_quality": quality.to_dict(orient="records"),
        "missing_input_cells": {"cleaned": int(cleaned[list(BASE)].isna().sum().sum()),
                                "development": int(development[list(BASE)].isna().sum().sum()),
                                "holdout": int(holdout[list(BASE)].isna().sum().sum())},
        "development_imputed_cells": int(quality["development_imputed"].sum()),
        "targets": {"columns": TARGETS, "range": [0, 100], "missing": 0, "imputed": False},
        "iqr": {"fit_scope": "observed development values", "multiplier": 1.5,
                "candidate_cells": candidate_count, "rows_deleted": 0, "action": "retain_for_review"},
        "fit_scope": "development 85% only; no holdout medians or scaler fitting",
        "cv_input": "development357.csv (unfilled); fit FoldPreprocessor and StandardScaler inside each training fold",
        "snapshot_use": "Imputed/features/standardized exports describe a full-development fit only",
        "reserved_segment_status": "Previously inspected during the project; not a fresh blind test",
        "external_data_used": False,
        "field_inventory": "Batch ID, analysis date, raw-material grade, eleven numeric inputs, and two recovery targets. No names, contact, or security fields observed.",
    }
    path = destination / "audit.json"
    _write_json(path, audit)
    files["audit"] = str(path)
    return {"output_dir": str(destination), "files": files, "audit": audit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", type=Path, default=None, help="Optional original RAW .xlsx or .csv")
    parser.add_argument("--output-dir", type=Path, default=None, help="Default: repository data/processed")
    args = parser.parse_args()
    result = run_preprocessing(args.data_path, args.output_dir)
    print(json.dumps({"output_dir": result["output_dir"], "rows": result["audit"]["rows"],
                      "development_imputed_cells": result["audit"]["development_imputed_cells"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
