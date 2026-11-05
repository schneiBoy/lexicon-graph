#!/usr/bin/env python3
"""Count occurrences of every Strong's number in the tagged KJV, with the helper-word rule.

A tag group looks like `loved{G25}{(G5656)}`. Verbs carry a second tag in parentheses (tense, voice, mood).
For a number that is mostly used on verb forms (at least half its tag groups), only tag groups that also carry that verb-form tag are counted;
the tagger also marks helper words ("doth", "let us") with the verb's number, and those are excluded.
For every other number, all tag groups are counted.

  python3 kjv_counts.py data/raw/kjv/kjv_strongs.json > counts.json
"""
import collections
import json
import re
import sys

GROUP = re.compile(r"((?:\{\(?[GH]\d+\)?\})+)")


def count(path, nt_only=True):
    verses = json.load(open(path, encoding="utf-8"))["verses"]
    total, with_tvm = collections.Counter(), collections.Counter()
    for v in verses:
        if nt_only and v["book"] < 40:
            continue
        for m in GROUP.finditer(v["text"]):
            grp = m.group(1)
            tvm = bool(re.search(r"\{\(G\d+\)\}", grp))
            for num in re.findall(r"\{([GH]\d+)\}", grp):
                total[num] += 1
                with_tvm[num] += tvm
    # helper-word rule only for numbers that are mostly verb-tagged; a stray verb tag must not collapse a noun's count
    return {n: (with_tvm[n] if with_tvm[n] * 2 >= total[n] else total[n]) for n in total}


if __name__ == "__main__":
    json.dump(count(sys.argv[1]), sys.stdout, indent=0, sort_keys=True)
