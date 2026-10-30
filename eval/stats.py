"""Bootstrap confidence intervals over requirements (or pairs) and paired comparisons."""
import numpy as np

SEED, N_BOOT = 42, 10000


def boot_ci(values, n=N_BOOT, seed=SEED):
    """Mean and 95% percentile bootstrap CI."""
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired(a, b, tol=1e-9, lower_is_better=False):
    """a, b aligned per requirement. Returns mean diff (a-b), CI, wins/losses/ties of a, verdict string.
    For lower-is-better metrics (FRR) pass lower_is_better=True: a wins where its value is LOWER and the verdict is
    "better" when the CI lies below 0. (Before the 2026-10-30 erratum the flag did not exist and FRR rows were inverted.)"""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    m, lo, hi = boot_ci(d)
    sign = -1.0 if lower_is_better else 1.0
    wins, losses = int((sign * d > tol).sum()), int((sign * d < -tol).sum())
    verdict = "not distinguishable" if lo <= 0 <= hi else ("better" if sign * m > 0 else "worse")
    return dict(diff=m, lo=lo, hi=hi, wins=wins, losses=losses, ties=len(d) - wins - losses, verdict=verdict)


def fmt_ci(m, lo, hi, digits=3):
    return f"{m:.{digits}f} [{lo:.{digits}f}, {hi:.{digits}f}]"
