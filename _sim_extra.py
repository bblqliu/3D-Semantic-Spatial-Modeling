# -*- coding: utf-8 -*-
"""Additional sweeps. Defaults match the main study; only the named factor changes."""
import json
import os
import numpy as np
import _sim_benchmark as sim

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "_sim_extra.json")
N = 12
SEED = 20261029


def run_cell(scenario, occ, policy, rng, **kw):
    rows = [sim.run_trial(scenario, occ, rng, policy=policy, **kw) for _ in range(N)]
    return sim.summarize(rows)


def main():
    rng = np.random.default_rng(SEED)
    out = {"trials": N, "seed": SEED, "scenario_note": "bin at nominal budget 0.80 unless stated"}
    out["budget"] = {}
    for n in (0, 1, 2, 4, 6, 8):
        out["budget"][str(n)] = {}
        for policy in ("active", "random"):
            # Zero probes is vision for both labels; still run once per policy so the axis is paired.
            pol = "vision" if n == 0 else policy
            out["budget"][str(n)][policy] = run_cell("bin", 0.80, pol, rng, n_probes=n)
            d = out["budget"][str(n)][policy]
            print("budget", n, policy, "t", round(d["trans_median"], 2), "cos", round(d["roi_cosine_mean"], 2), flush=True)
    out["noise"] = {}
    for noise in (0.5, 1.8, 4.0, 8.0):
        out["noise"][str(noise)] = {}
        for policy in ("vision", "static", "active"):
            out["noise"][str(noise)][policy] = run_cell(
                "bin", 0.80, policy, rng, vision_noise_mm=noise)
            d = out["noise"][str(noise)][policy]
            print("noise", noise, policy, "t", round(d["trans_median"], 2), flush=True)
    out["cameras"] = {}
    for nc in (1, 2):
        out["cameras"][str(nc)] = {}
        for policy in ("vision", "static", "active"):
            out["cameras"][str(nc)][policy] = run_cell(
                "bin", 0.80, policy, rng, n_cams=nc)
            d = out["cameras"][str(nc)][policy]
            print("cams", nc, policy, "t", round(d["trans_median"], 2), "cos", round(d["roi_cosine_mean"], 2), flush=True)
    out["outliers"] = {}
    for frac in (0.0, 0.12, 0.30):
        out["outliers"][str(frac)] = {}
        out["outliers"][str(frac)]["vision"] = run_cell(
            "bin", 0.80, "vision", rng, outlier_frac=frac)
        out["outliers"][str(frac)]["huber"] = run_cell(
            "bin", 0.80, "active", rng, outlier_frac=frac, huber=True)
        out["outliers"][str(frac)]["least_squares"] = run_cell(
            "bin", 0.80, "active", rng, outlier_frac=frac, huber=False)
        print("out", frac,
              "v", round(out["outliers"][str(frac)]["vision"]["trans_median"], 2),
              "h", round(out["outliers"][str(frac)]["huber"]["trans_median"], 2),
              "l", round(out["outliers"][str(frac)]["least_squares"]["trans_median"], 2),
              flush=True)
    out["length"] = {}
    old_ls = sim.CFG["rbf_length_m"]
    try:
        for ls in (0.006, 0.012, 0.024):
            sim.CFG["rbf_length_m"] = ls
            out["length"][str(ls)] = run_cell("bin", 0.80, "active", rng)
            d = out["length"][str(ls)]
            print("ls", ls, "t", round(d["trans_median"], 2),
                  "E", round(d["entropy_mean"][0], 2), "->", round(d["entropy_mean"][-1], 2),
                  "cos", round(d["roi_cosine_mean"], 2), flush=True)
    finally:
        sim.CFG["rbf_length_m"] = old_ls
    out["deform"] = {}
    for amp in (0.0, 1.2, 3.0, 6.0):
        out["deform"][str(amp)] = {}
        for policy in ("vision", "active"):
            out["deform"][str(amp)][policy] = run_cell(
                "deformable", 0.50, policy, rng, deform_mm=amp)
            d = out["deform"][str(amp)][policy]
            print("def", amp, policy, "t", round(d["trans_median"], 2),
                  "cos", round(d["roi_cosine_mean"], 2), flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
