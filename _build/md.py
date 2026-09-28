"""Tiny HTML -> Markdown converter used for llms-full.txt."""
import re
from html.parser import HTMLParser


class _Md(HTMLParser):
    """Tiny HTML -> Markdown converter for the article bodies (headings, paragraphs, lists, links, emphasis, images, quotes, code, tables)."""

    def __init__(self, site=""):
        super().__init__(convert_charrefs=True)
        self.site = site
        self.out, self.href, self.lists, self.pre, self.row = [], [], [], False, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h2", "h3", "h4"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in ("p", "blockquote", "figure", "table"):
            self.out.append("\n\n" + ("> " if tag == "blockquote" else ""))
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
            self.out.append("\n")
        elif tag == "li":
            kind = self.lists[-1] if self.lists else ["ul", 0]
            kind[1] += 1
            self.out.append("\n" + "  " * (len(self.lists) - 1) + ("- " if kind[0] == "ul" else f"{kind[1]}. "))
        elif tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "a":
            self.href.append(a.get("href"))
            self.out.append("[")
        elif tag == "img" and a.get("alt"):
            src = a.get("src", "")
            self.out.append(f"![{a['alt']}]({src if src.startswith('http') else self.site + src})")
        elif tag == "br":
            self.out.append("  \n")
        elif tag == "pre":
            self.pre = True
            self.out.append("\n\n```\n")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.row.append("")

    def handle_endtag(self, tag):
        if tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "a":
            href = self.href.pop() if self.href else None
            if href and href.startswith("/"):
                href = self.site + href
            self.out.append(f"]({href})" if href else "]")
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self.out.append("\n")
        elif tag == "pre":
            self.pre = False
            self.out.append("\n```\n")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "tr" and self.row is not None:
            self.out.append("\n| " + " | ".join(c.strip() for c in self.row) + " |")
            self.row = None

    def handle_data(self, d):
        if self.row is not None and self.row:
            self.row[-1] += d
            return
        self.out.append(d if self.pre else re.sub(r"\s+", " ", d))

    def markdown(self):
        md = "".join(self.out)
        md = re.sub(r"\*\*\s*\*\*|\[\s*\]\([^)]*\)", "", md)
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n[ \t]+(?=\S)", lambda m: "\n" if not re.match(r"\n {2,}[-\d]", m.group(0) + " ") else m.group(0), md)
        md = re.sub(r"(\S) +(!\[)", r"\1\n\n\2", md)
        return re.sub(r"\n{3,}", "\n\n", md).strip()


def to_markdown(body_html, site=""):
    m = _Md(site)
    m.feed(body_html)
    return m.markdown()
