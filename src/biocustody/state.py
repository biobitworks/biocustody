from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA

@dataclass
class StateDecision:
    decision: str
    distance2: float
    threshold2: float
    quantile: float

class ReferenceStateModel:
    """
    Robust-ish hackathon state model:
      control profiles
        -> median/MAD scaling
        -> PCA
        -> Ledoit-Wolf shrinkage covariance
        -> empirical control-distance acceptance threshold

    This avoids a naive inverse of the full high-dimensional covariance matrix.
    """
    def __init__(self, quantile: float = 0.95, max_components: int = 12):
        self.quantile = quantile
        self.max_components = max_components
        self.median_ = None
        self.scale_ = None
        self.pca_ = None
        self.cov_ = None
        self.center_ = None
        self.threshold2_ = None
        self.control_distances2_ = None

    def _robust_scale_fit(self, X: np.ndarray) -> np.ndarray:
        self.median_ = np.nanmedian(X, axis=0)
        mad = np.nanmedian(np.abs(X - self.median_), axis=0)
        scale = 1.4826 * mad
        # Safe fallback for invariant/tiny-MAD features.
        std = np.nanstd(X, axis=0, ddof=1)
        scale = np.where(scale > 1e-12, scale, np.where(std > 1e-12, std, 1.0))
        self.scale_ = scale
        return (X - self.median_) / self.scale_

    def _robust_scale(self, X: np.ndarray) -> np.ndarray:
        return (X - self.median_) / self.scale_

    def fit(self, controls) -> "ReferenceStateModel":
        X = np.asarray(controls, dtype=float)
        if X.ndim != 2 or X.shape[0] < 4:
            raise ValueError("Need a 2D control matrix with at least 4 replicates.")
        if not np.isfinite(X).all():
            raise ValueError("Controls contain NaN/inf; resolve upstream QC first.")

        Z = self._robust_scale_fit(X)
        n_components = min(self.max_components, X.shape[1], X.shape[0] - 1)
        if n_components < 1:
            raise ValueError("Insufficient dimensionality after QC.")
        self.pca_ = PCA(n_components=n_components, random_state=0)
        P = self.pca_.fit_transform(Z)

        self.cov_ = LedoitWolf().fit(P)
        self.center_ = self.cov_.location_
        d2 = np.array([self._mahalanobis_p(p) for p in P])
        self.control_distances2_ = d2
        self.threshold2_ = float(np.quantile(d2, self.quantile))
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X[None, :]
        if not np.isfinite(X).all():
            raise ValueError("Input contains NaN/inf; resolve upstream QC first.")
        return self.pca_.transform(self._robust_scale(X))

    def _mahalanobis_p(self, p: np.ndarray) -> float:
        diff = p - self.center_
        return float(diff @ self.cov_.precision_ @ diff.T)

    def distance2(self, x) -> float:
        p = self.transform(x)[0]
        return self._mahalanobis_p(p)

    def decide(self, x) -> StateDecision:
        d2 = self.distance2(x)
        decision = "CONTINUOUS" if d2 <= self.threshold2_ else "TRANSITION"
        return StateDecision(
            decision=decision,
            distance2=d2,
            threshold2=self.threshold2_,
            quantile=self.quantile,
        )
