#!/usr/bin/env python3
"""Ordinary-NEB energy profile of one Stage-7 path directory (00 ... NN), plain python3 for Vanda.

Per image: last energy(sigma->0) and its ionic step count, largest force on a free atom (VTST prints
"FORCES: max atom, RMS" in each image OUTCAR), Ce/total magnetisation. Energies relative to image 00.
The highest intermediate image gives only the ordinary-NEB screening estimate E_a(NEB) ~ max_i E_i - E_00,
not a saddle point (supervisor 2026-10-15); CI-NEB comes after the path review.

    python3 neb_profile.py <path dir>
"""
import os
import re
import sys


def last(pattern, txt, group=1):
    m = re.findall(pattern, txt)
    return m[-1] if m else None


def main(d):
    imgs = sorted(x for x in os.listdir(d) if re.fullmatch(r"\d\d", x))
    rows = []
    for k in imgs:
        f = os.path.join(d, k, "OUTCAR")
        t = open(f, errors="ignore").read() if os.path.exists(f) else ""
        # energy(sigma->0) is printed at every electronic step; take the one closing each ionic step
        es = re.findall(r"FREE ENERGIE OF THE ION-ELECTRON SYSTEM.*?energy\(sigma->0\) =\s*(-?\d+\.\d+)", t, re.S)
        e = es[-1] if es else None
        fm = last(r"FORCES: max atom, RMS\s+(\d+\.\d+)", t)
        mag = last(r"number of electron\s+[\d.]+\s+magnetization\s+(-?\d+\.\d+)", t)
        steps = len(es)
        rows.append((k, float(e) if e else None, fm, mag, steps))
    e0 = rows[0][1]
    print("image  E(sigma->0) eV   E-E00 eV  Fmax eV/A  mag   steps")
    for k, e, fm, mag, n in rows:
        print("%s   %14s  %8s  %9s  %5s  %5d" % (k, "%.5f" % e if e is not None else "-",
                                                  "%+.3f" % (e - e0) if e is not None and e0 is not None else "-",
                                                  fm or "-", mag or "-", n))
    mid = [(e, k) for k, e, *_ in rows[1:-1] if e is not None]
    if mid and e0 is not None and rows[-1][1] is not None:
        top = max(mid)
        print("highest image %s: E_a(ordinary NEB, screening estimate) = %+.3f eV; dE(FS-IS) = %+.3f eV"
              % (top[1], top[0] - e0, rows[-1][1] - e0))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
