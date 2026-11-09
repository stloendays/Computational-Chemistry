"""NEB D rebuilt (2026-11-09), explicit band.
Run 1526950 (single IDPP band D9 -> D7) collapsed: image 04 at +6.5 eV with H45-H42 1.09 A. D9 has CH4 2.85 A
(H45...O38) above the Ce2O2 rhombus of the cluster; D7 has CH3 on O40 and H45 on O38 across the rhombus
(O38-O40 3.67 A). Linear/IDPP interpolation abstracts H at long range and swings the CH3 through H45.
Band built here as abstraction then rebound:
  keyframe 02: C above the rhombus centre shifted toward O38 (C-O38 2.45 A), H45 on the C->O38 line (C-H 1.30),
               CH3 umbrella flattened (80 deg) opening away from O38, rotated so no H points at O40;
  keyframe 05: C 2.05 A from O40, H45 on O38 (O-H 0.98), CH3 umbrella (80 deg) opening away from O40.
CH3 orientation between keyframes by quaternion slerp (rigid CH3, C-H kept 1.09-1.10), C and H45 piecewise
linear, slab atoms blended linearly IS -> FS."""
import os, itertools, numpy as np
from ase.io import read, write
from ase.geometry import find_mic
from scipy.spatial.transform import Rotation as Rot, Slerp
P = 'neb_3x3/D_neb/%02d/POSCAR'
IS, FS = read(P % 0), read(P % 7)
s = IS.get_chemical_symbols(); C = s.index('C'); H = [i for i, x in enumerate(s) if x == 'H']; HB, O40, O38 = 45, 40, 38
rest = [h for h in H if h != HB]
def mic(v, a): return find_mic(v, a.cell)[0]
def unit(v): return v / np.linalg.norm(v)
# put every atom of IS in the periodic copy nearest O38, and FS atom by atom next to IS (continuous band)
# (the reacting O40 is the periodic copy on the far side of the CH4, 4.1 A from O38 in x - not O38's rhombus
# partner - so raw coordinates are kept; FS atoms are moved next to their IS positions)
FS.positions = IS.positions + mic(FS.positions - IS.positions, IS)
o38I = IS.positions[O38]; o40I = IS.positions[O40]
o38F = FS.positions[O38]; o40F = FS.positions[O40]
cI = IS.positions[C].copy(); cF = FS.positions[C].copy()
vI = np.array([unit(mic(IS.positions[h] - IS.positions[C], IS)) for h in rest])
vF = np.array([unit(mic(FS.positions[h] - FS.positions[C], FS)) for h in rest])
hbI = cI + 1.10 * unit(mic(IS.positions[HB] - IS.positions[C], IS))
hbF = o38F + mic(FS.positions[HB] - FS.positions[O38], FS)
def frame(vs):
    t = unit(vs.sum(0)); x = unit(vs[0] - vs[0].dot(t) * t); y = np.cross(t, x)
    th = np.degrees(np.mean([np.arccos(v.dot(t)) for v in vs]))
    ch = np.sign(np.cross(vs[0], vs[1]).dot(t))
    return np.array([x, y, t]).T, th, ch
RI, thI, chI = frame(vI); RF, thF, chF = frame(vF)
print('IS umbrella %.1f deg chir %+d; FS %.1f deg chir %+d' % (thI, chI, thF, chF))
assert chI == chF, 'handedness differs: the CH3 would have to invert'
def local(th, ch):  # H directions in the local frame, label k at angle 120*k*ch
    r = np.radians(th)
    return np.array([[np.sin(r) * np.cos(np.radians(120 * k * ch)), np.sin(r) * np.sin(np.radians(120 * k * ch)), np.cos(r)] for k in range(3)])
def frame_axis(t, phi):
    t = unit(t); e1 = unit(np.cross(t, [0, 0, 1])); e2 = np.cross(t, e1)
    x = np.cos(np.radians(phi)) * e1 + np.sin(np.radians(phi)) * e2
    return np.array([x, np.cross(t, x), t]).T
# keyframe positions (slab blended at the image fraction)
def blend(f, pI, pF): return pI + f * (pF - pI)
o38_2, o40_2 = blend(2 / 7, o38I, o38F), blend(2 / 7, o40I, o40F)
mid = 0.5 * (o38_2 + o40_2) + np.array([0, 0, 1.6])
c2 = o38_2 + 2.45 * unit(mid - o38_2); a2 = unit(o38_2 - c2); hb2 = c2 + 1.30 * a2
o38_5, o40_5 = blend(5 / 7, o38I, o38F), blend(5 / 7, o40I, o40F)
c5 = o40_5 + 2.05 * unit(unit(c2 - o40_5) + unit(cF - o40F)); a5 = unit(o40_5 - c5)
hb5 = o38_5 + 0.98 * unit(hbF - o38F)
best = None
for p2 in range(0, 360, 2):
    R2 = frame_axis(-a2, p2); h2 = (R2 @ local(80, chI).T).T
    if min(np.degrees(np.arccos(h.dot(unit(o40_2 - c2)))) for h in h2) < 50:
        continue
    for p5 in range(0, 360, 2):
        R5 = frame_axis(-a5, p5)
        ang = [Rot.from_matrix(B @ A.T).magnitude() for A, B in ((RI, R2), (R2, R5), (R5, RF))]
        sc = sum(x ** 2 for x in ang)
        if best is None or sc < best[0]:
            best = (sc, R2, R5, p2, p5, np.degrees(ang))
print('rotations IS->02 %.0f, 02->05 %.0f, 05->FS %.0f deg' % tuple(best[5]))
R2, R5 = best[1], best[2]
keys = [(0, cI, hbI, RI, thI), (2, c2, hb2, R2, 80.0), (5, c5, hb5, R5, 80.0), (7, cF, hbF, RF, thF)]
os.makedirs('Dnew', exist_ok=True)
for k in range(8):
    j = max(i for i in range(3) if keys[i][0] <= k) if k < 7 else 2
    (k0, c0, b0, Ra, t0), (k1, c1, b1, Rb, t1) = keys[j], keys[j + 1]
    u = (k - k0) / (k1 - k0)
    R = Slerp([0, 1], Rot.from_matrix([Ra, Rb]))(u).as_matrix(); th = t0 + u * (t1 - t0)
    c = c0 + u * (c1 - c0); hb = b0 + u * (b1 - b0)
    im = IS.copy(); im.positions = IS.positions + (k / 7) * (FS.positions - IS.positions)
    if 2 < k < 7:   # H45 rides on O38 after keyframe 02: O-H shortens 1.15 -> 0.98 -> FS, direction interpolated
        o38k = im.positions[O38]
        if k <= 5:
            u2 = (k - 2) / 3; d0, d1 = hb2 - o38_2, hb5 - o38_5
        else:
            u2 = (k - 5) / 2; d0, d1 = hb5 - o38_5, hbF - o38F
        L = (1 - u2) * np.linalg.norm(d0) + u2 * np.linalg.norm(d1)
        hb = o38k + L * unit((1 - u2) * unit(d0) + u2 * unit(d1))
    im.positions[C] = c; im.positions[HB] = hb
    for h, v in zip(rest, (R @ local(th, chI).T).T):
        im.positions[h] = c + 1.095 * v
    D = im.get_all_distances(mic=True); np.fill_diagonal(D, 99)
    hh = min(D[i, j_] for i in H for j_ in H if i < j_)
    o40 = im.positions[O40]
    ang = [np.degrees(np.arccos(unit(mic(im.positions[h] - c, im)).dot(unit(mic(o40 - c, im))))) for h in rest]
    nonCH = min(D[i, j_] for i in H + [C] for j_ in range(len(im)) if j_ not in H + [C])
    print('%02d HH %.2f | C-H45 %.2f H45-O38 %.2f C-O38 %.2f C-O40 %.2f | H-C-O40 %s | C/H-slab min %.2f' % (
        k, hh, D[C, HB], D[HB, O38], D[C, O38], D[C, O40], ' '.join('%.0f' % x for x in ang), nonCH))
    if 0 < k < 7:
        os.makedirs('Dnew/%02d' % k, exist_ok=True)
        im.wrap()
        write('Dnew/%02d/POSCAR' % k, im, format='vasp', direct=True, sort=False)
