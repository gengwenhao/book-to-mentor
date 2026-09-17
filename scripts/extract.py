#!/usr/bin/env python3
"""book-to-mentor 文本提取器。

用法:
  python extract.py <path...> --mode <technical|text> [--workdir DIR]
  python extract.py --check

输出:
  <workdir>/full_text.txt   - 全部提取文本合并，带 SOURCE 分隔标记
  <workdir>/metadata.json   - 统计与逐源信息
"""
import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

SUPPORTED = {".pdf", ".epub", ".docx", ".txt", ".md", ".markdown", ".html", ".htm", ".rtf"}


def _try_import(name):
    try:
        __import__(name)
        return True
    except Exception:
        return False


def report_check():
    deps = {
        "pypdf": "pip install pypdf",
        "pdfminer.high_level": "pip install pdfminer.six",
        "ebooklib": "pip install ebooklib beautifulsoup4",
        "bs4": "pip install beautifulsoup4",
        "docx": "pip install python-docx",
        "striprtf": "pip install striprtf",
    }
    print("=== 提取器可用性 ===")
    for mod, install in deps.items():
        ok = _try_import(mod)
        print(f"{'[OK]' if ok else '[--]'} {mod:24} {'' if ok else install}")


def extract_txt(path):
    return path.read_text(encoding="utf-8", errors="replace")


def extract_html(path):
    if _try_import("bs4"):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
        return soup.get_text("\n")
    return extract_txt(path)


def extract_pdf(path, technical):
    if technical and _try_import("docling"):
        try:
            from docling.document_converter import DocumentConverter
            res = DocumentConverter().convert(str(path))
            return res.document.export_to_markdown()
        except Exception as e:
            print(f"[warn] docling failed: {e}", file=sys.stderr)
    if _try_import("pypdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    if _try_import("pdfminer.high_level"):
        from pdfminer.high_level import extract_text
        return extract_text(str(path))
    raise RuntimeError("需要 pypdf 或 pdfminer.six 提取 PDF，请先安装（pip install pypdf）")


def extract_epub(path):
    if _try_import("ebooklib"):
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        book = epub.read_epub(str(path))
        parts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content().decode("utf-8", "replace"), "html.parser")
            parts.append(soup.get_text("\n"))
        return "\n\n".join(parts)
    # stdlib 回退：按文件名顺序拼 HTML 文本
    parts = []
    with zipfile.ZipFile(str(path)) as z:
        names = sorted(n for n in z.namelist() if n.lower().endswith((".xhtml", ".html", ".htm")))
        for n in names:
            raw = z.read(n).decode("utf-8", "replace")
            parts.append(re.sub(r"<[^>]+>", " ", raw))
    return "\n\n".join(parts)


def extract_docx(path):
    if _try_import("docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    raise RuntimeError("需要 python-docx 提取 DOCX，请先安装（pip install python-docx）")


def extract_rtf(path):
    if _try_import("striprtf"):
        from striprtf.striprtf import rtf_to_text
        return rtf_to_text(path.read_text(encoding="utf-8", errors="replace"))
    return re.sub(r"\\[a-z]+(-?\d+)? ?", "", path.read_text(encoding="utf-8", errors="replace"))


def extract(path, technical):
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"不支持格式: {ext}")
    if ext in (".txt",):
        return extract_txt(path)
    if ext in (".md", ".markdown"):
        return extract_txt(path)
    if ext in (".html", ".htm"):
        return extract_html(path)
    if ext == ".pdf":
        return extract_pdf(path, technical)
    if ext == ".epub":
        return extract_epub(path)
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".rtf":
        return extract_rtf(path)
    return extract_txt(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="文件/目录/glob")
    ap.add_argument("--mode", choices=["technical", "text"], default="text")
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        report_check()
        return

    if not args.paths:
        ap.error("至少需要一个文件/目录/glob")
    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="book_mentor_work-"))
    workdir.mkdir(parents=True, exist_ok=True)

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files += [f for f in path.rglob("*") if f.suffix.lower() in SUPPORTED]
        else:
            import glob
            files += [Path(f) for f in glob.glob(p) if Path(f).suffix.lower() in SUPPORTED]

    sources, full = [], []
    for f in sorted(set(files)):
        try:
            text = extract(f, args.mode == "technical")
            words = len(re.findall(r"\S+", text))
            sources.append({
                "source_file": str(f),
                "format": f.suffix.lower(),
                "words": words,
                "tokens": int(words * 1.3),
            })
            full.append(f"===== SOURCE: {f} =====\n{text}")
            print(f"[ok] {f} ({words} words)")
        except Exception as e:
            print(f"[skip] {f}: {e}", file=sys.stderr)

    if not sources:
        print("没有成功提取任何文件", file=sys.stderr)
        sys.exit(1)

    (workdir / "full_text.txt").write_text("\n\n".join(full), encoding="utf-8")
    meta = {
        "workdir": str(workdir),
        "sources": sources,
        "total_words": sum(s["words"] for s in sources),
        "total_tokens": sum(s["tokens"] for s in sources),
        "pages": 0,
    }
    (workdir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Workdir -> {workdir}")
    print(f"Text   -> {workdir / 'full_text.txt'}")
    print(f"Meta   -> {workdir / 'metadata.json'}")


if __name__ == "__main__":
    main()
