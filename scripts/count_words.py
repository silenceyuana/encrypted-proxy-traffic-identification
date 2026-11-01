from docx import Document
import re
for f in ['基于机器学习的加密代理流量识别_修订版.docx','Evaluating_Machine_Learning_Encrypted_Traffic_Classification_English_Main_Manuscript.docx']:
    d=Document(f)
    s=' '.join(p.text for p in d.paragraphs)
    print(f, 'chars', len(s), 'words', len(re.findall('[A-Za-z0-9]+', s)), 'paras', len(d.paragraphs))
