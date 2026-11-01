from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'latex_ieee/encrypted_proxy_traffic_ieee.tex'
OUT=ROOT/'Evaluating_Machine_Learning_Encrypted_Traffic_Classification_English_Main_Manuscript.docx'
BS=chr(92)

def font(run,size=10.5,bold=False):
    run.font.name='Arial'; run.font.size=Pt(size); run.bold=bold
    rpr=run._element.get_or_add_rPr(); fs=rpr.rFonts
    if fs is None: fs=OxmlElement('w:rFonts'); rpr.insert(0,fs)
    for k in ('ascii','hAnsi','cs'): fs.set(qn('w:'+k),'Arial')

def clean(s):
    while BS+'cite{' in s or BS+'ref{' in s:
        for tag in ('cite','ref'):
            start=s.find(BS+tag+'{')
            if start>=0:
                end=s.find('}',start)
                if end>=0: s=s[:start]+s[end+1:]
    for tag in ('texttt','emph','textbf','url'):
        s=s.replace(BS+tag+'{','').replace('}','')
    s=s.replace(BS+'%','%').replace(BS+'_','_').replace('~',' ').replace('$','')
    return ' '.join(s.split()).strip()

def para(doc,text):
    p=doc.add_paragraph(); p.paragraph_format.line_spacing=1.15; p.paragraph_format.space_after=Pt(6); font(p.add_run(text)); return p

def head(doc,text,level=1):
    p=doc.add_heading(clean(text),level=level); p.paragraph_format.keep_with_next=True
    for r in p.runs: font(r,13 if level==1 else 11,True)

def add_table(doc, headers, rows):
    t=doc.add_table(rows=1, cols=len(headers)); t.style='Table Grid'
    for i,h in enumerate(headers):
        t.rows[0].cells[i].text=str(h)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row): cells[i].text=str(v)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(0)
                for r in p.runs: font(r,8.5,row is t.rows[0])
    return t

def main():
    raw=TEX.read_text(encoding='utf-8'); body=raw.split(BS+'begin{document}',1)[1].split(BS+'end{document}',1)[0]
    doc=Document(); sec=doc.sections[0]; sec.top_margin=Inches(.8); sec.bottom_margin=Inches(.8); sec.left_margin=Inches(.85); sec.right_margin=Inches(.85)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run('Evaluating Machine Learning-Based Encrypted Traffic Classification Under Capture-Disjoint and Workload-Shift Conditions'),18,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run('Zhang Xiaoyuan | Independent Researcher | silenceyuan2018@gmail.com | ORCID 0009-0006-6147-9256'),10)
    buf=[]; env=False
    for line in body.splitlines():
        st=line.strip()
        if not st:
            if buf: para(doc,clean(' '.join(buf))); buf=[]
            continue
        if st.startswith(BS+'begin{'): env=True; continue
        if st.startswith(BS+'end{'): env=False; continue
        if env: continue
        if st.startswith(BS+'section{'):
            if buf: para(doc,clean(' '.join(buf))); buf=[]
            head(doc,st[len(BS+'section{'):-1],1); continue
        if st.startswith(BS+'subsection{'):
            if buf: para(doc,clean(' '.join(buf))); buf=[]
            head(doc,st[len(BS+'subsection{'):-1],2); continue
        if st.startswith(BS) or st.startswith('%'): continue
        buf.append(st)
    if buf: para(doc,clean(' '.join(buf)))
    head(doc,'Evaluation protocol names',2)
    para(doc,'The manuscript uses two exact names throughout. Fixed-split Evaluation means training on the complete public JA4Tor train.csv file with 20,000 flows and testing on the separate fixed test.csv file with 5,000 flows. Repeated Internal Evaluation means re-dividing the public train.csv file into 16,000 training flows and 4,000 internal test flows for ten seeds. The protocols share feature definitions, imputation, standardization, and model settings, but they do not share the same training size or test source.')
    head(doc,'Tables and Figures',1)
    para(doc,'Table 1. Dataset labels and evaluation scope.')
    add_table(doc,['Source','Observed labels','Samples and source','Difference from target four-class task'],[
        ['JA4Tor','NonTor, Tor, Tor-SS, Tor-Trojan, Tor-VMess','20,000 training flows; 5,000 test flows; 5,024 test-cross flows','No VLESS; NonTor is not verified ordinary HTTPS; proxy payload labels are Tor-based'],
        ['MineShark','ShadowsocksR, Trojan, VMess','208 original capture files; 12,401 extracted 60-second windows','ShadowsocksR is not identical to Shadowsocks; no VLESS or ordinary HTTPS']])
    para(doc,'Table 2. JA4Tor results on the two published test files (percent).')
    add_table(doc,['Test file','Model','Accuracy','Macro recall','Macro F1'],[
        ['test.csv','Random Forest','92.12','92.12','92.27'],['test.csv','SVM RBF','89.72','89.72','89.90'],['test.csv','KNN k=7','88.24','88.24','88.21'],['test-cross.csv','Random Forest','87.54','87.69','87.33'],['test-cross.csv','SVM RBF','76.73','76.99','74.38'],['test-cross.csv','KNN k=7','79.40','79.58','78.23']])
    para(doc,'Table 3. MineShark source-capture-disjoint classification results (percent).')
    add_table(doc,['Model','Training windows','Test windows','Accuracy','Macro recall','Macro F1'],[
        ['Random Forest','4,743','1,719','94.30','94.30','94.30'],['SVM RBF','4,743','1,719','97.27','97.27','97.27'],['KNN k=7','4,743','1,719','92.44','92.44','92.43']])
    para(doc,'Table 4. NBMiner-to-XMRig workload-shift results (percent).')
    add_table(doc,['Model','Training windows','Test windows','Accuracy','Macro recall','Macro F1'],[
        ['Random Forest','3,702','1,899','44.81','44.81','46.08'],['SVM RBF','3,702','1,899','46.66','46.66','42.87'],['KNN k=7','3,702','1,899','55.34','55.34','54.55']])
    para(doc,'The tables preserve the complete editable data from the Chinese source document. The fixed JA4Tor table, the MineShark 1,719-window table, and the workload-shift table are separate experiments and must not be merged into one leaderboard. The historical 2,220-support summary is discussed in the text because it belongs to an earlier experiment version and has no matching current capture-split table.')
    head(doc,'Figures',1)
    figures=[
        (ROOT/'results/figures/methodology.png','Figure 1. Data processing and classifier evaluation pipeline.'),
        (ROOT/'results/ja4tor/accuracy_recall.png','Figure 2. JA4Tor accuracy and macro recall.'),
        (ROOT/'results/mineshark/workload_shift_comparison.png','Figure 3. MineShark in-distribution and workload-shift performance.'),
        (ROOT/'results/ja4tor/feature_importance.png','Figure 4. Random Forest feature-importance ranking.'),
    ]
    for image_path, caption in figures:
        if image_path.exists():
            pic=doc.add_paragraph(); pic.alignment=WD_ALIGN_PARAGRAPH.CENTER; pic.add_run().add_picture(str(image_path), width=Inches(6.2))
            cap=doc.add_paragraph(); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(cap.add_run(caption),9)
    para(doc,'Figure 1. Data processing and classifier evaluation pipeline. Figure 2. JA4Tor accuracy and macro recall. Figure 3. MineShark workload-shift performance. Figure 4. Random Forest feature-importance ranking. High-resolution editable figure files are supplied separately in submission_assets/figures.')
    head(doc,'Declarations',1)
    head(doc,'Competing interests',2); para(doc,'The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.')
    head(doc,'Funding',2); para(doc,'This research received no external funding.')
    head(doc,'Data availability',2); para(doc,'Data and code available at https://github.com/silenceyuana/encrypted-proxy-traffic-identification. JA4Tor is available at https://github.com/das-lab/JA4Tor and MineShark at https://zenodo.org/records/13624058. Raw third-party archives are not redistributed. CIC-Darknet2020 and ISCXVPN2016 were not available and no external score is claimed.')
    head(doc,'Author contributions (CRediT)',2); para(doc,'Zhang Xiaoyuan: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review and editing, Visualization, Project administration.')
    head(doc,'Generative AI use',2); para(doc,'OpenAI Codex assisted with manuscript drafting, language polishing, experiment-code development, figure creation, and layout checking. Training, evaluation, and feature-importance values were computed by local Python programs. The author is responsible for all final text, references, code, and results.')
    head(doc,'References',1)
    refs=['[1] Draper-Gil et al., Characterization of encrypted and VPN traffic using time-related features, ICISSP, 2016.','[2] Panchenko et al., Website fingerprinting at Internet scale, NDSS, 2016.','[3] Hayes and Danezis, k-fingerprinting: A robust scalable approach to website fingerprinting, USENIX Security, 2018.','[4] Miller et al., I know why you went to the clinic: Risks and realization of HTTPS traffic analysis, PETS, 2014.','[5] AlSabah et al., A statistical analysis of Tor traffic for website fingerprinting, ACM CCS, 2016.','[6] Anderson and McGrew, Machine learning for encrypted malware traffic classification, IEEE MILCOM, 2016.','[7] Anderson and McGrew, Identifying encrypted malware traffic with contextual flow data, AISec, 2016.','[8] Xue et al., Fingerprinting obfuscated proxy traffic with encapsulated TLS handshakes, USENIX Security, 2024.','[9] Zhou et al., NESTTOR: Detecting Tor-over-Proxy traffic with factorized decisions, IEEE TNSM, 2026.','[10] Xi et al., MineShark: Cryptomining traffic detection at scale, NDSS, 2025.','[11] Breiman, Random forests, Machine Learning, 2001.','[12] Cortes and Vapnik, Support-vector networks, Machine Learning, 1995.','[13] Cover and Hart, Nearest neighbor pattern classification, IEEE TIT, 1967.','[14] Pedregosa et al., Scikit-learn: Machine learning in Python, JMLR, 2011.']
    for ref in refs: para(doc,ref)
    doc.save(OUT)

if __name__=='__main__': main()
