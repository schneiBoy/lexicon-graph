"""Closed vocabularies for checking Bullinger OCR: English from the KJV, Thayer's and Strong's text; Greek from Thayer's and Strong's."""
import re,json,glob,unicodedata,collections
def strip(s):
    d=unicodedata.normalize("NFD",s);return "".join(c for c in d if unicodedata.category(c)!="Mn").lower().replace("ς","σ")
GRK=re.compile(r"[Ͱ-Ͽἀ-῿]+")
ENG=re.compile(r"[A-Za-z]+(?:['’][a-z]+)?")
def build(kjv_json,thayers_dir,strongs_js):
    eng,grk=set(),set()
    kjv=json.load(open(kjv_json,encoding='utf-8'))['verses']
    for v in kjv:
        t=re.sub(r"\{[^}]*\}","",v['text'])
        eng|={w.lower() for w in ENG.findall(t)}
    for f in glob.glob(thayers_dir+'/*.md'):
        t=open(f,encoding='utf-8').read()
        eng|={w.lower() for w in ENG.findall(t)};grk|={strip(w) for w in GRK.findall(t)}
    src=open(strongs_js,encoding='utf-8').read()
    j=json.loads(src[src.index('{'):src.rindex('}')+1])
    for v in j.values():
        grk|={strip(w) for w in GRK.findall(v['lemma'])}
        eng|={w.lower() for w in ENG.findall(v.get('strongs_def','')+' '+v.get('kjv_def',''))}
    return eng,grk

