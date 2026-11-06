"""OCR Bullinger's Critical Lexicon one column at a time (two columns per page; whole-page OCR drops or interleaves them).

  BULLINGER_PDF=scan.pdf python3 bullinger_columns.py OUT_DIR PSM FIRST LAST [--keep-crops]

The column rule is found per page as the darkest vertical line near the page centre. The running header
(guide words and page number) and the scanner credit are cropped off. Resolution is BULLINGER_DPI (default 400). Writes OUT_DIR/<page>_psm<PSM>.txt and <page>_lines.json (line text, box in page pixels, min word confidence)
with the left column first, then the right, separated by a line containing only '=== COLUMN ==='.
"""
import json, os, subprocess, sys, numpy as np, concurrent.futures as cf
from PIL import Image
PDF=os.environ.get('BULLINGER_PDF','CriticalLexiconConcordance_EngGrkNT__Bullinger_1908__text.pdf')
SEP='\n=== COLUMN ===\n'
def split_columns(a):
    H,W=a.shape
    body=a[int(H*.11):int(H*.92)]
    prof=(body<130).mean(0)
    lo,hi=int(W*.42),int(W*.58)
    rule=lo+int(np.argmax(prof[lo:hi]))
    left=(int(W*.04),int(H*.11),rule-8,int(H*.92))
    right=(rule+8,int(H*.11),int(W*.96),int(H*.92))
    return left,right,rule
DPI=int(os.environ.get('BULLINGER_DPI','400'))
def tsv_lines(tsv,box):
    """Group Tesseract words into lines. Box coordinates are page pixels at DPI (crop offset added back)."""
    rows=[r.split('\t') for r in tsv.splitlines()[1:]]
    lines={}
    for r in rows:
        if len(r)<12 or r[0]!='5' or not r[11].strip(): continue
        key=(r[2],r[3],r[4]);l,t,w,h=int(r[6]),int(r[7]),int(r[8]),int(r[9])
        d=lines.setdefault(key,{'words':[],'l':l,'t':t,'r':l+w,'b':t+h,'conf':[]})
        d['words'].append(r[11]);d['l']=min(d['l'],l);d['t']=min(d['t'],t);d['r']=max(d['r'],l+w);d['b']=max(d['b'],t+h);d['conf'].append(float(r[10]))
    out=[]
    for d in lines.values():
        out.append({'text':' '.join(d['words']),'box':[d['l']+box[0],d['t']+box[1],d['r']-d['l'],d['b']-d['t']],'min_conf':min(d['conf'])})
    return sorted(out,key=lambda x:x['box'][1])
def page(n,out,psm,keep):
    base=f'{out}/p{n}'
    subprocess.run(['pdftoppm','-r',str(DPI),'-gray','-f',str(n),'-l',str(n),'-png','-singlefile',PDF,base],check=True)
    im=Image.open(base+'.png').convert('L')
    texts=[];allines=[]
    for i,box in enumerate(split_columns(np.array(im))[:2]):
        crop=f'{base}_c{i}.png';im.crop(box).save(crop)
        r=subprocess.run(['tesseract',crop,'stdout','--psm',str(psm),'-l','eng+grc','tsv'],capture_output=True,text=True)
        lines=tsv_lines(r.stdout,box)
        texts.append('\n'.join(l['text'] for l in lines))
        allines.append(lines)
        if not keep:os.remove(crop)
    os.remove(base+'.png')
    open(f'{out}/{n:04d}_psm{psm}.txt','w',encoding='utf-8').write(SEP.join(texts))
    json.dump({'page':n,'dpi':DPI,'psm':psm,'columns':allines},open(f'{out}/{n:04d}_lines.json','w'),ensure_ascii=False)
    return n
if __name__=='__main__':
    out,psm,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]);keep='--keep-crops' in sys.argv
    os.makedirs(out,exist_ok=True)
    with cf.ThreadPoolExecutor(2) as ex:
        for n in ex.map(lambda n:page(n,out,psm,keep),range(a,b+1)):print(n,flush=True)
