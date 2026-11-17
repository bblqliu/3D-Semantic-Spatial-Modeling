# -*- coding: utf-8 -*-
"""Controlled numerical benchmark for the visuo-tactile paper.

The study models pinhole visibility, axial depth noise, tactile patches, and
SE(3) refinement. It does not call Isaac Sim or a GPU renderer.
"""
import json
import os
import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(ROOT, "_sim_results.json")
FIGDIR = os.path.join(ROOT, "_sim_figs")

# Frozen configuration. Chosen to define the benchmark, then not edited
# after the full run.
CFG = {
    "n_surface": 700,
    "icp_iters": 18,
    "huber_mm": 2.5,
    "assoc_mm": 10.0,
    "vision_noise_mm": 1.8,
    "tactile_noise_mm": 0.35,
    "snap_mm": 18.0,
    "transparent_extra_noise_mm": 3.5,
    "transparent_keep": 0.45,
    "outlier_frac": 0.12,
    "prior_rot_deg": 14.0,
    "prior_trans_mm": 12.0,
    "n_probes_active": 6,
    "patch": 12,
    "rbf_length_m": 0.012,
    "rbf_var": 1.15,
    "gp_noise": 1e-3,
    "seed": 20261028,
    "trials_main": 24,
    "trials_sweep": 16,
    "trials_ablate": 16,
    "success_trans_mm": 5.0,
    "success_rot_deg": 5.0,
    "force_limit_n": 3.0,
    "stiffness": {"bin": 400.0, "transparent": 800.0, "deformable": 180.0, "insertion": 900.0},
    "approach_depth_mm": 1.2,
}


def rodrigues(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * (K @ K)


def rand_pose(rng, rot_deg, trans_mm):
    axis = rng.normal(size=3)
    axis /= np.linalg.norm(axis)
    ang = np.deg2rad(rot_deg) * rng.normal()
    R = rodrigues(axis * ang)
    t = rng.normal(size=3) * (trans_mm / 1000.0)
    return R, t


def apply(R, t, X):
    return (R @ X.T).T + t


def invert(R, t, P):
    return (R.T @ (P - t).T).T


def rot_angle_deg(R):
    c = (np.trace(R) - 1.0) * 0.5
    c = float(np.clip(c, -1.0, 1.0))
    return float(np.degrees(np.arccos(c)))


def huber_w(r, delta):
    a = np.abs(r)
    w = np.ones_like(a)
    m = a > delta
    w[m] = delta / np.maximum(a[m], 1e-12)
    return w


def sample_bottle(n, rng):
    # Corner-rich box so a partial view still constrains the pose, plus a
    # handle on the hidden face.
    n_box = int(n * 0.82)
    n_knob = n - n_box
    per = n_box // 6
    pts_l, n_l = [], []
    dims = np.array([0.028, 0.022, 0.040])
    for axis, sign in [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]:
        a, b = [i for i in range(3) if i != axis]
        P = np.zeros((per, 3))
        P[:, a] = rng.uniform(-dims[a], dims[a], per)
        P[:, b] = rng.uniform(-dims[b], dims[b], per)
        P[:, axis] = sign * dims[axis]
        N = np.zeros((per, 3))
        N[:, axis] = sign
        pts_l.append(P)
        n_l.append(N)
    box = np.vstack(pts_l)
    nb = np.vstack(n_l)
    k = rng.normal(size=(n_knob, 3))
    k /= np.linalg.norm(k, axis=1, keepdims=True)
    knob = k * 0.012 + np.array([-(dims[0] + 0.012), 0.0, 0.0])
    pts = np.vstack([box, knob])
    nrm = np.vstack([nb, k])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    region = np.zeros(len(pts), dtype=int)
    region[pts[:, 2] > dims[2] - 0.004] = 1
    region[pts[:, 2] < -(dims[2] - 0.004)] = 3
    region[-n_knob:] = 2
    mark = (region == 0) & (pts[:, 1] > dims[1] - 0.004) & (np.abs(pts[:, 2]) < 0.012)
    region[mark] = 4
    return pts[:n], nrm[:n], region[:n]


def sample_flask(n, rng):
    n_body = int(n * 0.55)
    n_neck = int(n * 0.25)
    n_rim = n - n_body - n_neck
    v = rng.normal(size=(n_body, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    body = v * np.array([0.032, 0.032, 0.04])
    nb = v / np.array([0.032, 0.032, 0.04])
    th = rng.uniform(0, 2 * np.pi, n_neck)
    z = rng.uniform(0.04, 0.09, n_neck)
    neck = np.stack([0.010 * np.cos(th), 0.010 * np.sin(th), z], 1)
    nn = np.stack([np.cos(th), np.sin(th), np.zeros_like(th)], 1)
    th = rng.uniform(0, 2 * np.pi, n_rim)
    rim = np.stack([0.016 * np.cos(th), 0.016 * np.sin(th), np.full(n_rim, 0.092)], 1)
    nr = np.stack([0.2 * np.cos(th), 0.2 * np.sin(th), np.ones(n_rim)], 1)
    pts = np.vstack([body, neck, rim])
    nrm = np.vstack([nb, nn, nr])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    region = np.array([0] * n_body + [1] * n_neck + [2] * n_rim)
    region[pts[:, 2] < -0.028] = 3
    mark = (region == 0) & (pts[:, 0] > 0.02)
    region[mark] = 4
    return pts, nrm, region


def sample_foam(n, rng):
    # Rectangular foam with one notched corner. Mild compliance is applied later.
    faces = []
    normals = []
    per = n // 6
    specs = [
        (0, 1, 0.04),
        (0, -1, -0.04),
        (1, 1, 0.03),
        (1, -1, -0.03),
        (2, 1, 0.025),
        (2, -1, -0.025),
    ]
    spans = [0.03, 0.04, 0.04]
    for axis, sign, pos in specs:
        m = per
        a, b = [i for i in range(3) if i != axis]
        ua = rng.uniform(-spans[a], spans[a], m)
        ub = rng.uniform(-spans[b], spans[b], m)
        P = np.zeros((m, 3))
        P[:, a] = ua
        P[:, b] = ub
        P[:, axis] = pos
        N = np.zeros((m, 3))
        N[:, axis] = sign
        faces.append(P)
        normals.append(N)
    pts = np.vstack(faces)
    nrm = np.vstack(normals)
    # notch: remove a corner and replace with a slanted face
    notch = (pts[:, 0] > 0.015) & (pts[:, 1] > 0.02) & (pts[:, 2] > 0.0)
    pts = pts[~notch]
    nrm = nrm[~notch]
    m = n - len(pts)
    if m > 0:
        u = rng.uniform(-0.01, 0.02, m)
        v = rng.uniform(-0.01, 0.02, m)
        slant = np.stack([0.02 - u, 0.025 - v, u + v], 1)
        ns = np.tile(np.array([0.4, 0.4, 0.8]), (m, 1))
        pts = np.vstack([pts, slant])
        nrm = np.vstack([nrm, ns])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    region = np.zeros(len(pts), dtype=int)
    region[pts[:, 2] > 0.018] = 1  # top
    region[pts[:, 2] < -0.018] = 3  # base
    region[(pts[:, 0] < -0.012) & (pts[:, 1] > 0.01)] = 2  # notch facing the occluded side
    region[(np.abs(pts[:, 1]) < 0.008) & (pts[:, 0] < 0) & (region == 0)] = 4
    return pts[:n], nrm[:n], region[:n]


def sample_peg(n, rng):
    # Rectangular peg with a side ridge so yaw is observable.
    n_shaft = int(n * 0.75)
    n_ridge = n - n_shaft
    th_side = rng.integers(0, 4, n_shaft)
    z = rng.uniform(-0.03, 0.03, n_shaft)
    along = rng.uniform(-0.008, 0.008, n_shaft)
    pts = np.zeros((n_shaft, 3))
    nrm = np.zeros((n_shaft, 3))
    for s, normal, tang in [
        (0, [1, 0, 0], [0, 1, 0]),
        (1, [-1, 0, 0], [0, 1, 0]),
        (2, [0, 1, 0], [1, 0, 0]),
        (3, [0, -1, 0], [1, 0, 0]),
    ]:
        sel = th_side == s
        pts[sel, 0] = normal[0] * 0.008 + tang[0] * along[sel]
        pts[sel, 1] = normal[1] * 0.008 + tang[1] * along[sel]
        pts[sel, 2] = z[sel]
        nrm[sel] = normal
    # close the top
    top = pts[:, 2] > 0.027
    nrm[top] = np.array([0, 0, 1.0])
    u = rng.uniform(-0.001, 0.007, n_ridge)
    z = rng.uniform(-0.018, 0.004, n_ridge)
    ridge = np.stack([0.008 + u, np.full(n_ridge, 0.0), z], 1)
    nr = np.tile(np.array([0.6, 0.8, 0.0]), (n_ridge, 1))
    pts = np.vstack([pts, ridge])
    nrm = np.vstack([nrm, nr])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    region = np.zeros(len(pts), dtype=int)
    region[pts[:, 2] > 0.02] = 1
    region[pts[:, 2] < -0.02] = 3
    region[-n_ridge:] = 2
    region[(pts[:, 0] < -0.005) & (region == 0)] = 4
    return pts[:n], nrm[:n], region[:n]


SAMPLERS = {
    "bin": sample_bottle,
    "transparent": sample_flask,
    "deformable": sample_foam,
    "insertion": sample_peg,
}

# Affordances the language query asks for.
ROI_REGION = {"bin": 2, "transparent": 2, "deformable": 2, "insertion": 2}
REGION_NAMES = ["body", "neck", "affordance", "base", "mark"]


def features_from_region(region, rng):
    proto = np.eye(5)
    # small within-region scatter so cosine is not identically one
    F = proto[region] + 0.02 * rng.normal(size=(len(region), 5))
    F /= np.linalg.norm(F, axis=1, keepdims=True)
    return F, proto


def visibility(pts, nrm, occ, scenario, rng, n_cams=2):
    cams = [
        np.array([0.00, 0.00, 0.42]),
        np.array([0.20, -0.14, 0.16]),
    ][:n_cams]
    n = len(pts)
    budget = max(8, int(round((1.0 - occ) * n)))
    chosen = np.zeros(n, dtype=bool)
    per = max(4, budget // len(cams))
    for c in cams:
        view = c - pts
        view /= np.linalg.norm(view, axis=1, keepdims=True)
        front = (nrm * view).sum(1)
        if scenario == "insertion":
            # The cavity hides the shaft and the ridge. The exposed collar
            # includes side faces, so the visible fragment is not a single plane.
            front = np.where(pts[:, 2] > 0.016, front, -1.0)
        if scenario == "bin":
            # The bin wall hides the handle side from both cameras.
            front = np.where(pts[:, 0] > -0.02, front, -1.0)
        order = np.argsort(-front)
        take = [i for i in order if front[i] > 0.15][:per]
        chosen[take] = True
    idx = np.where(chosen)[0]
    if scenario == "transparent":
        # A shelf hides the flask rim from both cameras.
        keep_z = pts[idx, 2] < 0.075
        idx = idx[keep_z]
        keep = rng.random(len(idx)) < CFG["transparent_keep"]
        idx = idx[keep]
    if scenario == "deformable":
        idx = idx[pts[idx, 0] > -0.008]
    return idx


def make_observations(pts, nrm, R, t, idx, noise_mm, rng, n_outliers):
    if len(idx) == 0:
        P = np.zeros((0, 3))
    else:
        P = apply(R, t, pts[idx])
        P = P + rng.normal(scale=noise_mm / 1000.0, size=P.shape)
    if n_outliers > 0 and len(P):
        clutter = P.mean(0) + rng.uniform(-0.03, 0.03, size=(n_outliers, 3))
        P = np.vstack([P, clutter])
    return P


def rbf(A, B, ls, var):
    d2 = np.sum((A[:, None, :] - B[None, :, :]) ** 2, axis=2)
    return var * np.exp(-0.5 * d2 / (ls ** 2))


def gp_factor(Xobs):
    ls = CFG["rbf_length_m"]
    var = CFG["rbf_var"]
    if len(Xobs) == 0:
        return None
    if len(Xobs) > 140:
        Xobs = Xobs[np.linspace(0, len(Xobs) - 1, 140).astype(int)]
    K = rbf(Xobs, Xobs, ls, var) + (CFG["gp_noise"] + 1e-5) * np.eye(len(Xobs))
    try:
        L = np.linalg.cholesky(K)
    except np.linalg.LinAlgError:
        L = np.linalg.cholesky(K + 1e-4 * np.eye(len(Xobs)))
    return L, Xobs, ls, var


def gp_variance_from(state, Xq):
    var = CFG["rbf_var"]
    if state is None or len(Xq) == 0:
        return np.full(len(Xq), var)
    L, Xobs, ls, var = state
    Ks = rbf(Xq, Xobs, ls, var)
    sol = np.linalg.solve(L, Ks.T)
    v = var - np.sum(sol ** 2, axis=0)
    return np.clip(v, 1e-8, None)


def roi_variance_after(state, roi_pts, cand_pts):
    """Mean ROI variance after hypothetically adding each candidate."""
    var = CFG["rbf_var"]
    noise = CFG["gp_noise"]
    if len(roi_pts) == 0:
        return np.zeros(len(cand_pts))
    if state is None:
        # cov = k(roi, cand), var_c = var
        ls = CFG["rbf_length_m"]
        Krc = rbf(roi_pts, cand_pts, ls, var)
        red = (Krc ** 2) / (var + noise)
        base = np.full(len(roi_pts), var)
        return np.clip(base[:, None] - red, 1e-8, None).mean(0)
    L, Xobs, ls, var = state
    Kro = rbf(roi_pts, Xobs, ls, var)
    Kco = rbf(cand_pts, Xobs, ls, var)
    Krc = rbf(roi_pts, cand_pts, ls, var)
    alpha_r = np.linalg.solve(L.T, np.linalg.solve(L, Kro.T))
    alpha_c = np.linalg.solve(L.T, np.linalg.solve(L, Kco.T))
    cov = Krc - Kro @ alpha_c
    var_r = np.clip(var - np.sum(Kro * alpha_r.T, axis=1), 1e-8, None)
    var_c = np.clip(var - np.sum(Kco * alpha_c.T, axis=1), 1e-8, None)
    red = (cov ** 2) / (var_c[None, :] + noise)
    return np.clip(var_r[:, None] - red, 1e-8, None).mean(0)


def entropy(v):
    return 0.5 * np.log(2 * np.pi * np.e * v)


def so3_log(R):
    c = float(np.clip((np.trace(R) - 1.0) * 0.5, -1.0, 1.0))
    th = np.arccos(c)
    if th < 1e-8:
        return np.zeros(3)
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return 0.5 * th / np.sin(th) * w


def point_to_plane(P, tmpl, nrm, R0, t0, huber=True, R_prior=None, t_prior=None):
    R, t = R0.copy(), t0.copy()
    if R_prior is None:
        R_prior = np.eye(3)
        t_prior = np.zeros(3)
    delta = CFG["huber_mm"] / 1000.0
    gate = CFG["assoc_mm"] / 1000.0
    if len(P) < 6:
        return R, t
    gates = np.linspace(gate, 0.004, CFG["icp_iters"])
    for it in range(CFG["icp_iters"]):
        pred = apply(R, t, tmpl)
        dist, nn = cKDTree(pred).query(P, k=1)
        ok = dist < gates[it]
        if ok.sum() < 6:
            break
        p = P[ok]
        x = pred[nn[ok]]
        n = (R @ nrm[nn[ok]].T).T
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)
        r = np.sum(n * (p - x), axis=1)
        Jw = -np.cross(x, n)
        Jr = -n
        J = np.hstack([Jw, Jr])
        if huber:
            w = huber_w(r, delta)
        else:
            w = np.ones_like(r)
        sw = np.sqrt(w)
        A = J * sw[:, None]
        b = r * sw
        H = A.T @ A + 1e-6 * np.eye(6)
        g = A.T @ b
        try:
            step = -np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            break
        step[:3] = np.clip(step[:3], -0.25, 0.25)
        step[3:] = np.clip(step[3:], -0.008, 0.008)
        R = rodrigues(step[:3]) @ R
        t = rodrigues(step[:3]) @ t + step[3:]
    return R, t


def pose_error(R, t, Rg, tg):
    te = float(np.linalg.norm(t - tg) * 1000.0)
    re = rot_angle_deg(Rg.T @ R)
    return te, re


def coverage_chamfer_mm(tmpl, obs_obj):
    if len(obs_obj) == 0:
        return float(np.mean(np.linalg.norm(tmpl, axis=1)) * 1000.0)
    d, _ = cKDTree(obs_obj).query(tmpl, k=1)
    return float(np.mean(d) * 1000.0)


def roi_chamfer_mm(tmpl, roi, obs_obj):
    if roi.sum() == 0:
        return 0.0
    return coverage_chamfer_mm(tmpl[roi], obs_obj)


def semantic_scores(region, observed_mask):
    # Mean cosine on each region. Unobserved points contribute zero.
    scores = []
    proto = np.eye(5)
    for r in range(5):
        m = region == r
        if m.sum() == 0:
            scores.append(0.0)
            continue
        # observed points keep their prototype; others add nothing
        hit = np.logical_and(m, observed_mask).sum()
        scores.append(float(hit / m.sum()))
    return scores


def feasible(nrm, scenario, pts):
    # Do not approach through the table. A finger may reach around a wall
    # that blocks the cameras, so the bin wall is not a reachability cut.
    approach = nrm[:, 2] > -0.45
    if scenario == "insertion":
        approach = approach & (pts[:, 2] > -0.02)
    return approach


def run_trial(scenario, occ, rng, policy="active", huber=True, n_probes=None, semantic_from_touch=True,
              vision_noise_mm=None, outlier_frac=None, n_cams=2, deform_mm=None):
    pts, nrm, region = SAMPLERS[scenario](CFG["n_surface"], rng)
    roi = region == ROI_REGION[scenario]
    Rg, tg = rand_pose(rng, CFG["prior_rot_deg"], CFG["prior_trans_mm"])
    # Prior is the identity; GT is the perturbation we must recover.
    R0, t0 = np.eye(3), np.zeros(3)
    vis = visibility(pts, nrm, occ, scenario, rng, n_cams=n_cams)
    noise = CFG["vision_noise_mm"] if vision_noise_mm is None else float(vision_noise_mm)
    if scenario == "transparent":
        noise = noise + CFG["transparent_extra_noise_mm"]
    if scenario == "deformable":
        amp = 0.0012 if deform_mm is None else float(deform_mm) / 1000.0
        if amp <= 0:
            pts_obs = pts
        else:
            disp = amp * np.sin(40.0 * pts[:, 0])[:, None] * nrm
            pts_obs = pts + disp
    else:
        pts_obs = pts
    ofrac = CFG["outlier_frac"] if outlier_frac is None else float(outlier_frac)
    n_out = int(ofrac * max(len(vis), 1)) if scenario in ("bin", "transparent") else 0
    V = make_observations(pts_obs, nrm, Rg, tg, vis, noise, rng, n_out)
    observed = np.zeros(len(pts), dtype=bool)
    observed[vis] = True
    if n_probes is None:
        n_probes = CFG["n_probes_active"] if policy in ("active", "random") else (1 if policy == "static" else 0)

    def observe_patch(center_idx):
        d = np.linalg.norm(pts - pts[center_idx], axis=1)
        local = np.argsort(d)[: CFG["patch"]]
        P = make_observations(pts_obs, nrm, Rg, tg, local, CFG["tactile_noise_mm"], rng, 0)
        if semantic_from_touch:
            observed[local] = True
        return P, local

    probes_used = 0
    tactile = []
    feas = feasible(nrm, scenario, pts)
    entropy_curve = []
    chamfer_curve = []
    true_world = apply(Rg, tg, pts)
    Rhat, that = point_to_plane(V if len(V) else np.zeros((0, 3)), pts, nrm, R0, t0, huber=huber) if len(V) else (R0.copy(), t0.copy())

    def model_frame_cloud():
        chunks = []
        if len(V):
            vis_only = V[: max(0, len(V) - n_out)] if n_out else V
            chunks.append(invert(Rhat, that, vis_only))
        for P in tactile:
            if len(P):
                chunks.append(invert(Rhat, that, P))
        if not chunks:
            return np.zeros((0, 3))
        return np.vstack(chunks)

    def oracle_coverage_cloud():
        # Evaluation only: measurements mapped by the true pose.
        chunks = []
        if len(V):
            vis_only = V[: max(0, len(V) - n_out)] if n_out else V
            chunks.append(invert(Rg, tg, vis_only))
        for P in tactile:
            if len(P):
                chunks.append(invert(Rg, tg, P))
        if not chunks:
            return np.zeros((0, 3))
        return np.vstack(chunks)

    def snapshot():
        est = model_frame_cloud()
        v = gp_variance_from(gp_factor(est), pts[roi] if roi.any() else pts)
        entropy_curve.append(float(np.mean(entropy(v))))
        chamfer_curve.append(roi_chamfer_mm(pts, roi, oracle_coverage_cloud()))

    snapshot()
    candidates = np.where(feas)[0]
    tried = np.zeros(len(pts), dtype=bool)
    for s in range(n_probes):
        if policy == "vision":
            break
        pool_mask = feas & ~tried
        if policy != "static":
            pool_mask = pool_mask & ~observed
        unseen = np.where(pool_mask)[0]
        if len(unseen) < 5:
            unseen = np.where(feas & ~tried)[0]
        if len(unseen) == 0:
            break
        if policy == "static":
            if s > 0:
                break
            pick_pool = np.where(observed & feas)[0]
            if len(pick_pool) == 0:
                pick_pool = candidates
            pick = int(pick_pool[np.argmax(pts[pick_pool, 2])])
        elif policy == "random":
            pick = int(rng.choice(unseen))
        else:
            pool = unseen
            if len(pool) > 48:
                pool = rng.choice(pool, size=48, replace=False)
            roi_pts = pts[roi] if roi.any() else pts
            state = gp_factor(model_frame_cloud())
            scores = roi_variance_after(state, roi_pts, pts[pool])
            pick = int(pool[int(np.argmin(scores))])
        tried[pick] = True
        # Command the contact in the estimated object frame, then snap to the
        # true surface only if the finger actually reaches it.
        target = apply(Rhat, that, pts[pick:pick + 1])[0]
        dist = np.linalg.norm(true_world - target, axis=1)
        j = int(np.argmin(dist))
        if dist[j] > CFG["snap_mm"] / 1000.0:
            continue
        Patch, local = observe_patch(j)
        tactile.append(Patch)
        probes_used += 1
        acc = np.vstack([V] + tactile) if len(V) else np.vstack(tactile)
        Rhat, that = point_to_plane(acc, pts, nrm, Rhat, that, huber=huber)
        snapshot()

    parts = [V] + tactile
    P = np.vstack([p for p in parts if len(p)])
    # Closed-loop estimate: continue from the pose that planned the contacts.
    Rest, test = point_to_plane(P, pts, nrm, Rhat, that, huber=huber)
    te, re = pose_error(Rest, test, Rg, tg)
    scores = semantic_scores(region, observed)
    roi_score = scores[ROI_REGION[scenario]]
    return {
        "trans_mm": te,
        "rot_deg": re,
        "roi_cosine": roi_score,
        "region_scores": scores,
        "entropy": entropy_curve,
        "roi_chamfer_mm": chamfer_curve,
        "probes": probes_used,
        "n_vision": int(len(vis)),
        "occ_realized": float(1.0 - len(vis) / len(pts)),
        "success": int(te < CFG["success_trans_mm"] and re < CFG["success_rot_deg"]),
    }


def summarize(rows):
    def col(k):
        return np.array([r[k] for r in rows], dtype=float)

    te, re = col("trans_mm"), col("rot_deg")
    def med(a):
        return float(np.median(a))

    out = {
        "n": len(rows),
        "trans_mean": float(te.mean()),
        "trans_std": float(te.std(ddof=1)) if len(rows) > 1 else 0.0,
        "trans_median": med(te),
        "rot_mean": float(re.mean()),
        "rot_std": float(re.std(ddof=1)) if len(rows) > 1 else 0.0,
        "rot_median": med(re),
        "success": float(col("success").mean()),
        "roi_cosine_mean": float(col("roi_cosine").mean()),
        "roi_cosine_std": float(col("roi_cosine").std(ddof=1)) if len(rows) > 1 else 0.0,
        "roi_cosine_median": med(col("roi_cosine")),
        "occ_realized_mean": float(col("occ_realized").mean()),
        "n_vision_mean": float(col("n_vision").mean()),
        "probes_mean": float(col("probes").mean()),
    }
    # curves: pad to max length
    curves_e = [r["entropy"] for r in rows]
    curves_c = [r["roi_chamfer_mm"] for r in rows]
    L = max(len(c) for c in curves_e)
    E = np.full((len(rows), L), np.nan)
    C = np.full((len(rows), L), np.nan)
    for i, (e, c) in enumerate(zip(curves_e, curves_c)):
        E[i, : len(e)] = e
        C[i, : len(c)] = c
    out["entropy_mean"] = [None if np.all(np.isnan(E[:, j])) else float(np.nanmean(E[:, j])) for j in range(L)]
    out["entropy_std"] = [None if np.all(np.isnan(E[:, j])) else float(np.nanstd(E[:, j], ddof=1)) for j in range(L)]
    out["chamfer_mean"] = [None if np.all(np.isnan(C[:, j])) else float(np.nanmean(C[:, j])) for j in range(L)]
    out["chamfer_std"] = [None if np.all(np.isnan(C[:, j])) else float(np.nanstd(C[:, j], ddof=1)) for j in range(L)]
    reg = np.array([r["region_scores"] for r in rows])
    out["region_mean"] = [float(reg[:, j].mean()) for j in range(5)]
    return out


def main():
    rng = np.random.default_rng(CFG["seed"])
    main_spec = [
        ("bin", 0.40),
        ("bin", 0.80),
        ("transparent", 0.60),
        ("deformable", 0.50),
        ("insertion", 0.75),
    ]
    methods = ["vision", "static", "active"]
    results = {"config": CFG, "main": {}, "sweep": {}, "ablation": {}, "regions": {}}
    for sc, occ in main_spec:
        key = "%s@%.2f" % (sc, occ)
        results["main"][key] = {}
        for m in methods:
            rows = [run_trial(sc, occ, rng, policy=m) for _ in range(CFG["trials_main"])]
            results["main"][key][m] = summarize(rows)
            print(key, m, "t", round(results["main"][key][m]["trans_median"], 2),
                  "rmean", round(results["main"][key][m]["trans_mean"], 2),
                  "r", round(results["main"][key][m]["rot_median"], 2),
                  "s", round(results["main"][key][m]["success"], 2),
                  "c", round(results["main"][key][m]["roi_cosine_mean"], 2),
                  flush=True)
    for occ in (0.0, 0.2, 0.4, 0.6, 0.8):
        key = "bin@%.2f" % occ
        results["sweep"][key] = {}
        for m in methods:
            rows = [run_trial("bin", occ, rng, policy=m) for _ in range(CFG["trials_sweep"])]
            results["sweep"][key][m] = summarize(rows)
            print("sweep", key, m, round(results["sweep"][key][m]["trans_mean"], 2), flush=True)
    ablations = {
        "active": dict(policy="active", huber=True, semantic_from_touch=True),
        "random": dict(policy="random", huber=True, semantic_from_touch=True),
        "least_squares": dict(policy="active", huber=False, semantic_from_touch=True),
        "touch_no_view": dict(policy="active", huber=True, semantic_from_touch=False),
        "static": dict(policy="static", huber=True, semantic_from_touch=True),
        "vision": dict(policy="vision", huber=True, semantic_from_touch=True),
    }
    for name, kw in ablations.items():
        rows = [run_trial("bin", 0.80, rng, **kw) for _ in range(CFG["trials_ablate"])]
        results["ablation"][name] = summarize(rows)
        print("ablate", name, round(results["ablation"][name]["trans_mean"], 2),
              "cos", round(results["ablation"][name]["roi_cosine_mean"], 2), flush=True)
    # region profile at bin 80 from the main active/vision rows is inside main
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    main()
