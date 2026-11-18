"""Mean and 95% confidence interval half-width (t distribution), used by every driver."""
import math
import statistics

from scipy.stats import t as _t


def t95(df: int) -> float:
    return float(_t.ppf(0.975, df)) if df > 0 else float("inf")


def ci95(values):
    vals = list(values)
    if len(vals) < 2:
        return (vals[0] if vals else 0.0), float("inf")
    return statistics.fmean(vals), t95(len(vals) - 1) * statistics.stdev(vals) / math.sqrt(len(vals))


assert abs(t95(14) - 2.1448) < 1e-3 and abs(t95(15) - 2.1314) < 1e-3
