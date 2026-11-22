"""Deterministic feature expansion; no fit, targets, or data-derived decisions."""

import numpy as np

from .schema import BASE

_CURVE_NAMES = [
    "acid2_L2", "temp2_C2", "time2_hr2", "acid_temp_L_C",
    "acid_time_L_hr", "temp_time_C_hr",
]
_IMPURITY_INTERACTIONS = ["impurity_acid_pct_L", "impurity_temp_pct_C", "impurity_time_pct_hr"]


def feature_names(mode="A17"):
    """Return names in the exact numerical output order for ``mode``."""
    names = list(BASE)
    if mode in ("A", "A11"):
        return names
    if mode in ("B", "B_Impurity", "B_TempTime"):
        names.append("황산_원료비_L_per_kg")
        if mode == "B_Impurity":
            names.append("불순물합계_pct")
        elif mode == "B_TempTime":
            names.append("온도시간_지표_C_hr")
        return names
    if mode in ("A17", "A20"):
        return names + _CURVE_NAMES + (_IMPURITY_INTERACTIONS if mode == "A20" else [])
    raise ValueError(f"Unknown feature mode: {mode}")


def feature_matrix(x, mode="A17"):
    """Expand an already filled (n, 11) matrix or a DataFrame in BASE order.

    A17 appends A², T², h², A*T, A*h, T*h, where A is acid in litres.
    A20 then appends total impurity multiplied by A, T, and h.
    """
    feature_names(mode)  # Reject unsupported modes even for an empty matrix.
    # DataFrames keep named-column ordering without making pandas a dependency
    # of the NumPy-only prediction path.
    if hasattr(x, "columns") and hasattr(x, "loc"):
        x = x.loc[:, list(BASE)]
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] != len(BASE):
        raise ValueError("Expected a two-dimensional matrix with exactly 11 base inputs.")
    if not np.isfinite(x).all():
        raise ValueError("Feature inputs must be finite; impute within the training fold first.")
    if mode in ("A", "A11"):
        return x.copy()
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        if mode in ("B", "B_Impurity", "B_TempTime"):
            extra = [x[:, 8] / x[:, 7]]
            if mode == "B_Impurity":
                extra.append(x[:, 4:7].sum(axis=1))
            elif mode == "B_TempTime":
                extra.append(x[:, 9] * x[:, 10])
            result = np.column_stack([x, *extra])
        else:
            a, t, h = x[:, 8], x[:, 9], x[:, 10]
            result = np.column_stack((x, a * a, t * t, h * h, a * t, a * h, t * h))
            if mode == "A20":
                result = np.column_stack((result, x[:, 4:7].sum(axis=1)[:, None] * x[:, 8:11]))
    if not np.isfinite(result).all():
        raise ValueError("Feature expansion produced a non-finite value.")
    return result
