"""2026-11-09 (user: 改用新层位置): B on the B5b layer registry. B11 = B5b without CH4 (from B5b WAVECAR, ICHARG 0);
B11b = same POSCAR from the old B0 WAVECAR+CHGCAR (ICHARG 1), backup start; B12 = B4 shifted onto the B5b registry
(from B5b WAVECAR+CHGCAR). ALGO Normal throughout (B lesson: ALGO All + WAVECAR diverges)."""
import os, re, shutil
S = '/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015'
IN3 = S + '/inputs_3x3'; B5b = IN3 + '/B5b_CH4_toB4_fromB2'; B0 = S + '/inputs/B0_ref'; UP = S + '/monitor/up_1109'
def rd(p): return open(p).read()
def wr(p, t): open(p, 'w').write(t)
jobs = {'B11_ref_fromB5b': ('B11', 3, 'B5b', 0, 's73_B11_ref'),
        'B11b_ref_fromB0': ('B11', 3, 'B0', 1, 's73_B11b_ref'),
        'B12_CH3Os_HOs_fromB5b': ('B12', 5, 'B5b', 1, 's73_B12_CH3O')}
for name, (pos, nsp, src, ichg, jn) in jobs.items():
    d = IN3 + '/' + name
    assert not os.path.exists(d), d
    os.makedirs(d)
    shutil.copyfile(UP + '/%s_POSCAR' % pos, d + '/POSCAR')
    shutil.copyfile(B5b + '/KPOINTS', d + '/KPOINTS')
    pd = B5b if nsp == 5 else B0
    shutil.copyfile(pd + '/POTCAR', d + '/POTCAR'); shutil.copyfile(pd + '/POTCAR.spec', d + '/POTCAR.spec')
    for f in ('INCAR_stageA_spinSP', 'INCAR_stageB_relax'):
        t = rd(B5b + '/' + f).replace('| B5b_CH4_toB4_fromB2 |', '| %s |' % name)
        if nsp == 3:
            t = t.replace('LDAUL = -1 3 -1 -1 -1', 'LDAUL = -1 3 -1').replace('LDAUU = 0.0 5.0 0.0 0.0 0.0', 'LDAUU = 0.0 5.0 0.0') \
                 .replace('LDAUJ = 0.0 0.0 0.0 0.0 0.0', 'LDAUJ = 0.0 0.0 0.0')
            assert 'LDAUL = -1 3 -1\n' in t
        if f == 'INCAR_stageA_spinSP':
            t = re.sub(r'^ICHARG = \d+', 'ICHARG = %d' % ichg, t, flags=re.M)
        assert name in t and 'ALGO = Normal' in t and 'ISTART = 1' in t
        wr(d + '/' + f, t)
    job = re.sub(r'^#PBS -N \S+', '#PBS -N ' + jn, rd(B5b + '/job.pbs'), count=1, flags=re.M)
    wr(d + '/job.pbs', job); os.chmod(d + '/job.pbs', 0o755)
    sd = B5b if src == 'B5b' else B0
    shutil.copyfile(sd + '/WAVECAR', d + '/WAVECAR')
    if ichg == 1:
        shutil.copyfile(sd + '/CHGCAR', d + '/CHGCAR')
    os.system('cd %s && head -1 POSCAR && sed -n 6,7p POSCAR && grep -h -e ICHARG -e LDAUL INCAR_stageA_spinSP && cat POTCAR.spec | tr "\n" " " && grep "^#PBS -N" job.pbs && ls' % d)
