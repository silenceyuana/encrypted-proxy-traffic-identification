from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'Cover_Letter_Computer_Communications.docx'
doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.9); sec.bottom_margin = Inches(0.9); sec.left_margin = Inches(1.0); sec.right_margin = Inches(1.0)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('Cover Letter'); r.bold = True; r.font.size = Pt(18)
texts = [
 'Dear Editors of Computer Communications,',
 'Please consider our manuscript, Evaluating Machine Learning-Based Encrypted Traffic Classification Under Capture-Disjoint and Workload-Shift Conditions, for publication in Computer Communications. The manuscript presents an auditable machine-learning baseline for encrypted traffic classification using packet-length, timing, and direction statistics. It focuses on evidence quality and distribution change rather than claiming a universal protocol detector.',
 'The study separates JA4Tor Fixed-split Evaluation from Repeated Internal Evaluation and explains why their Random Forest and XGBoost accuracies differ. It provides a source-capture-disjoint MineShark evaluation with explicit capture counts and quantifies the drop under NBMiner-to-XMRig workload shift. It preserves source labels and documents the absence of verified VLESS and ordinary-HTTPS labels and the lack of complete JA4Tor capture provenance.',
 'The manuscript addresses encrypted-network measurement, reproducible machine-learning evaluation, leakage control, and cross-domain robustness. The implementation records input hashes, run manifests, capture split files, feature definitions, predictions, confusion matrices, and repeated-run uncertainty.',
 'Data and code available at https://github.com/silenceyuana/encrypted-proxy-traffic-identification. JA4Tor is available at https://github.com/das-lab/JA4Tor and MineShark at https://zenodo.org/records/13624058. CIC-Darknet2020 and ISCXVPN2016 were not available in the current study; no external accuracy is claimed.',
 'The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper. This research received no external funding. OpenAI Codex assisted with manuscript drafting, language polishing, experiment-code development, figure creation, and layout checking; all reported experimental values were computed by local Python programs and the author is responsible for the final manuscript.',
 'This submission is an expanded and corrected version of an earlier internal draft. The revision reconciles the MineShark 1,719-versus-2,220 sample discrepancy, separates the two JA4Tor evaluation regimes, removes the unsupported JA4Tor capture-disjoint claim, adds peer-reviewed related work, and makes the external-validation status explicit. The manuscript is not under consideration elsewhere.',
 'Thank you for considering this submission.',
 'Sincerely, Zhang Xiaoyuan; Independent Researcher; silenceyuan2018@gmail.com; ORCID 0009-0006-6147-9256'
]
for text in texts:
    p = doc.add_paragraph(text); p.paragraph_format.space_after = Pt(8); p.paragraph_format.line_spacing = 1.15
    for run in p.runs: run.font.name = 'Arial'; run.font.size = Pt(10.5)
doc.save(out)
print(out)
