"""Reproducible cleaning and fold-local preprocessing for the course dataset.

Import the executable pipeline explicitly from ``module1_preprocessing.pipeline``.
Keeping it out of this initializer also makes ``python -m ...pipeline`` warning-free.
"""

from .schema import BASE, CHEM, LIMITS, PROCESS, ROOT, TARGETS
from .features import feature_matrix, feature_names

__all__ = ["BASE", "CHEM", "LIMITS", "PROCESS", "ROOT", "TARGETS", "feature_matrix", "feature_names"]
