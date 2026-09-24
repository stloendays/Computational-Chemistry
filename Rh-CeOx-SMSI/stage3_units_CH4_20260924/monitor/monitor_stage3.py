#!/usr/bin/env python3
"""DynSMSI stage-3 monitor. Runs on the Vanda login node (called every 5 h by monitor_stage3.ps1).

Protocol: DynSMSI_stage3_units_CH4_20260924/MONITOR_HANDOFF.md. Each run, per system in state.json:
  job held ("too many failed attempts")           -> qdel + resubmit the same script (max 2)
  job running                                     -> progress row + running checks (below)
  chain ended "stage=stageA_spinSP SCF NOT converged" (exit 3)
                                                  -> resume stage A from WAVECAR (ISTART 1, ALGO All), then B (max 1)
  chain ended "RELAX NOT converged" (exit 4: watchdog / NSW)
                                                  -> archive the segment, CONTCAR -> POSCAR, restart the relaxation
                                                     from WAVECAR/CHGCAR (max 4 segments)
  chain ended without an end line (crash)         -> archive, resubmit (max 3); >= 2 systems within 15 min -> ATTENTION
  chain ended "end=... rc=0"                      -> acceptance (free-atom Fmax <= 0.02, fixed atoms unmoved,
                                                     Ce moments, no desorption / O2); slabs then get final_sp/
                                                     (ISPIN 2, ENCUT 450, LDIPOL on, EDIFF 1e-6, from the relaxed
                                                     WAVECAR/CHGCAR); gas / bulk are final after acceptance
  final SP "SCF NOT converged"                    -> resume from WAVECAR with NELM 800 (max 1)
  final SP rc=0                                   -> E0(sigma->0), Ce moments, spin vs relaxation
  every system final                              -> results/stage3_step1_table.md, DONE
qsub refused for credit/project/amgr reasons -> run ~/hpc_login.sh silently, retry once, else ATTENTION.
`monitor/PAUSE` -> report only. Anything else it will not decide -> ATTENTION -> Claude Code CLI takeover.

HISTORY -> check (round 1-2 record in DynSMSI_stage2 SUBMISSION logs, MONITOR_HANDOFF, lessons)
  09-10/11  LDIPOL on metal/oxide slab: SCF charge-sloshing, dE 0.1-8 eV for 200+ steps   -> SCF oscillation check;
            LDIPOL only in the final SP, started from converged WAVECAR/CHGCAR, ALGO All
  09-11     spin SCF from scratch sloshed (Davidson)                                     -> stage A = ALGO All
  09-11     spin SCF hit NELM inside a relaxation; later ionic steps meaningless           -> NELM-in-relaxation check
  09-11/15  queues disabled before maintenance; qsub refused                              -> INFO, retried next run
  09-12     watchdog margin < one ionic step: 7 jobs killed at walltime                   -> walltime-kill classification
  09-12     ZBRENT "fatal error in bracketing" abort                                       -> fatal-marker scan, no blind restart
  09-12     restart helper silently did nothing                                            -> every action must yield a job id
  09-13     monitor counted queued jobs as running                                        -> job_state from qstat JSON
  09-15/20/23 PBS "too many failed attempts" system hold (Exit -3/-10)                   -> qdel+qsub, repeat -> ATTENTION
  09-18     "maxF" included fixed atoms                                                   -> free-atom forces only
  09-20/21/23 SP NELM hits while still descending                                         -> resume once; 2nd -> ATTENTION
  09-21     restart from a stale WAVECAR reset the Ce spins (4 up -> 3 up 1 down)          -> stale-WAVECAR + spin checks
  09-23     total mag ~0 read as spin collapse; really AFM                                 -> per-Ce spin comparison
  09-23     home quota 40 G exceeded: all jobs died in the same minute                     -> stage 3 runs on /scratch;
            scratch quota gate + simultaneous-death check
  09-24     allocation session expired between 14:05 and 19:09                           -> refresh with ~/hpc_login.sh
  09-24     a check that did not cd into the run directory saw no files                   -> absolute paths only
"""
import os, re, json, glob, math, shutil, subprocess, datetime, time, traceback

S = '/scratch/junbotong/Dynamic_SMSI_stage3_units_CH4_20260924'
IN = os.path.join(S, 'inputs')
MON = os.path.join(S, 'monitor')
STATE = os.path.join(MON, 'state.json')
SUBLOG = os.path.join(S, 'SUBMISSION_stage3.txt')
FMAX_ACCEPT = 0.02
CE3_RANGE = (0.8, 1.2)        # |m(Ce)| of Ce3+
CE_MAG_LOW = 0.5
MAX_A_RESUME, MAX_SP_RESUME, MAX_SEG, MAX_CRASH, MAX_HOLD = 1, 1, 4, 3, 2
SCRATCH_ATTN = 85.0           # % of the scratch quota
STALL_H = 2.0
OSC_MIN_STEPS, OSC_WINDOW, OSC_AMP = 150, 30, 1e-2
MAG_JUMP, E_RISE = 1.5, 0.10
DESORB_DZ, OO_MIN = 5.0, 1.45
QUEUE_WAIT_H, SIMUL_MIN, CADENCE_H = 24, 15, 5
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
]
# kind: ce = stage A spin SP + stage B relaxation; rh = single relaxation; bulk = ISIF 3
# role: slab (gets a dipole-corrected final SP) / gas / bulk; ce3 = Ce should be Ce3+
SYSTEMS = {
    'S1_00_Rh_bulk_450':       dict(kind='bulk', role='bulk', ce3=False, pbs='s3_S1_00_Rh_bul'),
    'S1_01_Rh111_4x4':         dict(kind='rh', role='slab', ce3=False, pbs='s3_S1_01_Rh111_'),
    'S1_02_Rh111_3x3':         dict(kind='rh', role='slab', ce3=False, pbs='s3_S1_02_Rh111_'),
    'S1_11a_CeO2_Rh_flat':     dict(kind='ce', role='slab', ce3=False, pbs='s3_S1_11a_CeO2_'),
    'S1_11b_CeO2_Rh_Cedown':   dict(kind='ce', role='slab', ce3=False, pbs='s3_S1_11b_CeO2_'),
    'S1_12a_Ce2O3_Rh_from10a': dict(kind='ce', role='slab', ce3=True, pbs='s3_S1_12a_Ce2O3'),
    'S1_12b_Ce2O3_Rh_from10b': dict(kind='ce', role='slab', ce3=True, pbs='s3_S1_12b_Ce2O3'),
    'S1_21_CeO2_gas':          dict(kind='ce', role='gas', ce3=False, pbs='s3_S1_21_CeO2_g'),
    'S1_22_Ce2O3_gas':         dict(kind='ce', role='gas', ce3=True, pbs='s3_S1_22_Ce2O3_'),
    'S1_23_Ce2O3_bulk_AFM':    dict(kind='bulk', role='bulk', ce3=True, pbs='s3_S1_23_Ce2O3_'),
    'S1_31_Ce4O6_layer_Rh3x3': dict(kind='ce', role='slab', ce3=True, pbs='s3_S1_31_Ce4O6_'),
}
RELAX_TAG = {'ce': 'stageB_relax', 'rh': 'relax', 'bulk': 'bulk_isif3'}

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


def qsub(script, cwd, sysname, retried=False):
    rc, out = sh('qsub %s' % script, cwd=cwd)
    if rc == 0 and 'stdct' in out:
        return out.split()[0].split('.')[0]
    low = out.lower()
    if any(k in low for k in ('disabled', 'not enabled', 'not accepting', 'queue is closed', 'stopped')):
        info.append('%s: 队列暂不接收作业（%s），多半是维护，下次检查自动重试' % (sysname, out[-120:]))
    elif any(k in low for k in ('project', 'credit', 'allocation', 'amgr', 'budget')) and not retried:
        sh('bash "$HOME/hpc_login.sh" > /dev/null 2>&1', timeout=180)      # never print the helper or its output
        return qsub(script, cwd, sysname, retried=True)
    elif any(k in low for k in ('project', 'credit', 'allocation', 'amgr', 'budget')):
        attention.append('%s: qsub %s 被拒（%s）；已用 ~/hpc_login.sh 刷新额度仍失败，需用户查额度' % (sysname, script, out[-160:]))
    else:
        attention.append('%s: qsub %s 失败（%s）' % (sysname, script, out[-200:]))
    return None


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
        attention.append('qstat 不可用或输出无法解析（rc=%s）：%s；本次只报告不操作' % (rc, out[:200]))
        return None
    return jobs


def job_hist(jid):
    rc, out = sh('qstat -xf -F json %s' % jid, timeout=60)
    try:
        return list(json.loads(out)['Jobs'].values())[0]
    except (ValueError, KeyError, IndexError):
        return {}


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


def scratch_quota():
    rc, out = sh('hpc space', timeout=90)
    m = re.search(r'/scratch/junbotong\s+([\d.]+)G\s+([\d.]+)G\s+([\d.]+)%', out)
    return (float(m.group(1)), float(m.group(2)), float(m.group(3))) if m else None


def readpos(fn):
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
    pos, flg = [], []
    for k in range(n):
        t = L[i + k].split()
        p = [float(x) for x in t[:3]]
        if cart:
            inv = _inv3(cell)
            p = [sum(p[j] * inv[j][c] for j in range(3)) for c in range(3)]
        pos.append(p)
        flg.append(t[3:6] if sd else ['T'] * 3)
    sym = [e for e, c in zip(el, cnt) for _ in range(c)]
    return el, cnt, pos, flg, sym, cell


def _inv3(m):
    a, b, c = m
    det = (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return [[(b[1] * c[2] - b[2] * c[1]) / det, (a[2] * c[1] - a[1] * c[2]) / det, (a[1] * b[2] - a[2] * b[1]) / det],
            [(b[2] * c[0] - b[0] * c[2]) / det, (a[0] * c[2] - a[2] * c[0]) / det, (a[2] * b[0] - a[0] * b[2]) / det],
            [(b[0] * c[1] - b[1] * c[0]) / det, (a[1] * c[0] - a[0] * c[1]) / det, (a[0] * b[1] - a[1] * b[0]) / det]]


def last_complete_block(txt, key, nlines, skip, first=False):
    parts = txt.split(key)[1:]
    for blk in (parts if first else reversed(parts)):
        rr = blk.split('\n')[skip:skip + nlines]
        if len(rr) == nlines and all(len(r.split()) >= 4 for r in rr):
            return rr
    return None


def forces_free(d, outcar='OUTCAR', first=False):
    try:
        flg, sym = readpos(os.path.join(d, 'POSCAR'))[3:5]
    except (IndexError, ValueError):
        return None
    rr = last_complete_block(read(os.path.join(d, outcar)), 'TOTAL-FORCE', len(sym), 2, first)
    if not rr:
        return None
    try:
        F = [[float(x) for x in r.split()[3:6]] for r in rr]
    except ValueError:
        return None
    free = [i for i, f in enumerate(flg) if f[0] == 'T']
    return max(math.sqrt(sum(c * c for c in F[i])) for i in free) if free else None


def ce_moments(outcar_txt, sym):
    rr = last_complete_block(outcar_txt, 'magnetization (x)', len(sym), 4)
    if not rr:
        return []
    try:
        return [float(rr[i].split()[-1]) for i in range(len(sym)) if sym[i] == 'Ce']
    except ValueError:
        return []


def spin_label(m):
    if not m:
        return '?'
    up = sum(1 for x in m if x > 0.3)
    dn = sum(1 for x in m if x < -0.3)
    if up == 0 and dn == 0:
        return '无磁（Ce⁴⁺）'
    return 'FM' if (up == 0 or dn == 0) else 'AFM %d↑%d↓' % (max(up, dn), min(up, dn))


SCF_RE = re.compile(r'^(?:DAV|RMM|CGA|SDA):\s*(\d+)\s+(\S+)\s+(\S+)')
ION_RE = re.compile(r'^\s*(\d+)\s+F=\s*(\S+)\s+E0=\s*(\S+)\s+d E =\s*(\S+)(?:\s+mag=\s*(\S+))?')


def fnum(s):
    try:
        return float(s)
    except ValueError:
        return float('nan')


def osz(d, name='OSZICAR'):
    ions, cur = [], []
    for l in read(os.path.join(d, name)).split('\n'):
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


def latest_o(d):
    fs = [f for f in glob.glob(os.path.join(d, '*.o*')) if re.search(r'\.o\d+$', f)]
    return max(fs, key=os.path.getmtime) if fs else None


def age_h(fn):
    try:
        return (time.time() - os.path.getmtime(fn)) / 3600
    except OSError:
        return None


def fatal_markers(d, extra=()):
    found = []
    for f in list(glob.glob(os.path.join(d, 'vasp*.out'))) + [x for x in extra if x]:
        if age_h(f) is not None and age_h(f) < 24 * 4:
            t = read(f, tail=200000)
            for pat, what in FATAL:
                if re.search(pat, t) and what not in found:
                    found.append(what)
    return found


def fmt(x, f='%.4f'):
    return (f % x) if isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x)) else (x or '—')


def e_sigma0(txt):
    v = re.findall(r'energy\(sigma->0\)\s*=\s*(-?[\d.]+)', txt)
    return float(v[-1]) if v else None


def structure_flags(sysname, d, role):
    fn = os.path.join(d, 'CONTCAR')
    if not read(fn).strip():
        fn = os.path.join(d, 'POSCAR')
    try:
        el, cnt, pos, flg, sym, cell = readpos(fn)
    except (IndexError, ValueError):
        return
    cart = [[sum(p[k] * cell[k][j] for k in range(3)) for j in range(3)] for p in pos]
    if role == 'slab' and 'Rh' in sym:
        zrh = max(c[2] for c, s in zip(cart, sym) if s == 'Rh')
        far = [(i + 1, s, c[2] - zrh) for i, (c, s) in enumerate(zip(cart, sym)) if s in ('Ce', 'O') and c[2] - zrh > DESORB_DZ]
        if far:
            attention.append('%s: 原子离开表面（%s，高于顶层 Rh > %.0f Å），疑似脱附' % (
                sysname, ', '.join('%s%d +%.1f Å' % (s, i, z) for i, s, z in far[:4]), DESORB_DZ))
    oi = [i for i, s in enumerate(sym) if s == 'O']
    for a in range(len(oi)):
        for b in range(a + 1, len(oi)):
            f = [pos[oi[a]][k] - pos[oi[b]][k] for k in range(3)]
            f = [x - round(x) for x in f]
            dv = [sum(f[k] * cell[k][j] for k in range(3)) for j in range(3)]
            dd = math.sqrt(sum(x * x for x in dv))
            if dd < OO_MIN:
                attention.append('%s: O%d–O%d 距离 %.2f Å，疑似形成 O₂' % (sysname, oi[a] + 1, oi[b] + 1, dd))
                return


def stages_in(o):
    t = read(o) if o else ''
    return (re.findall(r'stage=(\S+) start', t), re.findall(r'stage=(\S+) end=\S+ rc=0', t),
            re.findall(r'stage=(\S+) (SCF|RELAX) NOT converged', t), bool(re.search(r'^end=.* rc=0', t, re.M)),
            'watchdog_stop' in t)


def job_head(base):
    """Everything of a stage-3 job script up to the closing brace of the run_stage() function."""
    i = base.find('run_stage () {')
    j = base.find('\n}\n', i)
    if i < 0 or j < 0:
        raise ValueError('job.pbs has no run_stage() function')
    return base[:j + 3]


def job_from(d, name, calls, files):
    """New job script in d: header and run_stage() copied from job.pbs, stage calls replaced."""
    head = job_head(read(os.path.join(d, 'job.pbs')))
    head = re.sub(r'^for f in .*? POSCAR KPOINTS POTCAR; do', 'for f in %s POSCAR KPOINTS POTCAR; do' % files,
                  head, flags=re.M)
    write(os.path.join(d, name), head + calls + '\necho "end=$(date --iso-8601=seconds) rc=0"\n')


def incar_variant(src, dst, changes):
    t = read(src)
    for k, v in changes.items():
        if re.search(r'^%s\s*=' % k, t, re.M):
            t = re.sub(r'^%s\s*=.*$' % k, '%s = %s' % (k, v), t, flags=re.M)
        else:
            t += '%s = %s\n' % (k, v)
    write(dst, t)


# ---------------------------------------------------------------- handlers
def handle_held(sysname, j, st):
    comment = j.get('comment', '')
    if 'too many failed attempts' not in comment:
        return False
    args = j.get('Submit_arguments', '').split()
    vl = j.get('Variable_List', {})
    wd = vl.get('PBS_O_WORKDIR') if isinstance(vl, dict) else None
    st['hold'] = st.get('hold', 0) + 1
    if st['hold'] > MAX_HOLD:
        attention.append('%s: PBS %s 第 %d 次被系统挂起（%s），未再重投' % (sysname, j['id'], st['hold'], comment))
        return True
    sh('qdel %s' % j['id'])
    if len(args) == 1 and args[0].endswith('.pbs') and wd:
        new = qsub(args[0], wd, sysname)
        if new:
            log_action('%s: PBS %s 被系统挂起（%s），qdel 后原样重投 %s → %s' % (sysname, j['id'], comment, args[0], new))
            rows.append((sysname, new, 'Q（重投）', '挂起后重投', '—', '', 'qdel+qsub'))
        return True
    attention.append('%s: PBS %s 被系统挂起，提交参数 "%s" 不是单一脚本，已 qdel，需人工重投' % (sysname, j['id'], ' '.join(args)))
    return True


def running_row(sysname, cfg, st, j, d):
    stt = j.get('job_state')
    wall = j.get('resources_used', {}).get('walltime', '—')
    if stt != 'R':
        qt = pbs_time(j.get('qtime'))
        if qt and (NOW - qt).total_seconds() > QUEUE_WAIT_H * 3600:
            info.append('%s: 已排队 %.0f h（qstat -Qf batch_cpu | grep state_count 看拥堵）' % (sysname, (NOW - qt).total_seconds() / 3600))
        rows.append((sysname, j['id'], stt, '排队中', '—', '', ''))
        return
    o = latest_o(d)
    starts = stages_in(o)[0]
    tag = starts[-1] if starts else '?'
    ions, cur = osz(d)
    a = age_h(os.path.join(d, 'OSZICAR'))
    if a is not None and a > STALL_H and (hms(wall) or 0) >= 3600:
        attention.append('%s: 作业 R 但 OSZICAR 已 %.1f h 未更新（可能卡死）' % (sysname, a))
    if len(cur) >= OSC_MIN_STEPS:
        amp = max(abs(x[2]) for x in cur[-OSC_WINDOW:])
        if amp >= OSC_AMP:
            attention.append('%s: %s 当前 SCF 已 %d 步，最近 %d 步 |dE| 仍达 %.2g eV，在振荡' % (sysname, tag, len(cur), OSC_WINDOW, amp))
    relaxing = any(tag.startswith(t) for t in RELAX_TAG.values())
    if relaxing and ions:
        lim = incar_nelm(os.path.join(d, 'INCAR'))
        hit = [n for n, e0, mag, nscf in ions[-3:] if nscf >= lim]
        if hit:
            attention.append('%s: 弛豫第 %s 离子步 SCF 用满 NELM=%d，这些步的受力不可信' % (sysname, ','.join(map(str, hit)), lim))
        for (n0, e0, m0, _), (n1, e1, m1, _) in zip(ions, ions[1:]):
            if m0 is not None and m1 is not None and abs(m1 - m0) > MAG_JUMP:
                attention.append('%s: 第 %d→%d 离子步总磁矩 %.2f→%.2f μB 跳变（Ce 自旋翻转？）' % (sysname, n0, n1, m0, m1))
                break
        for (n0, e0, m0, _), (n1, e1, m1, _) in zip(ions, ions[1:]):
            if e1 - e0 > E_RISE:
                attention.append('%s: 第 %d→%d 离子步 E0 升高 %.3f eV' % (sysname, n0, n1, e1 - e0))
                break
        structure_flags(sysname, d, cfg['role'])
    if relaxing:
        fm = forces_free(d)
        prog = '%s 离子步 %d（累计 %d）%s' % (tag.replace('stage', ''), len(ions), st.get('ions_done', 0) + len(ions),
                                           '，当前 SCF %d' % cur[-1][0] if cur else '')
        rows.append((sysname, j['id'], 'R %s' % wall, prog, fmt(ions[-1][1] if ions else None),
                     'Fmax_free %s' % fmt(fm, '%.3f'), ''))
    else:
        rows.append((sysname, j['id'], 'R %s' % wall, '%s SCF %d' % (tag.replace('stage', ''), cur[-1][0] if cur else 0),
                     fmt(cur[-1][1] if cur else None), 'dE %s' % (('%.1e' % cur[-1][2]) if len(cur) > 1 else '—'), ''))


def classify_end(d, o):
    m = re.search(r'\.o(\d+)$', o or '')
    h = job_hist(m.group(1)) if m else {}
    used = hms(h.get('resources_used', {}).get('walltime'))
    lim = hms(h.get('Resource_List', {}).get('walltime'))
    return {'id': m.group(1) if m else '?', 'exit': h.get('Exit_status'),
            'walltime': used is not None and lim is not None and used >= lim - 300,
            'start': pbs_time(h.get('stime')), 'end': pbs_time(h.get('obittime')), 'fatal': fatal_markers(d, [o])}


def archive(d, what, files):
    arch = os.path.join(d, '%s_%s' % (what, NOW.strftime('%Y%m%d_%H%M')))
    os.makedirs(arch, exist_ok=True)
    for f in files:
        for g in glob.glob(os.path.join(d, f)):
            if os.path.isfile(g):
                shutil.move(g, os.path.join(arch, os.path.basename(g)))
    return arch


def restart_relax(sysname, cfg, st, d, c, how):
    st['seg'] = st.get('seg', 0) + 1
    if st['seg'] > MAX_SEG:
        attention.append('%s: 弛豫已续算 %d 段仍未收敛，停止自动续算（请判断是否换优化器/检查势能面）' % (sysname, st['seg'] - 1))
        return
    ions, _ = osz(d)
    wav = os.path.join(d, 'WAVECAR')
    wtime = datetime.datetime.fromtimestamp(os.path.getmtime(wav)) if os.path.exists(wav) else None
    if c['start'] and (wtime is None or wtime < c['start']):
        attention.append('%s: 上一段（PBS %s）没有写出新的 WAVECAR，续算从旧 WAVECAR 起步，Ce 自旋可能被重置（09-21 I1 教训）；已照常续算'
                         % (sysname, c['id']))
    fm, fm0 = forces_free(d), forces_free(d, first=True)
    if fm is not None and fm0 is not None and fm >= fm0 and len(ions) > 5:
        attention.append('%s: 这一段 %d 个离子步 Fmax_free 没有下降（%.3f → %.3f eV/Å）；已照常续算' % (sysname, len(ions), fm0, fm))
    tag = RELAX_TAG[cfg['kind']]
    if not os.path.exists(os.path.join(d, 'POSCAR_orig')):
        shutil.copy(os.path.join(d, 'POSCAR'), os.path.join(d, 'POSCAR_orig'))
    shutil.copy(os.path.join(d, 'CONTCAR'), os.path.join(d, 'CONTCAR_seg%02d' % st['seg']))
    arch = archive(d, 'seg%02d' % st['seg'], ['OSZICAR', 'OUTCAR', 'XDATCAR', 'vasprun.xml', 'OSZICAR_*', 'OUTCAR_*',
                                             'vasp_*.out', '*.o[0-9]*'])
    shutil.copy(os.path.join(arch, 'CONTCAR_seg%02d' % st['seg']) if os.path.exists(os.path.join(arch, 'CONTCAR_seg%02d' % st['seg']))
                else os.path.join(d, 'CONTCAR_seg%02d' % st['seg']), os.path.join(d, 'POSCAR'))
    rtag = tag + '_restart'
    incar_variant(os.path.join(d, 'INCAR_' + tag), os.path.join(d, 'INCAR_' + rtag), {'ISTART': 1, 'ICHARG': 1})
    job_from(d, 'job_restart.pbs', 'run_stage %s LSTOP relax' % rtag, 'INCAR_' + rtag)
    new = qsub('job_restart.pbs', d, sysname)
    st['ions_done'] = st.get('ions_done', 0) + len(ions)
    if new:
        log_action('%s: 弛豫%s（本段 %d 步，E0 %s，Fmax_free %s），归档到 %s，从 CONTCAR/WAVECAR 续算第 %d 段：%s'
                   % (sysname, how, len(ions), fmt(ions[-1][1] if ions else None, '%.5f'), fmt(fm, '%.3f'),
                      os.path.basename(arch), st['seg'] + 1, new))
        rows.append((sysname, new, 'Q（续算）', '上段 %d 步' % len(ions), fmt(ions[-1][1] if ions else None),
                     'Fmax_free %s' % fmt(fm, '%.3f'), '续算'))


def resume_stage_a(sysname, st, d):
    st['a_resume'] = st.get('a_resume', 0) + 1
    _, cur = osz(d, 'OSZICAR_stageA_spinSP') if os.path.exists(os.path.join(d, 'OSZICAR_stageA_spinSP')) else osz(d)
    if st['a_resume'] > MAX_A_RESUME:
        attention.append('%s: stage A（自旋单点，ALGO All）第 %d 次撞 NELM（末步 E %s, dE %s），停止自动续算，需诊断' % (
            sysname, st['a_resume'], fmt(cur[-1][1]) if cur else '?', ('%.1e' % cur[-1][2]) if cur else '?'))
        rows.append((sysname, '—', '停', 'stage A 撞 NELM', fmt(cur[-1][1]) if cur else '—', '', '需诊断'))
        return
    if len(cur) >= OSC_MIN_STEPS and max(abs(x[2]) for x in cur[-OSC_WINDOW:]) >= OSC_AMP:
        attention.append('%s: stage A 撞 NELM 时 |dE| 仍 ≥ %.0e eV（振荡而非缓慢下降）；已照常续算一次' % (sysname, OSC_AMP))
    archive(d, 'stageA_nelm%d' % st['a_resume'], ['OSZICAR_stageA_spinSP', 'OUTCAR_stageA_spinSP', 'vasp_stageA_spinSP.out', '*.o[0-9]*'])
    incar_variant(os.path.join(d, 'INCAR_stageA_spinSP'), os.path.join(d, 'INCAR_stageA_spinSP_r1'), {'ISTART': 1, 'ICHARG': 0})
    job_from(d, 'job_resumeA.pbs', 'run_stage stageA_spinSP_r1 LABORT scf\nrun_stage stageB_relax LSTOP relax',
             'INCAR_stageA_spinSP_r1 INCAR_stageB_relax')
    new = qsub('job_resumeA.pbs', d, sysname)
    if new:
        log_action('%s: stage A 自旋单点撞 NELM（末步 dE %s），从 WAVECAR 续算 A 再接 B：%s'
                   % (sysname, ('%.1e' % cur[-1][2]) if cur else '?', new))
        rows.append((sysname, new, 'Q（续算）', 'stage A 撞 NELM', fmt(cur[-1][1]) if cur else '—', '', '续算 A'))


def accept(sysname, cfg, d, outcar='OUTCAR'):
    """(ok, desc, E0, Ce moments) for a finished relaxation."""
    txt = read(os.path.join(d, outcar))
    el, cnt, p0, flg, sym, _ = readpos(os.path.join(d, 'POSCAR'))
    p1 = readpos(os.path.join(d, 'CONTCAR'))[2]
    fm = forces_free(d, outcar)
    fixed = [i for i in range(len(sym)) if flg[i][0] == 'F']
    disp = max([max(abs((a - b) - round(a - b)) for a, b in zip(p0[i], p1[i])) for i in fixed] or [0.0])
    m = ce_moments(txt, sym)
    e0 = e_sigma0(txt)
    ok = fm is not None and (fm <= FMAX_ACCEPT or cfg['role'] == 'bulk') and disp < 1e-6
    if cfg['ce3'] and m and not all(CE3_RANGE[0] <= abs(x) <= CE3_RANGE[1] for x in m):
        ok = False
    desc = 'Fmax_free %s, 固定原子位移 %.1e, Ce %s (%s), E0 %s' % (fmt(fm), disp, ['%.2f' % x for x in m], spin_label(m), fmt(e0, '%.5f'))
    n_attn = len(attention)
    structure_flags(sysname, d, cfg['role'])
    return ok and len(attention) == n_attn, desc, e0, m, fm


def build_final_sp(sysname, d):
    spd = os.path.join(d, 'final_sp')
    os.makedirs(spd)
    shutil.copy(os.path.join(d, 'CONTCAR'), os.path.join(spd, 'POSCAR'))
    for f in ('KPOINTS', 'POTCAR', 'POTCAR.spec'):
        shutil.copy2(os.path.join(d, f), os.path.join(spd, f))
    for f in ('WAVECAR', 'CHGCAR'):
        if os.path.exists(os.path.join(d, f)):
            os.symlink(os.path.join(d, f), os.path.join(spd, f))
    src = os.path.join(d, 'INCAR_stageB_relax') if os.path.exists(os.path.join(d, 'INCAR_stageB_relax')) else os.path.join(d, 'INCAR_relax')
    incar_variant(src, os.path.join(spd, 'INCAR_stageC_ldipol_final'), {
        'SYSTEM': 'final SP %s | stageC_ldipol_final' % sysname, 'ISTART': 1, 'ICHARG': 1, 'ALGO': 'All',
        'NELM': 500, 'EDIFF': '1E-6', 'IBRION': -1, 'NSW': 0, 'LDIPOL': '.TRUE.', 'IDIPOL': 3,
        'LWAVE': '.FALSE.', 'LCHARG': '.TRUE.'})
    t = read(os.path.join(spd, 'INCAR_stageC_ldipol_final'))
    t = re.sub(r'^(IOPT|POTIM|MAXMOVE|ISIF|EDIFFG)\s*=.*\n', '', t, flags=re.M)
    write(os.path.join(spd, 'INCAR_stageC_ldipol_final'), t)
    head = job_head(read(os.path.join(d, 'job.pbs')))
    head = re.sub(r'^#PBS -N (\S+)', lambda m: '#PBS -N %s' % ('sp' + m.group(1)[2:])[:15], head, flags=re.M)
    head = re.sub(r'^for f in .*? POSCAR KPOINTS POTCAR; do', 'for f in INCAR_stageC_ldipol_final POSCAR KPOINTS POTCAR; do', head, flags=re.M)
    write(os.path.join(spd, 'job.pbs'), head + 'run_stage stageC_ldipol_final LABORT scf\n'
          'echo "end=$(date --iso-8601=seconds) rc=0"\n')
    return spd


def ended(sysname, cfg, st, d, jobs_seen, scratch_ok):
    o = latest_o(d)
    starts, done_st, notconv, chain_ok, watchdog = stages_in(o)
    c = classify_end(d, o)
    if chain_ok:
        ok, desc, e0, m, fm = accept(sysname, cfg, d)
        if not ok:
            attention.append('%s: 弛豫已结束但验收未过（%s），未继续' % (sysname, desc))
            rows.append((sysname, '—', '收敛待判', '验收未过', fmt(e0), 'Fmax_free %s' % fmt(fm, '%.3f'), '需人工'))
            st['phase'] = 'hold'
            return
        st.update({'relax_E0': e0, 'relax_ce': m, 'relax_spin': spin_label(m)})
        if cfg['role'] != 'slab':
            st.update({'phase': 'final', 'E0': e0, 'ce': m, 'spin': spin_label(m)})
            if cfg['kind'] == 'bulk':
                cell = readpos(os.path.join(d, 'CONTCAR'))[5]
                st['cell'] = [round(math.sqrt(sum(x * x for x in v)), 5) for v in cell]
            log_action('%s 验收通过（%s），为最终值' % (sysname, desc))
            rows.append((sysname, '—', '完成', '已验收', fmt(e0, '%.5f'), spin_label(m), '收下'))
            return
        if not scratch_ok:
            attention.append('%s: 弛豫已验收，但 scratch 配额过高，暂不建最终单点' % sysname)
            return
        if os.path.exists(os.path.join(d, 'final_sp')):
            attention.append('%s: final_sp 已存在但不在队列中，未覆盖' % sysname)
            return
        spd = build_final_sp(sysname, d)
        new = qsub('job.pbs', spd, sysname)
        if new:
            st.update({'phase': 'sp', 'sp_pbs_name': re.search(r'^#PBS -N (\S+)', read(os.path.join(spd, 'job.pbs')), re.M).group(1)})
            log_action('%s 弛豫验收通过（%s）；建 final_sp（ISPIN 2, 450 eV, LDIPOL on, EDIFF 1e-6，从弛豫 WAVECAR/CHGCAR）：%s'
                       % (sysname, desc, new))
        rows.append((sysname, new or '—', '弛豫已收敛', '最终单点已提交', fmt(e0), 'Fmax_free %s' % fmt(fm, '%.3f'), '建单点'))
        return
    if c['fatal']:
        attention.append('%s: PBS %s 以致命错误结束（%s），未自动处理' % (sysname, c['id'], '；'.join(c['fatal'])))
        abnormal.append((sysname, c['end']))
        return
    if not scratch_ok:
        attention.append('%s: 需续算但 scratch 配额过高，暂不提交' % sysname)
        return
    if notconv:
        stg, what = notconv[-1]
        if what == 'SCF' and stg.startswith('stageA'):
            resume_stage_a(sysname, st, d)
            return
        if what == 'RELAX':
            restart_relax(sysname, cfg, st, d, c, '看门狗停机' if watchdog else '未收敛（NSW 用完）')
            return
        attention.append('%s: %s %s NOT converged（非预期组合），未自动处理' % (sysname, stg, what))
        return
    if c['walltime'] or watchdog:
        if starts and (starts[-1].startswith('stageB') or starts[-1] in RELAX_TAG.values() or starts[-1].endswith('_restart')):
            restart_relax(sysname, cfg, st, d, c, '撞墙被杀')
            return
    abnormal.append((sysname, c['end']))
    st['crash'] = st.get('crash', 0) + 1
    if st['crash'] > MAX_CRASH:
        attention.append('%s: 第 %d 次非正常结束（PBS %s, Exit %s），停止自动重投' % (sysname, st['crash'], c['id'], c['exit']))
        return
    last = starts[-1] if starts else None
    if last and (last.startswith('stageB') or last in RELAX_TAG.values() or last.endswith('_restart')) \
            and read(os.path.join(d, 'CONTCAR')).strip() and osz(d)[0]:
        restart_relax(sysname, cfg, st, d, c, '非正常结束（Exit %s）' % c['exit'])
        return
    arch = archive(d, 'crash', ['OSZICAR', 'OUTCAR', 'vasp_*.out', '*.o[0-9]*'])
    new = qsub('job.pbs', d, sysname)
    if new:
        log_action('%s: 在 %s 非正常结束（Exit %s），部分输出归档到 %s，重投 job.pbs：%s'
                   % (sysname, last or '启动前', c['exit'], os.path.basename(arch), new))
        rows.append((sysname, new, 'Q（重投）', '中断后重投', '—', '', 'resubmit'))


def ended_sp(sysname, cfg, st, d):
    spd = os.path.join(d, 'final_sp')
    o = latest_o(spd)
    starts, done_st, notconv, chain_ok, watchdog = stages_in(o)
    if chain_ok:
        oc = read(os.path.join(spd, 'OUTCAR'))
        sym = readpos(os.path.join(spd, 'POSCAR'))[4]
        e0 = e_sigma0(oc)
        m = ce_moments(oc, sym)
        st.update({'phase': 'final', 'E0': e0, 'ce': m, 'spin': spin_label(m)})
        log_action('%s 最终单点完成：E0 = %s eV，Ce %s（%s）' % (sysname, fmt(e0, '%.5f'), ['%.2f' % x for x in m], spin_label(m)))
        if cfg['ce3'] and [x for x in m if abs(x) < CE_MAG_LOW]:
            attention.append('%s: 最终单点 Ce 磁矩 %s，有 Ce 不再是 Ce³⁺' % (sysname, ['%.2f' % x for x in m]))
        if st.get('relax_spin') and st['relax_spin'] != spin_label(m):
            attention.append('%s: 最终单点自旋排列 %s 与弛豫 %s 不同；比较前需判断' % (sysname, spin_label(m), st['relax_spin']))
        if st.get('relax_E0') is not None and e0 is not None and abs(e0 - st['relax_E0']) > 0.3:
            attention.append('%s: 最终单点 − 弛豫能量差 %+.3f eV（> 0.3 eV），偶极校正前后差别异常' % (sysname, e0 - st['relax_E0']))
        rows.append((sysname, '—', '完成', '最终单点', fmt(e0, '%.5f'), spin_label(m), '取能量'))
        return
    c = classify_end(spd, o)
    if c['fatal']:
        attention.append('%s: 最终单点 PBS %s 以致命错误结束（%s）' % (sysname, c['id'], '；'.join(c['fatal'])))
        return
    st['sp_resume'] = st.get('sp_resume', 0) + 1
    if st['sp_resume'] > MAX_SP_RESUME:
        attention.append('%s: 最终单点第 %d 次未完成（PBS %s, Exit %s），停止自动续算，需诊断（LDIPOL 振荡？）'
                         % (sysname, st['sp_resume'], c['id'], c['exit']))
        return
    arch = archive(spd, 'try%d' % st['sp_resume'], ['OSZICAR*', 'OUTCAR*', 'vasp_*.out', '*.o[0-9]*'])
    if os.path.islink(os.path.join(spd, 'WAVECAR')) or not os.path.exists(os.path.join(spd, 'WAVECAR')):
        pass
    incar_variant(os.path.join(spd, 'INCAR_stageC_ldipol_final'), os.path.join(spd, 'INCAR_stageC_ldipol_final'), {'NELM': 800})
    new = qsub('job.pbs', spd, sysname)
    if new:
        log_action('%s: 最终单点未完成（%s），归档到 %s，NELM 800 重投：%s' % (
            sysname, 'SCF 未收敛' if notconv else 'Exit %s' % c['exit'], os.path.basename(arch), new))
        rows.append((sysname, new, 'Q（续算）', '最终单点重投', '—', '', 'resume'))


def results_table(state):
    s = state['systems']
    E = {k: v.get('E0') for k, v in s.items()}
    def de(x, rh, gas, n):
        if None in (E.get(x), E.get(rh), E.get(gas)):
            return None
        return (E[x] - E[rh] - n * E[gas]) / n
    rows_ = []
    for x, lab, rh, gas, n in (('S1_12a_Ce2O3_Rh_from10a', 'Ce₂O₃ 团簇（起点 10a）', 'S1_01_Rh111_4x4', 'S1_22_Ce2O3_gas', 1),
                               ('S1_12b_Ce2O3_Rh_from10b', 'Ce₂O₃ 团簇（起点 10b）', 'S1_01_Rh111_4x4', 'S1_22_Ce2O3_gas', 1),
                               ('S1_31_Ce4O6_layer_Rh3x3', 'Ce₂O₃ 层 Ce₄O₆（3×3）', 'S1_02_Rh111_3x3', 'S1_22_Ce2O3_gas', 2),
                               ('S1_11a_CeO2_Rh_flat', 'CeO₂ 单元（O 在穴位）', 'S1_01_Rh111_4x4', 'S1_21_CeO2_gas', 1),
                               ('S1_11b_CeO2_Rh_Cedown', 'CeO₂ 单元（Ce 朝下）', 'S1_01_Rh111_4x4', 'S1_21_CeO2_gas', 1)):
        v = de(x, rh, gas, n)
        nce = 2 if 'Ce2O3' in gas else 1
        rows_.append('| %s | %s | %s | %s |' % (lab, fmt(E.get(x), '%.5f'), fmt(v, '%+.3f'), fmt(v / nce if v is not None else None, '%+.3f')))
    ab = s.get('S1_00_Rh_bulk_450', {}).get('cell')
    a0 = ab[0] * math.sqrt(2) if ab else None
    return ('| 体系 | E0 (eV) | E_int 每单元 (eV) | E_int 每 Ce (eV) |\n|---|---|---|---|\n' + '\n'.join(rows_) +
            '\n\nE_int = [E(X/Rh) − E(Rh) − n·E(单元, 气相)] / n；Ce₂O₃ 层 n = 2。Rh a₀(450 eV) = %s Å（板用 3.8232 Å）。'
            % fmt(a0, '%.4f'))


# ---------------------------------------------------------------- main
def run(state):
    q = scratch_quota()
    scratch_ok = not (q and q[2] >= SCRATCH_ATTN)
    if not scratch_ok:
        attention.append('scratch 配额 %.1f%%（%.1f/%.0f G），暂停新提交' % (q[2], q[0], q[1]))
    jobs = queue()
    paused = os.path.exists(os.path.join(MON, 'PAUSE'))
    if paused:
        attention.append('monitor/PAUSE 存在：本次只报告，不执行任何操作')
    for sysname, cfg in (SYSTEMS.items() if jobs is not None else []):
        st = state['systems'].setdefault(sysname, {'phase': 'run'})
        d = os.path.join(IN, sysname)
        try:
            if st.get('phase') == 'final':
                rows.append((sysname, '—', '完成', '最终', fmt(st.get('E0'), '%.5f'), st.get('spin', ''), ''))
                continue
            if st.get('phase') == 'hold':
                rows.append((sysname, '—', '等待人工', '验收未过', fmt(st.get('relax_E0')), '', ''))
                continue
            name = st.get('sp_pbs_name') if st.get('phase') == 'sp' else cfg['pbs']
            js = [j for j in jobs.get(name, []) if j.get('job_state') in ('R', 'Q', 'H', 'W', 'E', 'B')]
            if js:
                j = js[0]
                if j.get('job_state') == 'H' and not paused and handle_held(sysname, j, st):
                    continue
                running_row(sysname, cfg, st, j, os.path.join(d, 'final_sp') if st.get('phase') == 'sp' else d)
            elif paused:
                rows.append((sysname, '—', '不在队列', '（PAUSE，未处理）', '—', '', ''))
            elif st.get('phase') == 'sp':
                ended_sp(sysname, cfg, st, d)
            else:
                ended(sysname, cfg, st, d, jobs, scratch_ok)
        except Exception as e:
            attention.append('%s: 监控脚本处理出错 %s: %s' % (sysname, type(e).__name__, str(e)[:150]))
    ends = sorted((t, s) for s, t in abnormal if t)
    for (t0, s0), (t1, s1) in zip(ends, ends[1:]):
        if (t1 - t0).total_seconds() <= SIMUL_MIN * 60:
            attention.append('%s 与 %s 在 %s 前后 %d 分钟内同时非正常结束，疑似集群/配额事件' % (s0, s1, t0.strftime('%m-%d %H:%M'), SIMUL_MIN))
            break
    names = {c['pbs'] for c in SYSTEMS.values()} | {v.get('sp_pbs_name') for v in state['systems'].values()}
    for name, js in (jobs or {}).items():
        for j in js:
            if name not in names and j.get('job_state') not in ('F', 'X'):
                rows.append((name, j['id'], j.get('job_state'), '（非监控对象）', '—', j.get('comment', '')[:40], ''))
    if all(state['systems'].get(k, {}).get('phase') == 'final' for k in SYSTEMS) and not state.get('done'):
        os.makedirs(os.path.join(S, 'results'), exist_ok=True)
        write(os.path.join(S, 'results', 'stage3_step1_table.md'),
              '# Stage 3 第 1 步：CeO₂ 单元 / Ce₂O₃ 团簇 / Ce₂O₃ 层与 Rh(111) 的相互作用能（%s）\n\n'
              '合同：ENCUT 450，ISPIN 2，PBE+U 5 eV，底层 z = 0；板为 LDIPOL 最终单点，气相为弛豫终值。\n\n%s\n'
              % (NOW.strftime('%Y-%m-%d %H:%M'), results_table(state)))
        state['done'] = True
        log_action('第 1 步全部完成，结果表写入 results/stage3_step1_table.md')
    return q


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
    q, state = None, None
    try:
        state = json.loads(read(STATE)) if os.path.exists(STATE) else {'systems': {}, 'done': False}
        state.setdefault('systems', {})
        q = run(state)
        write(STATE, json.dumps(state, indent=1, ensure_ascii=False))
    except Exception as e:
        attention.append('监控脚本整体出错 %s: %s | %s' % (type(e).__name__, str(e)[:200],
                                                        traceback.format_exc().strip().split('\n')[-2][:200]))
    finally:
        os.rmdir(lock)
    done = bool(state and state.get('done'))
    nxt = (NOW + datetime.timedelta(hours=CADENCE_H)).strftime('%m-%d %H:%M')
    if done:
        concl = '第 1 步全部完成，结果表已生成，监控可以结束。'
    elif attention:
        concl = '有 %d 项需要处理（见下）。' % len(attention)
    elif actions:
        concl = '本次自动执行了 %d 个操作，其余作业正常。' % len(actions)
    else:
        concl = '所有作业正常运行，无需操作。'
    out = ['# Vanda stage-3 监控 %s SGT' % NOW.strftime('%Y-%m-%d %H:%M'), '', concl, '',
           '| 体系 | PBS | 状态 | 进度 | E (eV) | Fmax_free / SCF dE / 自旋 | 本次操作 |',
           '|---|---|---|---|---|---|---|']
    out += ['| %s |' % ' | '.join(str(c) for c in r) for r in rows]
    if q:
        out += ['', 'scratch 配额：%.1f / %.0f G（%.1f%%）' % q]
    if attention:
        out += ['', '**需要处理：**'] + ['- ' + a for a in attention]
    if actions:
        out += ['', '**本次操作：**'] + ['- ' + a for a in actions]
    if info:
        out += ['', '**备注：**'] + ['- ' + a for a in info]
    if done:
        out += ['', results_table(state)]
    out += ['', '下次检查：%s SGT' % nxt]
    report = '\n'.join(out)
    write(os.path.join(MON, 'status_latest.md'), report + '\n')
    with open(os.path.join(MON, 'monitor.log'), 'a') as f:
        f.write(report + '\n\n')
    toast = '; '.join('%s %s %s' % (r[0][3:8], r[3], r[5]) for r in rows[:4]) or concl
    if attention:
        toast = '需要处理 %d 项：%s' % (len(attention), attention[0][:80])
    print('===REPORT===\n%s\n===ACTIONS===\n%s\n===ATTN===\n%s\n===TOAST===\n%s\n===FLAGS===\nATTENTION=%d\nDONE=%d' % (
        report, '\n'.join(actions), '\n'.join(attention), toast, 1 if attention else 0, 1 if done else 0))


if __name__ == '__main__':
    main()
