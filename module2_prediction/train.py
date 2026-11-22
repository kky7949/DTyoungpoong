"""CLI and Python wrapper for a separate, reproducible full-development refit."""
from __future__ import annotations

import argparse
import json
import pandas as pd

from .training import (compare_to_frozen, fit_final_model, json_safe,
                       load_development, output_directory, protocol_metadata, write_json)


def train_final(data_path=None, output_dir=None) -> dict:
    """Tune curve17 on development CV, refit 357 rows, and save a separate model.

    Returns output_dir plus portable filenames. The frozen inference artifact is
    never updated. The 63 reserved batches are never fit, tuned, or scored.
    """
    out = output_directory(output_dir)
    dev = load_development(data_path)
    state, models, histories, audit = fit_final_model(dev)
    comparison = compare_to_frozen(state, models, dev)
    files = {
        "model": "refit_model.json", "tuning": "final_tuning_results.csv",
        "imputation": "training_fit_audit.json", "comparison": "refit_comparison.json",
        "summary": "training_summary.json",
    }
    write_json(out / files["model"], state)
    pd.DataFrame(histories).to_csv(out / files["tuning"], index=False)
    write_json(out / files["imputation"], audit.as_dict())
    write_json(out / files["comparison"], comparison)
    summary = {**protocol_metadata(dev), "model_version": state["model_version"],
               "selected_alphas": state["selected_alphas"], "fit_rows": state["fit_rows"],
               "pipeline_fit_count": len(audit.fits), "distance_reference_rows": len(state["distance_points"]),
               "distance_threshold": state["distance_threshold"], "comparison": comparison, "files": files}
    write_json(out / files["summary"], summary)
    return {"output_dir": str(out), "files": files, "selected_alphas": state["selected_alphas"],
            "fit_rows": state["fit_rows"], "comparison": comparison}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=None, help="RAW workbook path; defaults to the bundled RAW workbook")
    parser.add_argument("--output-dir", default=None, help="Result directory; default module2_prediction/results")
    args = parser.parse_args(argv)
    result = train_final(args.data, args.output_dir)
    print(json.dumps(json_safe(result), ensure_ascii=False, indent=2, allow_nan=False))
    return result


if __name__ == "__main__":
    main()
