"""Original-input permutation importance and standardized curve17 coefficients."""
from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

from module1_preprocessing.features import feature_names
from module1_preprocessing.schema import BASE, TARGETS
from .training import (FEATURE_LABELS, SEED, compare_to_frozen, cross_validate,
                       fit_final_model, json_safe, load_development, model_inputs,
                       output_directory, protocol_metadata, write_json)

REPEATS = 10


def importance_figures(permutation, coefficients, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    label_map = dict(zip(feature_names("A17"), FEATURE_LABELS))
    colors = {"Ni": "#157F8C", "Co": "#C76D37"}
    files = {"permutation_plot": "permutation_importance.png", "coefficients_plot": "standardized_coefficients.png"}
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 5.8), constrained_layout=True)
    for ax, metal in zip(axes, TARGETS):
        rows = permutation[permutation.Metal == metal].sort_values("MeanDeltaMAE")
        ax.barh(np.arange(len(rows)), rows.MeanDeltaMAE, xerr=rows.StdDeltaMAE, color=colors[metal], alpha=.85,
                error_kw={"elinewidth": .9, "ecolor": "#314252", "capsize": 2})
        ax.set_yticks(np.arange(len(rows)), [label_map.get(f, f) for f in rows.Feature])
        ax.axvline(0, color="#5C6573", lw=.8)
        ax.set(title=metal, xlabel="Increase in validation MAE (pp)")
    fig.suptitle("Original 11 inputs: permutation importance\nMean +/- sample SD over 3 folds x 10 repeats; derived terms recomputed", fontsize=12)
    fig.savefig(output_dir / files["permutation_plot"], dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 7.6), constrained_layout=True)
    for ax, metal in zip(axes, TARGETS):
        rows = coefficients[coefficients.Metal == metal].iloc[::-1]
        values = rows.StandardizedCoefficient
        ax.barh(np.arange(len(rows)), values, color=[colors[metal] if v >= 0 else "#AEB8C3" for v in values])
        ax.set_yticks(np.arange(len(rows)), [label_map.get(f, f) for f in rows.Feature])
        ax.axvline(0, color="#5C6573", lw=.8)
        ax.set(title=metal, xlabel="Coefficient per 1 SD of model term (pp)")
    fig.suptitle("Full-development curve17 coefficients\nCorrelated polynomial terms: coefficients are not independent process effects", fontsize=12)
    fig.savefig(output_dir / files["coefficients_plot"], dpi=180)
    plt.close(fig)
    return files


def run_importance(data_path=None, output_dir=None) -> dict:
    """Permute raw input columns on outer validation; never refit on validation.

    Missing cells are shuffled along with observed values. Grade labels stay
    fixed. Each prediction reuses that outer model's imputer and scaler, then
    recomputes every square and product. No outer model is selected by importance.
    """
    out = output_directory(output_dir)
    dev = load_development(data_path)
    X = model_inputs(dev)
    run = cross_validate(dev, candidates=("curve17",))
    rng = np.random.default_rng(SEED)
    splits = list(TimeSeriesSplit(n_splits=3).split(X))
    # Identical permutations across features/metals within a fold make the
    # comparisons reproducible without treating the repeats as independent data.
    permutation_orders = {fold: [rng.permutation(len(va)) for _ in range(REPEATS)]
                          for fold, (_, va) in enumerate(splits, 1)}
    records = []
    for metal, target in TARGETS.items():
        y = dev[target].to_numpy(dtype=float)
        for fold, (_, va) in enumerate(splits, 1):
            fitted = run.fitted_models[(metal, "curve17", fold)]
            valid = X.iloc[va].copy()
            base_mae = float(mean_absolute_error(y[va], fitted.predict(valid)))
            for feature in BASE:
                original = valid[feature].to_numpy(copy=True)
                for repeat, order in enumerate(permutation_orders[fold], 1):
                    permuted = valid.copy()
                    permuted[feature] = original[order]
                    permuted_mae = float(mean_absolute_error(y[va], fitted.predict(permuted)))
                    records.append({"Metal": metal, "Feature": feature, "Fold": fold, "Repeat": repeat,
                                    "ValidN": len(va), "Alpha": fitted.alpha, "BaselineMAE": base_mae,
                                    "PermutedMAE": permuted_mae, "DeltaMAE": permuted_mae - base_mae,
                                    "MissingValuesPermuted": int(pd.isna(original).sum())})
    detail = pd.DataFrame(records)
    permutation = (detail.groupby(["Metal", "Feature"], sort=False).agg(
        MeanDeltaMAE=("DeltaMAE", "mean"), StdDeltaMAE=("DeltaMAE", "std"),
        BaselineMAE=("BaselineMAE", "mean"), Folds=("Fold", "nunique"), Repeats=("Repeat", "count")).reset_index())
    permutation["RepeatsPerFold"] = REPEATS
    by_fold = (detail.groupby(["Metal", "Feature", "Fold"], sort=False).agg(
        MeanDeltaMAE=("DeltaMAE", "mean"), StdDeltaMAE=("DeltaMAE", "std"), BaselineMAE=("BaselineMAE", "mean")).reset_index())
    state, models, histories, audit = fit_final_model(dev)
    comparison = compare_to_frozen(state, models, dev)
    coefficient_rows = []
    names = feature_names("A17")
    for metal, parameters in zip(TARGETS, state["parameters"]):
        for i, feature in enumerate(names):
            coefficient_rows.append({"Metal": metal, "Feature": feature, "FeatureIndex": i,
                                     "Mean": parameters[i], "Scale": parameters[17 + i],
                                     "StandardizedCoefficient": parameters[34 + i],
                                     "RawBasisCoefficient": parameters[34 + i] / parameters[17 + i],
                                     "SelectedAlpha": state["selected_alphas"][metal], "Intercept": parameters[51]})
    coefficients = pd.DataFrame(coefficient_rows)
    files = {"permutation_importance": "permutation_importance.csv", "permutation_details": "permutation_importance_details.csv",
             "permutation_by_fold": "permutation_importance_by_fold.csv", "coefficients": "standardized_coefficients.csv",
             "fit_audit": "importance_fit_audit.json", "tuning": "importance_tuning_results.csv",
             "comparison": "importance_refit_comparison.json", "summary": "importance_summary.json"}
    for key, frame in (("permutation_importance", permutation), ("permutation_details", detail),
                       ("permutation_by_fold", by_fold), ("coefficients", coefficients)):
        frame.to_csv(out / files[key], index=False)
    pd.concat([run.tuning_results, pd.DataFrame(histories)], ignore_index=True).to_csv(out / files["tuning"], index=False)
    write_json(out / files["fit_audit"], {"outer_validation": run.audit.as_dict(), "final_coefficients": audit.as_dict()})
    write_json(out / files["comparison"], comparison)
    files.update(importance_figures(permutation, coefficients, out))
    notes = [
        "MeanDeltaMAE is the increase in original-unit outer-validation MAE after shuffling one original input; greater positive values indicate stronger dependence in this fitted prediction pipeline.",
        "Each raw-column permutation recomputes derived squares/products using the outer training imputer/scaler. The grade label is held fixed; missing cells travel with the permuted column.",
        "StdDeltaMAE is sample SD (ddof=1) over 30 fold/repeat deltas, not a confidence interval. Outer training slices overlap and repeat errors are dependent.",
        "Correlated raw inputs can substitute for one another, so small importance does not establish that an input is unnecessary. Shuffling can create unsupported combinations even when marginal input ranges are valid; no distance or feasibility filter is applied to these diagnostic permutations.",
        "The 17 standardized coefficients are ridge weights on centered/scaled model terms; the model uses 11 raw inputs. Squared and interaction terms are correlated. Their signs and magnitudes are not independent causal effects or evidence that a process change will improve plant recovery.",
        "RawBasisCoefficient is coefficient/feature_scale for that basis term, not a derivative of the full model with respect to the original input. Intercept is the standardized-basis intercept.",
        "Importance does not change candidate choice, the optimization objective, or any Ni/Co target floor. No new validation labels or reserved holdout batches were used.",
    ]
    summary = {**protocol_metadata(dev), "candidate": "curve17", "permutation_seed": SEED, "repeats_per_fold": REPEATS,
               "importance_rows": len(permutation), "permutation_detail_rows": len(detail), "coefficient_rows": len(coefficients),
               "pipeline_fit_count": len(run.audit.fits) + len(audit.fits), "selected_final_alphas": state["selected_alphas"],
               "permutation_importance": permutation.to_dict(orient="records"), "coefficient_refit_comparison": comparison,
               "interpretation": notes, "files": files}
    write_json(out / files["summary"], summary)
    return {"output_dir": str(out), "files": files, "permutation_importance": summary["permutation_importance"],
            "coefficient_rows": len(coefficients), "comparison": comparison}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=None, help="RAW workbook path; defaults to bundled RAW")
    parser.add_argument("--output-dir", default=None, help="Result directory; default module2_prediction/results")
    args = parser.parse_args(argv)
    result = run_importance(args.data, args.output_dir)
    print(json.dumps(json_safe(result), ensure_ascii=False, indent=2, allow_nan=False))
    return result


if __name__ == "__main__":
    main()
