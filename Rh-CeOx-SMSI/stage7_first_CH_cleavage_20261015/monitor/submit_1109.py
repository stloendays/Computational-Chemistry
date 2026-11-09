"""2026-11-09: submit after the /scratch-full outage (11-09 ~02:00) once PBS answers.
B11/B11b/B12 = B on the B5b layer registry (user: 改用新层位置); NEB A resume (watchdog stop, 148 steps);
NEB C resume (killed by ENOSPC; NEB only); D8 r5 (FIRE, killed by ENOSPC).
NEB D (user 11-09 "现在重建 D"): new band from build_neb_D_two_keyframes_20261109.py, NEB only.
User 11-09: no stage A any more ("之后都不需要算"): B11/B11b/B12 run stage B only, NEBs start from ISTART 0."""
import json, os, re, shutil, sys
sys.path.insert(0, '/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/monitor')
import monitor_stage7 as m
S = m.S
DONE = os.path.join(m.MON, 'submit_1109.done')
if os.path.exists(DONE):
    print('ALREADY_DONE'); sys.exit(0)
rc, out = m.sh('qstat -u junbotong')
if rc != 0:
    print('PBS_DOWN'); sys.exit(9)
SUB = []
def qsub(pbs, d):
    rc, out = m.sh('qsub %s' % pbs, cwd=d)
    jid = out.strip().split('.')[0]
    assert rc == 0 and jid.isdigit(), out
    return jid
st = json.loads(m.read(m.STATE))
for name, why in [('B11_ref_fromB5b', 'B parent on the B5b registry (layer slid 0.65 A, B5b 0.262 eV below B2); start: B5b WAVECAR, ICHARG 0, ALGO Normal'),
                  ('B11b_ref_fromB0', 'same POSCAR as B11, backup start from the old B0 WAVECAR+CHGCAR (ICHARG 1)'),
                  ('B12_CH3Os_HOs_fromB5b', 'B4 shifted (-0.428, +0.498, 0) A onto the B5b registry; start: B5b WAVECAR+CHGCAR')]:
    d = os.path.join(m.IN3, name)
    j = qsub('job.pbs', d)
    st['systems']['3x3/' + name] = {'phase': 'run', 'jid': j}
    SUB.append(('3x3/' + name, j, why))
# NEB A: CONTCAR -> POSCAR per image, keep run-1 outputs
d = os.path.join(S, 'neb_3x3', 'A_neb')
for k in range(1, 7):
    m.sh('cp POSCAR POSCAR_run1 && cp CONTCAR POSCAR && cp OSZICAR OSZICAR_run1 && cp OUTCAR OUTCAR_run1', cwd=os.path.join(d, '%02d' % k))
m.sh('cp neb_profile.txt neb_profile_run1.txt; mv vasp_neb.out vasp_neb_run1.out', cwd=d)
j = qsub('job_neb.pbs', d)
st['neb']['A'] = {'jid': j, 'phase': 'run', 'E00': st['neb']['A'].get('E00'), 'run1': '1523636 148 steps, 05 +0.616, Fmax 0.083'}
SUB.append(('neb_3x3/A_neb', j, 'resume from image CONTCARs (1523636 watchdog stop at 148 steps, not converged, Fmax 0.083)'))
# NEB C: CONTCAR -> POSCAR, redo stage A on the current images, then NEB
d = os.path.join(S, 'neb_3x3', 'C_neb')
for k in range(1, 7):
    m.sh('cp POSCAR POSCAR_run1 && cp CONTCAR POSCAR && cp OSZICAR OSZICAR_run1 && cp OUTCAR OUTCAR_run1; rm -f WAVECAR CHGCAR', cwd=os.path.join(d, '%02d' % k))
m.sh('mkdir -p run1_1525494 && mv vasp_neb.out vasp_neb_stageA.out vasp_neb_stageA_r1.out s7neb_C_C10C9.o1525494 run1_1525494/', cwd=d)
j = qsub('job_neb.pbs', d)
st['neb']['C'] = {'jid': j, 'phase': 'run', 'E00': st['neb']['C'].get('E00'), 'run1': '1525494 killed by /scratch full at 197 steps'}
SUB.append(('neb_3x3/C_neb', j, '1525494 killed by /scratch full (ENOSPC) at 197 steps; CONTCAR -> POSCAR, NEB only (no stage A, user 11-09), ISTART 0 / MAGMOM Ce 1'))
d = os.path.join(S, 'neb_3x3', 'D_neb')
j = qsub('job_neb.pbs', d)
st['neb']['D'] = {'jid': j, 'phase': 'run', 'E00': st['neb']['D'].get('E00'),
                  'run1': '1526950 killed by ENOSPC at 80 steps; image 04 H45-H42 1.09 A, +6.5 eV (kept in D_neb_run1_1526950)'}
SUB.append(('neb_3x3/D_neb', j, 'path rebuilt (build_neb_D_two_keyframes_20261109.py): H abstraction by O38 (image 02 C-H 1.30, O-H 1.15), '
            'CH3 rotates and rebinds O40 (image 05 C-O40 2.05); stage A on the images, then NEB'))
# D8 r5 (FIRE as r4)
name = '3x3/D8_CH3Ce_HOs'; d = m.sysdir(name)
m.sh('cp POSCAR POSCAR_before_r5 && cp CONTCAR CONTCAR_before_r5 && cp CONTCAR POSCAR', cwd=d)
pbs, tag = m.make_resume(name, 'dis', d, 'B', 5)
m.write(os.path.join(d, 'INCAR_' + tag), m.read(os.path.join(d, 'INCAR_stageB_relax_r4')).replace('stageB_relax_r4', tag))
j = qsub(pbs, d)
st['systems'][name] = {'phase': 'run', 'jid': j, 'auto_n': 5}
SUB.append((name, j, 'r4 (FIRE) killed by /scratch full at step 168 (E0 -349.4495); CONTCAR -> POSCAR, %s (FIRE)' % tag))
m.write(m.STATE, json.dumps(st, indent=1, ensure_ascii=False))
open(DONE, 'w').write(m.ts())
for k, j, why in SUB:
    msg = '%s %s: %s' % (k, j, why)
    open(m.SUBLOG, 'a').write(msg + '\n'); m.log_action(msg); print(msg)
