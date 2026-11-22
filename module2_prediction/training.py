"""Reproduce the archived development-only Youngpoong learning protocol.

Inference never imports this module. Every fit starts with the unfilled CLEAN
inputs and owns its imputer and scaler. The final 63 batches are never selected,
fit, tuned, predicted, or scored here.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import hashlib
import json
import platform
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from module1_preprocessing.features import feature_matrix
from module1_preprocessing.pipeline import FoldPreprocessor, load_clean_data
from module1_preprocessing.schema import BASE, PROCESS, TARGETS

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results"
REFERENCE_PATH = Path(__file__).resolve().parent / "reference" / "model_comparison_reference.json"
FROZEN_PATH = Path(__file__).resolve().parent / "artifacts" / "frozen_model.json"
DEVELOPMENT_ROWS = 357
DATASET_ROWS = 420
SEED = 42
ALPHAS = (0.1, 1.0, 10.0, 100.0)
CANDIDATES = ("baseline", "ridge11", "curve17", "bounded17", "interaction20")
CANDIDATE_MODES = {"ridge11": "A11", "curve17": "A17", "bounded17": "A17", "interaction20": "A20"}
BASELINE_WEIGHTS = np.array([0.3366978614608818, 0.3365960332725443, 0.3267061052665740])
MODEL_VERSION = "YP-curve17-dev357-v2"
REPRODUCTION_ATOL = 1e-8
FEATURE_LABELS = (
    "Ni content", "Co content", "Li content", "Mn content", "Cu impurity",
    "Fe impurity", "Al impurity", "Feed mass", "Sulfuric acid", "Temperature", "Time",
    "Acid squared", "Temperature squared", "Time squared", "Acid x temperature",
    "Acid x time", "Temperature x time",
)


def json_safe(value: Any) -> Any:
    """Convert NumPy/pandas values; strict JSON uses null for unavailable values."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if value is pd.NA:
        return None
    if isinstance(value, Path):
        return value.name
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def output_directory(output_dir=None) -> Path:
    result = DEFAULT_OUTPUT if output_dir is None else Path(output_dir).expanduser().resolve()
    result.mkdir(parents=True, exist_ok=True)
    return result


def environment_versions() -> dict:
    result = {"python": platform.python_version(), "platform": platform.platform()}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "openpyxl", "matplotlib"):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result


def load_development(data_path=None) -> pd.DataFrame:
    """Load RAW/clean input through module 1, then isolate the first 357 rows."""
    clean = load_clean_data(data_path)
    if len(clean) != DATASET_ROWS:
        raise ValueError(f"Archived protocol requires {DATASET_ROWS} unique ordered rows; got {len(clean)}.")
    if "배치ID" not in clean or clean["배치ID"].duplicated().any():
        raise ValueError("Expected unique batch identifiers after module 1 cleaning.")
    # Do not expose holdout targets to any fit, hyperparameter choice, or score.
    dev = clean.iloc[:DEVELOPMENT_ROWS].copy().reset_index(drop=True)
    for target in TARGETS.values():
        values = dev[target].to_numpy(dtype=float)
        if not np.isfinite(values).all() or ((values < 0) | (values > 100)).any():
            raise ValueError(f"Development labels must be finite percentages: {target}")
    return dev


def model_inputs(dev: pd.DataFrame) -> pd.DataFrame:
    return dev[[*BASE, "원료등급"]].copy()


def development_fingerprint(dev: pd.DataFrame) -> str:
    columns = ["배치ID", "원료등급", *BASE, *TARGETS.values()]
    # A stable representation also records which cells remain missing before CV.
    payload = dev[columns].to_csv(index=False, float_format="%.17g", na_rep="<NA>").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def protocol_metadata(dev: pd.DataFrame) -> dict:
    return {
        "development_rows": DEVELOPMENT_ROWS,
        "development_first_batch": str(dev.iloc[0]["배치ID"]),
        "development_last_batch": str(dev.iloc[-1]["배치ID"]),
        "development_sha256": development_fingerprint(dev),
        "holdout_rows_excluded": DATASET_ROWS - DEVELOPMENT_ROWS,
        "holdout_used_for_fit_tune_predict_or_score": False,
        "outer_splits": [{"fold": i, "train_rows": len(tr), "valid_rows": len(va)} for i, (tr, va) in enumerate(TimeSeriesSplit(3).split(dev), 1)],
        "inner_splits": 3,
        "ordering": "Numeric batch-ID suffix; calendar-time order has not been independently verified.",
        "alpha_grid": list(ALPHAS),
        "tuning_metric": "pooled validation MAE in original recovery percentage points",
        "imputation": "Original grade-conditional chemical medians when training count >= 5; training global median fallback; process training global medians.",
        "imputation_and_scaling_fit_scope": "each individual inner or outer training slice only",
        "bounded_target": "logit(y/100); eps=1e-5 at exact 0/100 endpoints; inverse=100*sigmoid",
        "baseline_Ni_members": [
            {"estimator": "ElasticNet", "mode": "A", "alpha": 0.1, "l1_ratio": 0.8, "max_iter": 20000, "random_state": SEED},
            {"estimator": "Ridge", "mode": "B_Impurity", "alpha": 1.0},
            {"estimator": "SVR", "mode": "B_Impurity", "C": 10.0, "epsilon": 0.1, "gamma": "scale", "kernel": "rbf"},
        ],
        "baseline_Ni_weights": BASELINE_WEIGHTS.tolist(),
        "baseline_Co": {"estimator": "Ridge", "mode": "A", "alpha": 0.1},
        "candidates": list(CANDIDATES),
        "selection_excludes": ["different answers between recommendation modes", "predicted target success count"],
        "scope": "Reproduction on previously reused development data; no new independent validation or plant approval.",
        "environment": environment_versions(),
    }


class FitAudit:
    """Deduplicate actual fitted imputer states while recording every pipeline fit."""

    def __init__(self):
        self.imputation_states: dict[str, dict] = {}
        self.fits: list[dict] = []

    def record(self, pipe: Pipeline, X: pd.DataFrame, context: dict) -> str:
        pre = pipe.named_steps["preprocess"]
        state = json_safe({
            "global_median": pre.global_median_.to_dict(),
            "grade_median": pre.grade_median_.to_dict(orient="index"),
            "grade_count": pre.grade_count_.to_dict(orient="index"),
        })
        digest = hashlib.sha256(json.dumps(state, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()
        self.imputation_states[digest] = state
        self.fits.append({**context, "fit_rows": len(X), "first_row_index": int(X.index[0]),
                          "last_row_index": int(X.index[-1]), "feature_mode": pre.feature_mode,
                          "imputation_state_sha256": digest,
                          "scaler_mean": pipe.named_steps["scaler"].mean_.tolist(),
                          "scaler_scale": pipe.named_steps["scaler"].scale_.tolist()})
        return digest

    def as_dict(self) -> dict:
        return {"pipeline_fit_count": len(self.fits), "distinct_imputation_states": len(self.imputation_states),
                "imputation_states": self.imputation_states, "fits": self.fits}


def target_logit(y: np.ndarray) -> np.ndarray:
    q = np.asarray(y, dtype=float) / 100.0
    if not np.isfinite(q).all() or ((q < 0) | (q > 1)).any():
        raise ValueError("Logit training labels must be in [0,100].")
    q = q.copy()
    q[q == 0] = 1e-5
    q[q == 1] = 1 - 1e-5
    return np.log(q / (1 - q))


@dataclass
class FittedCandidate:
    candidate: str
    metal: str
    alpha: float | None
    pipelines: tuple[Pipeline, ...]
    weights: np.ndarray
    bounded: bool = False

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        predictions = np.column_stack([pipe.predict(X) for pipe in self.pipelines])
        result = predictions @ self.weights
        return 100.0 * expit(result) if self.bounded else result


def fit_candidate(X: pd.DataFrame, y: np.ndarray, candidate: str, metal: str,
                  alpha: float | None = None, audit: FitAudit | None = None,
                  context: dict | None = None) -> FittedCandidate:
    if candidate not in CANDIDATES or metal not in TARGETS:
        raise ValueError("Unknown candidate or metal.")
    if candidate == "baseline":
        if metal == "Ni":
            specs = [("A", ElasticNet(alpha=0.1, l1_ratio=0.8, max_iter=20000, random_state=SEED)),
                     ("B_Impurity", Ridge(alpha=1.0)),
                     ("B_Impurity", SVR(C=10.0, epsilon=0.1, gamma="scale", kernel="rbf"))]
            weights = BASELINE_WEIGHTS.copy()
        else:
            specs, weights = [("A", Ridge(alpha=0.1))], np.ones(1)
    else:
        if alpha not in ALPHAS:
            raise ValueError("A predeclared Ridge alpha is required.")
        specs, weights = [(CANDIDATE_MODES[candidate], Ridge(alpha=alpha))], np.ones(1)
    bounded = candidate == "bounded17"
    labels = target_logit(y) if bounded else np.asarray(y, dtype=float)
    pipes = []
    for member, (mode, estimator) in enumerate(specs, 1):
        pipe = Pipeline([("preprocess", FoldPreprocessor(feature_mode=mode)),
                         ("scaler", StandardScaler()), ("model", estimator)])
        pipe.fit(X, labels)
        pipes.append(pipe)
        if audit is not None:
            audit.record(pipe, X, {**(context or {}), "Metal": metal, "Candidate": candidate, "Alpha": alpha, "Member": member})
    return FittedCandidate(candidate, metal, alpha, tuple(pipes), weights, bounded)


def tune_alpha(X: pd.DataFrame, y: np.ndarray, candidate: str, metal: str,
               audit: FitAudit | None = None, scope="outer", outer_fold=0) -> tuple[float, list[dict]]:
    if candidate == "baseline":
        raise ValueError("The archived baseline is fixed, not retuned.")
    splits = list(TimeSeriesSplit(n_splits=3).split(X))
    records, errors_by_alpha = [], {}
    for alpha in ALPHAS:
        errors = []
        alpha_records = []
        for inner_fold, (tr, va) in enumerate(splits, 1):
            context = {"Scope": scope, "OuterFold": outer_fold, "InnerFold": inner_fold}
            fitted = fit_candidate(X.iloc[tr], y[tr], candidate, metal, alpha, audit, context)
            prediction = fitted.predict(X.iloc[va])
            absolute_errors = np.abs(y[va] - prediction)
            errors.extend(absolute_errors.tolist())
            alpha_records.append({**context, "Metal": metal, "Candidate": candidate, "Alpha": alpha,
                                  "TrainN": len(tr), "ValidN": len(va), "MAE": float(absolute_errors.mean())})
        errors_by_alpha[alpha] = float(np.mean(errors))
        records.extend({**row, "PooledInnerMAE": errors_by_alpha[alpha]} for row in alpha_records)
    # Python's stable min preserves the declared alpha order for an exact tie.
    selected = min(ALPHAS, key=lambda alpha: errors_by_alpha[alpha])
    for row in records:
        row["Selected"] = row["Alpha"] == selected
        row["SelectedAlpha"] = selected
    return selected, records


def regression_scores(y, prediction) -> dict:
    y, prediction = np.asarray(y, float), np.asarray(prediction, float)
    residual = prediction - y
    absolute = np.abs(residual)
    return {"N": len(y), "MAE": float(mean_absolute_error(y, prediction)),
            "RMSE": float(np.sqrt(mean_squared_error(y, prediction))), "R2": float(r2_score(y, prediction)),
            "P90_abs": float(np.quantile(absolute, 0.9)), "Max_abs": float(absolute.max()),
            "Bias": float(residual.mean()), "InvalidOutputN": int((~np.isfinite(prediction) | (prediction < 0) | (prediction > 100)).sum())}


@dataclass
class EvaluationRun:
    development: pd.DataFrame
    metrics: pd.DataFrame
    fold_metrics: pd.DataFrame
    oof_predictions: pd.DataFrame
    tuning_results: pd.DataFrame
    fitted_models: dict
    audit: FitAudit


def cross_validate(dev: pd.DataFrame, candidates=CANDIDATES) -> EvaluationRun:
    """Evaluate predeclared candidates; outer predictions never influence tuning."""
    X = model_inputs(dev)
    audit, fold_rows, oof_rows, tuning_rows, fitted_models = FitAudit(), [], [], [], {}
    outer = list(TimeSeriesSplit(n_splits=3).split(X))
    complete = dev[list(BASE)].notna().all(axis=1).to_numpy()
    process_complete = dev[list(PROCESS)].notna().all(axis=1).to_numpy()
    for metal, target in TARGETS.items():
        y = dev[target].to_numpy(dtype=float)
        for fold, (tr, va) in enumerate(outer, 1):
            for candidate in candidates:
                alpha = None
                if candidate != "baseline":
                    alpha, history = tune_alpha(X.iloc[tr], y[tr], candidate, metal, audit, "outer", fold)
                    tuning_rows.extend(history)
                fitted = fit_candidate(X.iloc[tr], y[tr], candidate, metal, alpha, audit,
                                       {"Scope": "outer_refit", "OuterFold": fold, "InnerFold": None})
                fitted_models[(metal, candidate, fold)] = fitted
                prediction, train_prediction = fitted.predict(X.iloc[va]), fitted.predict(X.iloc[tr])
                scores, train_scores = regression_scores(y[va], prediction), regression_scores(y[tr], train_prediction)
                fold_rows.append({"Metal": metal, "Candidate": candidate, "Fold": fold, "TrainN": len(tr), "ValidN": len(va),
                                  "Alpha": alpha, **scores, "TrainMAE": train_scores["MAE"], "TrainRMSE": train_scores["RMSE"],
                                  "TrainR2": train_scores["R2"], "MAE_gap": scores["MAE"] - train_scores["MAE"]})
                for idx, actual, predicted in zip(va, y[va], prediction):
                    oof_rows.append({"Metal": metal, "Candidate": candidate, "Fold": fold, "RowIndex": int(idx),
                                     "BatchID": str(dev.iloc[idx]["배치ID"]), "Actual": float(actual), "Predicted": float(predicted),
                                     "Residual": float(predicted - actual), "AbsoluteError": float(abs(predicted - actual)),
                                     "CompleteInputs": bool(complete[idx]), "ProcessComplete": bool(process_complete[idx])})
    folds, oof = pd.DataFrame(fold_rows), pd.DataFrame(oof_rows)
    summary = []
    for metal in TARGETS:
        for candidate in candidates:
            predictions = oof[(oof.Metal == metal) & (oof.Candidate == candidate)]
            detail = folds[(folds.Metal == metal) & (folds.Candidate == candidate)]
            summary.append({"Metal": metal, "Candidate": candidate, **regression_scores(predictions.Actual, predictions.Predicted),
                            "MeanFoldMAE": float(detail.MAE.mean()), "StdFoldMAE": float(detail.MAE.std(ddof=1)),
                            "MeanTrainMAE": float(detail.TrainMAE.mean()), "MeanGap": float(detail.MAE_gap.mean())})
    return EvaluationRun(dev, pd.DataFrame(summary), folds, oof, pd.DataFrame(tuning_rows), fitted_models, audit)


def classification_table(oof: pd.DataFrame) -> pd.DataFrame:
    """Descriptive threshold decisions on observed OOF batches, not recipe success."""
    curve = oof[oof.Candidate == "curve17"]
    ni = curve[curve.Metal == "Ni"].set_index("RowIndex").sort_index()
    co = curve[curve.Metal == "Co"].set_index("RowIndex").sort_index()
    if not ni.index.equals(co.index):
        raise ValueError("Ni and Co OOF rows must align for joint classification.")
    rows = []
    populations = {"all": np.ones(len(ni), bool), "complete": ni.CompleteInputs.to_numpy(bool),
                   "process_complete": ni.ProcessComplete.to_numpy(bool)}
    actual_ni, actual_co = ni.Actual.to_numpy() >= 95, co.Actual.to_numpy() >= 90
    pred_ni, pred_co = ni.Predicted.to_numpy() >= 95, co.Predicted.to_numpy() >= 90
    targets = {"Ni": (actual_ni, pred_ni), "Co": (actual_co, pred_co),
               "joint": (actual_ni & actual_co, pred_ni & pred_co)}
    for population, mask in populations.items():
        for target, (actual_all, pred_all) in targets.items():
            actual, pred = actual_all[mask], pred_all[mask]
            tp, fp = int((actual & pred).sum()), int((~actual & pred).sum())
            fn, tn = int((actual & ~pred).sum()), int((~actual & ~pred).sum())
            rows.append({"population": population, "target": target, "N": len(actual), "TP": tp, "FP": fp, "FN": fn, "TN": tn,
                         "predicted_pass": tp + fp, "actual_pass": tp + fn, "precision": tp / (tp + fp) if tp + fp else None,
                         "recall": tp / (tp + fn) if tp + fn else None, "Ni_threshold": 95, "Co_threshold": 90})
    return pd.DataFrame(rows)


def compare_to_archived(run: EvaluationRun, classification: pd.DataFrame) -> dict:
    if not REFERENCE_PATH.exists():
        return {"status": "reference_unavailable", "reference": str(REFERENCE_PATH.relative_to(PACKAGE_ROOT))}
    archived = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    reference_summary = archived.get("summary", [])
    reference_folds = archived.get("folds", [])
    differences, alpha_mismatches, missing_reference_rows = [], [], []
    fields = ("MAE", "RMSE", "R2", "P90_abs", "Max_abs", "Bias")
    for kind, current, reference, keys in (
        ("pooled", run.metrics, reference_summary, ("Metal", "Candidate")),
        ("fold", run.fold_metrics, reference_folds, ("Metal", "Candidate", "Fold")),
    ):
        lookup = {tuple(r[k] for k in keys): r for r in reference}
        for row in current.to_dict(orient="records"):
            ref = lookup.get(tuple(row[k] for k in keys))
            if ref is None:
                missing_reference_rows.append({"scope": kind, **{k: row[k] for k in keys}})
                continue
            for metric in fields + (("TrainMAE", "MAE_gap") if kind == "fold" else ()):
                differences.append({"scope": kind, **{k: row[k] for k in keys}, "metric": metric,
                                    "current": row[metric], "archived": ref[metric], "absolute_difference": abs(row[metric] - ref[metric])})
            if kind == "fold":
                current_alpha = None if pd.isna(row["Alpha"]) else row["Alpha"]
                if current_alpha != ref.get("Alpha"):
                    alpha_mismatches.append({**{k: row[k] for k in keys}, "current": current_alpha, "archived": ref.get("Alpha")})
    count_errors = []
    class_ref = archived.get("target_validation", [])
    class_lookup = {(r["population"], r["target"]): r for r in class_ref}
    for row in classification.to_dict(orient="records"):
        ref = class_lookup.get((row["population"], row["target"]))
        if ref:
            for field in ("N", "TP", "FP", "FN", "TN", "predicted_pass", "actual_pass"):
                if row[field] != ref[field]:
                    count_errors.append({"population": row["population"], "target": row["target"], "field": field, "current": row[field], "archived": ref[field]})
    maximum = max((r["absolute_difference"] for r in differences), default=None)
    passed = (maximum is not None and maximum <= REPRODUCTION_ATOL and not alpha_mismatches
              and not count_errors and not missing_reference_rows and len(class_ref) == len(classification))
    return {"status": "within_numeric_tolerance" if passed else "discrepancy_requires_review", "absolute_tolerance": REPRODUCTION_ATOL,
            "metric_comparisons": len(differences), "max_absolute_metric_difference": maximum,
            "alpha_mismatches": alpha_mismatches, "missing_reference_rows": missing_reference_rows,
            "classification_count_mismatches": count_errors,
            "classification_reference_rows": len(class_ref), "differences": differences,
            "archived_environment": archived.get("environment"), "current_environment": environment_versions(),
            "interpretation": "Numeric agreement is a development-data reproduction check, not fresh predictive validation or a claim of identical runtime floating point arithmetic."}


def fit_final_model(dev: pd.DataFrame) -> tuple[dict, dict, list[dict], FitAudit]:
    X, models, histories, audit = model_inputs(dev), {}, [], FitAudit()
    selected = {}
    parameters = []
    for metal, target in TARGETS.items():
        y = dev[target].to_numpy(dtype=float)
        alpha, history = tune_alpha(X, y, "curve17", metal, audit, "full_development", 0)
        histories.extend(history)
        fitted = fit_candidate(X, y, "curve17", metal, alpha, audit,
                               {"Scope": "full_development_refit", "OuterFold": None, "InnerFold": None})
        models[metal], selected[metal] = fitted, alpha
        pipe = fitted.pipelines[0]
        scaler, estimator = pipe.named_steps["scaler"], pipe.named_steps["model"]
        parameters.append(np.r_[scaler.mean_, scaler.scale_, estimator.coef_, estimator.intercept_].tolist())
    complete = dev.loc[dev[list(BASE)].notna().all(axis=1), list(BASE)].to_numpy(dtype=float)
    if len(complete) != 151:
        raise ValueError(f"Archived distance reference requires 151 complete development rows, got {len(complete)}.")
    distance_scaler = StandardScaler().fit(complete)
    z = distance_scaler.transform(complete)
    distances = np.sqrt(np.square(z[:, None, :] - z[None, :, :]).sum(axis=2))
    np.fill_diagonal(distances, np.inf)
    threshold = float(np.quantile(distances.min(axis=1), 0.95))
    state = {"model_version": MODEL_VERSION, "fit_rows": DEVELOPMENT_ROWS, "features": list(BASE),
             "parameters": parameters, "distance_mean": distance_scaler.mean_.tolist(), "distance_scale": distance_scaler.scale_.tolist(),
             "distance_points": complete.tolist(), "distance_threshold": threshold, "selected_alphas": selected}
    return state, models, histories, audit


def predict_numeric_state(state: dict, values: np.ndarray) -> np.ndarray:
    z = feature_matrix(np.asarray(values, dtype=float), mode="A17")
    parameters = np.asarray(state["parameters"], dtype=float)
    return np.column_stack([((z - p[:17]) / p[17:34]) @ p[34:51] + p[51] for p in parameters])


def compare_to_frozen(state: dict, models: dict, dev: pd.DataFrame) -> dict:
    if not FROZEN_PATH.exists():
        return {"status": "frozen_reference_unavailable", "reference": "artifacts/frozen_model.json"}
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    differences = {}
    for field in ("parameters", "distance_mean", "distance_scale", "distance_points", "distance_threshold"):
        current, reference = np.asarray(state[field], float), np.asarray(frozen[field], float)
        differences[field] = float(np.max(np.abs(current - reference))) if current.shape == reference.shape else None
    parameter_difference = np.abs(np.asarray(state["parameters"], float) - np.asarray(frozen["parameters"], float))
    parameter_components = {metal: {"mean": float(parameter_difference[i, :17].max()),
                                   "scale": float(parameter_difference[i, 17:34].max()),
                                   "coefficient": float(parameter_difference[i, 34:51].max()),
                                   "intercept": float(parameter_difference[i, 51])}
                            for i, metal in enumerate(TARGETS)}
    X = model_inputs(dev)
    # Exported numeric state has no imputer: compare on the full-development
    # imputer's 357 filled rows and separately on the 151 originally complete rows.
    filled = FoldPreprocessor(feature_mode="A11").fit_transform(X)
    complete = dev.loc[dev[list(BASE)].notna().all(axis=1), list(BASE)].to_numpy(float)
    pipeline_prediction = np.column_stack([models[metal].predict(X) for metal in TARGETS])
    numeric_prediction = predict_numeric_state(state, filled)
    comparison_sets = {"development_imputed357": filled, "development_raw_complete151": complete}
    low_high = np.array([(8, 30), (2, 15), (2, 6), (5, 16), (.3, 6), (.2, 6), (.5, 7), (80, 200), (400, 1500), (40, 95), (1, 8)], float)
    rng = np.random.default_rng(SEED)
    generated = rng.uniform(low_high[:, 0], low_high[:, 1], size=(1000, 11))
    comparison_sets["synthetic_in_range1000"] = generated
    prediction_differences = {name: {metal: float(np.max(np.abs(predict_numeric_state(state, values)[:, i] - predict_numeric_state(frozen, values)[:, i])))
                                   for i, metal in enumerate(TARGETS)} for name, values in comparison_sets.items()}
    max_numeric = max(v for v in differences.values() if v is not None)
    pipeline_difference = float(np.max(np.abs(pipeline_prediction - numeric_prediction)))
    maximum_prediction = max(v for group in prediction_differences.values() for v in group.values())
    passed = (all(v is not None for v in differences.values()) and max_numeric <= REPRODUCTION_ATOL
              and maximum_prediction <= REPRODUCTION_ATOL and pipeline_difference <= REPRODUCTION_ATOL)
    return {"status": "within_numeric_tolerance" if passed else "discrepancy_requires_review", "absolute_tolerance": REPRODUCTION_ATOL,
            "state_max_absolute_differences": differences, "parameter_component_differences": parameter_components,
            "max_state_difference": max_numeric,
            "prediction_max_absolute_differences": prediction_differences, "max_prediction_difference": maximum_prediction,
            "pipeline_vs_export_max_absolute_difference": pipeline_difference,
            "selected_alphas": state["selected_alphas"], "frozen_model_sha256": hashlib.sha256(FROZEN_PATH.read_bytes()).hexdigest(),
            "comparison_rows": {key: len(values) for key, values in comparison_sets.items()},
            "synthetic_input_note": "Synthetic inputs check only numerical serialization; they are not independent labeled validation.",
            "interpretation": "Frozen production values are not overwritten. Last-bit differences may depend on numerical library versions and matrix layout."}
