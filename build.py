import pandas as pd, json, re
U='/root/.claude/uploads/46b06f00-6383-5dda-a809-eb7b46cc4249/'
def fix(s):
    try: return s.encode('cp1252').decode('utf8')
    except Exception: return s
df=pd.read_excel(U+'39e453f9-contatos_grupos_tradenews_2.xlsx',dtype={'contact':str}).dropna(how='all')
df['Sub_area']=df.Sub_area.map(lambda s: fix(str(s)))
df['contact']=df.contact.str.replace(r'\D','',regex=True)
d=df.drop_duplicates('contact').copy()
d['auc']=pd.to_numeric(d.auc,errors='coerce')
d['Sub_area']=d.Sub_area.replace({'0':'SEM SUB_AREA'})
def key(p):
    p=re.sub(r'\D','',str(p))
    if p.startswith('55') and len(p)>=12: p=p[2:]
    return p[:2]+p[-8:] if len(p)>=10 else None
d['k']=d.contact.map(key)
# planilha de apoio: um registro por telefone (prefere cliente SIM, depois maior AUC)
b=pd.read_excel(U+'15427ea4-apoio1_tradenews.xlsx',sheet_name='CONTATOS UNICOS',dtype=str)
b['k']=b.phone.map(key); b['aucb']=pd.to_numeric(b.auc,errors='coerce').fillna(0)
ambk=b.groupby('k').document.nunique(); ambk=set(ambk[ambk>1].index)
b=b.assign(sim=(b.cliente_nomos=='SIM').astype(int)).sort_values(['sim','aucb'],ascending=False).drop_duplicates('k')
MAP={'ALOCAÇÃO':'ALTA RENDA','ALOCAÇÃO LONDON':'LONDON','B2C PRIVATE':'PRIVATE','B2C TRADER':'B2B WOLF','B2B TRADER':'B2B FGG'}
b['area']=b.area_negocio.replace(MAP).fillna('SEM SUB_AREA')
nfmask=d.Sub_area=='NÃO_ENCONTRADO'
amb=int(d[nfmask].k.isin(ambk).sum() and d[nfmask & d.k.isin(ambk) & d.k.isin(b.k)].shape[0])
new=d[nfmask][['contact','k']].merge(b[['k','area','aucb','cliente_nomos']],on='k',how='inner')
print('novos',len(new),new.cliente_nomos.value_counts().to_dict(),'ambíguos na apoio',amb)
old=d[~nfmask].copy()
old['Sub_area']=old.Sub_area.where(~old.Sub_area.str.startswith('B2B'),'B2B')
new['area']=new.area.where(~new.area.str.startswith('B2B'),'B2B')
g1=old.groupby('Sub_area').agg(u1=('contact','size'),a1=('auc','sum'))
g2=new.groupby('area').agg(u2=('contact','size'),a2=('aucb','sum'))
g=g1.join(g2,how='outer').fillna(0)
g.index.name='area'
nf_left=int(nfmask.sum()-len(new))
rows=[{'area':a,'users':int(r.u1+r.u2),'auc':round(float(r.a1+r.a2),2),'u2':int(r.u2),'a2':round(float(r.a2),2)} for a,r in g.iterrows()]
rows.append({'area':'NÃO_ENCONTRADO','users':nf_left,'auc':0,'u2':0,'a2':0})
ident=len(old)+len(new)
kpi={'rows':int(len(df)),'users':int(len(d)),'dups':int(len(df)-len(d)),'ident':ident,'new':int(len(new)),'newSim':int((new.cliente_nomos=='SIM').sum()),'old':int(len(old)),'nf':nf_left,'nf0':int(nfmask.sum()),'auc':round(float(old.auc.sum()+new.aucb.sum()),2),'aucNew':round(float(new.aucb.sum()),2),'amb':amb}
print(kpi); print(sorted(rows,key=lambda r:-r['users'])[:6])
html=open('tpl.html').read().replace('__DATA__',json.dumps({'rows':rows,'kpi':kpi},ensure_ascii=False))
open('tradenews.html','w').write(html)
