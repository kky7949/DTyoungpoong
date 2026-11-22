"""Behavior tests for cleaning, training-only filling, and feature order."""

import importlib
import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone


def api():
    try:
        schema = importlib.import_module("module1_preprocessing.schema")
        pipeline = importlib.import_module("module1_preprocessing.pipeline")
        features = importlib.import_module("module1_preprocessing.features")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Preprocessing API has not been implemented: {exc}")
    return schema, pipeline, features


def sample_frame(schema, count):
    row = [15, 7, 4, 10, 1, 2, 3, 100, 1000, 70, 5]
    frame = pd.DataFrame([row] * count, columns=schema.BASE)
    frame.insert(0, "배치ID", [f"BP-2025-{i + 1:04d}" for i in range(count)])
    frame.insert(1, "분석일자", ["03.01.2025"] * count)
    frame.insert(2, "원료등급", ["A"] * count)
    frame["Ni_회수율_pct"] = 90.0
    frame["Co_회수율_pct"] = 80.0
    return frame


def test_cleaning_keeps_first_batch_and_raw_date_and_masks_invalid_inputs(tmp_path):
    schema, pipeline, _ = api()
    frame = sample_frame(schema, 3)
    frame["배치ID"] = ["BP-2025-0010", " BP-2025-0002 ", "BP-2025-0002"]
    frame["원료등급"] = [" c급 ", "b", "A"]
    frame["Ni_함량_pct"] = [35, 18, 25]
    frame["Co_함량_pct"] = ["not numeric", "7", "8"]
    path = tmp_path / "raw.csv"
    frame.to_csv(path, index=False)
    cleaned = pipeline.load_clean_data(path)
    assert cleaned["배치ID"].tolist() == ["BP-2025-0002", "BP-2025-0010"]
    assert cleaned["원료등급"].tolist() == ["B", "C"]
    assert cleaned["분석일자"].tolist() == ["03.01.2025", "03.01.2025"]
    assert cleaned.loc[0, "Ni_함량_pct"] == 18
    assert np.isnan(cleaned.loc[1, "Ni_함량_pct"])
    assert np.isnan(cleaned.loc[1, "Co_함량_pct"])


@pytest.mark.parametrize("bad_target", [None, -0.1, 100.1, "invalid"])
def test_targets_are_observed_bounded_and_never_imputed(tmp_path, bad_target):
    schema, pipeline, _ = api()
    frame = sample_frame(schema, 2)
    frame["Ni_회수율_pct"] = [90, bad_target]
    path = tmp_path / "invalid_target.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError):
        pipeline.load_clean_data(path)


def test_fold_imputation_uses_training_counts_and_global_fallback():
    schema, pipeline, _ = api()
    train = sample_frame(schema, 10)
    train["원료등급"] = ["A"] * 5 + ["B"] * 5
    train["Ni_함량_pct"] = [10, 11, 12, 13, 14, 20, 21, 22, np.nan, np.nan]
    train["황산투입량_L"] = np.arange(500, 1500, 100)
    valid = sample_frame(schema, 3)
    valid["원료등급"] = ["A", "B", "C"]
    valid["Ni_함량_pct"] = np.nan
    valid["황산투입량_L"] = np.nan
    estimator = pipeline.FoldPreprocessor("A11").fit(train)
    filled = estimator.transform(valid)
    np.testing.assert_allclose(filled[:, 0], [12, 13.5, 13.5])
    np.testing.assert_allclose(filled[:, 8], [950, 950, 950])
    assert estimator.grade_count_.loc["A", "Ni_함량_pct"] == 5
    assert estimator.grade_count_.loc["B", "Ni_함량_pct"] == 3
    assert estimator.global_median_["Ni_함량_pct"] == 13.5
    assert clone(estimator).feature_mode == "A11"
    assert valid["Ni_함량_pct"].isna().all()
    changed_targets = train.copy()
    changed_targets["Ni_회수율_pct"] = -999
    np.testing.assert_array_equal(
        pipeline.FoldPreprocessor("A11").fit(changed_targets).transform(valid), filled
    )


def test_missing_entire_training_column_cannot_be_filled():
    schema, pipeline, _ = api()
    train = sample_frame(schema, 5)
    train["Fe_불순물_pct"] = np.nan
    with pytest.raises(ValueError, match="observ"):
        pipeline.FoldPreprocessor().fit(train)


def test_feature_values_have_the_documented_order():
    _, _, features = api()
    row = np.array([[15, 7, 4, 10, 1, 2, 3, 100, 1000, 70, 5]], dtype=float)
    np.testing.assert_array_equal(features.feature_matrix(row, "A"), row)
    np.testing.assert_array_equal(features.feature_matrix(row, "A11"), row)
    np.testing.assert_array_equal(
        features.feature_matrix(row, "B_Impurity")[0, 11:], [10, 6]
    )
    np.testing.assert_array_equal(
        features.feature_matrix(row, "A17")[0, 11:],
        [1000000, 4900, 25, 70000, 5000, 350],
    )
    np.testing.assert_array_equal(features.feature_matrix(row, "A20")[0, 17:], [6000, 420, 30])
    assert len(features.feature_names("A17")) == 17
    with pytest.raises(ValueError):
        features.feature_matrix(row, "unknown")
    with pytest.raises(ValueError):
        features.feature_matrix(np.ones((2, 10)))


def test_feature_expansion_imports_without_pandas_for_minimal_inference():
    code = """
import importlib.abc
import sys
class NoPandas(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'pandas':
            raise ModuleNotFoundError('pandas deliberately unavailable')
sys.meta_path.insert(0, NoPandas())
from module1_preprocessing.features import feature_matrix
assert feature_matrix([[15, 7, 4, 10, 1, 2, 3, 100, 1000, 70, 5]]).shape == (1, 17)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_released_data_split_and_preprocessing_match_existing_curve17(tmp_path):
    schema, pipeline, features = api()
    assert pipeline.load_raw_data().shape == (424, 16)
    cleaned = pipeline.load_clean_data()
    assert cleaned.shape == (420, 16)
    dev = cleaned.iloc[:357]
    assert dev[list(schema.BASE)].notna().all(axis=1).sum() == 151
    result = pipeline.run_preprocessing(output_dir=tmp_path)
    assert result["audit"]["rows"] == {
        "raw": 424, "duplicates_removed": 4, "cleaned": 420,
        "development": 357, "holdout": 63,
        "development_complete_observed": 151,
    }
    reserve = pd.read_csv(tmp_path / "holdout63.csv")
    assert len(reserve) == 63
    assert reserve[list(schema.BASE)].isna().any().any()
    state = json.loads((tmp_path / "scaler_state.json").read_text())
    expected = [18.882044817927174, 8.194369747899152, 3.8321568627450993,
                10.475952380952377, 1.8191876750700278, 1.615028011204482,
                2.567927170868348, 142.41652661064438, 941.3137254901961,
                67.50210084033614, 4.27985994397759, 980182.9215686275,
                4786.205399159669, 21.50527927170871, 63766.689495798324,
                4019.16288515406, 290.1827254901959]
    np.testing.assert_allclose(state["mean"], expected, rtol=0, atol=1e-9)
    matrix = pd.read_csv(tmp_path / "development_features17.csv")
    assert matrix.columns.tolist() == features.feature_names("A17")
    assert matrix.shape == (357, 17)
    standardized = pd.read_csv(tmp_path / "development_standardized17.csv")
    np.testing.assert_allclose(standardized.mean(), 0, atol=1e-12)
    np.testing.assert_allclose(standardized.std(ddof=0), 1, atol=1e-12)
