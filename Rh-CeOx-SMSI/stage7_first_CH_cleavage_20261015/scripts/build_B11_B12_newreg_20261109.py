import numpy as np
from ase.io import read, write
from ase.geometry import find_mic
b5=read('inputs_3x3/B5b_CH4_toB4_fromB2/CONTCAR'); b4=read('inputs/B4_CH3Os_HOs/CONTCAR'); b0=read('inputs/B0_ref/CONTCAR')
print('cells equal', np.allclose(b5.cell,b4.cell), np.allclose(b5.cell,b0.cell), b4.get_chemical_symbols()==b5.get_chemical_symbols())
s=b5.get_chemical_symbols()
lay=[i for i,x in enumerate(s) if x in ('Ce','O')]; ads=[i for i,x in enumerate(s) if x in ('C','H')]
# B11: B5b without CH4
b11=b5[[i for i,x in enumerate(s) if x not in ('C','H')]]
write('B11/POSCAR',b11,format='vasp',direct=True,sort=False)
# B12: B4 with layer+adsorbates translated (xy) onto the B5b registry
dv,_=find_mic(b5.positions[lay]-b4.positions[lay],b4.cell); t=dv.mean(0); t[2]=0
print('translation',np.round(t,3), 'resid per layer atom', np.round(np.linalg.norm(dv-t,axis=1),2))
b12=b4.copy(); b12.positions[lay+ads]+=t; b12.wrap()
c=b4.constraints
write('B12/POSCAR',b12,format='vasp',direct=True,sort=False)
for nm,a in [('B11',b11),('B12',b12),('B5b',b5),('B4',b4)]:
    D=a.get_all_distances(mic=True); np.fill_diagonal(D,99)
    rh=[i for i,x in enumerate(a.get_chemical_symbols()) if x=='Rh']; ot=[i for i,x in enumerate(a.get_chemical_symbols()) if x!='Rh']
    print(nm, 'min dist %.2f'%D.min(), 'min Rh-layer %.2f'%D[np.ix_(rh,ot)].min(), 'fixed', len(a.constraints[0].index) if a.constraints else 0)
