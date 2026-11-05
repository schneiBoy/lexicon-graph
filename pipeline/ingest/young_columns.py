"""OCR Young's Index-Lexicon one column at a time (6 columns per page; whole-page OCR scrambles them).

  YOUNGS_PDF=scan.pdf python3 young_columns.py OUT_DIR PSM FIRST_PAGE LAST_PAGE      # run with PSM 6 and again with PSM 4

The column grid is fitted per page from the positions of capital-letter headwords. Writes OUT_DIR/<page>_psm<PSM>.txt.
"""
import re, subprocess, sys, os, numpy as np, concurrent.futures as cf
from PIL import Image
PDF=os.environ.get('YOUNGS_PDF','analyticalconcor0000youn_j4x7.pdf')
PITCH=357.5; NCOL=6
def fit_x0_old(a):
    H,W=a.shape; body=(a[int(H*.09):int(H*.93)]<150)
    prof=body.mean(0); best=None
    for x0 in range(10,130):
        cost=sum(prof[max(0,int(x0+i*PITCH-14)):int(x0+i*PITCH-2)].mean() for i in range(1,NCOL))
        if best is None or cost<best[0]:best=(cost,x0)
    return best[1]
def fit_x0(img,png):
    import csv,math
    small=img.resize((img.width//2,img.height//2)); small.save(png+'_s.png')
    r=subprocess.run(['tesseract',png+'_s.png','stdout','--psm','4','-l','eng','tsv'],capture_output=True,text=True).stdout
    ang=[]
    for row in csv.DictReader(r.splitlines(),delimiter='\t',quoting=csv.QUOTE_NONE):
        t=row.get('text') or ''
        if row['level']=='5' and re.fullmatch(r'[A-Z]{5,}',t) and float(row['conf'])>60:
            ang.append(2*math.pi*(2*int(row['left']))/PITCH)
    os.remove(png+'_s.png')
    if len(ang)<5: return None
    m=math.atan2(sum(math.sin(x) for x in ang),sum(math.cos(x) for x in ang))
    ph=(m/(2*math.pi))*PITCH % PITCH
    return ph-4   # headword text starts ~4px inside the column
def page(n,out,psm):
    png=f'{out}/p{n}'
    subprocess.run(['pdftoppm','-r','300','-gray','-f',str(n),'-l',str(n),'-png','-singlefile',PDF,png],check=True)
    a=Image.open(png+'.png').convert('L'); W,H=a.size
    x0=fit_x0(a,png)
    if x0 is None: raise SystemExit(f'page {n}: cannot fit columns')
    while x0<-60: x0+=PITCH
    while x0>PITCH-60: x0-=PITCH
    texts=[]
    starts=[x0+k*PITCH for k in range(0,8) if x0+k*PITCH+300<W]
    for i,st in enumerate(starts):
        l=max(0,int(st-8)); box=(l,int(H*.085),min(W,l+372),int(H*.93))
        a.crop(box).save(f'{png}_c{i}.png')
        subprocess.run(['tesseract',f'{png}_c{i}.png',f'{png}_c{i}_psm{psm}','--psm',str(psm),'-l','eng+grc'],capture_output=True)
        texts.append(open(f'{png}_c{i}_psm{psm}.txt',encoding='utf-8').read())
    os.remove(png+'.png')
    open(f'{out}/{n}_psm{psm}.txt','w',encoding='utf-8').write('\n'.join(texts))
    return n,(round(x0),len(starts))
if __name__=='__main__':
    out=sys.argv[1]; psm=int(sys.argv[2]); os.makedirs(out,exist_ok=True)
    pages=range(int(sys.argv[3]),int(sys.argv[4])+1)
    with cf.ThreadPoolExecutor(2) as ex:
        for n,x0 in ex.map(lambda n:page(n,out,psm),pages):print(n,x0,flush=True)
