"""Measured six-model evaluations; no generated or synthetic observations."""
from pathlib import Path
import hashlib, json, pickle, platform, time, warnings
import numpy as np
import pandas as pd
import scipy, sklearn, xgboost
from scipy.stats import t as student_t
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from extended_experiments import JFEAT, MFEAT, JLAB, models, pipe, matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/audit_v2'
OUT.mkdir(parents=True,exist_ok=True)
SEEDS=list(range(42,52))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def estimators(seed, classes):
    result=models(seed)
    for model in result.values():
        params=model.get_params()
        model.set_params(**{k:1 for k in params if k.endswith('__n_jobs')})
    result['XGBoost']=pipe(XGBClassifier(n_estimators=150,max_depth=6,learning_rate=.1,subsample=.9,colsample_bytree=.9,objective='multi:softprob',num_class=classes,eval_metric='mlogloss',tree_method='hist',random_state=seed,n_jobs=1))
    return result

def split_capture(df, seed):
    rng=np.random.default_rng(seed); train=[]; test=[]; counts=[]; groups=[]
    for label in sorted(df.label.unique()):
        part=df[df.label==label]
        captures=np.array(sorted(part.capture.unique())); rng.shuffle(captures)
        held=set(captures[:max(1,round(.3*len(captures)))])
        a=part[~part.capture.isin(held)]; b=part[part.capture.isin(held)]
        train.append(a);test.append(b)
        counts.append(dict(seed=seed,label=label,train_captures=len(captures)-len(held),test_captures=len(held),candidate_train=len(a),candidate_test=len(b)))
        groups.extend(dict(seed=seed,label=label,capture=c,partition='test' if c in held else 'train') for c in captures)
    ntr=min(map(len,train)); nte=min(map(len,test))
    a=pd.concat([p.sample(ntr,random_state=seed) for p in train]);b=pd.concat([p.sample(nte,random_state=seed) for p in test])
    assert set(a.capture).isdisjoint(b.capture)
    for c in counts: c.update(selected_train=ntr,selected_test=nte,unused_train=c['candidate_train']-ntr,unused_test=c['candidate_test']-nte)
    return a,b,counts,groups

def split_workload(df,seed):
    a=df[df.capture.str.startswith('nbminer/')]; b=df[df.capture.str.startswith('xmrig/')]
    nt=a.label.value_counts().min(); ne=b.label.value_counts().min()
    a=pd.concat([p.sample(nt,random_state=seed) for _,p in a.groupby('label')]); b=pd.concat([p.sample(ne,random_state=seed) for _,p in b.groupby('label')])
    assert set(a.capture).isdisjoint(b.capture)
    return a,b

def evaluate(task, seed, train, test, features, target, names, permutation=False):
    folder=OUT/task/f'seed_{seed}';folder.mkdir(parents=True,exist_ok=True)
    X=matrix(train,features);Xt=matrix(test,features)
    enc=LabelEncoder().fit(list(names));y=enc.transform(train[target]);yt=enc.transform(test[target])
    for part,name in [(train,'train'),(test,'test')]:
        keys=[c for c in ['capture','window',target] if c in part]
        v=part[keys].copy();v.insert(0,'source_row',part.index.to_numpy());v.to_csv(folder/f'{name}_rows.csv',index=False)
    for name,model in estimators(seed,len(names)).items():
        dest=folder/name;dest.mkdir(exist_ok=True)
        if (dest/'metrics.json').exists():
            print('cached',task,seed,name,flush=True);continue
        began=time.perf_counter();model.fit(X,y);fit_s=time.perf_counter()-began
        model.predict(Xt[:min(32,len(Xt))])
        began=time.perf_counter();pred=model.predict(Xt);predict_s=time.perf_counter()-began
        report=classification_report(yt,pred,labels=range(len(enc.classes_)),target_names=enc.classes_,output_dict=True,zero_division=0)
        pd.DataFrame([dict(label=label,**report[label]) for label in enc.classes_]).to_csv(dest/'per_class.csv',index=False)
        pd.DataFrame(confusion_matrix(yt,pred,labels=range(len(enc.classes_))),index=enc.classes_,columns=enc.classes_).to_csv(dest/'confusion.csv')
        np.savez_compressed(dest/'predictions.npz',true=yt,predicted=pred,labels=enc.classes_,test_rows=test.index.to_numpy())
        values=dict(task=task,seed=seed,model=name,n_train=len(train),n_test=len(test),accuracy=accuracy_score(yt,pred),macro_precision=report['macro avg']['precision'],macro_recall=report['macro avg']['recall'],macro_f1=report['macro avg']['f1-score'],fit_s=fit_s,predict_s=predict_s,predict_us_per_sample=predict_s/len(test)*1e6,model_bytes=len(pickle.dumps(model,protocol=5)))
        (dest/'metrics.json').write_text(json.dumps(values,indent=2),encoding='utf-8')
        print(task,seed,name,round(values['accuracy'],4),round(fit_s,2),flush=True)
        if permutation and name=='RF':
            pi=permutation_importance(model,Xt,yt,n_repeats=5,random_state=seed,n_jobs=1,scoring='accuracy')
            pd.DataFrame(dict(feature=features,mean_decrease=pi.importances_mean,std_decrease=pi.importances_std)).sort_values('mean_decrease',ascending=False).to_csv(dest/'permutation_importance.csv',index=False)
            np.save(dest/'permutation_raw.npy',pi.importances)

def summarize():
    rows=[json.loads(p.read_text(encoding='utf-8')) for p in OUT.glob('*/*/*/metrics.json')]
    df=pd.DataFrame(rows);df.to_csv(OUT/'all_runs.csv',index=False)
    summaries=[]
    for (task,model),part in df.groupby(['task','model']):
        for metric in ['accuracy','macro_precision','macro_recall','macro_f1','fit_s','predict_s','predict_us_per_sample','model_bytes']:
            x=part[metric];n=len(x);mean=x.mean();sd=x.std(ddof=1) if n>1 else 0.;half=student_t.ppf(.975,n-1)*sd/np.sqrt(n) if n>1 else 0.
            summaries.append(dict(task=task,model=model,metric=metric,n=n,mean=mean,sd=sd,ci_low=mean-half,ci_high=mean+half))
    pd.DataFrame(summaries).to_csv(OUT/'summary.csv',index=False)

def main():
    jpath=ROOT/'data/raw/ja4tor'; mpath=ROOT/'results/mineshark/features.csv'
    jtrain=pd.read_csv(jpath/'train.csv',low_memory=False);jt=pd.read_csv(jpath/'test.csv',low_memory=False);jc=pd.read_csv(jpath/'test-cross.csv',low_memory=False)
    for d in [jtrain,jt,jc]: d['label']=d.traffic_type.map(JLAB)
    mine=pd.read_csv(mpath)
    manifest=dict(seeds=SEEDS,python=platform.python_version(),platform=platform.platform(),processor=platform.processor(),sklearn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,xgboost=xgboost.__version__,threads=1,serialization='pickle protocol 5, uncompressed fitted preprocessing and estimator',prediction_timing='one full-batch wall-clock predict after up to 32-row warmup; preprocessing included; feature extraction excluded',ci='Student t(9) 95% interval of mean across 10 repeats; overlapping resamples are dependent, so this is descriptive resampling uncertainty, not a population guarantee',inputs={str(p.relative_to(ROOT)):digest(p) for p in [jpath/'train.csv',jpath/'test.csv',jpath/'test-cross.csv',mpath]},ja4tor_features=JFEAT,mineshark_features=MFEAT)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    evaluate('J_fixed',42,jtrain,jt,JFEAT,'label',JLAB.values(),True)
    evaluate('J_second',42,jtrain,jc,JFEAT,'label',JLAB.values())
    a,b,counts,groups=split_capture(mine,42)
    pd.DataFrame(counts).to_csv(OUT/'window_accounting_seed42.csv',index=False)
    evaluate('M_fixed',42,a,b,MFEAT,'label',sorted(mine.label.unique()),True)
    countsall=[];groupsall=[]
    for seed in SEEDS:
        tr,va=next(StratifiedShuffleSplit(n_splits=1,test_size=.2,random_state=seed).split(jtrain,jtrain.label))
        evaluate('J_internal',seed,jtrain.iloc[tr],jtrain.iloc[va],JFEAT,'label',JLAB.values())
        a,b,counts,groups=split_capture(mine,seed);countsall.extend(counts);groupsall.extend(groups)
        evaluate('M_capture',seed,a,b,MFEAT,'label',sorted(mine.label.unique()))
        a,b=split_workload(mine,seed)
        evaluate('M_workload',seed,a,b,MFEAT,'label',sorted(mine.label.unique()))
        summarize()
    pd.DataFrame(countsall).to_csv(OUT/'window_accounting_repeated.csv',index=False)
    pd.DataFrame(groupsall).to_csv(OUT/'capture_partitions.csv',index=False)
    summarize()

if __name__=='__main__': main()
