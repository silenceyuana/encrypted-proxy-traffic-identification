from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

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
    # Keep the submission body compact: detailed audit material is retained in the repository appendix/results files.
    cut_start = body.find(BS+'section{Extended Results and Resource Costs}')
    cut_end = body.find(BS+'section{Code and Data Availability}')
    if cut_start >= 0 and cut_end > cut_start:
        discussion = (BS+'section{Discussion}\n'
          'The primary comparison uses Random Forest, RBF SVM, and KNN. Logistic Regression, HistGradientBoosting, and XGBoost are supplementary baselines; XGBoost is also retained in the JA4Tor headline comparison. The three primary models define the consistent MineShark tables.\n\n'
          'The evaluation regimes answer different deployment questions. Fixed-split Evaluation measures compatibility with the released JA4Tor files. Repeated Internal Evaluation measures sensitivity to resampling within the public training file. MineShark source-capture separation tests unseen capture files, while the NBMiner-to-XMRig experiment changes workload while retaining the broad task and labels. These estimates are complementary and must not be averaged.\n\n'
          'RF reaches 92.12% and XGBoost 92.08% on the JA4Tor 20,000/5,000 split. Repeated 16,000/4,000 evaluation yields 87.47% +/- 0.39% and 87.97% +/- 0.44%, respectively. The difference reflects both training size and test source. Because the public CSV files lack complete row-to-PCAP provenance, these results do not establish capture-disjointness or cross-node generalization.\n\n'
          'MineShark assigns complete captures before balancing. The current evaluation contains 4,743 training and 1,719 test windows, with 573 per class; SVM reaches 97.27%. The historical 2,220-window summary belongs to an earlier sampling version. Capture separation reduces direct leakage but does not guarantee independence when captures share hosts, pools, software, or collection periods.\n\n'
          'Training on NBMiner and testing on XMRig reduces SVM accuracy from 97.27% to 46.66%, a loss of 50.61 percentage points. RF and KNN also fall to 44.81% and 55.34%. The change may reflect scheduling, buffering, pool interaction, library defaults, or packet batching. Deployed detectors should declare their operating domain, detect drift, retrain or recalibrate after domain change, and allow an unknown or reject output.\n\n'
          'The evidence is bounded by label coverage and external validity. Neither source provides a complete verified Shadowsocks, VLESS, Trojan, and ordinary-HTTPS taxonomy. JA4Tor NonTor is not ordinary-HTTPS ground truth, and JA4Tor capture provenance is incomplete. CIC-Darknet2020 and ISCXVPN2016 remain pending because authorized data files were unavailable. Any future validation must preserve source labels, record hashes, verify capture grouping, and fit preprocessing on the source training partition only.\n\n'
          'For monitoring points and edge nodes, reports should include the training domain, capture or run grouping, class supports, uncertainty under repeated splits, and a drift response. Calibration and abstention should be evaluated before unfamiliar workloads are forced into known classes. The evidence supports interpretable baselines and a reproducible measurement protocol, not universal protocol recognition.\n\n'
          +BS+'section{Conclusion}\n'
          'This study separates fixed-file compatibility, repeated internal resampling, source-capture separation, and workload transfer for encrypted proxy traffic classification. The reported scores support domain declarations, retraining or recalibration, and unknown-class handling in deployed detectors. They do not establish a complete four-class benchmark or JA4Tor capture-disjointness, and no external dataset score is claimed.\n\n'
          +BS+'appendix\n'+BS+'section{Audit Details}\n'
          'Candidate-window counts, selected supports, capture partitions, hashes, model parameters, predictions, per-class metrics, confusion matrices, timing measurements, and serialized model sizes remain in the repository results/extended directory. They are supporting audit material and do not redefine the primary tables.\n\n')
        body = body[:cut_start] + discussion + body[cut_end:]
    doc=Document(); sec=doc.sections[0]; sec.top_margin=Inches(.8); sec.bottom_margin=Inches(.8); sec.left_margin=Inches(.85); sec.right_margin=Inches(.85)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run('Evaluating Machine Learning-Based Encrypted Traffic Classification Under Capture-Disjoint and Workload-Shift Conditions'),18,True)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(p.add_run('Zhang Xiaoyuan | Independent Researcher | silenceyuan2018@gmail.com | ORCID 0009-0006-6147-9256'),10)
    head(doc,'Abstract',1)
    para(doc,'Encrypted proxies conceal application payloads, but packet length, timing, and direction remain observable. Existing evaluations often combine random row splits, fixed test files, capture-disjoint results, and workload-transfer results, making leakage and workload dependence difficult to assess. This study establishes a reproducible network-monitoring baseline and separates these conditions explicitly. JA4Tor Fixed-split Evaluation uses 20,000 public training flows and 5,000 fixed test flows; Random Forest reaches 92.12% accuracy and XGBoost 92.08%. Repeated Internal Evaluation resamples the public training file into 16,000 training and 4,000 internal test flows for ten runs, yielding 87.47% ± 0.39% for Random Forest and 87.97% ± 0.44% for XGBoost. MineShark uses 4,743 training windows and 1,719 test windows, with 573 per class. SVM reaches 97.27% under the current source-capture-disjoint split, but falls to 46.66% when training on NBMiner and testing on XMRig, a loss of 50.61 percentage points. The results show why deployed detectors should state their training domain, retrain or recalibrate after workload changes, and support an unknown or reject output. JA4Tor lacks complete capture provenance, and no external score is reported for CIC-Darknet2020 or ISCXVPN2016 because the required data files were unavailable. Neither source provides complete labels for a Shadowsocks, VLESS, Trojan, and ordinary-HTTPS four-class benchmark.')
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
    para(doc,'Model roles are defined explicitly. Random Forest, RBF SVM, and KNN are the primary comparison models used in the consistent three-model tables. Logistic Regression, HistGradientBoosting, and XGBoost are supplementary baselines reported in the extended results; XGBoost is additionally included in the JA4Tor headline comparison.')
    para(doc,'The manuscript uses two exact names throughout. Fixed-split Evaluation means training on the complete public JA4Tor train.csv file with 20,000 flows and testing on the separate fixed test.csv file with 5,000 flows. Repeated Internal Evaluation means re-dividing the public train.csv file into 16,000 training flows and 4,000 internal test flows for ten seeds. The protocols share feature definitions, imputation, standardization, and model settings, but they do not share the same training size or test source.')
    head(doc,'Tables and Figures',1)
    para(doc,'Tables 1–4 report the label scope, file-level JA4Tor comparison, source-capture-disjoint MineShark result, and workload-shift result. Each table is tied to one evaluation condition so that denominators and model roles remain clear.')
    para(doc,'Table 1. Dataset labels and evaluation scope.')
    add_table(doc,['Source','Observed labels','Samples and source','Difference from target four-class task'],[
        ['JA4Tor','NonTor, Tor, Tor-SS, Tor-Trojan, Tor-VMess','20,000 training flows; 5,000 test flows; 5,024 test-cross flows','No VLESS; NonTor is not verified ordinary HTTPS; proxy payload labels are Tor-based'],
        ['MineShark','ShadowsocksR, Trojan, VMess','208 original capture files; 12,401 extracted 60-second windows','ShadowsocksR is not identical to Shadowsocks; no VLESS or ordinary HTTPS']])
    para(doc,'Table 2 reports the JA4Tor file-level comparison; the fixed-file and repeated-internal protocols remain separate because their training sizes and test sources differ.')
    para(doc,'Table 2. JA4Tor results on the two published test files (percent).')
    add_table(doc,['Test file','Model','Accuracy','Macro recall','Macro F1'],[
        ['test.csv','Random Forest','92.12','92.12','92.27'],['test.csv','SVM RBF','89.72','89.72','89.90'],['test.csv','KNN k=7','88.24','88.24','88.21'],['test-cross.csv','Random Forest','87.54','87.69','87.33'],['test-cross.csv','SVM RBF','76.73','76.99','74.38'],['test-cross.csv','KNN k=7','79.40','79.58','78.23']])
    para(doc,'Table 3 reports the MineShark result after complete capture files are assigned before window sampling, with totals that make the denominator explicit.')
    para(doc,'Table 3. MineShark source-capture-disjoint classification results (percent).')
    add_table(doc,['Model','Training windows','Test windows','Accuracy','Macro recall','Macro F1'],[
        ['Random Forest','4,743','1,719','94.30','94.30','94.30'],['SVM RBF','4,743','1,719','97.27','97.27','97.27'],['KNN k=7','4,743','1,719','92.44','92.44','92.43']])
    para(doc,'Table 4 quantifies the deployment penalty when training uses NBMiner and testing uses XMRig; labels remain fixed, isolating workload shift.')
    para(doc,'Table 4. NBMiner-to-XMRig workload-shift results (percent).')
    add_table(doc,['Model','Training windows','Test windows','Accuracy','Macro recall','Macro F1'],[
        ['Random Forest','3,702','1,899','44.81','44.81','46.08'],['SVM RBF','3,702','1,899','46.66','46.66','42.87'],['KNN k=7','3,702','1,899','55.34','55.34','54.55']])
    para(doc,'The tables preserve the complete editable data from the Chinese source document. The fixed JA4Tor table, the MineShark 1,719-window table, and the workload-shift table are separate experiments and must not be merged into one leaderboard. The historical 2,220-support summary is discussed in the text because it belongs to an earlier experiment version and has no matching current capture-split table.')
    head(doc,'Figures',1)
    para(doc,'The figures provide a visual audit of the protocol and its implications: the processing order, the JA4Tor test-file comparison, the MineShark workload-shift penalty, and the features most used by the Random Forest. Each figure is interpreted as evidence for a defined evaluation question rather than as an isolated performance illustration.')
    figures=[
        (ROOT/'results/figures/methodology.png','Figure 1. Data processing and classifier evaluation pipeline.'),
        (ROOT/'results/ja4tor/accuracy_recall.png','Figure 2. JA4Tor accuracy and macro recall.'),
        (ROOT/'results/mineshark/workload_shift_comparison.png','Figure 3. MineShark in-distribution and workload-shift performance.'),
        (ROOT/'results/ja4tor/feature_importance.png','Figure 4. Random Forest feature-importance ranking.'),
    ]
    figure_explanations=[
        'Figure 1 shows the ordered path from public artifacts and label checks to feature extraction, train-only preprocessing, and evaluation.',
        'Figure 2 compares accuracy and macro recall across the two JA4Tor test files, making file-level ranking changes visible.',
        'Figure 3 quantifies the performance penalty when the mining workload changes from NBMiner to XMRig.',
        'Figure 4 ranks the observable packet-length, direction, and timing statistics used by the JA4Tor Random Forest; the ranking is associative rather than causal.'
    ]
    for idx,(image_path, caption) in enumerate(figures):
        para(doc, figure_explanations[idx])
        if image_path.exists():
            pic=doc.add_paragraph(); pic.alignment=WD_ALIGN_PARAGRAPH.CENTER; pic.add_run().add_picture(str(image_path), width=Inches(6.2))
            cap=doc.add_paragraph(); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER; font(cap.add_run(caption),9)
    para(doc,'High-resolution editable figure files are supplied separately in submission_assets/figures.')
    head(doc,'Declarations',1)
    head(doc,'Competing interests',2); para(doc,'The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.')
    head(doc,'Funding',2); para(doc,'This research received no external funding.')
    head(doc,'Data availability',2); para(doc,'Data and code available at https://github.com/silenceyuana/encrypted-proxy-traffic-identification. JA4Tor is available at https://github.com/das-lab/JA4Tor and MineShark at https://zenodo.org/records/13624058. Raw third-party archives are not redistributed. CIC-Darknet2020 and ISCXVPN2016 were not available and no external score is claimed.')
    head(doc,'Author contributions (CRediT)',2); para(doc,'Zhang Xiaoyuan: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review and editing, Visualization, Project administration.')
    head(doc,'Generative AI use',2); para(doc,'OpenAI Codex assisted with manuscript drafting, language polishing, experiment-code development, figure creation, and layout checking. Training, evaluation, and feature-importance values were computed by local Python programs. The author is responsible for all final text, references, code, and results.')
    head(doc,'References',1)
    refs=['[1] Draper-Gil G, Lashkari A H, Mamun M, et al. Characterization of encrypted and VPN traffic using time-related features. Proc. ICISSP, 2016, pp. 407-414. Available: https://www.unb.ca/cic/datasets/vpn.html','[2] Xue D, Kallitsis M, Houmansadr A, et al. Fingerprinting obfuscated proxy traffic with encapsulated TLS handshakes. Proc. 33rd USENIX Security Symposium, 2024. Available: https://www.usenix.org/conference/usenixsecurity24/presentation/xue-fingerprinting','[3] Zhou C, Huang C, Zhang Q, et al. NESTTOR: Detecting Tor-over-Proxy traffic with factorized decisions. IEEE Transactions on Network and Service Management, 2026. DOI: 10.1109/TNSM.2026.3743261.','[4] Xi S, Fu T, Bu K, et al. MineShark: Cryptomining traffic detection at scale. Proc. NDSS, 2025. DOI: 10.14722/ndss.2025.230402.','[5] Breiman L. Random forests. Machine Learning, 45, 2001, pp. 5-32. DOI: 10.1023/A:1010933404324.','[6] Cortes C, Vapnik V. Support-vector networks. Machine Learning, 20, 1995, pp. 273-297. DOI: 10.1007/BF00994018.','[7] Cover T, Hart P. Nearest neighbor pattern classification. IEEE Transactions on Information Theory, 13(1), 1967, pp. 21-27. DOI: 10.1109/TIT.1967.1053964.','[8] Pedregosa F, Varoquaux G, Gramfort A, et al. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2011, pp. 2825-2830. Available: https://jmlr.org/papers/v12/pedregosa11a.html','[9] Panchenko A, Lanze F, Zinnen A, et al. Website fingerprinting at Internet scale. Proc. NDSS, 2016. DOI: 10.14722/ndss.2016.23477.','[10] Hayes J, Danezis G. k-fingerprinting: A robust scalable approach to website fingerprinting. Proc. USENIX Security, 2018, pp. 1187-1203.','[11] Miller B, Huang L, Dyer K P, et al. I know why you went to the clinic: Risks and realization of HTTPS traffic analysis. Proceedings on Privacy Enhancing Technologies, 2014(1), pp. 143-163. DOI: 10.1515/popets-2014-0012.','[12] AlSabah M, Briffa J A, et al. A statistical analysis of Tor traffic for website fingerprinting. Proc. ACM CCS, 2016. DOI: 10.1145/2976749.2989057.','[13] Anderson B, McGrew D. Machine learning for encrypted malware traffic classification. IEEE MILCOM, 2016, pp. 1-6. DOI: 10.1109/MILCOM.2016.7795421.','[14] Anderson B, McGrew D. Identifying encrypted malware traffic with contextual flow data. Proc. ACM Workshop on Artificial Intelligence and Security, 2016, pp. 35-46. DOI: 10.1145/2996758.2996760.','[15] JA3: SSL/TLS Client Fingerprinting. Salesforce Engineering, 2017. Peer-reviewed context: Anderson and McGrew [13]-[14]; this web description is not used as the sole evidence.']
    for ref in refs: para(doc,ref)
    doc.save(OUT)

if __name__=='__main__': main()
