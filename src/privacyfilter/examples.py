import difflib
import html
import os
import re

from .core import PrivacyFilter

folder = "example_texts"
output_file = "results.html"


def tokenize(string):
    return re.split(r"\s+", string)


def render_tokens(tokens, highlighted=False, color="red"):
    text = " ".join(html.escape(token) for token in tokens if token != "_")
    if highlighted:
        return f'<b style="color:{color};">{text}</b>'
    return text


def compare(s1, s2, color):
    left_tokens = tokenize(s1.strip())
    right_tokens = tokenize(s2.strip())
    left = []
    right = []
    previous = difflib.Match(0, 0, 0)

    for match in difflib.SequenceMatcher(a=left_tokens, b=right_tokens).get_matching_blocks():
        left_difference = left_tokens[previous.a + previous.size:match.a]
        right_difference = right_tokens[previous.b + previous.size:match.b]
        if left_difference:
            left.append(render_tokens(left_difference, highlighted=True, color=color))
        if right_difference:
            right.append(render_tokens(right_difference))
        left.append(render_tokens(left_tokens[match.a:match.a + match.size]))
        right.append(render_tokens(right_tokens[match.b:match.b + match.size]))
        previous = match

    return " ".join(part for part in left if part), " ".join(part for part in right if part)


def main():
    print("Initializing filter.")
    pfilter_wl = PrivacyFilter()
    pfilter_wl.initialize(clean_accents=True, nlp_filter=False, wordlist_filter=True)
    pfilter_nlp = PrivacyFilter()
    pfilter_nlp.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=False)

    print("Running example texts:")

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(
            "<html><style>table,th {padding: 10px;border: 2px solid black;border-collapse: "
            "collapse;text-align:left}</style><style>td {padding: 10px;border: 1px solid "
            "#e0e0e0;border-collapse:collapse;text-align:left}</style>\n<body>\n"
        )
        for filename in os.listdir(folder):
            if not filename.endswith(".txt"):
                continue

            print(filename)
            out.write('&nbsp;\n<table style="width:1000px;">')
            out.write(
                '<thead>\n<tr><th style="width:25%;">'
                + html.escape(filename)
                + '</th><th style="width:25%;"><small>'
                + html.escape(pfilter_wl.to_string())
                + '</small></th><th style="width:25%;"></th><th style="width:25%;"><small>'
                + html.escape(pfilter_nlp.to_string())
                + "</small></th></tr>\n</thead>\n<tbody>"
            )
            with open(os.path.join(folder, filename), encoding="utf-8") as inputfile:
                for line in inputfile:
                    out.write("<tr>")
                    origin, result = compare(line, pfilter_wl.filter(line), "red")
                    out.write("<td>" + origin + "</td><td>" + result + "</td>")
                    origin, result = compare(line, pfilter_nlp.filter(line), "blue")
                    out.write("<td>" + origin + "</td><td>" + result + "</td>")
                    out.write("</tr>")
            out.write("</tbody>\n</table>\n")

        out.write("</body></html>")


if __name__ == "__main__":
    main()
