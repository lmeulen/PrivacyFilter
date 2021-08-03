import os
from PrivacyFilter import PrivacyFilter
import difflib
import re

folder = 'example_texts'
output_file = 'results.html'


def tokenize(string):
    return re.split('\s+', string)


def untokenize(tokens):
    return ' '.join(tokens)


def equalize(s1, s2):
    l1 = tokenize(s1)
    l2 = tokenize(s2)
    res1 = []
    res2 = []
    prev = difflib.Match(0, 0, 0)
    for match in difflib.SequenceMatcher(a=l1, b=l2).get_matching_blocks():
        if prev.a + prev.size != match.a:
            for i in range(prev.a + prev.size, match.a):
                res2 += ['_' * len(l1[i])]
            res1 += ['<b  style="color:red;">'] + l1[prev.a + prev.size:match.a] + ['</b>']
        if prev.b + prev.size != match.b:
            for i in range(prev.b + prev.size, match.b):
                res1 += ['_' * len(l2[i])]
            res2 += l2[prev.b + prev.size:match.b]
        res1 += l1[match.a:match.a + match.size]
        res2 += l2[match.b:match.b + match.size]
        prev = match
    return untokenize(res1), untokenize(res2)


def compare(s1, s2):
    s1, s2 = equalize(s1, s2)
    lft = re.sub(' +', ' ', s1.replace('_', '')).replace('<FILTERED>', '[FILTERED]')
    rgt = re.sub(' +', ' ', s2.replace('_', '')).replace('<FILTERED>', '[FILTERED]')
    return lft, rgt


def main():
    print("Initializing filter.")
    pfilter = PrivacyFilter()
    pfilter.initialize(clean_accents=True, nlp_filter=False)

    print("Running example texts:")

    with open(output_file, 'w') as out:
        out.write('<html><style>table,th {padding: 10px;border: 2px solid black;border-collapse: collapse;text-align:'
                  'left}</style><style >td {padding: 10px;border: 1px solid #e0e0e0;border-collapse: '
                  'collapse;text-align:left}</style>\n')
        out.write('<body>\n')
        for filename in os.listdir(folder):
            if filename.endswith(".txt"):
                print(filename)
                out.write('&nbsp\n<table style="width:1000px;">')
                out.write('<thead>\n<tr><th style="width:50%"; colspan=2>' + filename + '</th></tr>\n</thead>\n')
                out.write('<tbody>')
                with open(os.path.join(folder, filename), 'r') as inputfile:
                    for line in inputfile.readlines():
                        origin, result = compare(line, pfilter.filter(line))
                        out.write('<tr><td>' + origin + '</td><td>' + result + '</td></tr>')
                out.write('</tbody>\n</table>\n')
        out.write('</body>')
        out.write('</html>')


if __name__ == "__main__":
    main()
