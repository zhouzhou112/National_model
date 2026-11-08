"""Render exported PDFs and create a local Chinese gallery; no data changes.

Run with a Python containing pymupdf and Pillow (the Codex bundled runtime was
used for the delivered run). Image generation remains in matplotlib scripts.
"""
from pathlib import Path
import hashlib
import html
import json
import re
from urllib.parse import quote

import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
ATLAS=ROOT/"Base2060全要素图集"
QA=ATLAS/"核验记录"


def main():
    registry=json.loads((QA/"图件登记.json").read_text(encoding="utf-8"))
    registry=sorted(registry,key=lambda x:(x["folder"],x["stem"]))
    entries=[("现有装机示例",p) for p in sorted((ROOT/"示例图_现有风光装机").rglob("*.pdf"))]
    entries += [(r["folder"]+" / "+r["stem"],ATLAS/r["pdf"]) for r in registry]
    preview=QA/"PDF渲染预览";preview.mkdir(parents=True,exist_ok=True)
    checks=[];images=[]
    font=ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc",18)
    for i,(label,pdf) in enumerate(entries,1):
        with pymupdf.open(pdf) as doc:
            assert len(doc)==1
            page=doc[0];pix=page.get_pixmap(dpi=150,alpha=False)
            target=preview/f"{i:02d}_{pdf.stem}.png";pix.save(str(target))
            arr=np.asarray(Image.open(target).convert("RGB"),dtype=float)
            original=Image.open(pdf.with_suffix(".png")).convert("RGB").resize((pix.width,pix.height),Image.Resampling.LANCZOS)
            difference=float(np.mean(np.abs(arr-np.asarray(original,dtype=float))))
            outside=[w[:4] for w in page.get_text("words") if not (w[0]>=-.5 and w[1]>=-.5 and w[2]<=page.rect.width+.5 and w[3]<=page.rect.height+.5)]
            assert not outside,(pdf,outside)
            contract=json.loads((pdf.parent/(pdf.stem+"_检查.json")).read_text(encoding="utf-8"))
            panel_count=len(contract["map_panels"])
            north_count=sum(w[4]=="N" for w in page.get_text("words"))
            scale_count=len(re.findall(r"500\s+km",page.get_text()))
            assert north_count==scale_count==panel_count,(pdf,panel_count,north_count,scale_count)
            ink_checks=[]
            for w in page.get_text("words"):
                if w[4] not in {"N","500"}:continue
                x0,y0,x1,y1=[int(v*150/72) for v in w[:4]]
                ink=int((arr[max(0,y0):y1,max(0,x0):x1].min(axis=2)<180).sum())
                assert ink>5,(pdf,w,"Label exists as text but has no rendered ink")
                ink_checks.append({"label":w[4],"bbox_pt":list(w[:4]),"dark_pixels":ink})
            checks.append({"pdf":str(pdf.relative_to(ROOT)),"rendered_png":str(target.relative_to(ROOT)),
                           "pages":len(doc),"mediabox_pt":list(page.mediabox),"text_words_outside_page":outside,
                           "map_panels":panel_count,"north_labels_visible":north_count,"scale_labels_visible":scale_count,
                           "rendered_label_ink_checks":ink_checks,
                           "pdf_vs_png_mean_absolute_rgb_difference_150dpi":difference,
                           "pdf_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),"visual_review":"PENDING"})
            tile=Image.new("RGB",(1050,1030),"white")
            im=ImageOps.contain(Image.open(target),(1030,960))
            tile.paste(im,((1050-im.width)//2,38))
            ImageDraw.Draw(tile).text((15,8),f"{i:02d} {pdf.stem}",font=font,fill="#233B49")
            images.append(tile)
    for start in range(0,len(images),4):
        sheet=Image.new("RGB",(2100,2060),"#E8EDEF")
        for j,im in enumerate(images[start:start+4]):sheet.paste(im,((j%2)*1050,(j//2)*1030))
        sheet.save(QA/f"视觉检查总览_{start//4+1:02d}.png")
    # Preserve separate pages and searchable embedded vector text in the combined atlas.
    combined=pymupdf.open()
    for r in registry:
        with pymupdf.open(ATLAS/r["pdf"]) as d:combined.insert_pdf(d)
    combined.set_metadata({"title":"Base 2060 全国电力系统地图册","author":"National_RL","subject":"Identified solved outputs; no new optimization"})
    combined.save(str(ATLAS/"Base2060全要素地图册.pdf"),garbage=3,deflate=True);combined.close()
    with pymupdf.open(ATLAS/"Base2060全要素地图册.pdf") as d:assert len(d)==len(registry)
    (QA/"PDF渲染检查.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
    cards=[]
    for label,pdf in entries:
        rel=pdf.relative_to(ROOT).as_posix();png=pdf.with_suffix('.png').relative_to(ROOT).as_posix()
        caption=pdf.parent/(pdf.stem+"_图注.md")
        desc=caption.read_text(encoding="utf-8").split("\n\n")[1] if caption.exists() else "2025年已有装机估计分布：四技术分开、全量格网、线性色标。"
        cards.append(f'<article><h2>{html.escape(label)}</h2><a href="{quote(png)}"><img loading="lazy" src="{quote(png)}"></a><p>{html.escape(desc)}</p><a href="{quote(rel)}">打开 PDF</a> · <a href="{quote(png)}">打开 450 dpi PNG</a></article>')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>全国地图模板与 Base 2060 图集</title><style>body{font:16px/1.7 "Microsoft YaHei",Arial,sans-serif;background:#edf2f4;color:#233B49;margin:0}header,main{max-width:1150px;margin:auto;padding:30px}header{padding-bottom:0}h1{margin:0}article{background:white;border:1px solid #d6e1e6;border-radius:8px;padding:24px;margin:24px 0}h2{font-size:21px;margin-top:0}img{max-width:100%;height:auto}a{color:#16558A}p{color:#4d626b}</style><header><h1>全国地图模板与 Base 2060 图集</h1><p>可复用模板 · 已有风光装机示例 · 全年已解结果专题地图</p><p>英文图内标签，中文目录与解释。点击图片可查看原尺寸；来源、单位和限制见各图注。</p><a href="Base2060全要素图集/Base2060全要素地图册.pdf">打开合并地图册</a></header><main>'''+"".join(cards)+"</main></html>"
    (ROOT/"地图图集浏览.html").write_text(page,encoding="utf-8")
    print(json.dumps({"pdfs_rendered":len(entries),"atlas_pages":len(registry),"max_pdf_png_rgb_difference":max(c["pdf_vs_png_mean_absolute_rgb_difference_150dpi"] for c in checks)},ensure_ascii=False))


if __name__=="__main__":main()
