#!/usr/bin/env python3
"""Build Strong's Greek fields from the openscriptures XML, not from the derived JSON.

Why: the JSON (strongs-greek-dictionary.js) drops the Greek word from 469 of 5,624 derivations (G25 reads
"perhaps from (much)" instead of "perhaps from ἄγαν (much)") and adds a lemma after every cross-reference that the
source does not contain. The XML keeps the words. The XML labels a few Hebrew cross-references as GREEK (G25 -> 5689,
G137 -> 5869, G4460 -> 7343); the xhtml edition of the same repo links them as Old Testament, so the xhtml settles the language.

  python3 strongs_xml.py strongs/greek/StrongsGreekDictionaryXML_1.4/strongsgreek.xml strongs/strongs-dictionary.xhtml > greek.json
"""
import json
import re
import sys


def text(fragment, hebrew_refs):
    fragment = re.sub(r'<greek [^>]*unicode="([^"]+)"[^>]*/>', r'\1', fragment)

    def ref(m):
        lang, num = m.group(1), m.group(2)
        if (lang == 'GREEK') and num in hebrew_refs:
            return 'H' + num
        return ('G' if lang == 'GREEK' else 'H') + num
    fragment = re.sub(r'<strongsref language="(\w+)" strongs="(\d+)"/>', ref, fragment)
    fragment = re.sub(r'<[^>]+>', '', fragment)
    return ' '.join(fragment.split())


def main(xml_path, xhtml_path):
    xml = open(xml_path, encoding='utf-8').read()
    xhtml = open(xhtml_path, encoding='utf-8').read()
    ot_links = {}
    for m in re.finditer(r'<li value="(\d+)" id="nt:\d+">(.*?)</li>', xhtml, re.S):
        ot_links[m.group(1)] = set(re.findall(r'href="#ot:(\d+)"', m.group(2)))
    out, fixed = {}, []
    for m in re.finditer(r'<entry strongs="0*(\d+)">(.*?)</entry>', xml, re.S):
        n, body = m.group(1), m.group(2)
        hebrew = ot_links.get(n, set())
        g = re.search(r'<greek [^>]*unicode="([^"]+)"[^>]*translit="([^"]*)"', body)
        d = re.search(r'<strongs_derivation>(.*?)</strongs_derivation>', body, re.S)
        s = re.search(r'<strongs_def>(.*?)</strongs_def>', body, re.S)
        k = re.search(r'<kjv_def>(.*?)</kjv_def>', body, re.S)
        rec = {'lemma': g.group(1) if g else '', 'translit': g.group(2) if g else '',
               'derivation': text(d.group(1), hebrew) if d else '',
               'definition': text(s.group(1), hebrew) if s else '',
               'kjv_def': text(k.group(1), hebrew).lstrip(':-').strip() if k else ''}
        if d and re.search(rf'language="GREEK" strongs="({"|".join(hebrew)})"', d.group(1)) and hebrew:
            fixed.append(n)
        out['G' + n] = rec
    json.dump({'source': 'openscriptures/strongs XML 1.4 + xhtml', 'language_fixed': ['G' + n for n in fixed], 'entries': out},
              sys.stdout, ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
