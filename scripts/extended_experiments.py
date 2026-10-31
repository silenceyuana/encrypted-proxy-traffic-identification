from __future__ import annotations
import json, time, pickle, warnings
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT=Path(__file__).resolve().parents[1]; J=ROOT/'data/raw/ja4tor'; JO=ROOT/'results/ja4tor'; M=ROOT/'results/mineshark'; MO=ROOT/'results/extended'; MO.mkdir(parents=True,exist_ok=True)
JLAB={0:'NonTor',1:'Tor',2:'Tor-SS',3:'Tor-Trojan',4:'Tor-VMess'}
JFEAT=['Total Fwd Packets','Total Bwd Packets','Total Length of Fwd Packets','Total Length of Bwd Packets','Fwd Packet Length Max','Fwd Packet Length Min','Fwd Packet Length Mean','Fwd Packet Length Std','Bwd Packet Length Max','Bwd Packet Length Min','Bwd Packet Length Mean','Bwd Packet Length Std','Packet Length Variance','Down/Up Ratio','Average Packet Size','Flow Duration','Flow Bytes/s','Flow Packets/s','Flow IAT Mean','Flow IAT Std','Flow IAT Max','Flow IAT Min','Fwd IAT Mean','Fwd IAT Std','Fwd IAT Max','Fwd IAT Min','Bwd IAT Mean','Bwd IAT Std','Bwd IAT Max','Bwd IAT Min']
MFEAT=['packet_count','total_bytes','duration_s','packet_rate','frame_mean','frame_std','frame_median','frame_p90','frame_min','frame_max','iat_mean_ms','iat_std_ms','iat_median_ms','iat_p90_ms','iat_max_ms','up_count_ratio','down_up_bytes_ratio','up_frame_mean','down_frame_mean','direction_switch_rate']

def pipe(model, scale=False): return make_pipeline(SimpleImputer(strategy='median'), *( [StandardScaler()] if scale else []), model)
def models(seed): return {'RF':pipe(RandomForestClassifier(n_estimators=200,max_features='sqrt',min_samples_leaf=2,random_state=seed,n_jobs=-1)), 'SVM':pipe(SVC(C=10,gamma='scale'),True), 'KNN':pipe(KNeighborsClassifier(n_neighbors=7),True), 'LogReg':pipe(LogisticRegression(max_iter=2000,C=1),True), 'HistGB':pipe(HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=31,random_state=seed))}

def matrix(df, feats):
 x=df[feats].apply(pd.to_numeric,errors='coerce').to_numpy(float); x[~np.isfinite(x)]=np.nan; return x

def ja4tor():
 train=pd.read_csv(J/'train.csv',low_memory=False); test=pd.read_csv(J/'test.csv',low_memory=False)
 y= train.traffic_type.to_numpy(); yt=test.traffic_type.to_numpy(); X=matrix(train,JFEAT); Xt=matrix(test,JFEAT)
 rows=[]; per=[]; cms=[]; timing=[]
 splitter=StratifiedShuffleSplit(n_splits=10,test_size=.2,random_state=42)
 for rep,(tr,va) in enumerate(splitter.split(X,y),1):
  for name,base in models(rep).items():
   t=time.perf_counter(); mod=clone(base); mod.fit(X[tr],y[tr]); fit=time.perf_counter()-t
   t=time.perf_counter(); pred=mod.predict(X[va]); predtime=time.perf_counter()-t
   repd=classification_report(y[va],pred,labels=list(JLAB),target_names=list(JLAB.values()),output_dict=True,zero_division=0)
   rows.append({'dataset':'JA4Tor_internal20','repeat':rep,'model':name,'accuracy':accuracy_score(y[va],pred),'macro_recall':recall_score(y[va],pred,average='macro'),'macro_f1':repd['macro avg']['f1-score'],'fit_s':fit,'predict_s':predtime,'model_bytes':len(pickle.dumps(mod))})
  # official test only once per seed/model below
 for name,base in models(42).items():
  mod=clone(base); t=time.perf_counter(); mod.fit(X,y); fit=time.perf_counter()-t; t=time.perf_counter(); pred=mod.predict(Xt); pt=time.perf_counter()-t
  repd=classification_report(yt,pred,labels=list(JLAB),target_names=list(JLAB.values()),output_dict=True,zero_division=0)
  for lab in JLAB.values(): per.append({'dataset':'JA4Tor_test','model':name,'class':lab,'precision':repd[lab]['precision'],'recall':repd[lab]['recall'],'f1':repd[lab]['f1-score'],'support':repd[lab]['support']})
  cm=confusion_matrix(yt,pred,labels=list(JLAB)); cms.append(pd.DataFrame(cm,index=JLAB.values(),columns=JLAB.values()).assign(model=name))
  timing.append({'dataset':'JA4Tor_test','model':name,'fit_s':fit,'predict_s':pt,'model_bytes':len(pickle.dumps(mod)),'accuracy':accuracy_score(yt,pred),'macro_recall':recall_score(yt,pred,average='macro'),'macro_f1':repd['macro avg']['f1-score']})
 # permutation RF
 rf=clone(models(42)['RF']); rf.fit(X,y); pi=permutation_importance(rf,Xt,yt,n_repeats=5,random_state=42,n_jobs=1,scoring='accuracy'); pd.DataFrame({'feature':JFEAT,'importance_mean':pi.importances_mean,'importance_std':pi.importances_std}).sort_values('importance_mean',ascending=False).to_csv(MO/'ja4tor_permutation_importance.csv',index=False)
 pd.DataFrame(rows).to_csv(MO/'ja4tor_repeated_internal.csv',index=False); pd.DataFrame(per).to_csv(MO/'ja4tor_test_per_class.csv',index=False); pd.concat(cms).to_csv(MO/'ja4tor_test_confusions.csv'); pd.DataFrame(timing).to_csv(MO/'ja4tor_timing.csv',index=False)

def mineshark():
 df=pd.read_csv(M/'features.csv'); y=df.label.to_numpy(); X=matrix(df,MFEAT); labels=sorted(df.label.unique()); rows=[]; per=[]; cms=[]; timing=[]
 rng=np.random.default_rng(42)
 captures=df.capture.unique()
 for rep in range(1,11):
  trparts=[]; teparts=[]
  for lab in labels:
   caps=np.array(sorted(df.loc[df.label==lab,'capture'].unique())); rng=np.random.default_rng(1000+rep); rng.shuffle(caps); n=max(1,round(.3*len(caps))); tes=set(caps[:n]); trparts.append(df[(df.label==lab)&(~df.capture.isin(tes))]); teparts.append(df[(df.label==lab)&(df.capture.isin(tes))])
  ntr=min(len(x) for x in trparts); nte=min(len(x) for x in teparts); train=pd.concat([x.sample(ntr,random_state=rep) for x in trparts]); test=pd.concat([x.sample(nte,random_state=rep) for x in teparts]); Xt=matrix(test,MFEAT); yt=test.label.to_numpy(); Xtr=matrix(train,MFEAT); ytr=train.label.to_numpy()
  for name,base in models(rep).items():
   mod=clone(base); t=time.perf_counter(); mod.fit(Xtr,ytr); fit=time.perf_counter()-t; t=time.perf_counter(); pred=mod.predict(Xt); pt=time.perf_counter()-t; repd=classification_report(yt,pred,labels=labels,output_dict=True,zero_division=0)
   rows.append({'dataset':'MineShark_capture_disjoint','repeat':rep,'model':name,'n_train':len(train),'n_test':len(test),'accuracy':accuracy_score(yt,pred),'macro_recall':recall_score(yt,pred,average='macro'),'macro_f1':repd['macro avg']['f1-score'],'fit_s':fit,'predict_s':pt,'model_bytes':len(pickle.dumps(mod))})
   if rep==1:
    for lab in labels: per.append({'dataset':'MineShark_capture_disjoint','model':name,'class':lab,'precision':repd[lab]['precision'],'recall':repd[lab]['recall'],'f1':repd[lab]['f1-score'],'support':repd[lab]['support']})
    cms.append(pd.DataFrame(confusion_matrix(yt,pred,labels=labels),index=labels,columns=labels).assign(model=name))
 pd.DataFrame(rows).to_csv(MO/'mineshark_repeated.csv',index=False); pd.DataFrame(per).to_csv(MO/'mineshark_per_class.csv',index=False); pd.concat(cms).to_csv(MO/'mineshark_confusions.csv');
 # candidate window accounting
 pd.DataFrame([{'label':k,'candidate_windows':int(v)} for k,v in df.label.value_counts().items()]).to_csv(MO/'mineshark_candidate_windows.csv',index=False)

if __name__=='__main__': ja4tor(); mineshark(); json.dump({'repeats':10,'xgboost':'not run: package unavailable in environment','histgradientboosting':'included as native tree boosting comparator','ja4tor_features':JFEAT,'mineshark_features':MFEAT},open(MO/'manifest.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
