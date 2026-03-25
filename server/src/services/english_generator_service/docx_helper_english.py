
import re

from bs4 import BeautifulSoup,NavigableString

def add_html_formatted_text(paragraph, html_text: str):
    """
    Parse đơn giản các tag: <u>, <i>, <strong>, <b>
    """
    
    # regex bắt các cụm có tag hoặc text thường
    pattern = r'(<[^>]+>.*?</[^>]+>|[^<]+)'
    parts = re.findall(pattern, html_text)

    for part in parts:
        text = part
        bold = False
        italic = False
        underline = False

        # detect tag
        if "<u>" in part:
            underline = True
            text = re.sub(r"</?u>", "", text)

        if "<i>" in part:
            italic = True
            text = re.sub(r"</?i>", "", text)

        if "<strong>" in part or "<b>" in part:
            bold = True
            text = re.sub(r"</?(strong|b)>", "", text)

        # remove leftover tags
        text = re.sub(r"<.*?>", "", text)

        run = paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
        run.underline = underline


def render_formatted_paragraph(doc, text, prefix=None):
    """
    Render text có format Markdown + HTML vào docx.

    Hỗ trợ:
    - **bold**
    - *italic*
    - __underline__
    - <b>, <strong>, <u>, <i>
    """

    if not text:
        return

    # ── 1. Convert Markdown → HTML ─────────────────
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)   # bold
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)                 # italic
    text = re.sub(r"__(.*?)__", r"<u>\1</u>", text)                 # underline

    # ── 2. Parse HTML ──────────────────────────────
    soup = BeautifulSoup(text, "html.parser")

    p = doc.add_paragraph()

    # prefix (in đậm)
    if prefix:
        run = p.add_run(prefix)
        run.bold = True

    # ── 3. Render từng đoạn text ───────────────────
    for element in soup.descendants:
        if isinstance(element, NavigableString):
            content = str(element)

            if not content.strip():
                continue

            run = p.add_run(content)

            parent = element.parent

            # check toàn bộ ancestor để support nested
            run.bold = any(tag.name in ["strong", "b"] for tag in parent.parents) or parent.name in ["strong", "b"]
            run.italic = any(tag.name == "i" for tag in parent.parents) or parent.name == "i"
            run.underline = any(tag.name == "u" for tag in parent.parents) or parent.name == "u"

def parse_html_like(text):
    # pattern = re.compile(
    #     r'(<strong>)?(<u>)?(<i>)?(.*?)(</i>)?(</u>)?(</strong>)?',
    #     re.DOTALL
    # )
    pattern = re.compile(
        r'(<strong>|<b>)?(<u>)?(<i>)?(.*?)(</i>)?(</u>)?(</strong>|</b>)?',
        re.DOTALL
    )
    results = []

    for match in pattern.finditer(text):
        content = match.group(4)
        if not content:
            continue

        bold = bool(match.group(1) or match.group(7))
        underline = bool(match.group(2) or match.group(6))
        italic = bool(match.group(3) or match.group(5))

        results.append({
            "text": content,
            "bold": bold,
            "underline": underline,
            "italic": italic
        })

    return results

def add_formatted_paragraph(doc, prefix, text):
    p = doc.add_paragraph()
    p.add_run(prefix).bold = True

    soup = BeautifulSoup(text, "html.parser")

    for element in soup.descendants:
        if isinstance(element, NavigableString):
            content = str(element)
            if not content.strip():
                continue

            run = p.add_run(content)

            parent = element.parent

            # check toàn bộ ancestor
            run.bold = any(tag.name in ["strong", "b"] for tag in parent.parents) or parent.name in ["strong", "b"]
            run.underline = any(tag.name == "u" for tag in parent.parents) or parent.name == "u"
            run.italic = any(tag.name == "i" for tag in parent.parents) or parent.name == "i"
