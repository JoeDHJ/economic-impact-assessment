"""Type I domestic industry model. Rows sell; columns buy. All money is GBP m."""
from dataclasses import dataclass
from numbers import Real
import numpy as np


def numeric(value, name):
    try:
        a = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain numbers") from exc
    if not np.isfinite(a).all():
        raise ValueError(f"{name} contains missing or non-finite values")
    return a


def scalar(value, name, low=0, high=None):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a number, not text or a boolean")
    a = numeric(value, name)
    if a.ndim != 0:
        raise ValueError(f"{name} must be one number")
    v = float(a)
    if v < low or (high is not None and v > high):
        raise ValueError(f"{name} must be between {low} and {high if high is not None else 'infinity'}")
    return v


@dataclass
class IOModel:
    a: np.ndarray
    employment: np.ndarray  # direct FTE per GBP m output
    gva: np.ndarray
    income: np.ndarray
    imports_ruk: np.ndarray
    imports_row: np.ndarray

    def __post_init__(self):
        self.a = numeric(self.a, "technical coefficients")
        if self.a.ndim != 2 or self.a.shape[0] != self.a.shape[1] or not self.a.size:
            raise ValueError("technical coefficients must be a nonempty square matrix")
        n = len(self.a)
        if (self.a < 0).any():
            raise ValueError("technical coefficients cannot be negative")
        for name in ("employment", "gva", "income", "imports_ruk", "imports_row"):
            v = numeric(getattr(self, name), name)
            if v.shape != (n,) or (v < 0).any():
                raise ValueError(f"{name} must be a nonnegative vector of length {n}")
            setattr(self, name, v)
        self.system = np.eye(n) - self.a
        # Productive, stable systems only. Condition alone cannot establish productivity.
        self.spectral_radius = float(max(abs(np.linalg.eigvals(self.a))))
        self.condition = float(np.linalg.cond(self.system))
        if self.spectral_radius >= 1 - 1e-10 or self.condition > 1e8:
            raise ValueError("input-output system is nonproductive, singular or ill-conditioned")

    def solve(self, final_demand, supplier_retention=1.0):
        f = numeric(final_demand, "final demand")
        if f.shape != self.employment.shape or (f < 0).any():
            raise ValueError("final demand must be nonnegative and match industry dimensions")
        r = scalar(supplier_retention, "supplier_retention", 0, 1)
        # Scottish domestic A already excludes UK/world imports. r is an ADDITIONAL
        # scenario erosion of purchases otherwise made in Scotland; base r=1.
        x = np.linalg.solve(np.eye(len(f)) - r * self.a, f)
        indirect = np.maximum(x - f, 0)
        def effect(v):
            return {"direct": float(v @ f), "indirect": float(v @ indirect), "total": float(v @ x)}
        return {
            "direct_output": f.tolist(), "indirect_output": indirect.tolist(), "total_output": x.tolist(),
            "output_gbp_m": effect(np.ones(len(f))), "employment_fte": effect(self.employment),
            "gva_gbp_m": effect(self.gva), "income_gbp_m": effect(self.income),
            "intermediate_imports_ruk_gbp_m": float(self.imports_ruk @ x),
            "intermediate_imports_row_gbp_m": float(self.imports_row @ x),
            "additional_supplier_leakage_gbp_m": float((1-r) * (self.a @ x).sum()),
            "balance_max_error": float(np.max(abs(x-r*self.a@x-f))),
        }
