from pathlib import Path
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / '基于机器学习的加密代理流量识别_修订版.docx'
out = ROOT / '基于机器学习的加密代理流量识别_修订版.pdf'
pdfmetrics.registerFont(TTFont('NotoSC', 'C:/Windows/Fonts/NotoSansSC-VF.ttf'))
docx = Document(src)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CNBody', parent=styles['BodyText'], fontName='NotoSC', fontSize=9.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=5, firstLineIndent=18))
styles.add(ParagraphStyle(name='CNHead', parent=styles['Heading1'], fontName='NotoSC', fontSize=13, leading=18, spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name='CNTitle', parent=styles['Title'], fontName='NotoSC', fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name='CNCapt', parent=styles['BodyText'], fontName='NotoSC', fontSize=8.5, leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4))
story=[]
for p in docx.paragraphs:
    t=p.text.strip()
    if not t: continue
    if p.style.name == 'Title': story.append(Paragraph(t, styles['CNTitle']))
    elif p.style.name.startswith('Heading'): story.append(Paragraph(t, styles['CNHead']))
    else: story.append(Paragraph(t.replace('&','&amp;'), styles['CNBody']))
    story.append(Spacer(1, 2))
for tbl in docx.tables:
    data=[[c.text for c in row.cells] for row in tbl.rows]
    if data:
        t=Table(data, repeatRows=1, hAlign='CENTER')
        t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'NotoSC'),('FONTSIZE',(0,0),(-1,-1),7),('LEADING',(0,0),(-1,-1),9),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#24425C')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F8')])]))
        story.append(Spacer(1,5)); story.append(t); story.append(Spacer(1,8))
SimpleDocTemplate(str(out), pagesize=A4, rightMargin=2.2*cm, leftMargin=2.2*cm, topMargin=2.0*cm, bottomMargin=2.0*cm, title='基于机器学习的加密代理流量识别').build(story)
print(out)
