"""Nested chronological validation of the five archived learning candidates."""
from __future__ import annotations

import argparse
import json

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_regression(y_true, y_pred, prefix: str = "Test") -> dict:
    """Return the original team project regression metrics with prefixed keys."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    metrics = {
        f"{prefix}_RMSE": float(rmse),
        f"{prefix}_MAE": float(mae),
        f"{prefix}_R2": float(r2)
    }

    print(f"[{prefix} Evaluation]")
    print(f"  - RMSE: {rmse:.4f}")
    print(f"  - MAE : {mae:.4f}")
    print(f"  - R²  : {r2:.4f}")

    return metrics


def evaluation_figures(run, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from .training import CANDIDATES

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    colors = {"Ni": "#157F8C", "Co": "#C76D37"}
    files = {"predicted_vs_actual": "predicted_vs_actual.png", "residuals": "residuals.png", "mae_comparison": "model_mae_comparison.png"}
    curve = run.oof_predictions[run.oof_predictions.Candidate == "curve17"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4), constrained_layout=True)
    for ax, metal in zip(axes, ("Ni", "Co")):
        rows = curve[curve.Metal == metal]
        ax.scatter(rows.Actual, rows.Predicted, color=colors[metal], alpha=.62, s=22, edgecolors="none")
        lo, hi = min(rows.Actual.min(), rows.Predicted.min()) - 1, max(rows.Actual.max(), rows.Predicted.max()) + 1
        ax.plot([lo, hi], [lo, hi], color="#5C6573", lw=1, ls="--")
        score = run.metrics[(run.metrics.Metal == metal) & (run.metrics.Candidate == "curve17")].iloc[0]
        ax.set(xlabel="Observed recovery (%)", ylabel="OOF predicted recovery (%)", title=f"{metal} | MAE {score.MAE:.3f} pp", xlim=(lo, hi), ylim=(lo, hi))
        ax.grid(alpha=.15)
    fig.suptitle("Curve17: chronological out-of-fold predictions (267 batches)", fontsize=13)
    fig.savefig(output_dir / files["predicted_vs_actual"], dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(10.4, 6.8), constrained_layout=True)
    for col, metal in enumerate(("Ni", "Co")):
        rows = curve[curve.Metal == metal].sort_values("RowIndex")
        axes[0, col].scatter(rows.RowIndex + 1, rows.Residual, s=15, color=colors[metal], alpha=.7)
        axes[0, col].axhline(0, color="#5C6573", lw=1)
        for boundary in (179.5, 268.5):
            axes[0, col].axvline(boundary, color="#5C6573", ls=":", lw=.8)
        axes[0, col].set(title=metal, xlabel="Ordered development batch", ylabel="Prediction - observation (pp)")
        axes[1, col].hist(rows.Residual, bins=22, color=colors[metal], alpha=.8)
        axes[1, col].axvline(0, color="#5C6573", lw=1)
        axes[1, col].set(xlabel="Prediction - observation (pp)", ylabel="Batch count")
    fig.suptitle("Curve17 residuals | outer validation only", fontsize=13)
    fig.savefig(output_dir / files["residuals"], dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    labels = {"baseline": "Fixed baseline", "ridge11": "Ridge 11", "curve17": "Curve 17", "bounded17": "Bounded 17", "interaction20": "Interaction 20"}
    for ax, metal in zip(axes, ("Ni", "Co")):
        rows = run.metrics[run.metrics.Metal == metal].set_index("Candidate").loc[list(CANDIDATES)]
        bars = ax.bar(np.arange(len(CANDIDATES)), rows.MAE, color=[colors[metal] if c == "curve17" else "#AEB8C3" for c in CANDIDATES])
        for i, candidate in enumerate(CANDIDATES):
            fold_mae = run.fold_metrics[(run.fold_metrics.Metal == metal) & (run.fold_metrics.Candidate == candidate)].MAE
            ax.scatter(np.full(len(fold_mae), i), fold_mae, marker="_", color="#263342", s=85, zorder=3)
            ax.text(i, max(float(rows.loc[candidate, "MAE"]), float(fold_mae.max())) + .045,
                    f"{rows.loc[candidate, 'MAE']:.3f}", ha="center", va="bottom", fontsize=9)
        ax.set_xticks(np.arange(len(CANDIDATES)), [labels[c] for c in CANDIDATES], rotation=25, ha="right")
        ax.set(title=metal, ylabel="MAE (percentage points)", ylim=(0, run.fold_metrics.MAE.max() * 1.22))
    fig.suptitle("Pooled MAE; short marks show the three outer-fold MAEs", fontsize=13)
    fig.savefig(output_dir / files["mae_comparison"], dpi=180)
    plt.close(fig)
    return files


def evaluate_models(data_path=None, output_dir=None) -> dict:
    """Write real OOF predictions, nested tuning records, metrics, and figures."""
    from .training import (
        classification_table, compare_to_archived, cross_validate, load_development,
        output_directory, protocol_metadata, write_json,
    )

    out = output_directory(output_dir)
    dev = load_development(data_path)
    run = cross_validate(dev)
    classifications = classification_table(run.oof_predictions)
    reproduction = compare_to_archived(run, classifications)
    files = {"metrics": "metrics.csv", "fold_metrics": "fold_metrics.csv", "oof_predictions": "oof_predictions.csv",
             "tuning": "tuning_results.csv", "target_classification": "target_classification.csv",
             "fit_audit": "evaluation_fit_audit.json", "reproduction": "evaluation_reproduction.json", "summary": "evaluation_summary.json"}
    for key, frame in (("metrics", run.metrics), ("fold_metrics", run.fold_metrics), ("oof_predictions", run.oof_predictions),
                       ("tuning", run.tuning_results), ("target_classification", classifications)):
        frame.to_csv(out / files[key], index=False)
    write_json(out / files["fit_audit"], run.audit.as_dict())
    write_json(out / files["reproduction"], reproduction)
    files.update(evaluation_figures(run, out))
    summary = {**protocol_metadata(dev), "pipeline_fit_count": len(run.audit.fits), "oof_rows_per_metal_candidate": 267,
               "oof_predictions_rows": len(run.oof_predictions), "metrics": run.metrics.to_dict(orient="records"),
               "target_classification": classifications.to_dict(orient="records"), "reproduction": reproduction, "files": files,
               "interpretation": "Regression errors are in recovery percentage points. Target classification is descriptive at observed validation conditions; it does not validate optimized recipes. Last 63 batches remain excluded."}
    write_json(out / files["summary"], summary)
    return {"output_dir": str(out), "files": files, "metrics": summary["metrics"], "reproduction": reproduction}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=None, help="RAW workbook path; defaults to bundled RAW")
    parser.add_argument("--output-dir", default=None, help="Result directory; default module2_prediction/results")
    args = parser.parse_args(argv)
    from .training import json_safe

    result = evaluate_models(args.data, args.output_dir)
    brief = {**result, "reproduction": {k: v for k, v in result["reproduction"].items() if k != "differences"}}
    print(json.dumps(json_safe(brief), ensure_ascii=False, indent=2, allow_nan=False))
    return result


if __name__ == "__main__":
    main()
