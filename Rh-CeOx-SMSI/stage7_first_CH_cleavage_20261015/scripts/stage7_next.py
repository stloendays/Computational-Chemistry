"""Stage 7 next steps driver (2026-10-25). Runs on this PC; talks to Vanda through the `vanda` ssh alias.

    python stage7_next.py d-parent                 report D1-D3 and the lowest finished parent
    python stage7_next.py d-endpoints [--submit]   lowest D parent -> D4-D8 inputs -> upload [-> qsub]
    python stage7_next.py neb A B C [--submit]     next_steps/neb/<M>_neb -> upload, endpoint OUTCARs [-> qsub]

Without --submit everything is staged on Vanda and nothing is queued. Every qsub is appended to
SUBMISSION_stage7.txt. Interpreter: D:/Research/CatalystForge/.venv/Scripts/python.exe (ASE).
"""
import argparse
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
REMOTE = "/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015"
D_STARTS = ["D1_Ce2O3_hO_2Odown", "D2_Ce2O3_hO_1Odown", "D3_Ce2O3_gasgeom"]
D_SETS = ["D4_CH4_Ce", "D5_CH4_edge", "D6_CH3Ce_HOc", "D7_CH3Os_HOc", "D8_CH3Ce_HOs"]


def ssh(cmd, check=True):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "vanda", cmd], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8")
    if check and r.returncode:
        sys.exit("ssh failed: %s\n%s" % (cmd, r.stderr[-500:]))
    return r.stdout


def scp(src, dst, recursive=False):
    subprocess.run(["scp", "-q"] + (["-r"] if recursive else []) + [src, dst], check=True)


def log_submit(name, jid, note):
    with open(os.path.join(HERE, "SUBMISSION_stage7.txt"), "a", newline="\n") as fh:
        fh.write("%s %s %s\n" % (name, jid, note))


def d_parent():
    """{start: (relax converged, final E or None)} from the newest stage files on Vanda."""
    out = {}
    for n in D_STARTS:
        d = "%s/inputs/%s" % (REMOTE, n)
        t = ssh("cd %s; r=$(ls -t vasp_stageB_relax*.out | head -1); grep -c 'reached required accuracy' $r; "
                "s=$(ls -t OUTCAR_stageC_SP* 2>/dev/null | head -1); "
                "[ -n \"$s\" ] && grep -q 'EDIFF is reached' $s && grep 'energy(sigma->0)' $s | tail -1 || true" % d,
                check=False).split("\n")
        ok = t[0].strip() not in ("", "0")
        e = float(t[1].split()[-1]) if len(t) > 1 and "sigma" in t[1] else None
        out[n] = (ok, e)
    return out


def cmd_d_parent(_):
    st = d_parent()
    for n, (ok, e) in st.items():
        print("%-20s relax %-9s final E %s" % (n, "converged" if ok else "running", "%.5f" % e if e else "-"))
    done = {n: e for n, (_, e) in st.items() if e is not None}
    if len(done) == len(D_STARTS):
        print("lowest parent:", min(done, key=done.get))
    else:
        print("not all three starts are final yet")
    return st


def cmd_d_endpoints(a):
    st = cmd_d_parent(a)
    done = {n: e for n, (_, e) in st.items() if e is not None}
    if len(done) < len(D_STARTS) and not a.allow_partial:
        sys.exit("wait for D1-D3 (or pass --allow-partial to use the lowest finished one)")
    par = min(done, key=done.get)
    loc = os.path.join(HERE, "next_steps", "parents", "%s_CONTCAR_final" % par)
    os.makedirs(os.path.dirname(loc), exist_ok=True)
    scp("vanda:%s/inputs/%s/CONTCAR" % (REMOTE, par), loc)
    out = os.path.join(HERE, "next_steps", "D_endpoints")
    subprocess.run([PY, os.path.join(HERE, "build_D_endpoints.py"), loc, out], check=True)
    for n in D_SETS:
        rd = "%s/inputs/%s" % (REMOTE, n)
        if ssh("test -e %s && echo exists || true" % rd).strip():
            sys.exit("%s already exists on Vanda; not overwriting" % rd)
        scp(os.path.join(out, n), "vanda:%s/inputs/" % REMOTE, recursive=True)
        # POTCAR Ce O (D parent) + C H (CH4 gas reference), order = POSCAR species Ce O C H
        ssh("cd %s && cat ../%s/POTCAR ../G_CH4/POTCAR > POTCAR && grep TITEL POTCAR | awk '{print $4}' | "
            "tr '\\n' ' '" % (rd, par))
        if a.submit:
            jid = ssh("cd %s && qsub job.pbs" % rd).strip()
            log_submit(n, jid, "D_endpoint_parent_%s_%s" % (par, datetime.date.today().strftime("%Y%m%d")))
            print(n, jid)
    print("staged" if not a.submit else "submitted", "D endpoints on parent", par)


def cmd_neb(a):
    for m in a.models:
        loc = os.path.join(HERE, "next_steps", "neb", "%s_neb" % m)
        ini, fin = open(os.path.join(loc, "ENDPOINTS")).read().split()
        rd = "%s/neb/%s_neb" % (REMOTE, m)
        if ssh("test -e %s && echo exists || true" % rd).strip():
            sys.exit("%s already exists on Vanda; not overwriting" % rd)
        ssh("mkdir -p %s/neb" % REMOTE)
        scp(loc, "vanda:%s/neb/" % REMOTE, recursive=True)
        scp(os.path.join(HERE, "neb_profile.py"), "vanda:%s/" % rd)
        last = sorted(x for x in os.listdir(loc) if x.isdigit())[-1]
        # endpoint energies in the same smearing (ISMEAR 1) as the NEB images: newest relaxation OUTCAR
        ssh("cd %s && cp ../../inputs/%s/POTCAR . && "
            "cp \"$(ls -t ../../inputs/%s/OUTCAR_stageB_relax* | head -1)\" 00/OUTCAR && "
            "cp \"$(ls -t ../../inputs/%s/OUTCAR_stageB_relax* | head -1)\" %s/OUTCAR" % (rd, ini, ini, fin, last))
        # Images start from scratch (ISTART 0, ICHARG 2, as built). Do not copy endpoint WAVECARs into the images:
        # on 2026-10-26 every interpolated image away from the ends then failed (A04 -1508 eV, B05 -1220 eV,
        # C04 -3.8e7 eV with a frozen or exploding rms(c); B02/B03 hit NELM 300) while 01/06 converged; the A, B, C
        # bands were restarted from scratch (1493946, 1496320, 1496321).
        # Ce-containing bands: MAGMOM = 1 on every Ce, 0 elsewhere (user, 2026-10-27, "1可以的"). Without it the
        # default 1 uB/atom start sent the B/C images into high-spin states (B06 -326.5 vs ~-353 eV, mag 31-42;
        # C01 -452 vs ~-502 eV, mag 58). All Ce of the B, C endpoints are Ce3+; for D check the endpoint moments.
        # MAGMOM alone was not enough: with ALGO Normal / NELM 300 the B/C images still did not converge (NELM hit,
        # moments drifting). Ce-containing bands therefore run in two steps in one job - stage A on every image
        # (endpoint INCAR_stageA_spinSP + IMAGES, NEB parallel layout, MAGMOM), then the NEB reading each image's
        # own WAVECAR - generated by neb_two_step_20261027.sh (user, 2026-10-27). Run it after this staging.
        if "Ce" in open(os.path.join(loc, "00", "POSCAR")).read().split("\n")[5].split():
            print(ssh("cd %s && sp=($(sed -n 6p 00/POSCAR)); nn=($(sed -n 7p 00/POSCAR)); mg=''; "
                      "for i in \"${!sp[@]}\"; do v=0; [ \"${sp[$i]}\" = Ce ] && v=1; mg=\"$mg ${nn[$i]}*$v\"; done; "
                      "sed -i '/^MAGMOM/d' INCAR; echo \"MAGMOM =$mg\" >> INCAR; grep ^MAGMOM INCAR" % rd))
        if a.submit:
            jid = ssh("cd %s && qsub job_neb.pbs" % rd).strip()
            log_submit("%s_neb" % m, jid, "ordinary_NEB_LCLIMB_F_%s" % datetime.date.today().strftime("%Y%m%d"))
            print(m, jid)
        else:
            print(m, "staged at", rd)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("d-parent").set_defaults(f=cmd_d_parent)
    p = sp.add_parser("d-endpoints")
    p.add_argument("--submit", action="store_true")
    p.add_argument("--allow-partial", action="store_true")
    p.set_defaults(f=cmd_d_endpoints)
    p = sp.add_parser("neb")
    p.add_argument("models", nargs="+")
    p.add_argument("--submit", action="store_true")
    p.set_defaults(f=cmd_neb)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
