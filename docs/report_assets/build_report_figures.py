"""Reproduce report-specific scientific figures without changing the existing plots."""
from pathlib import Path
import re
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 12, 'axes.spines.top': False, 'axes.spines.right': False})
from matplotlib import font_manager
font_manager.fontManager.addfont('/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts/meiryo.ttc')
plt.rcParams['font.family'] = 'Meiryo'
df = pd.read_csv(ROOT/'data/processed/pilot_batch_results.csv')
df['selectivity_gcmc'] = df.co2_mol_kg / df.n2_mol_kg * 0.85 / 0.15
df.to_csv(OUT/'pilot_plot_data.csv', index=False)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout='constrained')
for ax, x, y, label, logarithmic in [
    (axes[0], 'pred_co2_binary_uptake_0p15bar_298K', 'co2_mol_kg', 'CO2 uptake [mmol/g]', False),
    (axes[1], 'pred_co2_n2_selectivity', 'selectivity_gcmc', 'CO2/N2 selectivity [-]', True)]:
    for tier, color in [('A','#2a78d6'),('B','#d66a28'),('C','#159c77')]:
        for oms, marker in [(True,'^'),(False,'o')]:
            d = df[(df.tier==tier)&(df.has_oms==oms)]
            ax.scatter(d[x],d[y],c=color,marker=marker,s=45,label=f'Tier {tier}, OMS {"yes" if oms else "no"}')
    lo, hi = (1,2000) if logarithmic else (0,8)
    ax.plot([lo,hi],[lo,hi],ls='--',color='gray',lw=1)
    if logarithmic: ax.set_xscale('log'); ax.set_yscale('log')
    ax.set(xlim=(lo,hi),ylim=(lo,hi),xlabel='ML prediction: '+label,ylabel='GCMC calculation: '+label)
    ax.set_title(f'Spearman rho = {spearmanr(df[x], df[y]).statistic:.2f} (n=20)')
    ax.grid(alpha=.2)
axes[0].legend(fontsize=8,loc='lower right')
fig.savefig(OUT/'pilot_parity.png',dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10,4.5),layout='constrained')
rows=[]
for sid, label in [('2022[Tb][umc]3[ASR]1','Tb'),('2020[Sc][nan]3[ASR]1','Sc'),('2014[Eu][esg]3[ASR]1','Eu'),('2019[Zr][scu]3[ASR]4','Zr')]:
    path=next((ROOT/'simulations/pilot_batch'/sid/'Output/System_0').glob('*.data'))
    raw=path.read_text()
    matches=list(re.finditer(r'^(\[Init\]\s*)?Current cycle:\s*(\d+) out of (\d+)',raw,re.M))
    points=[]
    for i,m in enumerate(matches):
        block=raw[m.end(): matches[i+1].start() if i+1<len(matches) else len(raw)]
        val=re.search(r'absolute adsorption:.*?\[mol/uc\],\s*([\d.]+)',block)
        if val:
            phase='initialization' if m.group(1) else 'production'
            cycle=int(m.group(2))+(0 if m.group(1) else 5000); q=float(val.group(1))
            points.append((cycle,q));rows.append([sid,cycle,q,phase,str(path.relative_to(ROOT))])
    ax.plot([p[0] for p in points],[p[1] for p in points],'-o',label=label)
ax.axvline(5000,color='gray',ls='--',label='Production starts')
ax.set(xlabel='Cumulative MC cycle',ylabel='Instantaneous CO2 loading [mmol/g]',title='Saved instantaneous loadings: initialization and production')
ax.legend(title='Metal');ax.grid(alpha=.2)
fig.savefig(OUT/'initialization_trace.png',dpi=180)
with (OUT/'initialization_plot_data.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['structure_id','cycle','co2_mmol_g','phase','source']);w.writerows(rows)

en = pd.read_csv(ROOT/'data/processed/pilot_batch_enriched.csv')
fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
for flag,x,label,color in [(False,0,'OMSなし','#2a78d6'),(True,1,'OMSあり','#df7637')]:
    sub=en[en.has_oms==flag]
    offsets=[(i-(len(sub)-1)/2)*0.035 for i in range(len(sub))]
    axes[0].scatter([x+v for v in offsets],sub.co2_mol_kg,s=40,color=color)
    avg=sub.co2_mol_kg.mean()
    axes[0].plot([x-.23,x+.23],[avg,avg],color='black',lw=2)
    axes[0].text(x,7.4,f'n={len(sub)} / 平均 {avg:.2f}',ha='center',fontsize=10)
axes[0].set(xticks=[0,1],xticklabels=['OMSなし','OMSあり'],ylabel='CO₂吸着量 [mmol/g]',ylim=(0,8.1),title='OMS有無と乾燥吸着量')
colors={True:'#df7637',False:'#2a78d6'}
for flag in [False,True]:
    sub=en[en.has_oms==flag]
    axes[1].scatter(sub.density,sub.s_gcmc,c=colors[flag],s=40,label='OMSあり' if flag else 'OMSなし')
axes[1].set(yscale='log',xlabel='結晶密度 [g/cm³]',ylabel='CO₂/N₂選択性 [−]',title=f'密度と選択性：ρ={spearmanr(en.density,en.s_gcmc).statistic:.2f}')
axes[1].legend(fontsize=9)
for ax in axes: ax.grid(alpha=.2)
fig.savefig(OUT/'discussion.png',dpi=180)
en.to_csv(OUT/'discussion_plot_data.csv',index=False)
