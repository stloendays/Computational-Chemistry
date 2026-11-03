#!/usr/bin/env python3
"""DynSMSI stage 7 (first C-H cleavage of CH4 on four models), REPORT-ONLY monitor. Runs on the Vanda login node,
called every 5 h by monitor_stage7.ps1 (Windows task "vanda-stage7-monitor-5h"), which uploads this file first.
Adapted from monitor_d3.py (D3 sensitivity, 2026-10-13).

Jobs (2026-10-15, CFP04-CF-046, batch_cpu, 72 h, watchdog 250200 s), one chain per job.pbs:
  run_stage stageA_spinSP LABORT scf     (ISPIN 2, ALGO All, NELM 500, ISMEAR 1)
  run_stage stageB_relax  LSTOP relax    (IBRION 2, NSW 400, EDIFFG -0.02, ISMEAR 1)
  cp POSCAR POSCAR_start; cp CONTCAR POSCAR
  run_stage stageC_SP     LABORT scf     (ISMEAR 0, SIGMA 0.05, EDIFF 1E-6)   -- G_CH4 has only A + B
  exit 3 = "<stage> SCF NOT converged", exit 4 = "<stage> RELAX NOT converged", exit 2 = missing input
Models: A = Rh(111) p(4x4); B = Ce4O6 layer/Rh(111); C = Ce2O3 cluster/Rh(111); D = Ce2O3 on CeO2(111) (support only);
G = gas CH4. Kinds: ref (clean model), ch4 (molecular CH4), dis (CH3 + H), sup (D series), gas.

Mechanical in-protocol actions (user, 2026-10-17: "授予监控更大的权利，让他可以自动继续跑"):
  * refresh the allocation session (~/hpc_login.sh, silent) when `hpc project` asks for amgr login;
  * AUTO-RESUME a chain that ended without a fatal error, up to MAX_AUTO times per system, same physics settings:
      stageA* SCF not converged / killed at walltime  -> INCAR_stageA_spinSP_rN (ISTART 1, ICHARG 0, reads WAVECAR)
                                                         -> stageB_relax -> stageC_SP     (10-17 precedent, stage-4 L6)
      stageB* relax not converged / watchdog / wall   -> CONTCAR -> POSCAR (backups kept), INCAR_stageB_relax_rN
                                                         (ISTART 1/ICHARG 1 if WAVECAR else 0/2) -> stageC_SP
      stageC* SCF not converged / wall                -> INCAR_stageC_SP_rN (ALGO All, NELM 500, reads WAVECAR)
    No resume when: fatal VASP marker, PBS Exit < 0 / hold, missing input, adsorbate/structure flag, no ionic step
    written (stage B), missing WAVECAR (stage A/C) or MAX_AUTO reached -> ATTENTION -> headless Claude takeover,
    which may resume under the same rules (claude_takeover_prompt_stage7.md).

Per job: PBS state, stage, ionic steps, free-atom Fmax, energy, Ce moment summary, exit code.
Done (rc=0 chain) -> acceptance: relaxation "reached required accuracy", SP "EDIFF is reached", free-atom
Fmax <= 0.02 eV/A, fixed (F F F) atoms unmoved vs POSCAR_start, Ce |m| ~0 or ~1, |m(Rh)| <= 0.3, adsorbate checks.
All 20 accepted -> $S/E_stage7.txt + $S/results/stage7_table.md, DONE.

HISTORY -> check (DynSMSI stage 2-6 + D3 records)
  09-10/11  LDIPOL metal/oxide slab SCF charge-sloshing                                   -> SCF oscillation check
  09-11     spin SCF hit NELM inside a relaxation                                          -> NELM-in-relaxation check
  09-12     watchdog margin < one ionic step: jobs killed at walltime                     -> walltime-kill / watchdog
  09-12     ZBRENT fatal / EDDDAV / segfault aborts                                        -> fatal-marker scan
  09-13     queued jobs counted as running                                                -> job_state from qstat JSON
  09-15/20/23 PBS "too many failed attempts" system hold (Exit -3/-10)                   -> held / Exit -3 ATTENTION
  09-18     "maxF" included fixed atoms                                                   -> free-atom forces only
  09-20/21/23 SP NELM hits                                                                -> exit 3 ATTENTION
  09-21     stale WAVECAR reset Ce spins; 09-23 AFM read as collapse                       -> per-Ce moment summary
  09-23     home quota 40 G exceeded: all jobs died in the same minute                    -> home + scratch quota gate,
                                                                                             simultaneous-death check
  09-24     allocation session expired                                                    -> hpc_login.sh refresh
  09-24     check that did not cd into the run dir saw no files                           -> absolute paths only
  09-30     MAGMOM-free seeds gave intermediate moments                                   -> 0.3<|m(Ce)|<0.8, |m(Rh)|>0.3
  09-30     truncated pbs names mismatched                                                -> jobs tracked by PBS id
                                                                                             (SUBMISSION_stage7.txt) and
                                                                                             by the full '#PBS -N' name
  10-13     desorption / O2 formation during a relaxation                                  -> structure flags
  stage 7   (new) adsorbate left the surface, CH4 dissociated spontaneously, CH3+H recombined, H2 formed
                                                                                          -> adsorbate flags (report only)
"""
import os, re, json, glob, math, subprocess, datetime, time, traceback

S = '/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015'
IN = os.path.join(S, 'inputs')
MON = os.path.join(S, 'monitor')
STATE = os.path.join(MON, 'state.json')
SUBLOG = os.path.join(S, 'SUBMISSION_stage7.txt')
EOUT = os.path.join(S, 'E_stage7.txt')
RES = os.path.join(S, 'results', 'stage7_table.md')
FMAX_ACCEPT = 0.02
FIX_TOL = 1e-3
SCRATCH_ATTN, HOME_ATTN = 85.0, 90.0
STALL_H = 2.0
OSC_MIN_STEPS, OSC_WINDOW, OSC_AMP = 150, 30, 1e-2
MAG_JUMP, E_RISE = 1.5, 0.10
DESORB_DZ, OO_MIN = 5.0, 1.45
CH_BOND, HH_BOND, CO_BOND = 1.40, 0.90, 1.60
QUEUE_WAIT_H, SIMUL_MIN, CADENCE_H = 24, 15, 5
D_SUPPORT_TOP = 7.897 + 0.4     # A, top of the CeO2(111) support (D0 zmax, BUILD_REPORT); above = Ce2O3 cluster
FATAL = [
    (r'No space left on device|Disk quota exceeded', '磁盘/配额写满'),
    (r'ZBRENT: fatal', 'ZBRENT 线搜索致命错误'),
    (r'Error EDDDAV|EDDDAV: Call to ZHEGV|ZHEGV failed', 'EDDDAV/ZHEGV 对角化失败'),
    (r'Sub-Space-Matrix is not hermitian', '子空间矩阵非厄米'),
    (r'BRMIX: very serious problems', 'BRMIX 电荷混合严重错误'),
    (r'VERY BAD NEWS|internal error in subroutine', 'VASP 内部错误'),
    (r'forrtl: severe|[Ss]egmentation fault|SIGSEGV', '程序崩溃（forrtl/段错误）'),
    (r'BAD TERMINATION|killed by signal', 'MPI 进程被杀'),
    (r'Cannot allocate memory|out of memory|oom-kill', '内存不足'),
    # 2026-11-02: 3x3 C adsorbate INCARs had 3 LDAUL entries for 5 species -> "Error reading item LDAUL"
    (r'I REFUSE TO CONTINUE|Error reading item', 'VASP 拒绝 INCAR（输入错误）'),
]
# name: (PBS id at submission, kind)
SYSTEMS = {
    'A0_ref': ('1460278', 'ref'), 'A1_CH4_top': ('1460279', 'ch4'), 'A2_CH3top_Hfcc': ('1460280', 'dis'),
    'B0_ref': ('1460281', 'ref'), 'B1_CH4_Ce': ('1460282', 'ch4'), 'B2_CH4_Os': ('1460283', 'ch4'),
    'B3_CH3Ce_HOs': ('1460284', 'dis'), 'B4_CH3Os_HOs': ('1460285', 'dis'),
    'C0_ref': ('1460286', 'ref'), 'C1_CH4_perimRh': ('1460287', 'ch4'), 'C2_CH4_Ce': ('1460288', 'ch4'),
    'C3_CH3perimRh_HOt': ('1460289', 'dis'), 'C4_CH3perimRh_Hfcc': ('1460290', 'dis'),
    'C5_CH3Ce_HOt': ('1460291', 'dis'), 'C6_CH3farRh_Hfcc': ('1460292', 'dis'),
    'C7_CH4_Ot': ('1506831', 'ch4'), 'C8_CH3Ot_HOb': ('1506832', 'dis'),
    'D0_CeO2_111': ('1460293', 'sup'), 'D1_Ce2O3_hO_2Odown': ('1460294', 'sup'),
    'D2_Ce2O3_hO_1Odown': ('1460295', 'sup'), 'D3_Ce2O3_gasgeom': ('1460296', 'sup'),
    'D4_CH4_Ce': ('1507327', 'ch4'), 'D5_CH4_edge': ('1507330', 'ch4'),
    'D6_CH3Ce_HOc': ('1507331', 'dis'), 'D7_CH3Os_HOc': ('1507333', 'dis'), 'D8_CH3Ce_HOs': ('1507334', 'dis'),
    'G_CH4': ('1460297', 'gas'),
}
RETIRED = {'C7_CH4_Ot', 'C8_CH3Ot_HOb', 'D2_Ce2O3_hO_1Odown', 'D3_Ce2O3_gasgeom', 
           'D4_CH4_Ce', 'D5_CH4_edge', 'D6_CH3Ce_HOc', 'D7_CH3Os_HOc', 'D8_CH3Ce_HOs'}  # 2026-10-29 supervisor: A/C -> Rh p(3x3), D -> CeO2 p(2x2); 4x4 jobs cancelled by the user
D_ENDPOINTS = ['D4_CH4_Ce', 'D5_CH4_edge', 'D6_CH3Ce_HOc', 'D7_CH3Os_HOc', 'D8_CH3Ce_HOs']   # parent D3, 2026-10-29
STAGES = ['stageA_spinSP', 'stageB_relax', 'stageC_SP']
# 2026-10-29 supervisor (Notion 14): A and C on Rh(111) p(3x3), D on CeO2(111) p(2x2) 3 TL; no separate final single
# point, the energy is E0 of the converged relaxation. Two-stage chains (stage A -> stage B) in inputs_3x3/.
IN3 = os.path.join(S, 'inputs_3x3')
# 2026-11-02: all but C0_ref resubmitted with per-species LDAU (old runs in inputs_3x3_bad_ldau_20261102/)
SYSTEMS3 = {
    '3x3/A0_ref': ('1510390', 'ref'), '3x3/A1_CH4_top': ('1510391', 'ch4'), '3x3/A2_CH3top_Hfcc': ('1510392', 'dis'),
    '3x3/C0_ref': ('1507566', 'ref'), '3x3/C1_CH4_perimRh': ('1510393', 'ch4'), '3x3/C2_CH4_Ce': ('1510394', 'ch4'),
    '3x3/C7_CH4_Ot': ('1510398', 'ch4'), '3x3/C3_CH3perimRh_HOt': ('1510395', 'dis'), '3x3/C4_CH3perimRh_Hfcc': ('1510396', 'dis'),
    '3x3/C5_CH3Ce_HOt': ('1510397', 'dis'), '3x3/C8_CH3Ot_HOb': ('1510399', 'dis'),
    '3x3/D0_CeO2_111_p2x2': ('1510400', 'sup'), '3x3/D1_Ce2O3_hO_2Odown': ('1510401', 'sup'), '3x3/D3_Ce2O3_gasgeom': ('1510402', 'sup'),
}


def two_stage(name):
    return name.startswith('3x3/')


def sysdir(name):
    return os.path.join(IN3, name[4:]) if two_stage(name) else os.path.join(IN, name)
MAX_AUTO = 4          # automatic resumes per system
QUOTA_BLOCK = False   # set in run() when a quota gate trips: no automatic resume

NOW = datetime.datetime.now()
actions, attention, info, rows, abnormal = [], [], [], [], []


# ---------------------------------------------------------------- helpers
def ts():
    return datetime.datetime.now().isoformat(timespec='seconds')


def sh(cmd, cwd=None, timeout=120):
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except subprocess.TimeoutExpired:
        return 124, 'timeout after %d s: %s' % (timeout, cmd)


def read(fn, tail=None):
    try:
        with open(fn, errors='replace') as f:
            if tail:
                f.seek(max(0, os.path.getsize(fn) - tail))
            return f.read()
    except (OSError, TypeError):
        return ''


def write(fn, s):
    with open(fn, 'w') as f:
        f.write(s)


def log_action(msg):
    actions.append(msg)
    with open(SUBLOG, 'a') as f:
        f.write('%s [monitor] %s\n' % (ts(), msg))


def fnum(s):
    try:
        return float(s)
    except ValueError:
        return float('nan')


def fmt(x, f='%.4f'):
    return (f % x) if isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x)) else (x or '—')


def hms(s):
    try:
        h, m, x = (int(v) for v in s.split(':'))
        return h * 3600 + m * 60 + x
    except (ValueError, AttributeError):
        return None


def pbs_time(s):
    try:
        return datetime.datetime.strptime(s, '%a %b %d %H:%M:%S %Y')
    except (ValueError, TypeError):
        return None


def age_h(fn):
    try:
        return (time.time() - os.path.getmtime(fn)) / 3600
    except OSError:
        return None


def newest(d, pattern):
    fs = [f for f in glob.glob(os.path.join(d, pattern)) if os.path.isfile(f)]
    return max(fs, key=os.path.getmtime) if fs else None


# ---------------------------------------------------------------- cluster
def queue():
    rc, out = sh('qstat -f -F json', timeout=60)
    jobs = {}
    try:
        if rc != 0:
            raise ValueError
        for jid, j in json.loads(out).get('Jobs', {}).items():
            j['id'] = jid.split('.')[0]
            jobs.setdefault(j.get('Job_Name'), []).append(j)
    except ValueError:
        attention.append('qstat 不可用或输出无法解析（rc=%s）：%s；本次只报告' % (rc, out[:200]))
        return None
    return jobs


def job_hist(jid):
    rc, out = sh('qstat -xf -F json %s' % jid, timeout=60)
    try:
        return list(json.loads(out)['Jobs'].values())[0]
    except (ValueError, KeyError, IndexError):
        return {}


def quotas():
    rc, out = sh('hpc space', timeout=90)
    res = {}
    for key, pat in (('home', r'/home/svu/junbotong\s+([\d.]+)G\s+([\d.]+)G\s+([\d.]+)%'),
                     ('scratch', r'/scratch/junbotong\s+([\d.]+)G\s+([\d.]+)G\s+([\d.]+)%')):
        m = re.search(pat, out)
        if m:
            res[key] = tuple(float(m.group(k)) for k in (1, 2, 3))
    return res


def allocation():
    """Balance line of CFP04-CF-046; refresh the amgr session silently if hpc project asks for a login."""
    rc, out = sh('hpc project', timeout=90)
    m = re.search(r'CFP04-CF-046\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', out)
    if not m:
        sh('bash "$HOME/hpc_login.sh" > /dev/null 2>&1', timeout=180)      # never print the helper or its output
        rc, out = sh('hpc project', timeout=90)
        m = re.search(r'CFP04-CF-046\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', out)
        if m:
            log_action('hpc project 未返回 CFP04-CF-046 额度，已用 ~/hpc_login.sh 静默刷新 amgr 会话，刷新后正常')
        else:
            attention.append('hpc project 读不到 CFP04-CF-046 额度，~/hpc_login.sh 刷新后仍失败（需用户 ssh -tt vanda amgr login）')
            return None
    alloc, left = float(m.group(1)), float(m.group(2))
    if left <= 0:
        attention.append('CFP04-CF-046 余额 %.0f ≤ 0，排队作业可能无法启动' % left)
    return alloc, left


# ---------------------------------------------------------------- structures
def _inv3(m):
    a, b, c = m
    det = (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return [[(b[1] * c[2] - b[2] * c[1]) / det, (a[2] * c[1] - a[1] * c[2]) / det, (a[1] * b[2] - a[2] * b[1]) / det],
            [(b[2] * c[0] - b[0] * c[2]) / det, (a[0] * c[2] - a[2] * c[0]) / det, (a[2] * b[0] - a[0] * b[2]) / det],
            [(b[0] * c[1] - b[1] * c[0]) / det, (a[1] * c[0] - a[0] * c[1]) / det, (a[0] * b[1] - a[1] * b[0]) / det]]


def readpos(fn):
    """(symbols, fractional positions, selective flags, cell)."""
    L = read(fn).split('\n')
    sc = float(L[1].split()[0])
    cell = [[float(x) * sc for x in L[k].split()[:3]] for k in (2, 3, 4)]
    el = L[5].split()
    cnt = [int(x) for x in L[6].split()]
    n = sum(cnt)
    i = 7
    sd = L[i].strip()[:1] in 'sS'
    i += 2 if sd else 1
    cart = L[i - 1].strip()[:1] in 'cCkK'
    inv = _inv3(cell) if cart else None
    pos, flg = [], []
    for k in range(n):
        t = L[i + k].split()
        p = [float(x) for x in t[:3]]
        if cart:
            p = [sum(p[j] * inv[j][c] for j in range(3)) for c in range(3)]
        pos.append(p)
        flg.append(t[3:6] if sd else ['T'] * 3)
    sym = [e for e, c in zip(el, cnt) for _ in range(c)]
    return sym, pos, flg, cell


def dist(cell, a, b):
    f = [x - y for x, y in zip(a, b)]
    f = [x - round(x) for x in f]
    v = [sum(f[k] * cell[k][j] for k in range(3)) for j in range(3)]
    return math.sqrt(sum(x * x for x in v))


def zc(cell, p):
    return sum(p[k] * cell[k][2] for k in range(3))


def geom_files(d):
    """(initial, current) structure files: POSCAR_start is written after the relaxation; before that POSCAR is the input."""
    ini = os.path.join(d, 'POSCAR_start')
    if not os.path.exists(ini):
        ini = os.path.join(d, 'POSCAR')
    cur = os.path.join(d, 'CONTCAR')
    if not read(cur).strip():
        cur = os.path.join(d, 'POSCAR')
    return ini, cur


def last_complete_block(txt, key, nlines, skip):
    for blk in reversed(txt.split(key)[1:]):
        rr = blk.split('\n')[skip:skip + nlines]
        if len(rr) == nlines and all(len(r.split()) >= 4 for r in rr):
            return rr
    return None


def outcar_tail(fn):
    t = read(fn, tail=6000000)
    return t


def forces_free(outcar_txt, flg):
    rr = last_complete_block(outcar_txt, 'TOTAL-FORCE', len(flg), 2)
    if not rr:
        return None
    try:
        F = [[float(x) for x in r.split()[3:6]] for r in rr]
    except ValueError:
        return None
    free = [i for i, f in enumerate(flg) if f[0] == 'T']
    return max(math.sqrt(sum(c * c for c in F[i])) for i in free) if free else None


def moments(outcar_txt, sym):
    rr = last_complete_block(outcar_txt, 'magnetization (x)', len(sym), 4)
    if not rr:
        return None
    try:
        return [float(r.split()[-1]) for r in rr]
    except ValueError:
        return None


def ce_summary(sym, mom):
    if mom is None:
        return '—', []
    m = [x for s, x in zip(sym, mom) if s == 'Ce']
    rh = [abs(x) for s, x in zip(sym, mom) if s == 'Rh']
    if not m:
        return ('Rh|m|max %.2f' % max(rh)) if rh else '—', []
    up = sum(1 for x in m if x >= 0.8)
    dn = sum(1 for x in m if x <= -0.8)
    mid = sum(1 for x in m if 0.3 < abs(x) < 0.8)
    if len(m) <= 6:
        signs = ''.join('↑' if x >= 0.8 else '↓' if x <= -0.8 else '0' if abs(x) < 0.3 else '?' for x in m)
        s = 'Ce³⁺ %d %s' % (up + dn, signs)
    else:
        s = 'Ce³⁺ %d（↑%d↓%d）/%d' % (up + dn, up, dn, len(m))
    if mid:
        s += '，中间值 %d' % mid
    return s, m


def e_sigma0(txt):
    v = re.findall(r'energy\(sigma->0\)\s*=\s*(-?[\d.]+)', txt)
    return float(v[-1]) if v else None


SCF_RE = re.compile(r'^(?:DAV|RMM|CGA|SDA):\s*(\d+)\s+(\S+)\s+(\S+)')
ION_RE = re.compile(r'^\s*(\d+)\s+F=\s*(\S+)\s+E0=\s*(\S+)\s+d E =\s*(\S+)(?:\s+mag=\s*(\S+))?')


def osz(fn):
    ions, cur = [], []
    for l in read(fn).split('\n'):
        m = SCF_RE.match(l)
        if m:
            cur.append((int(m.group(1)), fnum(m.group(2)), fnum(m.group(3))))
            continue
        m = ION_RE.match(l)
        if m:
            ions.append((int(m.group(1)), fnum(m.group(3)), fnum(m.group(5)) if m.group(5) else None, len(cur)))
            cur = []
    return ions, cur


def incar_nelm(fn):
    m = re.search(r'^\s*NELM\s*=\s*(\d+)', read(fn), re.M)
    return int(m.group(1)) if m else 60


def current_stage(d):
    m = re.search(r'\|\s*(stage\w+)\s*$', read(os.path.join(d, 'INCAR')).split('\n')[0])
    return m.group(1) if m else None


def structure_flags(name, kind, d, out):
    """Adsorbate / desorption / O2 / H2 flags (report only); appends to `out`. Returns a short note for the row."""
    ini, cur = geom_files(d)
    try:
        sym, p1, flg, cell = readpos(cur)
        p0 = readpos(ini)[1]
    except (IndexError, ValueError):
        return ''
    note = []
    sub = [i for i, s in enumerate(sym) if s not in ('C', 'H')]
    C = [i for i, s in enumerate(sym) if s == 'C']
    H = [i for i, s in enumerate(sym) if s == 'H']
    if C and sub:
        c = C[0]

        def near(p, i):
            return min(dist(cell, p[i], p[j]) for j in sub)
        dC0, dC = near(p0, c), near(p1, c)
        bonded0 = [h for h in H if dist(cell, p0[c], p0[h]) < CH_BOND]
        bonded = [h for h in H if dist(cell, p1[c], p1[h]) < CH_BOND]
        note.append('C–H %d' % len(bonded))
        if kind == 'ch4':
            if len(bonded) < 4:
                out.append('%s: CH₄ 自发解离（C–H 键 4→%d，判据 < %.1f Å）' % (name, len(bonded), CH_BOND))
            if dC > max(4.5, dC0 + 1.5):
                out.append('%s: CH₄ 离开表面（C 到最近表面原子 %.1f→%.1f Å）' % (name, dC0, dC))
        if kind == 'dis':
            if len(bonded) >= 4:
                out.append('%s: CH₃+H 复合成 CH₄（C–H 键 %d）' % (name, len(bonded)))
            elif len(bonded) < 3:
                out.append('%s: CH₃ 继续脱氢（C–H 键 3→%d）' % (name, len(bonded)))
            if dC > max(3.0, dC0 + 0.8):
                out.append('%s: CH₃ 离开表面（C 到最近表面原子 %.1f→%.1f Å）' % (name, dC0, dC))
            for h in [h for h in H if h not in bonded0 and h not in bonded]:
                dH0, dH = near(p0, h), near(p1, h)
                if dH > max(2.5, dH0 + 0.8):
                    out.append('%s: 解离 H%d 离开表面（到最近表面原子 %.1f→%.1f Å）' % (name, h + 1, dH0, dH))
        for a in range(len(H)):
            for b in range(a + 1, len(H)):
                if dist(cell, p1[H[a]], p1[H[b]]) < HH_BOND:
                    out.append('%s: H%d–H%d %.2f Å，形成 H₂' % (name, H[a] + 1, H[b] + 1, dist(cell, p1[H[a]], p1[H[b]])))
        O = [i for i, s in enumerate(sym) if s == 'O']
        co0 = min([dist(cell, p0[c], p0[o]) for o in O] or [9])
        co = min([dist(cell, p1[c], p1[o]) for o in O] or [9])
        if co < CO_BOND <= co0:
            info.append('%s: C–O 成键 %.2f Å（初始 %.2f Å），吸附位变为 O 上（甲氧基类）' % (name, co, co0))
    # Ce/O leaving the surface (carried over from the D3 monitor)
    if 'Rh' in sym:
        ztop = max(zc(cell, p1[i]) for i, s in enumerate(sym) if s == 'Rh')
        far = [(i + 1, s, zc(cell, p1[i]) - ztop) for i, s in enumerate(sym) if s in ('Ce', 'O') and zc(cell, p1[i]) - ztop > DESORB_DZ]
    elif kind == 'sup':
        supp = [i for i in range(len(sym)) if zc(cell, p0[i]) <= D_SUPPORT_TOP]
        ztop = max(zc(cell, p1[i]) for i in supp) if supp else 0
        far = [(i + 1, sym[i], zc(cell, p1[i]) - ztop) for i in range(len(sym)) if i not in supp and zc(cell, p1[i]) - ztop > DESORB_DZ]
    else:
        far = []
    if far:
        out.append('%s: 原子离开表面（%s，高于表面 > %.0f Å），疑似脱附' % (
            name, ', '.join('%s%d +%.1f Å' % (s, i, z) for i, s, z in far[:4]), DESORB_DZ))
    oi = [i for i, s in enumerate(sym) if s == 'O']
    for a in range(len(oi)):
        for b in range(a + 1, len(oi)):
            dd = dist(cell, p1[oi[a]], p1[oi[b]])
            if dd < OO_MIN:
                out.append('%s: O%d–O%d 距离 %.2f Å，疑似形成 O₂' % (name, oi[a] + 1, oi[b] + 1, dd))
                return ', '.join(note)
    return ', '.join(note)


def fixed_disp(d):
    """max displacement of the F F F atoms, POSCAR_start -> POSCAR (the relaxed geometry used for the SP)."""
    a, b = os.path.join(d, 'POSCAR_start'), os.path.join(d, 'POSCAR')
    if not os.path.exists(a):
        return None
    sym, p0, flg, cell = readpos(a)
    p1 = readpos(b)[1]
    fx = [i for i, f in enumerate(flg) if f[0] == 'F']
    return max([dist(cell, p0[i], p1[i]) for i in fx] or [0.0])


def fatal_markers(d, extra=()):
    found = []
    for f in list(glob.glob(os.path.join(d, 'vasp*.out'))) + [x for x in extra if x]:
        if age_h(f) is not None and age_h(f) < 24 * 5:
            t = read(f, tail=200000)
            for pat, what in FATAL:
                if re.search(pat, t) and what not in found:
                    found.append(what)
    return found


# ---------------------------------------------------------------- per job
def running_row(name, kind, st, j, d):
    stt = j.get('job_state')
    wall = j.get('resources_used', {}).get('walltime', '—')
    jid = j['id']
    if stt == 'H' or 'too many failed attempts' in j.get('comment', ''):
        attention.append('%s: PBS %s 被挂起（%s）；监控不 qdel/重投，需用户决定' % (name, jid, j.get('comment', '')[:120]))
        rows.append([name, jid, 'H', '挂起', '—', '—', '—', '—', '—', j.get('comment', '')[:40]])
        return
    if stt != 'R':
        qt = pbs_time(j.get('qtime'))
        waited = (NOW - qt).total_seconds() / 3600 if qt else 0
        if waited > QUEUE_WAIT_H:
            info.append('%s: 已排队 %.0f h（qstat -Qf batch_cpu 看拥堵）' % (name, waited))
        rows.append([name, jid, stt, '排队中', '—', '—', '—', '—', '—', ''])
        return
    stage = current_stage(d) or '?'
    ions, cur = osz(os.path.join(d, 'OSZICAR'))
    a = age_h(os.path.join(d, 'OSZICAR'))
    if a is not None and a > STALL_H and (hms(wall) or 0) >= 3600:
        attention.append('%s: 作业 R 但 OSZICAR 已 %.1f h 未更新（可能卡死）' % (name, a))
    if len(cur) >= OSC_MIN_STEPS:
        amp = max(abs(x[2]) for x in cur[-OSC_WINDOW:])
        if amp >= OSC_AMP:
            attention.append('%s: %s 当前 SCF 已 %d 步，最近 %d 步 |dE| 仍达 %.2g eV，在振荡' % (name, stage, len(cur), OSC_WINDOW, amp))
    try:
        sym, _, flg, _ = readpos(os.path.join(d, 'POSCAR'))
    except (IndexError, ValueError):
        sym, flg = [], []
    lp = ldau_problem(d, sym)
    if lp:
        attention.append('%s: %s' % (name, lp))
    oc = outcar_tail(os.path.join(d, 'OUTCAR'))
    ce, _ = ce_summary(sym, moments(oc, sym)) if sym else ('—', [])
    fm, note = None, ''
    if stage == 'stageB_relax':
        lim = incar_nelm(os.path.join(d, 'INCAR'))
        hit = [n for n, e0, mag, nscf in ions[-3:] if nscf >= lim]
        if hit:
            attention.append('%s: 弛豫第 %s 离子步 SCF 用满 NELM=%d，这些步的受力不可信' % (name, ','.join(map(str, hit)), lim))
        for (n0, e0, m0, _), (n1, e1, m1, _) in zip(ions, ions[1:]):
            if m0 is not None and m1 is not None and abs(m1 - m0) > MAG_JUMP:
                attention.append('%s: 第 %d→%d 离子步总磁矩 %.2f→%.2f μB 跳变（Ce 自旋翻转？）' % (name, n0, n1, m0, m1))
                break
        for (n0, e0, m0, _), (n1, e1, m1, _) in zip(ions, ions[1:]):
            if e1 - e0 > E_RISE:
                attention.append('%s: 第 %d→%d 离子步 E0 升高 %.3f eV' % (name, n0, n1, e1 - e0))
                break
        fm = forces_free(oc, flg) if flg else None
    if stage in ('stageB_relax', 'stageC_SP'):
        note = structure_flags(name, kind, d, attention)
    e = ions[-1][1] if (stage == 'stageB_relax' and ions) else (cur[-1][1] if cur else None)
    prog = 'SCF %d' % (cur[-1][0] if cur else 0)
    rows.append([name, jid, 'R %s' % wall, stage, '%d（%s）' % (len(ions), prog) if stage == 'stageB_relax' else prog,
                 fmt(fm, '%.3f'), fmt(e, '%.4f'), ce, '—', note])


def ldau_problem(d, sym):
    """U must sit on Ce 4f only (L 3, U 5), one LDAUL entry per POSCAR species. 2026-11-02: the 3x3 inputs took
    B0's 'LDAUL = -1 3 -1' (Rh Ce O) unchanged, which put U on C in A1/A2 and on O instead of Ce in D0-D3."""
    t = read(os.path.join(d, 'INCAR')) or read(os.path.join(d, 'INCAR_stageB_relax'))
    if not t or not sym:
        return None
    spec = list(dict.fromkeys(sym))
    on = re.search(r'^\s*LDAU\s*=\s*\.?T', t, re.M | re.I)
    ml = re.search(r'^\s*LDAUL\s*=\s*(.+)$', t, re.M)
    want = ['3' if s == 'Ce' else '-1' for s in spec]
    if 'Ce' not in spec:
        if on and ml and any(x != '-1' for x in ml.group(1).split()[:len(spec)]):
            return 'LDAUL %s 把 U 加在了非 Ce 元素上（物种 %s）' % (ml.group(1).strip(), ' '.join(spec))
        return None
    if not on or not ml or [x.split('.')[0] for x in ml.group(1).split()[:len(spec)]] != want \
            or len(ml.group(1).split()) < len(spec):
        return 'LDAUL %s 与物种 %s 不符（应为 %s）' % (ml.group(1).strip() if ml else '缺', ' '.join(spec), ' '.join(want))
    return None


def accept(name, kind, d):
    """(ok, problems, E, Fmax, ce, note) for a finished chain."""
    probs = []
    # newest stage file, so a resumed stage (OUTCAR_stageB_relax_rN, OUTCAR_stageC_SP_rN) is the one judged
    # (2026-10-21: C1 r2 converged in OUTCAR_stageB_relax_r2 but the stale OUTCAR_stageB_relax was read)
    ro = newest(d, 'OUTCAR_stageB_relax*') or os.path.join(d, 'OUTCAR_stageB_relax')
    so = (newest(d, 'OUTCAR_stageC_SP*') or os.path.join(d, 'OUTCAR_stageC_SP')) \
        if kind != 'gas' and not two_stage(name) else ro
    rtxt, stxt = read(ro), read(so)
    if not rtxt or not stxt:
        return False, ['缺少 %s' % (os.path.basename(ro) if not rtxt else os.path.basename(so))], None, None, '—', ''
    sym, _, flg, _ = readpos(os.path.join(d, 'POSCAR'))
    fm = forces_free(rtxt, flg)
    lp = ldau_problem(d, sym)
    if lp:
        probs.append(lp)
    if 'reached required accuracy' not in rtxt:
        probs.append('弛豫 OUTCAR 无 "reached required accuracy"')
    if kind != 'gas' and not two_stage(name) and 'aborting loop because EDIFF is reached' not in stxt:
        probs.append('单点 OUTCAR 无 "EDIFF is reached"')
    if fm is None or fm > FMAX_ACCEPT:
        probs.append('Fmax_free %s > %.2f eV/Å' % (fmt(fm, '%.3f'), FMAX_ACCEPT))
    fd = fixed_disp(d)
    if fd is not None and fd >= FIX_TOL:
        probs.append('固定原子相对 POSCAR_start 移动 %.2e Å' % fd)
    mom = moments(stxt, sym)
    ce, m = ce_summary(sym, mom)
    if any(0.3 < abs(x) < 0.8 for x in m):
        probs.append('Ce 磁矩有中间值（%s）' % ce)
    rh = [abs(x) for s, x in zip(sym, mom or []) if s == 'Rh']
    if rh and max(rh) > 0.3:
        probs.append('Rh 局域磁矩最大 %.2f μB（> 0.3）' % max(rh))
    e0 = e_sigma0(stxt)
    if e0 is None:
        probs.append('读不到 energy(sigma->0)')
    flags = []
    note = structure_flags(name, kind, d, flags)
    attention.extend(flags)
    return not probs and not flags, probs, e0, fm, ce, note


def make_resume(name, kind, d, stage, n):
    """Write INCAR_<stage>_r<n> and job_resume_r<n>.pbs for the chain stage -> ... -> stageC_SP."""
    base = {'A': 'stageA_spinSP', 'B': 'stageB_relax', 'C': 'stageC_SP'}[stage]
    tag = '%s_r%d' % (base, n)
    inc = read(os.path.join(d, 'INCAR_' + base))
    wf = os.path.join(d, 'WAVECAR')
    wav = os.path.exists(wf) and os.path.getsize(wf) > 0
    if stage == 'A':
        inc = re.sub(r'^ISTART = \d+', 'ISTART = 1', inc, flags=re.M)
        inc = re.sub(r'^ICHARG = \d+', 'ICHARG = 0', inc, flags=re.M)
    elif stage == 'B':
        inc = re.sub(r'^ISTART = \d+', 'ISTART = %d' % (1 if wav else 0), inc, flags=re.M)
        inc = re.sub(r'^ICHARG = \d+', 'ICHARG = %d' % (1 if wav else 2), inc, flags=re.M)
    else:
        inc = re.sub(r'^ALGO = \w+', 'ALGO = All', inc, flags=re.M)
        inc = re.sub(r'^NELM = \d+', 'NELM = 500', inc, flags=re.M)
    inc = re.sub(r'\| %s\s*$' % base, '| ' + tag, inc, count=1, flags=re.M)
    write(os.path.join(d, 'INCAR_' + tag), inc)
    chain = [tag] + (['stageB_relax'] if stage == 'A' else []) + \
        (['stageC_SP'] if stage in ('A', 'B') and kind != 'gas' and not two_stage(name) else [])
    job = read(os.path.join(d, 'job.pbs'))
    # split at the first run_stage *call*, keeping the run_stage () { ... } definition
    # (2026-10-19: splitting at '\nrun_stage ' dropped the definition -> Exit 127 "run_stage: command not found")
    head = re.split(r'\nrun_stage (?!\()', job, 1)[0]
    need = ' '.join('INCAR_' + t for t in chain) + ' POSCAR KPOINTS POTCAR' + (' WAVECAR' if stage != 'B' else '')
    head = re.sub(r'^for f in .*; do$', 'for f in %s; do' % need, head, count=1, flags=re.M)
    head = re.sub(r'^#PBS -N \S+', '#PBS -N s7r%d_%s' % (n, os.path.basename(name)[:10]), head, count=1, flags=re.M)
    # D1-D3 (user, 2026-10-17): relax with Gamma-only KPOINTS_relax, final SP with KPOINTS_final (2x2x1)
    split_k = os.path.exists(os.path.join(d, 'KPOINTS_relax')) and os.path.exists(os.path.join(d, 'KPOINTS_final'))
    body = []
    if split_k:
        body.append('cp KPOINTS_%s KPOINTS' % ('final' if stage == 'C' else 'relax'))
    for t in chain:
        if t == 'stageC_SP':
            body.append('cp POSCAR POSCAR_start; cp CONTCAR POSCAR' + ('; cp KPOINTS_final KPOINTS' if split_k else ''))
        relax = t.startswith('stageB')
        body.append('run_stage %s %s %s' % (t, 'LSTOP' if relax else 'LABORT', 'relax' if relax else 'scf'))
    pbs = 'job_resume_r%d.pbs' % n
    write(os.path.join(d, pbs), head + '\n' + '\n'.join(body) + '\necho "end=$(date --iso-8601=seconds) rc=0"\n')
    return pbs, tag


def auto_resume(name, kind, st, d, last, why, fatal, ex):
    """Mechanical resume of a non-fatal stop; returns the new PBS id or None (caller then raises ATTENTION)."""
    if fatal or not last or (ex is not None and int(ex) in (2,)) or (ex is not None and int(ex) < 0):
        return None
    n = st.get('auto_n', 0) + 1
    if n > MAX_AUTO:
        why.append('自动续算已达上限 %d 次' % MAX_AUTO)
        return None
    stage = last.replace('stage', '')[:1]
    if stage not in ('A', 'B', 'C'):
        return None
    flags = []
    structure_flags(name, kind, d, flags)
    if flags:
        why.append('结构标记（%s），不自动续算' % '；'.join(flags)[:80])
        return None
    if stage in ('A', 'C') and not os.path.exists(os.path.join(d, 'WAVECAR')):
        why.append('缺 WAVECAR，不自动续算')
        return None
    if stage == 'B':
        ions, _ = osz(os.path.join(d, 'OSZICAR'))
        con = os.path.join(d, 'CONTCAR')
        if not ions or not os.path.exists(con) or os.path.getsize(con) == 0:
            why.append('弛豫没有写出离子步/CONTCAR，不自动续算')
            return None
        sh('cp POSCAR POSCAR_before_r%d && cp CONTCAR CONTCAR_before_r%d && cp CONTCAR POSCAR' % (n, n), cwd=d)
    pbs, tag = make_resume(name, kind, d, stage, n)
    rc, out = sh('qsub %s' % pbs, cwd=d, timeout=60)
    if rc != 0 or not re.match(r'^\d+', out):
        why.append('自动续算 qsub 失败：%s' % out[:100])
        return None
    new = out.split('.')[0]
    st.update({'auto_n': n, 'jid': new, 'phase': 'run'})
    for k in ('exit', 'msg', 'walltime_hit', 'end'):
        st.pop(k, None)
    log_action('%s 自动续算 r%d：%s → 从 %s 续（%s），新作业 %s' % (name, n, '；'.join(why), tag, pbs, new))
    return new


def ended(name, kind, st, d):
    jid = st['jid']
    o = newest(d, '*.o%s' % jid) or newest(d, '*.o[0-9]*')
    t = read(o) if o else ''
    h = job_hist(jid)
    if h:
        st['exit'] = h.get('Exit_status')
        used, lim = hms(h.get('resources_used', {}).get('walltime')), hms(h.get('Resource_List', {}).get('walltime'))
        st['walltime_hit'] = used is not None and lim is not None and used >= lim - 300
        st['end'] = h.get('obittime')
    ex = st.get('exit')
    starts = re.findall(r'stage=(\S+) start', t)
    notconv = re.findall(r'stage=(\S+) (SCF|RELAX) NOT converged', t)
    watchdog = 'watchdog_stop' in t
    chain_ok = bool(re.search(r'^end=.* rc=0', t, re.M))
    if chain_ok:
        ok, probs, e0, fm, ce, note = accept(name, kind, d)
        if ok:
            st.update({'phase': 'final', 'E0': e0, 'fmax': fm, 'ce': ce, 'note': note, 'exit': ex})
            log_action('%s 验收通过（E0 %s, Fmax_free %s, %s %s）' % (name, fmt(e0, '%.5f'), fmt(fm, '%.4f'), ce, note))
            rows.append([name, jid, '完成', '已验收', '—', fmt(fm, '%.3f'), fmt(e0, '%.5f'), ce, fmt(ex, '%s'), note])
            return
        msg = '%s: 链正常结束（Exit %s）但验收未过：%s' % (name, ex, '；'.join(probs) or '见结构标记')
        st.update({'phase': 'stopped', 'msg': msg, 'E0': e0, 'fmax': fm, 'ce': ce, 'note': note})
        attention.append(msg)
        rows.append([name, jid, '结束', '验收未过', '—', fmt(fm, '%.3f'), fmt(e0, '%.5f'), ce, fmt(ex, '%s'), note])
        return
    fatal = fatal_markers(d, [o])
    last = starts[-1] if starts else None
    why = []
    if notconv:
        stg, what = notconv[-1]
        why.append('%s %s' % (stg, 'SCF 未收敛（exit 3）' if what == 'SCF' else '弛豫未收敛（exit 4）'))
    if watchdog:
        why.append('看门狗 250200 s 触发 STOPCAR')
    if st.get('walltime_hit'):
        why.append('撞 72 h 墙被杀')
    if fatal:
        why.append('致命错误：' + '；'.join(fatal))
    if ex is not None and int(ex) < 0:
        why.append('PBS Exit %s（系统/节点问题）' % ex)
    if ex is not None and int(ex) == 2 and not last:
        why.append('输入缺失（exit 2）')
    if not o:
        why.append('没有 .o%s 输出文件' % jid)
    if last and not os.path.exists(os.path.join(d, 'OUTCAR')):
        why.append('缺 OUTCAR')
    if not why:
        why.append('非正常结束（Exit %s，最后阶段 %s）' % (ex, last or '启动前'))
    newjid = None if QUOTA_BLOCK else auto_resume(name, kind, st, d, last, why, fatal, ex)
    if newjid:
        rows.append([name, newjid, 'Q', '自动续算 r%d' % st['auto_n'], '—', '—', '—', '—', fmt(ex, '%s'),
                     ('；'.join(why))[:60]])
        return
    if QUOTA_BLOCK:
        why.append('配额超限，暂不自动续算')
    ions, cur = osz(os.path.join(d, 'OSZICAR'))
    msg = '%s: PBS %s 已结束，%s；未自动续算，需要处理' % (name, jid, '；'.join(why))
    st.update({'phase': 'stopped', 'msg': msg})
    attention.append(msg)
    abnormal.append((name, pbs_time(st.get('end'))))
    rows.append([name, jid, '结束', last or '—', str(len(ions)) if ions else '—', '—',
                 fmt(ions[-1][1] if ions else None, '%.4f'), '—', fmt(ex, '%s'), '；'.join(why)[:60]])


# ---------------------------------------------------------------- results
def results_table3(state):
    """3x3 / p(2x2) set (2026-10-29): E0 of the converged relaxation; references within the same model."""
    s = state['systems']
    E = {k: s.get(k, {}).get('E0') for k in SYSTEMS3}
    eg = s.get('G_CH4', {}).get('E0')
    out = ['| 体系 | 类型 | E0 (eV) | E − E(ref) − E(CH₄,g) (eV) | 相对本模型最稳 CH₄ 态 (eV) | Fmax_free | Ce 磁矩 | 备注 |',
           '|---|---|---|---|---|---|---|---|']
    for k, (_, kind) in SYSTEMS3.items():
        v = s.get(k, {})
        mdl = k[4]
        ref = E.get('3x3/%s0_ref' % mdl)
        ch4 = [E[x] for x, (_, kk) in SYSTEMS3.items() if x[4] == mdl and kk == 'ch4' and E.get(x) is not None]
        dads = E[k] - ref - eg if kind in ('ch4', 'dis') and None not in (E[k], ref, eg) else None
        drel = E[k] - min(ch4) if kind in ('ch4', 'dis') and ch4 and E[k] is not None else None
        out.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
            k[4:], kind, fmt(E[k], '%.5f'), fmt(dads, '%+.3f'), fmt(drel, '%+.3f'), fmt(v.get('fmax'), '%.3f'),
            v.get('ce', '—'), v.get('note', '') or '—'))
    out += ['', 'E0 = energy(sigma->0) of the converged relaxation (OUTCAR_stageB_relax*, ISMEAR 1, SIGMA 0.10); '
            'G_CH4 = the stage-7 CH₄ box. %d/%d 已验收。' % (sum(1 for k in SYSTEMS3 if s.get(k, {}).get('phase') == 'final'),
                                                       len(SYSTEMS3))]
    return '\n'.join(out)


def results_table(state):
    s = state['systems']
    E = {k: s.get(k, {}).get('E0') for k in SYSTEMS}
    eg = E.get('G_CH4')
    out = ['| 体系 | 类型 | E0 (eV) | E − E(ref) − E(CH₄,g) (eV) | 相对本模型最稳 CH₄ 态 (eV) | Fmax_free | Ce 磁矩 | C–H |',
           '|---|---|---|---|---|---|---|---|']
    for k, (jid, kind) in SYSTEMS.items():
        v = s.get(k, {})
        mdl = k[0]
        ref = E.get('%s0_ref' % mdl)
        ch4 = [E[x] for x, (_, kk) in SYSTEMS.items() if x[0] == mdl and kk == 'ch4' and E.get(x) is not None]
        dads = E[k] - ref - eg if kind in ('ch4', 'dis') and None not in (E[k], ref, eg) else None
        drel = E[k] - min(ch4) if kind in ('ch4', 'dis') and ch4 and E[k] is not None else None
        out.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
            k, kind, fmt(E[k], '%.5f'), fmt(dads, '%+.3f'), fmt(drel, '%+.3f'), fmt(v.get('fmax'), '%.3f'),
            v.get('ce', '—'), v.get('note', '') or '—'))
    out.append('')
    out.append('E0 = energy(sigma->0)：OUTCAR_stageC_SP（ISMEAR 0, SIGMA 0.05, EDIFF 1E-6）；G_CH4 取 OUTCAR_stageB_relax。'
               ' N = %d 个作业全部验收。' % len(SYSTEMS))
    return '\n'.join(out)


# ---------------------------------------------------------------- main
def run(state):
    global QUOTA_BLOCK
    qq = quotas()
    for key, lim, label in (('home', HOME_ATTN, 'home'), ('scratch', SCRATCH_ATTN, 'scratch')):
        if key in qq and qq[key][2] >= lim:
            QUOTA_BLOCK = True
            attention.append('%s 配额 %.1f%%（%.1f/%.0f G）超过 %.0f%%，作业可能被一起杀掉（09-23 教训）' % (label, qq[key][2], qq[key][0], qq[key][1], lim))
    al = allocation()
    jobs = queue()
    for name, (jid0, kind) in (list(SYSTEMS.items()) + list(SYSTEMS3.items()) if jobs is not None else []):
        if name in RETIRED:
            continue
        st = state['systems'].setdefault(name, {'phase': 'run', 'jid': jid0})
        d = sysdir(name)
        try:
            names = []                                   # job.pbs plus any stageA resume script (2026-10-17: s7r_*)
            for js in ['job.pbs'] + sorted(os.path.basename(x) for x in glob.glob(os.path.join(d, 'job_resume*.pbs'))):
                if os.path.exists(os.path.join(d, js)):
                    nm = re.search(r'^#PBS -N (\S+)', read(os.path.join(d, js)), re.M)
                    if nm:
                        names.append(nm.group(1))
            live = [j for n in names for j in jobs.get(n, []) if j.get('job_state') in ('R', 'Q', 'H', 'W', 'E', 'B', 'S', 'T')]
            if not live:
                live = [j for js in jobs.values() for j in js if j['id'] == st['jid'] and j.get('job_state') not in ('F', 'X')]
            if live:
                j = sorted(live, key=lambda x: int(x['id']))[-1]
                if j['id'] != st['jid']:
                    info.append('%s: 队列中的作业号 %s 与记录 %s 不同（用户重投？），改为跟踪新作业' % (name, j['id'], st['jid']))
                    st.update({'jid': j['id'], 'phase': 'run'})
                    for k in ('exit', 'msg', 'walltime_hit', 'end'):
                        st.pop(k, None)
                running_row(name, kind, st, j, d)
            elif st.get('phase') == 'final':
                rows.append([name, st['jid'], '完成', '已验收', '—', fmt(st.get('fmax'), '%.3f'), fmt(st.get('E0'), '%.5f'),
                             st.get('ce', '—'), fmt(st.get('exit'), '%s'), st.get('note', '')])
            elif st.get('phase') == 'stopped':
                attention.append(st['msg'])
                rows.append([name, st['jid'], '结束', '待用户', '—', fmt(st.get('fmax'), '%.3f'), fmt(st.get('E0'), '%.5f'),
                             st.get('ce', '—'), fmt(st.get('exit'), '%s'), '见需要处理'])
            else:
                ended(name, kind, st, d)
        except Exception as e:
            attention.append('%s: 监控脚本处理出错 %s: %s' % (name, type(e).__name__, str(e)[:150]))
    # 2026-10-29 user: "你把D的NEB跑起来吧" -> once D4-D8 are accepted, hand the D ordinary NEB to the takeover
    if jobs is not None and all(state['systems'].get(k, {}).get('phase') == 'final' for k in D_ENDPOINTS)             and not os.path.isdir(os.path.join(os.path.dirname(IN), 'neb', 'D_neb')):
        attention.append('D4–D8 全部验收、neb/D_neb 尚未建立：按 PLAN_after_D_parent_20261025 第 5 步建模型 D 的普通 NEB 并提交'
                         '（用户 2026-10-29 指示"把 D 的 NEB 跑起来"）')
    ends = sorted((t, s) for s, t in abnormal if t)
    for (t0, s0), (t1, s1) in zip(ends, ends[1:]):
        if (t1 - t0).total_seconds() <= SIMUL_MIN * 60:
            attention.append('%s 与 %s 在 %s 前后 %d 分钟内同时非正常结束，疑似集群/配额事件' % (s0, s1, t0.strftime('%m-%d %H:%M'), SIMUL_MIN))
            break
    if jobs is not None and any(state['systems'].get(k, {}).get('phase') == 'final' for k in SYSTEMS3):
        os.makedirs(os.path.dirname(RES), exist_ok=True)
        write(os.path.join(os.path.dirname(RES), 'stage7_3x3_table.md'),
              '# Stage 7（3×3 / CeO₂ p(2×2)）首次 C–H 断裂端点（%s）\n\n%s\n' % (NOW.strftime('%Y-%m-%d %H:%M'),
                                                                        results_table3(state)))
        if all(state['systems'].get(k, {}).get('phase') == 'final' for k in SYSTEMS3) and not state.get('done3'):
            state['done3'] = True
            log_action('3×3 / p(2×2) 的 %d 个端点全部验收，results/stage7_3x3_table.md 已写出' % len(SYSTEMS3))
    if jobs is not None and all(state['systems'].get(k, {}).get('phase') == 'final' for k in SYSTEMS):
        if not state.get('done') or not os.path.exists(RES):
            write(EOUT, ''.join('%s %.8f\n' % (k, state['systems'][k]['E0']) for k in SYSTEMS))
            os.makedirs(os.path.dirname(RES), exist_ok=True)
            write(RES, '# DynSMSI stage 7：CH₄ 首次 C–H 断裂（四模型）结果表（%s）\n\n%s\n' % (NOW.strftime('%Y-%m-%d %H:%M'), results_table(state)))
            state['done'] = True
            log_action('20 个作业全部验收，E_stage7.txt 与 results/stage7_table.md 已写出')
    return qq, al


def main():
    os.makedirs(MON, exist_ok=True)
    lock = os.path.join(MON, 'lock')
    try:
        os.mkdir(lock)
    except FileExistsError:
        if (age_h(lock) or 0) < 1:
            print('===REPORT===\n另一个监控实例正在运行，本次跳过。\n===ACTIONS===\n===ATTN===\n===TOAST===\n'
                  '监控跳过（已有实例在运行）\n===FLAGS===\nATTENTION=0\nDONE=0')
            return
        os.rmdir(lock)
        os.mkdir(lock)
    qq, al, state = {}, None, None
    try:
        state = json.loads(read(STATE)) if os.path.exists(STATE) else {'systems': {}, 'done': False}
        state.setdefault('systems', {})
        qq, al = run(state)
        write(STATE, json.dumps(state, indent=1, ensure_ascii=False))
    except Exception as e:
        attention.append('监控脚本整体出错 %s: %s | %s' % (type(e).__name__, str(e)[:200],
                                                        traceback.format_exc().strip().split('\n')[-2][:200]))
    finally:
        os.rmdir(lock)
    done = bool(state and state.get('done'))
    nxt = (NOW + datetime.timedelta(hours=CADENCE_H)).strftime('%m-%d %H:%M')

    def tag(r):
        s = str(r[2])
        if s.startswith('完成'):
            return 'done'
        if s.startswith('R'):
            return 'run'
        if s in ('Q', 'W'):
            return 'queue'
        if s in ('H', '结束'):
            return 'bad'
        return ''
    tags = [tag(r) for r in rows]
    cnt = '共 %d：完成 %d，运行 %d，排队 %d，异常 %d' % (len(rows), tags.count('done'), tags.count('run'), tags.count('queue'), tags.count('bad'))
    if done:
        concl = 'stage-7 的 20 个作业全部完成并验收，results/stage7_table.md 已写出，监控可以结束。'
    elif attention:
        concl = '%s；有 %d 项需要处理（见下）。' % (cnt, len(attention))
    else:
        concl = '%s；全部正常，无需操作。' % cnt
    cols = ['体系', 'PBS', '状态', '阶段', '离子步', 'Fmax_free (eV/Å)', 'E (eV)', 'Ce 磁矩', 'Exit', '备注']
    out = ['# Vanda stage-7 监控 %s SGT' % NOW.strftime('%Y-%m-%d %H:%M'), '', concl, '',
           '| %s |' % ' | '.join(cols), '|' + '---|' * len(cols)]
    out += ['| %s |' % ' | '.join(str(c) for c in r) for r in rows]
    notes = []
    for key in ('home', 'scratch'):
        if key in qq:
            notes.append('%s 配额：%.1f / %.0f G（%.1f%%）' % ((key,) + qq[key]))
    if al:
        notes.append('CFP04-CF-046 额度：剩余 %.0f / %.0f' % (al[1], al[0]))
    out += [''] + notes
    if attention:
        out += ['', '**需要处理：**'] + ['- ' + a for a in attention]
    if actions:
        out += ['', '**本次操作：**'] + ['- ' + a for a in actions]
    if info:
        out += ['', '**备注：**'] + ['- ' + a for a in info]
    if done:
        out += ['', results_table(state)]
    if any(state['systems'].get(k, {}).get('phase') == 'final' for k in SYSTEMS3):
        out += ['', results_table3(state)]
    out += ['', '下次检查：%s SGT' % nxt]
    report = '\n'.join(out)
    write(os.path.join(MON, 'status_latest.md'), report + '\n')
    with open(os.path.join(MON, 'monitor.log'), 'a') as f:
        f.write(report + '\n\n')
    toast = ('需要处理 %d 项：%s' % (len(attention), attention[0][:80])) if attention else concl
    hub = {'headline': concl, 'done': done, 'attention': attention, 'actions': actions, 'notes': info + notes,
           'table': {'cols': cols, 'rows': [[str(c) for c in r] for r in rows], 'tags': tags},
           'summary': '完成 %d，运行 %d，排队 %d，异常 %d' % tuple(tags.count(t) for t in ('done', 'run', 'queue', 'bad'))}
    print('===REPORT===\n%s\n===ACTIONS===\n%s\n===ATTN===\n%s\n===TOAST===\n%s\n===HUB===\n%s\n===FLAGS===\nATTENTION=%d\nDONE=%d' % (
        report, '\n'.join(actions), '\n'.join(attention), toast, json.dumps(hub, ensure_ascii=False),
        1 if attention else 0, 1 if done else 0))


if __name__ == '__main__':
    main()
