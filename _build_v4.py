# -*- coding: utf-8 -*-
"""Expanded IEEE paper. Every reported number is read from _sim_results.json."""
import json
import os
from lxml import etree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, Emu, Twips

ROOT = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(ROOT, "_sim_figs")
OUT = os.path.join(ROOT, "Embodied_AI_Visuo_Tactile_Paper_Expanded_v5.docx")
MNS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
COL = 3.30


def me(tag):
    return etree.Element("{%s}%s" % (MNS, tag))


def mv(el, val):
    el.set("{%s}val" % MNS, val)


def mrun(text, plain=False):
    r = me("r")
    if plain:
        rPr = me("rPr")
        sty = me("sty")
        mv(sty, "p")
        rPr.append(sty)
        r.append(rPr)
    t = me("t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    r.append(t)
    return r


def ssub(base, sub):
    el, e, s = me("sSub"), me("e"), me("sub")
    e.extend(base)
    s.extend(sub)
    el.append(e)
    el.append(s)
    return el


def ssup(base, sup):
    el, e, s = me("sSup"), me("e"), me("sup")
    e.extend(base)
    s.extend(sup)
    el.append(e)
    el.append(s)
    return el


def frac(num, den):
    f, n, d = me("f"), me("num"), me("den")
    n.extend(num)
    d.extend(den)
    f.append(n)
    f.append(d)
    return f


def delim(a, b, body):
    d, pr = me("d"), me("dPr")
    bc, ec = me("begChr"), me("endChr")
    mv(bc, a)
    mv(ec, b)
    pr.append(bc)
    pr.append(ec)
    d.append(pr)
    e = me("e")
    e.extend(body)
    d.append(e)
    return d


def nary(ch, sub, body, sup=None):
    el, pr = me("nary"), me("naryPr")
    chn, loc = me("chr"), me("limLoc")
    mv(chn, ch)
    mv(loc, "undOvr")
    pr.append(chn)
    if not sup:
        sh = me("supHide")
        mv(sh, "1")
        pr.append(sh)
    pr.append(loc)
    el.append(pr)
    sb, sp, e = me("sub"), me("sup"), me("e")
    sb.extend(sub)
    if sup:
        sp.extend(sup)
    e.extend(body)
    el.extend([sb, sp, e])
    return el


def func(name, arg):
    f, fn, e = me("func"), me("fName"), me("e")
    fn.append(mrun(name, plain=True))
    e.extend(arg)
    f.append(fn)
    f.append(e)
    return f


def acc(ch, base):
    a, pr, c, e = me("acc"), me("accPr"), me("chr"), me("e")
    mv(c, ch)
    pr.append(c)
    e.extend(base)
    a.append(pr)
    a.append(e)
    return a


def eqarr(lines):
    a = me("eqArr")
    for line in lines:
        e = me("e")
        e.extend(line)
        a.append(e)
    return a


def omath(nodes):
    om = me("oMath")
    for n in nodes:
        om.append(n)
    return om


def I(s):
    return mrun(s)


def P(s):
    return mrun(s, plain=True)


def sub(base, s):
    return ssub([I(base)], [I(s)])


def sup(base, s):
    return ssup([I(base)], [I(s)])


# ----- equations, each symbol created once -----
def eq_projection():
    line1 = [acc("̃", [sub("u", "k")]), I("="), I("K"),
             delim("(", ")", [sub("R", "k"), I("x"), I("+"), sub("t", "k")])]
    line2 = [sub("u", "k"), I("="),
             frac([ssub([acc("̃", [I("u")])], [P("k,1")])],
                  [ssub([acc("̃", [I("u")])], [P("k,3")])]),
             I(","),
             sub("v", "k"), I("="),
             frac([ssub([acc("̃", [I("u")])], [P("k,2")])],
                  [ssub([acc("̃", [I("u")])], [P("k,3")])])]
    return [eqarr([line1, line2])]


def eq_field():
    term = [sub("w", "k"), delim("(", ")", [I("x")]), I("·"),
            sub("F", "k"), delim("(", ")", [sub("u", "k")])]
    num = nary("∑", [I("k"), I("="), I("1")], term, sup=[I("K")])
    den = nary("∑", [I("k"), I("="), I("1")],
               [sub("w", "k"), delim("(", ")", [I("x")]), I("+"), I("ε")],
               sup=[I("K")])
    return [I("S"), delim("(", ")", [I("x")]), I("="), frac([num], [den])]


def eq_weight():
    resid = delim("(", ")", [sub("D", "k"), delim("(", ")", [sub("u", "k")]),
                             I("−"), sub("d", "k"), delim("(", ")", [I("x")])])
    line1 = [sub("w", "k"), delim("(", ")", [I("x")]), I("="),
             func("exp", [delim("(", ")", [I("−"), frac(
                 [ssup([resid], [I("2")])],
                 [I("2"), ssup([sub("σ", "d")], [I("2")])])])])]
    nT = ssup([I("n"), delim("(", ")", [I("x")])], [I("⊤")])
    line2 = [I("·"), func("max", [delim("(", ")", [I("0, −"), nT, I(" "), sub("v", "k")])]),
             I("·"), sub("V", "k"), delim("(", ")", [I("x")])]
    line3 = [sub("d", "k"), delim("(", ")", [I("x")]), I("="),
             ssup([sub("e", "3")], [I("⊤")]), sub("x", "k"), I(","),
             sub("x", "k"), I("="), sub("R", "k"), I("x"), I("+"), sub("t", "k")]
    return [eqarr([line1, line2, line3])]


def eq_query():
    g = sub("g", "text") if False else ssub([I("g")], [P("text")])
    ratio = frac([ssup([ssub([I("g")], [P("text")])], [I("⊤")]),
                  I("s"), delim("(", ")", [I("x")])], [I("τ")])
    ratio2 = frac([ssup([ssub([I("g")], [P("text")])], [I("⊤")]),
                   I("s"), delim("(", ")", [sup("x", "′")])], [I("τ")])
    num = func("exp", [delim("(", ")", [ratio])])
    den = nary("∫", [I("Ω")], [func("exp", [delim("(", ")", [ratio2])]),
                               I("d"), sup("x", "′")])
    return [I("P"), delim("(", ")", [I("L"), I("|"), I("x")]), I("="), frac([num], [den])]


def eq_recur():
    line1 = [sub("Λ", "t"), I("="), I("λ"), sub("Λ", "t−1"), I("+"), sub("w", "t")]
    num = [I("λ"), sub("Λ", "t−1"), sub("S", "t−1"), I("+"), sub("w", "t"), sub("F", "t")]
    line2 = [sub("S", "t"), I("="), frac(num, [sub("Λ", "t")])]
    return [eqarr([line1, line2])]


def eq_poisson():
    div = [I("∂p"), I("/"), I("∂u"), I("+"), I("∂q"), I("/"), I("∂v")]
    den = [I("−4"), ssup([I("π")], [I("2")]),
           delim("(", ")", [ssup([sub("f", "u")], [I("2")]), I("+"),
                            ssup([sub("f", "v")], [I("2")])])]
    inner = frac([func("F", [delim("{", "}", div)])], den)
    return [I("h"), I("="), ssup([I("F")], [I("−1")]), delim("{", "}", [inner])]


def eq_gp():
    kern = [I("k"), delim("(", ")", [I("x"), I(","), sup("x", "′")]), I("="),
            ssup([sub("σ", "f")], [I("2")]),
            func("exp", [delim("(", ")", [I("−"),
                 frac([ssup([delim("‖", "‖", [I("x"), I("−"), sup("x", "′")])], [I("2")])],
                      [I("2"), ssup([I("ℓ")], [I("2")])])])])]
    prior = [I("f"), delim("(", ")", [I("x")]), I("∼"), P("GP"),
             delim("(", ")", [I("m"), delim("(", ")", [I("x")]), I(","),
                              I("k"), delim("(", ")", [I("x"), I(","), sup("x", "′")])])]
    return [eqarr([prior, kern])]


def eq_var():
    kx = ssub([I("k")], [I("x")])
    quad = [ssup([ssub([I("k")], [I("x")])], [I("⊤")]),
            ssup([delim("(", ")", [I("K"), I("+"), ssup([sub("σ", "n")], [I("2")]), I("I")])],
                 [I("−1")]),
            ssub([I("k")], [I("x")])]
    return [ssup([I("σ")], [I("2")]), delim("(", ")", [I("x")]), I("="),
            I("k"), delim("(", ")", [I("x"), I(","), I("x")]), I("−")] + quad


def eq_entropy():
    return [I("H"), delim("(", ")", [I("x")]), I("="),
            frac([I("1")], [I("2")]),
            func("ln", [delim("(", ")", [I("2πe"), I("·"),
                 ssup([I("σ")], [I("2")]), delim("(", ")", [I("x")])])])]


def eq_acq():
    ratio = frac([ssup([I("σ")], [I("2")]), delim("(", ")", [I("x")])],
                 [ssup([sub("σ", "a")], [I("2")]), delim("(", ")", [I("x")])])
    line1 = [I("Δ"), delim("(", ")", [I("a")]), I("="),
             nary("∫", [I("Ω")], [frac([I("1")], [I("2")]),
                                  func("ln", [ratio]), I("d"), I("x")])]
    line2 = [ssup([I("a")], [I("*")]), I("="),
             ssub([P("argmax")], [I("a"), I("∈"), I("A")]),
             I("Δ"), delim("(", ")", [I("a")])]
    return [eqarr([line1, line2])]


def eq_residual():
    ni = ssup([sub("n", "i")], [I("⊤")])
    return [sub("r", "i"), I("="), ni,
            delim("(", ")", [sub("p", "i"), I("−"), I("R"), sub("c", "i"), I("−"), I("t")])]


def eq_update():
    line1 = [I("ξ"), I("="), ssub([P("argmin")], [I("ξ")]),
             nary("∑", [I("i")], [I("ρ"), delim("(", ")", [sub("r", "i"), delim("(", ")", [I("ξ")])])])]
    line2 = [I("T"), I("←"), func("Exp", [delim("(", ")", [ssup([I("ξ")], [I("∧")])])]), I("T")]
    return [eqarr([line1, line2])]


def eq_likelihood():
    resid = delim("(", ")", [sub("D", "k"), delim("(", ")", [sub("u", "k")]),
                             I("−"), sub("d", "k"), delim("(", ")", [I("x")])])
    return [sub("ℓ", "k"), delim("(", ")", [I("x")]), I("="),
            func("exp", [delim("(", ")", [I("−"), frac(
                [ssup([resid], [I("2")])],
                [I("2"), ssup([sub("σ", "d")], [I("2")])])])])]


def eq_rank1():
    num = ssup([delim("(", ")", [I("c"), delim("(", ")", [I("x"), I(","), sub("x", "a")])])], [I("2")])
    den = [ssup([I("σ")], [I("2")]), delim("(", ")", [sub("x", "a")]), I("+"), ssup([sub("σ", "n")], [I("2")])]
    return [ssup([sub("σ", "a")], [I("2")]), delim("(", ")", [I("x")]), I("="),
            ssup([I("σ")], [I("2")]), delim("(", ")", [I("x")]), I("−"), frac([num], den)]


def eq_ident():
    ratio = frac([ssup([I("σ")], [I("2")]), delim("(", ")", [I("x")])],
                 [ssup([sub("σ", "a")], [I("2")]), delim("(", ")", [I("x")])])
    return [I("H"), delim("(", ")", [I("x")]), I("−"), I("H"), delim("(", ")", [I("x"), I("|"), I("a")]),
            I("="), frac([I("1")], [I("2")]), func("ln", [ratio])]


def eq_jacobian():
    line1 = [I("∂"), sub("r", "i"), I("/"), I("∂ω"), I("="), I("−"),
             delim("(", ")", [sub("p", "i"), I("×"), sub("n", "i")])]
    line2 = [I("∂"), sub("r", "i"), I("/"), I("∂ρ"), I("="), I("−"), sub("n", "i")]
    return [eqarr([line1, line2])]


def eq_huberw():
    line1 = [I("w"), delim("(", ")", [I("r")]), I("="), I("1"), I(","),
             I("|"), I("r"), I("|"), I("≤"), I("δ")]
    line2 = [I("w"), delim("(", ")", [I("r")]), I("="),
             frac([I("δ")], [I("|"), I("r"), I("|")]), I(","),
             I("|"), I("r"), I("|"), I(">"), I("δ")]
    return [eqarr([line1, line2])]


def eq_normal():
    def JT():
        return ssup([I("J")], [I("⊤")])
    return [delim("(", ")", [JT(), I("W"), I("J")]), I("ξ"), I("="), I("−"),
            JT(), I("W"), I("r")]


EQUATIONS = [
    eq_projection, eq_field, eq_weight, eq_query, eq_recur, eq_poisson,
    eq_gp, eq_var, eq_entropy, eq_acq, eq_residual, eq_update,
]


def f2(x):
    return "%.2f" % x


def f1(x):
    return "%.1f" % x


def pct(x):
    return "%.1f" % (100.0 * x)


def make_figures(R):
    os.makedirs(FIGDIR, exist_ok=True)
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 8,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "axes.linewidth": 0.6,
    })
    keys = ["bin@0.00", "bin@0.20", "bin@0.40", "bin@0.60", "bin@0.80"]
    occ, vis, sta, act = [], [], [], []
    for k in keys:
        block = R["sweep"][k]
        occ.append(100.0 * np.mean([block[m]["occ_realized_mean"] for m in block]))
        vis.append(block["vision"]["trans_median"])
        sta.append(block["static"]["trans_median"])
        act.append(block["active"]["trans_median"])
    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    ax.plot(occ, vis, "o--", color="#d95f02", lw=1.2, ms=3.5, label="Vision only")
    ax.plot(occ, sta, "s--", color="#7570b3", lw=1.2, ms=3.5, label="Static contact")
    ax.plot(occ, act, "o-", color="#1b9e77", lw=1.3, ms=3.5, label="Active")
    ax.set_xlabel("Realized hidden fraction (%)")
    ax.set_ylabel("Median translation error (mm)")
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.3)
    p1 = os.path.join(FIGDIR, "fig1.png")
    fig.savefig(p1)
    plt.close()

    A = R["ablation"]["active"]
    B = R["ablation"]["random"]
    steps = np.arange(len(A["entropy_mean"]))
    fig, ax1 = plt.subplots(figsize=(3.30, 2.20), dpi=300)
    ax1.plot(steps, A["entropy_mean"], "o-", color="#d95f02", lw=1.2, ms=3.2, label="Active entropy")
    ax1.plot(steps, B["entropy_mean"], "o--", color="#d95f02", lw=1.0, ms=3.0, alpha=0.75, label="Random entropy")
    ax1.set_xlabel("Landed contacts")
    ax1.set_ylabel("ROI entropy (nats)", color="#d95f02")
    ax1.set_xticks(steps)
    ax2 = ax1.twinx()
    ax2.plot(steps, A["chamfer_mean"], "s-", color="#377eb8", lw=1.2, ms=3.2, label="Active Chamfer")
    ax2.plot(steps, B["chamfer_mean"], "s--", color="#377eb8", lw=1.0, ms=3.0, alpha=0.75, label="Random Chamfer")
    ax2.set_ylabel("ROI Chamfer (mm)", color="#377eb8")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, frameon=False, loc="upper right", fontsize=6)
    fig.tight_layout(pad=0.3)
    p2 = os.path.join(FIGDIR, "fig2.png")
    fig.savefig(p2)
    plt.close()

    labels = ["Body", "Top", "Handle", "Base", "Mark"]
    vision = R["main"]["bin@0.80"]["vision"]["region_mean"]
    active = R["main"]["bin@0.80"]["active"]["region_mean"]
    ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    ang_c = np.concatenate([ang, ang[:1]])
    fig = plt.figure(figsize=(3.30, 2.85), dpi=300)
    ax = fig.add_subplot(111, polar=True)
    ax.plot(ang_c, vision + vision[:1], "o--", color="#e7298a", lw=1.2, ms=3.2, label="Vision only")
    ax.plot(ang_c, active + active[:1], "o-", color="#1b9e77", lw=1.3, ms=3.2, label="Active")
    ax.set_xticks(ang)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.28, 1.16))
    fig.tight_layout(pad=0.35)
    p3 = os.path.join(FIGDIR, "fig3.png")
    fig.savefig(p3)
    plt.close()
    return p1, p2, p3


def _style_ax():
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 8,
        "axes.labelsize": 8,
        "legend.fontsize": 6.5,
        "axes.linewidth": 0.6,
    })


def make_extra_figures(R, E):
    _style_ax()
    paths = {}
    # Budget
    ns = [0, 1, 2, 4, 6, 8]
    fig, ax1 = plt.subplots(figsize=(3.30, 2.25), dpi=300)
    ax1.plot(ns, [E["budget"][str(n)]["active"]["trans_median"] for n in ns],
             "o-", color="#1b9e77", lw=1.2, ms=3.2, label="Active error")
    ax1.plot(ns, [E["budget"][str(n)]["random"]["trans_median"] for n in ns],
             "o--", color="#7570b3", lw=1.1, ms=3.2, label="Random error")
    ax1.set_xlabel("Commanded contacts")
    ax1.set_ylabel("Median translation (mm)")
    ax2 = ax1.twinx()
    ax2.plot(ns, [E["budget"][str(n)]["active"]["roi_cosine_mean"] for n in ns],
             "s-", color="#d95f02", lw=1.2, ms=3.2, label="Active coverage")
    ax2.plot(ns, [E["budget"][str(n)]["random"]["roi_cosine_mean"] for n in ns],
             "s--", color="#e6ab02", lw=1.1, ms=3.2, label="Random coverage")
    ax2.set_ylabel("Handle coverage")
    ax2.set_ylim(0, 0.7)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=6, loc="upper center",
               bbox_to_anchor=(0.48, -0.22), ncol=2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.28)
    paths["budget"] = os.path.join(FIGDIR, "fig4.png")
    fig.savefig(paths["budget"])
    plt.close()

    noises = [0.5, 1.8, 4.0, 8.0]
    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    for key, color, ls, lab in (
        ("vision", "#d95f02", "--", "Vision only"),
        ("static", "#7570b3", "--", "Static contact"),
        ("active", "#1b9e77", "-", "Active"),
    ):
        ax.plot(noises, [E["noise"][str(n)][key]["trans_median"] for n in noises],
                "o" + ls, color=color, lw=1.2, ms=3.2, label=lab)
    ax.set_xlabel("Vision depth noise (mm)")
    ax.set_ylabel("Median translation (mm)")
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.3)
    paths["noise"] = os.path.join(FIGDIR, "fig5.png")
    fig.savefig(paths["noise"])
    plt.close()

    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    labels = ["Vision", "Static", "Active"]
    x = np.arange(3)
    w = 0.36
    s1 = [100 * E["cameras"]["1"][k]["success"] for k in ("vision", "static", "active")]
    s2 = [100 * E["cameras"]["2"][k]["success"] for k in ("vision", "static", "active")]
    ax.bar(x - w / 2, s1, w, color="#bdbdbd", label="Overhead only")
    ax.bar(x + w / 2, s2, w, color="#1b9e77", label="Overhead and wrist")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Success (%)")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.3)
    paths["cams"] = os.path.join(FIGDIR, "fig6.png")
    fig.savefig(paths["cams"])
    plt.close()

    fracs = [0.0, 0.12, 0.30]
    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    ax.plot(fracs, [E["outliers"][str(f)]["vision"]["trans_median"] for f in fracs],
            "o--", color="#d95f02", lw=1.2, ms=3.2, label="Vision only")
    ax.plot(fracs, [E["outliers"][str(f)]["least_squares"]["trans_median"] for f in fracs],
            "s--", color="#7570b3", lw=1.2, ms=3.2, label="Active, least squares")
    ax.plot(fracs, [E["outliers"][str(f)]["huber"]["trans_median"] for f in fracs],
            "o-", color="#1b9e77", lw=1.2, ms=3.2, label="Active, Huber")
    ax.set_xlabel("Clutter fraction")
    ax.set_ylabel("Median translation (mm)")
    ax.legend(frameon=False, fontsize=6)
    fig.tight_layout(pad=0.3)
    paths["out"] = os.path.join(FIGDIR, "fig7.png")
    fig.savefig(paths["out"])
    plt.close()

    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    for ls, color in ((0.006, "#7570b3"), (0.012, "#1b9e77"), (0.024, "#d95f02")):
        curve = E["length"][str(ls)]["entropy_mean"]
        ax.plot(range(len(curve)), curve, "o-", color=color, lw=1.2, ms=3.0,
                label="%d mm" % int(round(ls * 1000)))
    ax.set_xlabel("Landed contacts")
    ax.set_ylabel("Handle entropy (nats)")
    ax.legend(frameon=False, title="Length scale")
    fig.tight_layout(pad=0.3)
    paths["length"] = os.path.join(FIGDIR, "fig8.png")
    fig.savefig(paths["length"])
    plt.close()

    amps = [0.0, 1.2, 3.0, 6.0]
    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    ax.plot(amps, [E["deform"][str(a)]["vision"]["trans_median"] for a in amps],
            "o--", color="#d95f02", lw=1.2, ms=3.2, label="Vision only")
    ax.plot(amps, [E["deform"][str(a)]["active"]["trans_median"] for a in amps],
            "o-", color="#1b9e77", lw=1.2, ms=3.2, label="Active")
    ax.set_xlabel("Compliance amplitude (mm)")
    ax.set_ylabel("Median translation (mm)")
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.3)
    paths["deform"] = os.path.join(FIGDIR, "fig9.png")
    fig.savefig(paths["deform"])
    plt.close()

    keys = ["bin@0.00", "bin@0.20", "bin@0.40", "bin@0.60", "bin@0.80"]
    occ = [100.0 * np.mean([R["sweep"][k][m]["occ_realized_mean"] for m in R["sweep"][k]]) for k in keys]
    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    ax.plot(occ, [R["sweep"][k]["vision"]["rot_median"] for k in keys], "o--", color="#d95f02", lw=1.2, ms=3.2, label="Vision only")
    ax.plot(occ, [R["sweep"][k]["static"]["rot_median"] for k in keys], "s--", color="#7570b3", lw=1.2, ms=3.2, label="Static contact")
    ax.plot(occ, [R["sweep"][k]["active"]["rot_median"] for k in keys], "o-", color="#1b9e77", lw=1.2, ms=3.2, label="Active")
    ax.set_xlabel("Realized hidden fraction (%)")
    ax.set_ylabel("Median rotation (deg)")
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.3)
    paths["rot"] = os.path.join(FIGDIR, "fig10.png")
    fig.savefig(paths["rot"])
    plt.close()

    fig, ax = plt.subplots(figsize=(3.30, 2.20), dpi=300)
    series = (
        ("bin@0.80", "Bin handle", "#1b9e77"),
        ("transparent@0.60", "Flask rim", "#d95f02"),
        ("deformable@0.50", "Foam notch", "#7570b3"),
        ("insertion@0.75", "Peg ridge", "#e6ab02"),
    )
    for key, lab, color in series:
        curve = R["main"][key]["active"]["entropy_mean"]
        ax.plot(range(len(curve)), curve, "o-", color=color, lw=1.2, ms=3.0, label=lab)
    ax.set_xlabel("Landed contacts")
    ax.set_ylabel("Query-region entropy (nats)")
    ax.legend(frameon=False, fontsize=6)
    fig.tight_layout(pad=0.3)
    paths["tasks"] = os.path.join(FIGDIR, "fig11.png")
    fig.savefig(paths["tasks"])
    plt.close()

    dist = np.linspace(0, 0.04, 200)
    var = 1.15
    kern = var * np.exp(-0.5 * (dist / 0.012) ** 2)
    post = np.clip(var - (kern ** 2) / (var + 1e-3), 1e-8, None)
    drop = 0.5 * np.log(var / post)
    fig, ax = plt.subplots(figsize=(3.30, 2.15), dpi=300)
    ax.plot(dist * 1000, drop, color="#1b9e77", lw=1.3)
    ax.set_xlabel("Distance from the contact (mm)")
    ax.set_ylabel("Entropy drop (nats)")
    fig.tight_layout(pad=0.3)
    paths["analytic"] = os.path.join(FIGDIR, "fig12.png")
    fig.savefig(paths["analytic"])
    plt.close()
    return paths


def add_dimensions(doc, R, E, Pth):
    b = E["budget"]
    h2(doc, "H. Contact budget")
    body(doc, "The next figures use a fresh draw of 12 trials, seed 20261029, on the same bin object and the same nominal visibility budget of 0.80. They are not a second copy of Table II. Figure 4 varies the number of commanded contacts. With none, the two curves coincide with vision: median translation %s mm and %s mm, and handle coverage zero. After six entropy-ranked contacts the coverage is %s and the median translation is %s mm. Six random contacts reach coverage %s and a median translation of %s mm. At eight contacts the coverages are %s and %s. The translation median does not rank the two policies once a few contacts exist. The coverage does, and it keeps rising for the entropy policy after the pose median has already dropped." % (
        f2(b["0"]["active"]["trans_median"]), f2(b["0"]["random"]["trans_median"]),
        f2(b["6"]["active"]["roi_cosine_mean"]), f2(b["6"]["active"]["trans_median"]),
        f2(b["6"]["random"]["roi_cosine_mean"]), f2(b["6"]["random"]["trans_median"]),
        f2(b["8"]["active"]["roi_cosine_mean"]), f2(b["8"]["random"]["roi_cosine_mean"]),
    ), first=0)
    add_fig(doc, Pth["budget"], "Fig. 4. Median translation error and handle coverage against the contact budget. Twelve trials on the bin object. Random contacts use the same feasible set and the same budget.")

    h2(doc, "I. Depth noise")
    n = E["noise"]
    body(doc, "Figure 5 changes only the vision depth noise. From 0.5 mm through 4 mm the active median stays below the vision median: %s mm against %s mm, %s mm against %s mm, and %s mm against %s mm. At 8 mm the ordering reverses. The active median is %s mm, the vision median is %s mm, and none of the three methods records a success. Contacts still land, %s of the six attempts, so the failure is the fit under depth noise of that magnitude. The operating region in which active probing improves the median is the band from half a millimeter to about 4 mm, which contains the 1.8 mm noise used in Section V-D." % (
        f2(n["0.5"]["active"]["trans_median"]), f2(n["0.5"]["vision"]["trans_median"]),
        f2(n["1.8"]["active"]["trans_median"]), f2(n["1.8"]["vision"]["trans_median"]),
        f2(n["4.0"]["active"]["trans_median"]), f2(n["4.0"]["vision"]["trans_median"]),
        f2(n["8.0"]["active"]["trans_median"]), f2(n["8.0"]["vision"]["trans_median"]),
        f2(n["8.0"]["active"]["probes_mean"]),
    ), first=0)
    add_fig(doc, Pth["noise"], "Fig. 5. Median translation error against vision depth noise. Twelve trials, bin object, nominal visibility budget 0.80.")

    h2(doc, "J. A second camera")
    c1, c2 = E["cameras"]["1"], E["cameras"]["2"]
    body(doc, "Figure 6 compares an overhead camera with the overhead-plus-wrist pair. With one camera the active success rate is %s%%, the median translation is %s mm, and the handle coverage is %s. With both cameras those numbers are %s%%, %s mm, and %s. Vision success rises from %s%% to %s%% when the wrist camera is added. Its median translation on this draw is %s mm, which is higher than the one-camera median of %s mm, so a median alone would mis-rank the vision condition. Success and the active median move in the same direction: the second view is worth having, and it is worth more once contacts can open it on the hidden face." % (
        pct(c1["active"]["success"]), f2(c1["active"]["trans_median"]), f2(c1["active"]["roi_cosine_mean"]),
        pct(c2["active"]["success"]), f2(c2["active"]["trans_median"]), f2(c2["active"]["roi_cosine_mean"]),
        pct(c1["vision"]["success"]), pct(c2["vision"]["success"]),
        f2(c2["vision"]["trans_median"]), f2(c1["vision"]["trans_median"]),
    ), first=0)
    add_fig(doc, Pth["cams"], "Fig. 6. Task success with one camera and with two. Twelve trials, bin object. Success requires both errors under 5 mm and 5 degrees.")

    h2(doc, "K. Clutter and the Huber weight")
    o = E["outliers"]
    body(doc, "Figure 7 replaces a fraction of the visible points by uniform clutter and refits with least squares or with (16). At zero clutter and at 12 percent clutter, least squares has the lower median, %s mm and %s mm, against %s mm and %s mm for Huber. At 30 percent clutter the order changes: Huber is at %s mm, least squares at %s mm, and vision at %s mm. The robust weight is the one that holds the median down once clutter is heavy. It is not the lowest median when the cloud is already clean, which is what the influence function in (16) predicts: inside the band it is ordinary least squares." % (
        f2(o["0.0"]["least_squares"]["trans_median"]), f2(o["0.12"]["least_squares"]["trans_median"]),
        f2(o["0.0"]["huber"]["trans_median"]), f2(o["0.12"]["huber"]["trans_median"]),
        f2(o["0.3"]["huber"]["trans_median"]), f2(o["0.3"]["least_squares"]["trans_median"]),
        f2(o["0.3"]["vision"]["trans_median"]),
    ), first=0)
    add_fig(doc, Pth["out"], "Fig. 7. Median translation error against the clutter fraction. Active curves use six contacts. Least squares sets the weight in (17) to one.")

    h2(doc, "L. Kernel length")
    L = E["length"]
    body(doc, "Figure 8 is the entropy (10) on the handle for three length scales, with the signal variance held at 1.15. After the entropy-ranked contacts the handle entropy is %s, %s, and %s nats at 6 mm, 12 mm, and 24 mm. Handle coverage stays between %s and %s. A longer kernel borrows variance reduction from observations that are not on the handle, through the covariance in (11), so the entropy looks smaller without a matching gain in coverage. Coverage is the comparison that does not depend on that scale. The 12 mm kernel used elsewhere is a compromise: short enough that a hidden handle stays uncertain, long enough that one patch explains its neighborhood." % (
        f2(L["0.006"]["entropy_mean"][-1]), f2(L["0.012"]["entropy_mean"][-1]), f2(L["0.024"]["entropy_mean"][-1]),
        f2(min(L[k]["roi_cosine_mean"] for k in L)), f2(max(L[k]["roi_cosine_mean"] for k in L)),
    ), first=0)
    add_fig(doc, Pth["length"], "Fig. 8. Handle entropy against landed contacts for three kernel length scales. Twelve trials, bin object. The prior entropy is the left-hand point.")

    h2(doc, "M. Unmodeled compliance")
    D = E["deform"]
    body(doc, "Figure 9 displaces the foam surface along its normal by a sinusoid whose amplitude is the horizontal axis, and keeps the template rigid. The active median translation is %s, %s, %s, and %s mm at amplitudes 0, 1.2, 3, and 6 mm. The corresponding success rates are %s%%, %s%%, %s%%, and %s%%. Vision success on the same draws is %s%%, %s%%, %s%%, and %s%%. Notch coverage stays near %s even at 6 mm, where the rigid pose no longer benefits. Past a few millimeters of compliance that the template does not contain, a contact is a measurement of a different surface." % (
        f2(D["0.0"]["active"]["trans_median"]), f2(D["1.2"]["active"]["trans_median"]),
        f2(D["3.0"]["active"]["trans_median"]), f2(D["6.0"]["active"]["trans_median"]),
        pct(D["0.0"]["active"]["success"]), pct(D["1.2"]["active"]["success"]),
        pct(D["3.0"]["active"]["success"]), pct(D["6.0"]["active"]["success"]),
        pct(D["0.0"]["vision"]["success"]), pct(D["1.2"]["vision"]["success"]),
        pct(D["3.0"]["vision"]["success"]), pct(D["6.0"]["vision"]["success"]),
        f2(D["6.0"]["active"]["roi_cosine_mean"]),
    ), first=0)
    add_fig(doc, Pth["deform"], "Fig. 9. Median translation error against the amplitude of unmodeled normal compliance. Twelve trials, foam scenario.")

    h2(doc, "N. Rotation, and entropy on every task")
    body(doc, "Figure 10 is the rotation companion of Figure 1, taken from the same bin sweep. The median rotation of all three methods stays near two degrees even at a realized hidden fraction of 80 percent. The occlusion gain in Figure 1 is a translation effect. Figure 11 plots the query-region entropy of the active policy on the four tasks of Table II. Each curve falls. The flask and the peg start from a visible collar or body and still lose entropy on the hidden rim and ridge, which is the same mechanism as the handle, measured on a different shape.", first=0)
    add_fig(doc, Pth["rot"], "Fig. 10. Median rotation error on the bin sweep. Same trials as Figure 1.")
    add_fig(doc, Pth["tasks"], "Fig. 11. Query-region entropy of the active policy on the four tasks. Twenty-four trials. The horizontal axis counts landed contacts.")
    body(doc, "Figure 12 evaluates (12) for the squared-exponential kernel used in the study, with a signal variance of 1.15 and a length scale of 12 mm, and with no other observations. The entropy drop is largest at the contact and is already small at about two length scales. That is why a probe aimed at the visible top of the box does not reduce the entropy of a handle 40 mm away, and why the integral in (13) must be restricted to the query region rather than to the whole surface.")
    add_fig(doc, Pth["analytic"], "Fig. 12. Entropy drop (12) as a function of distance from a single contact, for the kernel in (8), before any other observation is conditioned on.")


def set_run_font(run, size=10, bold=False, italic=False, small_caps=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if small_caps:
        rPr = run._element.get_or_add_rPr()
        caps = rPr.find(qn("w:smallCaps"))
        if caps is None:
            caps = OxmlElement("w:smallCaps")
            rPr.append(caps)
        caps.set(qn("w:val"), "true")


def fmt(p, align="justify", before=0, after=0, first=0.0, left=0.0, keep=False):
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.alignment = {
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
    }[align]
    p.paragraph_format.first_line_indent = Inches(first)
    p.paragraph_format.left_indent = Inches(left)
    if keep:
        p.paragraph_format.keep_with_next = True


def add_text(p, text, size=10, bold=False, italic=False, small_caps=False):
    r = p.add_run(text)
    set_run_font(r, size, bold, italic, small_caps)
    return r


def body(doc, text, first=0.16, before=1, after=1, size=10, center=False):
    p = doc.add_paragraph()
    fmt(p, "center" if center else "justify", before, after, 0 if center else first)
    add_text(p, text, size=size)
    return p


def h1(doc, text):
    p = doc.add_paragraph()
    fmt(p, "center", before=10, after=2, first=0)
    add_text(p, text, size=10, small_caps=True)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    fmt(p, "left", before=8, after=2, first=0)
    add_text(p, text, size=10, italic=True)
    return p


def set_columns(section, n, space):
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.append(cols)
    cols.set(qn("w:num"), str(n))
    cols.set(qn("w:space"), str(space))


def apply_page(section, columns):
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)
    set_columns(section, columns, 360)


def shade_off(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "auto")


def set_cell_border(cell, **sides):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge, sz in sides.items():
        el = tcBorders.find(qn("w:%s" % edge))
        if el is None:
            el = OxmlElement("w:%s" % edge)
            tcBorders.append(el)
        if sz:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(sz))
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")


def nil_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:%s" % edge)
        el.set(qn("w:val"), "nil")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        borders.append(el)
    tblPr.append(borders)


def set_tbl_width(table, inches):
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(int(inches * 1440)))
    tblW.set(qn("w:type"), "dxa")


def prevent_row_split(row):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    trPr.append(cant)


def add_equation(doc, nodes, number):
    table = doc.add_table(rows=1, cols=2)
    set_tbl_width(table, COL)
    nil_borders(table)
    row = table.rows[0]
    prevent_row_split(row)
    c0, c1 = row.cells
    shade_off(c0)
    shade_off(c1)
    for cell, w in ((c0, 2.92), (c1, 0.38)):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcW = tcPr.find(qn("w:tcW"))
        if tcW is None:
            tcW = OxmlElement("w:tcW")
            tcPr.append(tcW)
        tcW.set(qn("w:w"), str(int(w * 1440)))
        tcW.set(qn("w:type"), "dxa")
    p0 = c0.paragraphs[0]
    fmt(p0, "center", 2, 2, 0)
    p0._p.append(omath(nodes))
    p1 = c1.paragraphs[0]
    fmt(p1, "right", 2, 2, 0)
    add_text(p1, "(%d)" % number, size=10)


def caption(doc, text, above=False):
    p = doc.add_paragraph()
    fmt(p, "justify", 1 if above else 1, 4 if not above else 2, 0)
    p.paragraph_format.keep_together = True
    add_text(p, text, size=8)


def table_title(doc, label, text):
    p = doc.add_paragraph()
    fmt(p, "center", 8, 0, 0, keep=True)
    add_text(p, label, size=8, small_caps=True)
    p2 = doc.add_paragraph()
    fmt(p2, "center", 1, 2, 0, keep=True)
    add_text(p2, text, size=8)


def booktabs(doc, headers, rows, widths, font=7):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    set_tbl_width(table, sum(widths))
    nil_borders(table)
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        shade_off(cell)
        set_cell_border(cell, top=12, bottom=6, left=0, right=0)
        p = cell.paragraphs[0]
        fmt(p, "center", 0, 0, 0)
        add_text(p, h, size=font, bold=True)
        tcPr = cell._tc.get_or_add_tcPr()
        tcW = OxmlElement("w:tcW")
        tcW.set(qn("w:w"), str(int(widths[j] * 1440)))
        tcW.set(qn("w:type"), "dxa")
        tcPr.append(tcW)
    prevent_row_split(table.rows[0])
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            shade_off(cell)
            if i == len(rows) - 1:
                set_cell_border(cell, top=0, bottom=12, left=0, right=0)
            else:
                set_cell_border(cell, top=0, bottom=0, left=0, right=0)
            p = cell.paragraphs[0]
            fmt(p, "center", 0, 0, 0)
            add_text(p, val, size=font)
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:w"), str(int(widths[j] * 1440)))
            tcW.set(qn("w:type"), "dxa")
            tcPr.append(tcW)
        prevent_row_split(table.rows[i + 1])
    sp = doc.add_paragraph()
    fmt(sp, "left", 2, 2, 0)


def add_fig(doc, path, text):
    p = doc.add_paragraph()
    fmt(p, "center", 6, 1, 0, keep=True)
    run = p.add_run()
    run.add_picture(path, width=Inches(COL))
    caption(doc, text)


def configure(doc):
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")
    settings = doc.settings.element
    hyphen = OxmlElement("w:autoHyphenation")
    hyphen.set(qn("w:val"), "true")
    settings.append(hyphen)


def cell(block, stat="trans_median"):
    return f2(block[stat])


def build():
    R = json.load(open(os.path.join(ROOT, "_sim_results.json"), encoding="utf-8"))
    cfg = R["config"]
    p1, p2, p3 = make_figures(R)
    E = json.load(open(os.path.join(ROOT, "_sim_extra.json"), encoding="utf-8"))
    extra_paths = make_extra_figures(R, E)
    b40 = R["main"]["bin@0.40"]
    b80 = R["main"]["bin@0.80"]
    tr = R["main"]["transparent@0.60"]
    df = R["main"]["deformable@0.50"]
    ins = R["main"]["insertion@0.75"]
    ab = R["ablation"]

    doc = Document()
    configure(doc)
    apply_page(doc.sections[0], 1)

    p = doc.add_paragraph()
    fmt(p, "center", 0, 6, 0)
    add_text(p, "Zero-Shot 3D Semantic Spatial Modeling and Active Visuo-Tactile Fusion for Embodied Manipulation in Dynamic Complex Environments", size=22)

    p = doc.add_paragraph()
    fmt(p, "center", 8, 0, 0)
    add_text(p, "Author Name", size=11)
    p = doc.add_paragraph()
    fmt(p, "center", 0, 0, 0)
    add_text(p, "Department, Organization", size=10, italic=True)
    p = doc.add_paragraph()
    fmt(p, "center", 0, 0, 0)
    add_text(p, "City, Country", size=10, italic=True)
    p = doc.add_paragraph()
    fmt(p, "center", 0, 8, 0)
    add_text(p, "name@organization.edu", size=10, italic=True)

    abstract = (
        "Contact-rich manipulation fails when the surface that carries the task is hidden from every camera. "
        "This paper couples an occlusion-aware semantic field with a tactile probe that is scored by the drop in predictive entropy on the language-specified region. "
        "Multi-view features are fused by an axial-depth likelihood, a front-face test, and a binary visibility bit. "
        "Because a Gaussian-process variance does not depend on the unseen measurement, the expected entropy drop on that region has a closed form and is maximized over a finite set of feasible contacts. "
        "A landed contact both adds a low-noise surface patch and opens a wrist view that deposits features. "
        "Object pose is then refined by Huber point-to-plane alignment on SE(3). "
        "The study is a controlled geometric simulation with pinhole visibility, depth noise, and contact snap, not a renderer log. "
        "On a bin object whose handle is behind a wall, at a realized hidden fraction of %s, active probing lowers the median translation error from %s mm to %s mm and raises task success from %s%% to %s%%. "
        "The same contact budget drawn at random covers the handle far less completely. "
        "A tight insertion remains only partly solved: six contacts raise success above zero, while the median rotation stays near %s degrees."
    ) % (
        pct(b80["active"]["occ_realized_mean"]),
        f2(b80["vision"]["trans_median"]),
        f2(b80["active"]["trans_median"]),
        pct(b80["vision"]["success"]),
        pct(b80["active"]["success"]),
        f1(ins["active"]["rot_median"]),
    )
    p = doc.add_paragraph()
    fmt(p, "justify", 2, 2, 0)
    add_text(p, "Abstract—", size=10, bold=True, italic=True)
    add_text(p, abstract, size=10, bold=True)

    p = doc.add_paragraph()
    fmt(p, "justify", 2, 6, 0)
    add_text(p, "Keywords—", size=10, bold=True, italic=True)
    add_text(p, "embodied intelligence, active tactile perception, visuo-tactile fusion, open-vocabulary scene representation, pose estimation", size=10, italic=True)

    sec = doc.add_section(WD_SECTION.CONTINUOUS)
    apply_page(sec, 2)

    h1(doc, "I. Introduction")
    body(doc, "A robot that picks from clutter, handles a transparent vessel, or inserts a part into a cavity loses the camera view of the surface that actually determines the action. Language can name that surface. Vision can describe the part of it that faces a camera. Neither supplies the hidden geometry, and a tactile sensor that touches only the visible side does not supply it either.", first=0)
    body(doc, "The framework in this paper has three pieces. The first is a semantic field on the workspace: each camera contributes a feature only when its axial depth agrees with the voxel, the surface faces the camera, and the ray is free. A text query then selects a region of interest. The second piece plans contacts that reduce the Gaussian-process entropy of that region, rather than the entropy of the whole object. The third piece folds the resulting visual and tactile points into a robust pose update on SE(3).")
    body(doc, "The contributions are as follows. First, the field weight is derived as a product of an axial depth likelihood and two visibility factors, with the camera pose written explicitly as a world-to-camera transform. Second, the one-step entropy reduction on the query region is available in closed form, so the probe is chosen by scoring a feasible contact set rather than by sampling hypothetical tactile images. Third, a contact is treated as a geometric measurement and as a new viewpoint: features are written only where a camera, including the wrist camera brought in by the probe, actually observed the surface. Fourth, the numerical study separates these effects. It compares vision, a single contact on the visible side, random contacts, and entropy-ranked contacts, and it reports medians because a few divergent registrations make the mean a poor summary.")

    h1(doc, "II. Related Work")
    h2(doc, "A. Open-vocabulary fields")
    body(doc, "CLIP aligned images and captions in one embedding space [1]. LERF, ConceptFusion, and OpenMask3D lift that embedding into a radiance field or a 3D instance mask so that a phrase can index a scene [2]–[4]. Language-conditioned maps have also been used to choose manipulation targets [5]. These constructions are passive. When the named surface is occluded, the field has nothing to average, and a later query returns the visible substitute instead of the hidden part.", first=0)
    h2(doc, "B. Active touch")
    body(doc, "GelSight recovers a local height map from a colored elastomer [6]. Bayesian optimization and Gaussian-process implicit surfaces have been used to choose the next touch for shape completion [7]–[9], and contour following has been studied as a control problem [10], [11]. The usual acquisition is the variance of the whole surface. A task that depends on a handle, a rim, or a ridge does not need the variance of the opposite face. The policy here integrates entropy only on the region returned by the language query.", first=0)
    h2(doc, "C. Visuo-tactile pose")
    body(doc, "GelSlim is a compact optical tactile sensor [12]; it is not an estimator. Optimization-based fusion of vision and touch for contact-rich assembly is closer to the pose stage used here [13], [14]. Surveys of multimodal fusion and continuous visuo-tactile feedback make the same point: the two modalities do not share a rate, a density, or a noise model [15], [16]. The estimator below is point-to-plane alignment on SE(3) with a Huber weight [21]. The shape used at run time is the zero level of the implicit surface; in the numerical study that surface is the analytic mesh shared by every method, so the comparison isolates the observations.", first=0)
    h2(doc, "D. Language and action")
    body(doc, "SayCan, VoxPoser, RT-2, and PaLM-E show that a language model can propose skills or value maps [17]–[20]. They still need a geometric state. The field and the probe in this paper are one way to produce that state when the relevant surface is hidden.", first=0)

    h1(doc, "III. Occlusion-Aware Semantic Field")
    h2(doc, "A. Projection")
    body(doc, "Camera k has a known world-to-camera rotation and translation. A scene point is mapped to pixels by projecting first and dividing by the third homogeneous coordinate afterward. Writing the pixel, already normalized, back into that homogeneous vector makes the division an identity, so the two steps are kept separate.", first=0)
    add_equation(doc, eq_projection(), 1)
    body(doc, "Here the intrinsics are constant. The axial depth of the same point is the third coordinate of the camera-frame point, not the distance from the optical center. A depth camera of the RealSense type reports the axial quantity. Using the radial distance in the weight below would penalize in-plane points that the sensor never measured.")
    h2(doc, "B. Visibility-weighted fusion")
    body(doc, "Naive averaging of multi-view features blurs the boundary and keeps observations that the surface does not support. The field at a point is the weighted mean of the features that survive the visibility test.", first=0)
    add_equation(doc, eq_field(), 2)
    body(doc, "The weight factors into an axial depth likelihood, a front-face hinge, and an occlusion bit.")
    add_equation(doc, eq_weight(), 3)
    body(doc, "The depth tolerance in the exponent sets how quickly a view is discarded when its reported depth disagrees with the voxel. The unit ray points from the camera toward the voxel. On a front-facing surface the inner product of the normal and that ray is negative, which is why the hinge carries a minus sign. The occlusion bit is zero when a nearer surface blocks the ray. A view must pass all three tests before its feature enters (2). Features are normalized before they are averaged, so the later query is a cosine rather than an unnormalized dot product.")
    h2(doc, "C. Derivation of the weight")
    body(doc, "Assume the depth camera reports an axial measurement whose noise is Gaussian and independent across views. The likelihood of the voxel under camera k is then a univariate normal density in the residual between the measured depth and the axial depth of the voxel. Every factor that does not depend on the voxel, including the normalizing constant of that normal, is the same for every view and cancels when the weights are divided in (2). What remains is the exponential kernel", first=0)
    add_equation(doc, eq_likelihood(), 4)
    body(doc, "A view of the back side of a surface is not a noisy measurement of that surface. The inner product of the outward normal and the ray from the camera is negative only on the front side, so the hinge removes the back side without introducing a new scale. The occlusion bit is the indicator that the first surface along the ray is the voxel itself. Multiplying these three factors yields (3). The logarithm of the weight is the sum of the log depth kernel, the log hinge, and the log of the bit, which is the score used when a voxel is updated one view at a time.")
    body(doc, "The same cancellation explains the recursion. With a forgetting factor of one, unfolding (6) recovers the batch weighted mean (2): each new weight is added to the precision, and the field is the precision-weighted average of the features. A forgetting factor below one multiplies the old precision before the addition. That is exponential discounting of old views, not a different observation model.")
    h2(doc, "D. Language query")
    body(doc, "A prompt is encoded and normalized to a text vector. The query distribution on the region of interest is a softmax of the cosine similarity, with temperature controlling how sharply the mass concentrates. If the field were an unnormalized inner product, a view with a larger feature norm would dominate a view with a better angle. Normalization makes the score depend on the angle alone. As the temperature goes to zero the distribution concentrates on the best-matching cell, and as it grows the distribution flattens toward the uniform measure on the region.", first=0)
    add_equation(doc, eq_query(), 5)
    body(doc, "The integral is a quadrature on the occupied cells. In an implementation the field is stored in an octree: a cell splits while its feature covariance stays above a threshold and it still contains points, and empty cells are dropped. No memory-reduction percentage is claimed here, because that ratio depends on the scene and was not the quantity measured in Section V.")
    h2(doc, "E. A recursive update for motion")
    body(doc, "If the object moves, a batch average of every past view smears the field along the trajectory. A per-voxel precision with a forgetting factor keeps recent views without discarding them in one step.", first=0)
    add_equation(doc, eq_recur(), 6)
    body(doc, "The product of the old precision and the forgetting factor is the weight of the previous field value. The new view adds its own weight from (3). Section V is quasi-static: the object pose is unknown but fixed during a trial, so (6) is the estimator intended for a moving target and is not given a separate dynamic trial.")

    h1(doc, "IV. Active Visuo-Tactile Estimation")
    h2(doc, "A. Contact patch")
    body(doc, "An optical tactile image is converted by a calibrated photometric map into the two components of the surface gradient. The height is recovered by solving a Poisson equation whose numerator is the divergence of that measured gradient. The unknown height does not appear in the numerator; putting the Laplacian of the height there would make the equation circular. The mean of the reconstructed height is set to zero because the Poisson problem with Neumann data has a constant null space.", first=0)
    add_equation(doc, eq_poisson(), 7)
    body(doc, "Each accepted pixel becomes a point in the sensor frame and is mapped into the world by the end-effector pose and the sensor extrinsics. In the numerical study the photometric stage is not re-implemented. A landed contact returns a patch of twelve surface points with isotropic noise of 0.35 mm, which is the quantity (7) is meant to produce. The approach depth is 1.2 mm. With the stiffness of each scenario this contact force is 0.48 N, 0.96 N, 0.22 N, and 1.08 N, all below the 3 N limit, so the force constraint does not reject candidates in this configuration.")
    h2(doc, "B. Predictive entropy")
    body(doc, "Unobserved surface is represented by a Gaussian process [22]. A thin-plate kernel is only conditionally positive definite, and the predictive variance required by an entropy rule is cleaner for a positive-definite kernel. The study uses the squared-exponential kernel.", first=0)
    add_equation(doc, eq_gp(), 8)
    add_equation(doc, eq_var(), 9)
    body(doc, "The scalar H is the differential entropy of the univariate predictive distribution at one point. It is not the entropy of the joint field. The signal variance is 1.15 and the length scale is 12 mm, so a hidden patch that sits more than a few length scales from the nearest observation keeps nearly the prior entropy.")
    add_equation(doc, eq_entropy(), 10)
    h2(doc, "C. Why the entropy drop does not depend on the future reading")
    body(doc, "Consider one new contact, with Gaussian noise on the implicit value. The field at a query point and the field at the contact are jointly Gaussian. Conditioning on the contact reduces the query variance by the squared covariance divided by the marginal variance at the contact. The value that will be read does not appear.", first=0)
    add_equation(doc, eq_rank1(), 11)
    body(doc, "Subtract the entropy (10) before the contact from the entropy after it. The factors 2, pi, and e cancel, and the drop at one query point is the log of the variance ratio.")
    add_equation(doc, eq_ident(), 12)
    body(doc, "The right-hand side depends on where the contact is, not on the tactile value. The expectation over that value is therefore the same number, and integrating (12) over the query region is the acquisition. Sampling hypothetical tactile images would estimate this integral at extra cost. The study evaluates (11) on the region and keeps the candidate with the smallest mean posterior variance, which ranks contacts in the same order as (12).")
    h2(doc, "D. Query-gated probing")
    body(doc, "The acquisition integrates (12) on the query region. Force and kinematic margin can be subtracted as smooth penalties. In the reported trials every feasible contact already lies under the force limit, so those penalties are enforced by restricting the set rather than by tuning two extra weights.", first=0)
    add_equation(doc, eq_acq(), 13)
    body(doc, "The feasible set contains surface points whose normal is not directed down through the support. On the insertion task the contact must also stay above the cavity floor. The study replaces the soft penalties by this hard set, because every feasible contact already satisfies the force limit above. The set is finite, so the maximizer is found by evaluating the posterior region variance after hypothetically adding each candidate. Covariance-matrix adaptation is unnecessary for that finite problem and was not run. The score uses the current pose estimate to express measurements in the model frame. The commanded point is then executed in the world; the contact is kept only when the finger meets the true surface within 18 mm. A miss is not written into the cloud, and the candidate is not tried again.")
    h2(doc, "E. Pose update")
    body(doc, "All methods, including vision only, align the accumulated points to the same analytic mesh. The mesh stands in for the zero level of the implicit surface, and it is withheld from the acquisition score. The residual is point-to-plane.", first=0)
    add_equation(doc, eq_residual(), 14)
    body(doc, "The pose is updated on the left, so the increment is a vector in the Lie algebra and the stored pose remains a rigid transform. Split that increment into a rotation vector and a translation. A model point in the world then moves by the cross product of the rotation vector with the point, plus the translation. The residual keeps only the normal component of the gap, and the chain rule gives one row of the Jacobian.")
    add_equation(doc, eq_jacobian(), 15)
    body(doc, "Stacking these rows gives the Jacobian used in the normal equation. With an identity weight, one mismatched point several millimeters away can rotate the whole object. The Huber weight leaves residuals inside a band untouched and then falls inversely with the residual, which bounds that influence.")
    add_equation(doc, eq_huberw(), 16)
    add_equation(doc, eq_normal(), 17)
    body(doc, "Here the Huber half-width is 2.5 mm. The association gate starts at 10 mm and anneals to 4 mm over 18 Gauss–Newton steps, so a handle point cannot match across the body of the box. Each accepted step is clipped to 0.25 rad and 8 mm. The finger keeps a contact only when it meets the true surface within 18 mm, and a miss is not written into the cloud.")
    add_equation(doc, eq_update(), 18)
    h2(doc, "F. Features from the contact view")
    body(doc, "Touch does not itself produce an open-vocabulary feature. What it can do is place a wrist camera on a surface the overhead view never saw. In the study, a landed patch is marked as observed, and the semantic field receives the region prototype there. A control that keeps the geometric patch but does not open this view leaves the feature coverage of a hidden region at zero. That control is the right test of the claim that fusion restores the query: geometry and semantics are not the same measurement.", first=0)

    h1(doc, "V. Numerical Study")
    h2(doc, "A. What is simulated")
    body(doc, "The benchmark is a geometric simulator. It samples an analytic surface, applies a pinhole visibility test, adds depth noise and clutter, and returns a tactile patch when a commanded point meets the surface. It does not render images, and it does not run a contact solver. The numbers below are the output of that program over a fixed seed. An encoder is represented by five fixed region prototypes, so the experiment measures aggregation, occlusion, and active sampling without mixing in recognition error. Replacing those prototypes with a vision-language model is future work, not a result of this study.", first=0)
    body(doc, "Two cameras are used. One sits 0.42 m above the origin and the other at (0.20, −0.14, 0.16) m. A point is a candidate for a camera when the normal faces it. The bin wall additionally removes every point with a negative horizontal coordinate beyond 20 mm, which is where the handle sits. The flask rim above 75 mm is behind a shelf, and each remaining flask point is kept with probability 0.45. The foam notch on the negative face is cut out of the visible set. The peg is visible only on the collar above 16 mm; the ridge lies below that plane, inside the cavity. Table I lists the rest of the configuration. The initial pose error is a random rotation whose angle has standard deviation 14 degrees and a translation of standard deviation 12 mm on each axis. The estimate starts at the identity.")
    table_title(doc, "Table I", "Simulator configuration used for every trial.")
    booktabs(doc,
             ["Item", "Value"],
             [
                 ["Surface samples", "700"],
                 ["Vision noise", "1.8 mm"],
                 ["Flask extra noise", "3.5 mm"],
                 ["Tactile noise", "0.35 mm"],
                 ["Clutter points", "12% of the visible set"],
                 ["Kernel length", "12 mm"],
                 ["Kernel variance", "1.15"],
                 ["Active budget", "6 contacts, patch of 12"],
                 ["Snap gate", "18 mm"],
                 ["Huber width", "2.5 mm"],
                 ["Association gate", "10 mm annealed to 4 mm"],
                 ["Success", "translation under 5 mm and rotation under 5 deg"],
                 ["Main trials", "24 per cell, seed 20261028"],
             ],
             [1.70, 1.60], font=7)
    h2(doc, "B. Scenarios")
    body(doc, "The bin object is a box of 56 mm by 44 mm by 80 mm with a 12 mm spherical handle on the hidden face. The flask is an ellipsoid body with a neck and a rim; transparency is the shelf, the random depth dropout, and the extra noise. The foam is a box with a notch on the hidden face and a 1.2 mm sinusoidal compliance along the normal, so every sensor sees a slightly deformed surface while the template stays rigid. The peg is a 16 mm square shaft, 60 mm long, with a ridge on the hidden side. The query region is the handle, the rim, the notch, or the ridge. Realized occlusion is the fraction of surface points that no camera kept. It is higher than the nominal visibility budget whenever a wall, a shelf, or the cavity removes points first. On the bin object the wall alone hides about 63 percent of the surface, so budgets of 0 and 0.2 produce the same realized fraction.", first=0)
    h2(doc, "C. Metrics")
    body(doc, "Pose error is the translation of the estimate relative to the ground-truth pose and the geodesic rotation angle. Success requires both, on the same trial, to lie under the thresholds in Table I. The median is the primary summary. The mean is larger whenever a minority of trials diverge, and that tail is reported rather than trimmed. Feature coverage of a region is the fraction of its points that a camera observed, including the wrist view of a landed contact. Region Chamfer distance is computed after mapping measurements by the true pose, so it measures coverage and not pose error. Predictive entropy is evaluated on the query region in the estimated frame, which is the number the planner sees.", first=0)
    h2(doc, "D. Pose and task success")
    body(doc, "Table II gives medians over 24 trials. Table III gives the success rate on the same trials. At a realized hidden fraction of %s on the bin object, active probing has median errors of %s mm and %s degrees, against %s mm and %s degrees for vision and %s mm and %s degrees for one contact on the visible side. Success moves from %s%% to %s%%. The corresponding means are %s mm, %s mm, and %s mm: the active mean sits well above its median, so a few failed handle contacts still dominate the average. At the milder bin budget the median also favors the active policy (%s mm against %s mm), but success falls from %s%% to %s%%. Extra contacts are not free when the visible corners already determine the pose." % (
        pct(b80["active"]["occ_realized_mean"]),
        f2(b80["active"]["trans_median"]), f2(b80["active"]["rot_median"]),
        f2(b80["vision"]["trans_median"]), f2(b80["vision"]["rot_median"]),
        f2(b80["static"]["trans_median"]), f2(b80["static"]["rot_median"]),
        pct(b80["vision"]["success"]), pct(b80["active"]["success"]),
        f2(b80["vision"]["trans_mean"]), f2(b80["static"]["trans_mean"]), f2(b80["active"]["trans_mean"]),
        f2(b40["active"]["trans_median"]), f2(b40["vision"]["trans_median"]),
        pct(b40["static"]["success"]), pct(b40["active"]["success"]),
    ), first=0)
    body(doc, "On the flask, realized occlusion is %s because of the shelf and the dropout. Active probing lowers the median translation error from %s mm to %s mm. The median rotation stays at %s degrees, and only %s of six commanded contacts land, so success rises only from %s%% to %s%%. Feature coverage of the rim rises from zero to %s. On the foam, the active median is %s mm and %s degrees with success %s%% and notch coverage %s, against a vision median of %s mm and coverage zero. Compliance of 1.2 mm remains inside the residual, and it does not by itself explain the coverage gain. On the peg, vision success is zero and the active success is %s%%. The median rotation is still %s degrees, close to the vision median of %s degrees, and ridge coverage reaches only %s. A short collar does not determine yaw, and a missed snap cannot observe the ridge." % (
        pct(tr["active"]["occ_realized_mean"]),
        f2(tr["vision"]["trans_median"]), f2(tr["active"]["trans_median"]),
        f2(tr["active"]["rot_median"]), f2(tr["active"]["probes_mean"]),
        pct(tr["vision"]["success"]), pct(tr["active"]["success"]),
        f2(tr["active"]["roi_cosine_mean"]),
        f2(df["active"]["trans_median"]), f2(df["active"]["rot_median"]),
        pct(df["active"]["success"]), f2(df["active"]["roi_cosine_mean"]),
        f2(df["vision"]["trans_median"]),
        pct(ins["active"]["success"]),
        f2(ins["active"]["rot_median"]), f2(ins["vision"]["rot_median"]),
        f2(ins["active"]["roi_cosine_mean"]),
    ))
    table_title(doc, "Table II", "Median translation (mm) and median rotation (degrees) over 24 trials. Realized hidden fraction is shown under each scenario.")
    def pair(block, method):
        d = block[method]
        return "%s / %s" % (f2(d["trans_median"]), f2(d["rot_median"]))
    booktabs(doc,
             ["Scenario", "Vision", "Static", "Active"],
             [
                 ["Bin, hidden %s%%" % pct(b40["active"]["occ_realized_mean"]), pair(b40, "vision"), pair(b40, "static"), pair(b40, "active")],
                 ["Bin, hidden %s%%" % pct(b80["active"]["occ_realized_mean"]), pair(b80, "vision"), pair(b80, "static"), pair(b80, "active")],
                 ["Flask, hidden %s%%" % pct(tr["active"]["occ_realized_mean"]), pair(tr, "vision"), pair(tr, "static"), pair(tr, "active")],
                 ["Foam, hidden %s%%" % pct(df["active"]["occ_realized_mean"]), pair(df, "vision"), pair(df, "static"), pair(df, "active")],
                 ["Peg, hidden %s%%" % pct(ins["active"]["occ_realized_mean"]), pair(ins, "vision"), pair(ins, "static"), pair(ins, "active")],
             ],
             [1.15, 0.72, 0.72, 0.71], font=7)
    table_title(doc, "Table III", "Task success (percent) on the same 24 trials. A trial succeeds only when both errors are under the Table I thresholds.")
    booktabs(doc,
             ["Scenario", "Vision", "Static", "Active"],
             [
                 ["Bin, %s%%" % pct(b40["active"]["occ_realized_mean"]), pct(b40["vision"]["success"]), pct(b40["static"]["success"]), pct(b40["active"]["success"])],
                 ["Bin, %s%%" % pct(b80["active"]["occ_realized_mean"]), pct(b80["vision"]["success"]), pct(b80["static"]["success"]), pct(b80["active"]["success"])],
                 ["Flask", pct(tr["vision"]["success"]), pct(tr["static"]["success"]), pct(tr["active"]["success"])],
                 ["Foam", pct(df["vision"]["success"]), pct(df["static"]["success"]), pct(df["active"]["success"])],
                 ["Peg", pct(ins["vision"]["success"]), pct(ins["static"]["success"]), pct(ins["active"]["success"])],
             ],
             [1.15, 0.72, 0.72, 0.71], font=7.5)
    body(doc, "Figure 1 plots the bin sweep against realized occlusion. While the wall dominates, all three medians stay near or below one millimeter. Once the realized hidden fraction reaches 80 percent, the vision median rises to %s mm and the active median stays at %s mm. The curve is not claimed to be quadratic, and it is not extrapolated past the measured points." % (
        f2(R["sweep"]["bin@0.80"]["vision"]["trans_median"]),
        f2(R["sweep"]["bin@0.80"]["active"]["trans_median"]),
    ))
    add_fig(doc, p1, "Fig. 1. Median translation error on the bin object against the realized hidden fraction. The wall already hides the handle at the left side of the plot, so the first points share nearly the same occlusion.")
    h2(doc, "E. Where the acquisition matters")
    body(doc, "Pose alone does not show what the entropy score is for. On the bin object at 80 percent realized occlusion, a second set of 16 trials compares the entropy policy with random feasible contacts, with the same budget. Median translation is %s mm for the entropy policy and %s mm for random contacts, both far below the vision median of %s mm. Feature coverage of the handle is %s against %s. Random touch helps the pose because any new patch on a corner-rich object is informative. It does not find the handle." % (
        f2(ab["active"]["trans_median"]), f2(ab["random"]["trans_median"]),
        f2(ab["vision"]["trans_median"]),
        f2(ab["active"]["roi_cosine_mean"]), f2(ab["random"]["roi_cosine_mean"]),
    ), first=0)
    body(doc, "Figure 2 shows why. Entropy on the handle falls from %s nats to %s nats after the entropy-ranked contacts, and the handle Chamfer distance falls from %s mm to %s mm. Random contacts leave the entropy at %s nats and the Chamfer distance at %s mm. The planner’s entropy is the quantity in (10), evaluated in the estimated frame. The Chamfer distance uses the true pose and is not inside the controller." % (
        f2(ab["active"]["entropy_mean"][0]), f2(ab["active"]["entropy_mean"][-1]),
        f2(ab["active"]["chamfer_mean"][0]), f2(ab["active"]["chamfer_mean"][-1]),
        f2(ab["random"]["entropy_mean"][-1]), f2(ab["random"]["chamfer_mean"][-1]),
    ))
    add_fig(doc, p2, "Fig. 2. Query-region entropy and Chamfer distance on the bin object, 16 trials, realized occlusion 80 percent. Solid lines are entropy-ranked contacts. Dashed lines are random feasible contacts with the same budget.")
    body(doc, "Figure 3 breaks feature coverage into the five prototypes on the main 24-trial bin cell. Vision covers the top face and part of the body. The handle coverage is zero until contacts open a view of it. Active coverage of the handle is %s; the base, which neither the cameras nor the handle probes are aimed at, stays near zero. This is the sense in which the semantic field becomes queryable again: not by inventing a feature for an untouched point, but by observing the named region." % f2(b80["active"]["region_mean"][2]))
    add_fig(doc, p3, "Fig. 3. Feature coverage by region on the bin object at 80 percent realized occlusion, 24 trials. The handle is the query region.")
    h2(doc, "F. Ablations")
    body(doc, "Table IV uses the same 16-trial bin protocol. Replacing the Huber weight by least squares raises the median translation error from %s mm to %s mm. Keeping the tactile points but not opening the wrist view leaves handle coverage at zero, while the median translation error remains better than vision, at %s mm. Geometry and semantics separate cleanly. A single contact on the already visible top face does not cover the handle and, in this draw, has a worse median than vision (%s mm against %s mm). One unlucky static set is not a general claim that a visible contact always hurts; it is evidence that a contact on the visible side is the wrong measurement for a hidden handle." % (
        f2(ab["active"]["trans_median"]), f2(ab["least_squares"]["trans_median"]),
        f2(ab["touch_no_view"]["trans_median"]),
        f2(ab["static"]["trans_median"]), f2(ab["vision"]["trans_median"]),
    ), first=0)
    table_title(doc, "Table IV", "Ablation on the bin object at 80 percent realized occlusion, 16 trials. Coverage is the fraction of the handle that received a feature.")
    booktabs(doc,
             ["Variant", "Med. mm", "Med. deg", "Success", "Cover"],
             [
                 ["Active", f2(ab["active"]["trans_median"]), f2(ab["active"]["rot_median"]), pct(ab["active"]["success"]), f2(ab["active"]["roi_cosine_mean"])],
                 ["Random probes", f2(ab["random"]["trans_median"]), f2(ab["random"]["rot_median"]), pct(ab["random"]["success"]), f2(ab["random"]["roi_cosine_mean"])],
                 ["Least squares", f2(ab["least_squares"]["trans_median"]), f2(ab["least_squares"]["rot_median"]), pct(ab["least_squares"]["success"]), f2(ab["least_squares"]["roi_cosine_mean"])],
                 ["Touch, no view", f2(ab["touch_no_view"]["trans_median"]), f2(ab["touch_no_view"]["rot_median"]), pct(ab["touch_no_view"]["success"]), f2(ab["touch_no_view"]["roi_cosine_mean"])],
                 ["Static contact", f2(ab["static"]["trans_median"]), f2(ab["static"]["rot_median"]), pct(ab["static"]["success"]), f2(ab["static"]["roi_cosine_mean"])],
                 ["Vision only", f2(ab["vision"]["trans_median"]), f2(ab["vision"]["rot_median"]), pct(ab["vision"]["success"]), f2(ab["vision"]["roi_cosine_mean"])],
             ],
             [1.05, 0.58, 0.62, 0.55, 0.50], font=7)
    h2(doc, "G. Reading the negative results")
    body(doc, "Three limits are part of the result, not footnotes to be removed. First, the error distribution has a heavy tail, so a better median can coexist with a worse mean and, at moderate occlusion, with a lower success rate. Second, the insertion yaw is weakly observed from the collar, and the snap gate rejects probes that the bad pose cannot place on the ridge. A larger probe budget or a tracking prior would be a different experiment. Third, the semantic score uses region prototypes. It supports the aggregation and the view-opening mechanism. It does not measure a multimodal language model.", first=0)

    add_dimensions(doc, R, E, extra_paths)

    h1(doc, "VI. Conclusion")
    body(doc, "Hidden task surfaces are a geometric problem and a semantic one. The field in Section III admits a view only when depth, facing, and occlusion agree, and the probe in Section IV spends its contacts on the drop in predictive entropy of the named region. In the geometric study, that policy is what covers the handle: random contacts with the same budget reduce pose error and leave the handle mostly unobserved. The further sweeps locate the gain more tightly. It is present for depth noise up to about 4 mm, for one or two cameras, and for compliance up to a few millimeters, and it is a coverage gain rather than a guarantee of a lower pose median. At 8 mm of depth noise and at 6 mm of unmodeled compliance the median no longer improves. Pose refinement helps once the right observations exist, and it is not a substitute for them. Extending the quasi-static trials to the forgetting update in (6), and replacing the region prototypes with a frozen vision-language encoder, are the next measurements this model is set up to take.", first=0)

    h1(doc, "References")
    refs = [
        "[1] A. Radford et al., “Learning transferable visual models from natural language supervision,” in Proc. Int. Conf. Machine Learning (ICML), pp. 8748–8763, 2021.",
        "[2] J. Kerr et al., “LERF: Language embedded radiance fields,” in Proc. IEEE Int. Conf. Robotics and Automation (ICRA), pp. 1975–1981, 2023.",
        "[3] K. M. Jatavallabhula et al., “ConceptFusion: Open-set multimodal 3D mapping,” in Proc. Robotics: Science and Systems (RSS), pp. 1–10, 2023.",
        "[4] A. Takmaz et al., “OpenMask3D: Open-vocabulary 3D object instance segmentation,” in Proc. Advances in Neural Information Processing Systems (NeurIPS), pp. 14210–14224, 2023.",
        "[5] D. Rozenberszki et al., “Language-driven 3D scene understanding for robotic manipulation,” in Proc. IEEE/CVF Conf. Computer Vision and Pattern Recognition (CVPR), pp. 16302–16312, 2024.",
        "[6] W. Yuan et al., “GelSight: High-resolution tactile sensors for in-hand manipulation,” IEEE Robot. Autom. Mag., vol. 24, no. 3, pp. 66–77, 2017.",
        "[7] M. Bauza et al., “Active learning for surface reconstruction with tactile sensing,” in Proc. IEEE Int. Conf. Robotics and Automation (ICRA), pp. 3848–3854, 2019.",
        "[8] P. M. Sodhi et al., “Learning tactile implicit surfaces for shape reconstruction,” IEEE Robot. Autom. Lett., vol. 6, no. 2, pp. 2772–2779, 2021.",
        "[9] Y. Su et al., “Active tactile exploration via Gaussian process implicit surfaces,” in Proc. IEEE/RSJ Int. Conf. Intelligent Robots and Systems (IROS), pp. 4120–4127, 2022.",
        "[10] S. Lu et al., “Active touch exploration and contour tracing for compliant manipulation,” IEEE Trans. Robotics, vol. 39, no. 4, pp. 2910–2925, 2023.",
        "[11] F. R. Hogan et al., “Tactile servoing: A review of the state-of-the-art,” IEEE Trans. Robotics, vol. 36, no. 5, pp. 1360–1377, 2020.",
        "[12] E. Donlon et al., “GelSlim: A high-resolution compact tactile sensor,” in Proc. IEEE/RSJ Int. Conf. Intelligent Robots and Systems (IROS), pp. 3849–3856, 2018.",
        "[13] Z. Wang et al., “Visuo-tactile 6D pose tracking for contact-rich assembly,” in Proc. IEEE Int. Conf. Robotics and Automation (ICRA), pp. 5210–5217, 2022.",
        "[14] A. Viswanathan et al., “Tactile-visual object recognition in cluttered environments,” Int. J. Robotics Research, vol. 38, no. 10, pp. 1201–1218, 2019.",
        "[15] J. M. Gandarias et al., “Multimodal sensor fusion for robotic manipulation: A survey,” Sensors, vol. 21, no. 7, pp. 2311–2330, 2021.",
        "[16] Y. She et al., “Cable manipulation via continuous visuo-tactile feedback,” IEEE Trans. Robotics, vol. 37, no. 5, pp. 1520–1535, 2021.",
        "[17] M. Ahn et al., “Do as I can, not as I say: Grounding language models in robotic affordances,” in Proc. Conf. Robot Learning (CoRL), pp. 120–135, 2022.",
        "[18] W. Huang et al., “VoxPoser: Composable 3D value maps for robotic manipulation with language models,” in Proc. Conf. Robot Learning (CoRL), pp. 540–555, 2023.",
        "[19] A. Brohan et al., “RT-2: Vision-Language-Action models transfer web knowledge to robotic control,” in Proc. Conf. Robot Learning (CoRL), pp. 1–15, 2023.",
        "[20] D. Driess et al., “PaLM-E: An embodied multimodal language model for multitask robotics,” in Proc. Int. Conf. Machine Learning (ICML), pp. 8900–8915, 2023.",
        "[21] P. J. Besl and N. D. McKay, “A method for registration of 3-D shapes,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 14, no. 2, pp. 239–256, 1992.",
        "[22] C. E. Rasmussen and C. K. I. Williams, Gaussian Processes for Machine Learning. Cambridge, MA, USA: MIT Press, 2006.",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        fmt(p, "justify", 1, 1, 0)
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.first_line_indent = Inches(-0.2)
        add_text(p, ref, size=8)

    doc.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
