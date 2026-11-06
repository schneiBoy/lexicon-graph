"""Flag OCR tokens that are not in the closed vocabularies. This catches only about half of real OCR errors (measured), so it only
prioritises; the gate for anything that enters the dataset is proofreading the quoted lines against the page image."""
import argparse,re,sys,json
from bullinger_vocab import build,strip,GRK,ENG
ENGV=GRKV=None
def load(kjv_json,thayers_dir,strongs_js):
    global ENGV,GRKV
    ENGV,GRKV=build(kjv_json,thayers_dir,strongs_js)
def tokens(text):
    for m in re.finditer(r"[A-Za-z]+(?:['’][a-z]+)?|[Ͱ-Ͽἀ-῿]+|[^\s]",text):
        yield m.group(0)
def check(text):
    """List of (token, reason) that are not in the closed vocabularies."""
    bad=[]
    for raw in text.split():
        core=raw.strip(".,;:()[]{}\"“”‘’'!?—-|*")
        if not core or core.isdigit():continue
        g=GRK.findall(core);e=ENG.findall(core)
        if g and e: bad.append((raw,'mixed scripts'));continue
        if g:
            for w in g:
                if strip(w) not in GRKV: bad.append((raw,'Greek word not in Strong/Thayer'))
        elif e:
            for w in e:
                if w.lower() not in ENGV and len(w)>1: bad.append((raw,'English word not in vocabulary'))
        elif re.search(r"[|¡¢£§]|\w[}{]\w",raw): bad.append((raw,'stray symbol'))
        # stray bracket glyphs
        if re.search(r"[\[\]]",raw) and not re.fullmatch(r"\[?[\w'’.,;:\-()]*\]?[.,;:)]*",raw): bad.append((raw,'odd bracket'))
    return bad
