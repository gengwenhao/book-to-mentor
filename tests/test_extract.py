"""Regression tests using real, minimal documents; no downloaded books required."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract.py"
SPEC = importlib.util.spec_from_file_location("book_mentor_extract", SCRIPT)
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)


def make_epub(path):
    """Archive order and filenames deliberately disagree with the reading order."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OPS/package.opf"
    media-type="application/oebps-package+xml"/></rootfiles>
</container>""")
        archive.writestr("OPS/package.opf", """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="id">regression-fixture</dc:identifier>
    <dc:title>Fixture</dc:title><dc:language>zh</dc:language>
    <meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="second" href="a-second.xhtml" media-type="application/xhtml+xml"/>
    <item id="decoy" href="b-unused.xhtml" media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="first" href="z-first.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="first"/><itemref idref="second"/></spine>
</package>""")
        for name, body in [
            ("a-second.xhtml", "<h1>第二章</h1><p>第二步：检查证据。</p>"),
            ("b-unused.xhtml", "<p>UNREFERENCED_DECOY</p>"),
            ("nav.xhtml", '<nav epub:type="toc"><p>NAVIGATION_ONLY</p></nav>'),
            ("z-first.xhtml", "<h1>第一章</h1><p>第一步：提出假设。</p>"),
        ]:
            archive.writestr("OPS/" + name, """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Hidden document title</title></head><body>""" + body + "</body></html>")


def make_docx(path):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", """<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        archive.writestr("_rels/.rels", """<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>""")
        archive.writestr("word/document.xml", """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>表格前：先定义问题。</w:t></w:r></w:p>
    <w:tbl>
      <w:tblPr/><w:tblGrid><w:gridCol w:w="3000"/><w:gridCol w:w="3000"/></w:tblGrid>
      <w:tr>
        <w:tc><w:p><w:r><w:t>条件</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>行动</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>证据不足</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>暂停判断</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:p><w:r><w:t>表格后：记录下一步。</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>""")


def make_pdf(path, texts):
    """Write an uncompressed, valid PDF with one text-bearing page per string."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_numbers = []
    for text in texts:
        page_id = len(objects) + 1
        page_numbers.append(page_id)
        content_id = page_id + 1
        objects.append((
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii"))
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") +
                       b" >>\nstream\n" + stream + b"\nendstream")
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(texts)} >>".encode("ascii")
    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    result.extend((f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
                   f"startxref\n{xref}\n%%EOF\n").encode("ascii"))
    path.write_bytes(result)


class ExtractionRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="book-mentor-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.out = self.root / "output"

    def document(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_cli(self, *paths, workdir=None, expected=0):
        output = workdir or self.out
        command = [sys.executable, str(SCRIPT), *(str(path) for path in paths),
                   "--workdir", str(output)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def metadata(self, output=None):
        return json.loads(((output or self.out) / "metadata.json").read_text(encoding="utf-8"))

    def test_54000_contiguous_chinese_characters_exceed_large_book_threshold(self):
        content = "学" * 54000
        path = self.document("中文书.txt", content)
        self.run_cli(path)
        meta = self.metadata()
        self.assertEqual(meta["total_characters"], 54000)
        self.assertGreater(meta["total_tokens"], 50000)
        self.assertLessEqual(meta["total_tokens"], 162000)
        self.assertEqual(meta["total_tokens"], meta["sources"][0]["tokens"])
        self.assertIn("heuristic", str(meta["sources"][0]["token_estimation"]).lower())
        full = (self.out / "full_text.txt").read_text(encoding="utf-8")
        self.assertEqual(full.split("\n", 1)[1].strip(), content)

    def test_mixed_language_counts_are_not_whitespace_word_count_only(self):
        content = "证据判断" * 1000 + "\n" + "evidence " * 1000
        path = self.document("mixed.md", content)
        self.run_cli(path)
        meta = self.metadata()
        self.assertEqual(meta["total_characters"], len(content))
        self.assertGreater(meta["total_tokens"], 5000)
        self.assertEqual(meta["status"], "success")
        self.assertIsNone(meta["pages"])

    def test_empty_and_whitespace_only_sources_fail_with_diagnostics(self):
        for index, content in enumerate(("", " \n\t\r\n ")):
            with self.subTest(content=repr(content)):
                path = self.document(f"empty-{index}.txt", content)
                output = self.root / f"empty-output-{index}"
                self.run_cli(path, workdir=output, expected=1)
                meta = self.metadata(output)
                self.assertEqual(meta["status"], "failed")
                self.assertEqual(meta["successful_sources"], 0)
                self.assertEqual(meta["failed_sources"], 1)
                self.assertEqual(meta["total_tokens"], 0)
                self.assertEqual(meta["sources"][0]["status"], "failed")
                self.assertTrue(meta["sources"][0]["errors"])
                full = output / "full_text.txt"
                self.assertTrue(not full.exists() or not full.read_text(encoding="utf-8").strip())

    def test_epub_follows_spine_and_excludes_unused_documents(self):
        path = self.root / "ordered.epub"
        make_epub(path)
        with patch.object(extractor, "_try_import", return_value=False):
            text = extractor.extract_epub(path)
        normalized = " ".join(text.split())
        expected = ["第一章", "第一步：提出假设。", "第二章", "第二步：检查证据。"]
        positions = [normalized.index(fragment) for fragment in expected]
        self.assertEqual(positions, sorted(positions), normalized)
        for fragment in expected:
            self.assertEqual(normalized.count(fragment), 1)
        self.assertNotIn("UNREFERENCED_DECOY", normalized)
        self.assertNotIn("NAVIGATION_ONLY", normalized)

    def test_epub_missing_package_is_reported_as_failure(self):
        path = self.root / "invalid.epub"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("chapter.xhtml", "<p>A body without a declared reading order.</p>")
        self.run_cli(path, expected=1)
        self.assertTrue(self.metadata()["sources"][0]["errors"])

    def test_docx_preserves_paragraph_table_paragraph_order(self):
        path = self.root / "table.docx"
        make_docx(path)
        with patch.object(extractor, "_try_import", return_value=False):
            text = extractor.extract_docx(path)
        expected = ["表格前：先定义问题。", "条件", "行动", "证据不足", "暂停判断", "表格后：记录下一步。"]
        positions = [text.index(fragment) for fragment in expected]
        self.assertEqual(positions, sorted(positions), text)
        for fragment in expected:
            self.assertEqual(text.count(fragment), 1)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        self.assertEqual(lines[0], expected[0])
        self.assertEqual(lines[-1], expected[-1])

    def test_corrupt_docx_fails_instead_of_succeeding_with_empty_body(self):
        path = self.root / "broken.docx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", "<not-valid-xml")
        self.run_cli(path, expected=1)
        self.assertTrue(self.metadata()["sources"][0]["errors"])

    def test_rtf_requires_decoder_instead_of_silently_corrupting_chinese(self):
        path = self.document("中文.rtf", r"{\rtf1\ansi\uc1 \u20013?\u25991?}")
        with patch.object(extractor, "_try_import", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "striprtf"):
                extractor.extract_rtf(path)

    @unittest.skipUnless(importlib.util.find_spec("striprtf"), "optional striprtf not installed")
    def test_rtf_unicode_escapes_decode_to_exact_chinese_text(self):
        path = self.document("中文.rtf", r"{\rtf1\ansi\uc1 \u20013?\u25991?}")
        self.assertEqual(extractor.extract_rtf(path).strip(), "中文")

    def test_html_keeps_body_order_decodes_entities_and_excludes_active_content(self):
        path = self.document("source.html", """<!doctype html><html><head>
<title>HEAD_METADATA</title><style>.secret { content: 'STYLE_NOISE'; }</style>
</head><body><h1>第一节</h1><p>甲 &amp; 乙，先观察。</p>
<script>const message = "SCRIPT_NOISE";</script>
<p>第二步：检查 <strong>证据</strong>。</p></body></html>""")
        with patch.object(extractor, "_try_import", return_value=False):
            text = extractor.extract_html(path)
        self.assertNotIn("SCRIPT_NOISE", text)
        self.assertNotIn("STYLE_NOISE", text)
        self.assertNotIn("HEAD_METADATA", text)
        self.assertNotIn("<p>", text)
        self.assertNotIn("&amp;", text)
        self.assertIn("甲 & 乙，先观察。", text)
        positions = [text.index(fragment) for fragment in ["第一节", "甲 & 乙", "第二步", "证据"]]
        self.assertEqual(positions, sorted(positions))

    def test_html_with_only_scripts_does_not_count_as_content(self):
        path = self.document("script-only.html", "<html><script>fake content</script></html>")
        self.run_cli(path, expected=1)
        self.assertEqual(self.metadata()["status"], "failed")

    def test_invalid_utf8_fails_instead_of_inserting_replacement_characters(self):
        path = self.root / "bad-encoding.txt"
        path.write_bytes(b"Valid prefix followed by corrupt bytes: \xff\xfe\x80")
        self.run_cli(path, expected=1)
        meta = self.metadata()
        self.assertEqual(meta["status"], "failed")
        self.assertTrue(meta["sources"][0]["errors"])
        self.assertIn("UTF-8", " ".join(meta["errors"]))

    def test_utf16_bom_decodes_chinese_exactly_and_discloses_conversion(self):
        path = self.root / "utf16.txt"
        content = "第一步：检查证据。\n第二步：修正判断。"
        path.write_bytes(content.encode("utf-16"))
        self.run_cli(path)
        meta = self.metadata()
        self.assertEqual(meta["total_characters"], len(content))
        self.assertTrue(meta["sources"][0]["warnings"])
        full = (self.out / "full_text.txt").read_text(encoding="utf-8")
        self.assertEqual(full.split("\n", 1)[1], content)

    def test_missing_paths_argument_has_usage_error(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_missing_path_is_failure_and_diagnosed(self):
        self.run_cli(self.root / "absent.txt", expected=1)
        meta = self.metadata()
        self.assertEqual(meta["status"], "failed")
        self.assertTrue(meta["errors"])

    def test_unmatched_glob_is_failure_and_diagnosed(self):
        self.run_cli(self.root / "absent-*.txt", expected=1)
        self.assertEqual(self.metadata()["status"], "failed")
        self.assertTrue(self.metadata()["errors"])

    def test_explicit_unsupported_file_is_failure_and_diagnosed(self):
        path = self.document("unsupported.xyz", "must not be accepted as plain text")
        self.run_cli(path, expected=1)
        meta = self.metadata()
        self.assertEqual(meta["status"], "failed")
        self.assertTrue(meta["errors"])

    def test_partial_run_keeps_good_content_and_reports_bad_source(self):
        good = self.document("good.txt", "有效内容：证据先于结论。")
        bad = self.document("empty.txt", "")
        self.run_cli(good, bad, expected=2)
        meta = self.metadata()
        self.assertEqual(meta["status"], "partial")
        self.assertEqual(meta["successful_sources"], 1)
        self.assertEqual(meta["failed_sources"], 1)
        by_name = {Path(source["source_file"]).name: source for source in meta["sources"]}
        self.assertEqual(by_name["good.txt"]["status"], "success")
        self.assertEqual(by_name["empty.txt"]["status"], "failed")
        self.assertTrue(by_name["empty.txt"]["errors"])
        self.assertEqual(meta["total_tokens"], by_name["good.txt"]["tokens"])
        self.assertEqual(meta["total_characters"], len(good.read_text(encoding="utf-8")))
        full = (self.out / "full_text.txt").read_text(encoding="utf-8")
        self.assertEqual(full.count("===== SOURCE:"), 1)
        self.assertIn(good.read_text(encoding="utf-8"), full)
        self.assertNotIn(str(bad), full)

    def test_explicit_missing_path_is_not_hidden_by_another_success(self):
        good = self.document("good.txt", "有内容的源文件。")
        self.run_cli(good, self.root / "missing.txt", expected=2)
        meta = self.metadata()
        self.assertEqual(meta["status"], "partial")
        self.assertEqual(meta["successful_sources"], 1)
        self.assertTrue(meta["errors"])

    def test_nested_output_is_not_reingested_on_first_or_repeated_run(self):
        input_dir = self.root / "books"
        good = self.document("books/chapter.txt", "唯一章节：用证据检查判断。")
        output = input_dir / "generated"
        output.mkdir()
        (output / "stale.txt").write_text("GENERATED_DECOY", encoding="utf-8")
        for _ in range(2):
            self.run_cli(input_dir, workdir=output)
            meta = self.metadata(output)
            self.assertEqual(meta["successful_sources"], 1)
            self.assertEqual(len(meta["sources"]), 1)
            self.assertEqual(Path(meta["sources"][0]["source_file"]).resolve(), good.resolve())
            full = (output / "full_text.txt").read_text(encoding="utf-8")
            self.assertEqual(full.count("===== SOURCE:"), 1)
            self.assertEqual(full.count("唯一章节"), 1)
            self.assertNotIn("GENERATED_DECOY", full)

    def test_duplicate_path_and_directory_inputs_do_not_duplicate_content(self):
        good = self.document("books/lesson.txt", "不要把同一来源计算两次。")
        self.run_cli(good, good.parent, good)
        meta = self.metadata()
        self.assertEqual(meta["successful_sources"], 1)
        self.assertEqual(meta["total_characters"], len(good.read_text(encoding="utf-8")))

    def test_recursive_glob_excludes_nested_generated_content(self):
        good = self.document("books/lesson.txt", "唯一原始内容。")
        output = good.parent / "generated"
        output.mkdir()
        (output / "stale.txt").write_text("GENERATED_DECOY", encoding="utf-8")
        self.run_cli(good.parent / "**" / "*.txt", workdir=output)
        self.assertEqual(self.metadata(output)["successful_sources"], 1)
        self.assertEqual(self.metadata(output)["total_characters"], len(good.read_text(encoding="utf-8")))

    def test_failed_rerun_clears_previous_successful_output(self):
        good = self.document("good.txt", "PREVIOUS_SUCCESS_MUST_NOT_SURVIVE_FAILURE")
        self.run_cli(good)
        bad = self.document("empty.txt", "")
        self.run_cli(bad, expected=1)
        self.assertEqual(self.metadata()["status"], "failed")
        full = self.out / "full_text.txt"
        self.assertTrue(not full.exists() or not full.read_text(encoding="utf-8").strip())

    def test_input_output_collision_does_not_overwrite_the_source(self):
        self.out.mkdir()
        content = "这是原始输入，禁止输出阶段覆盖。"
        source = self.out / "full_text.txt"
        source.write_text(content, encoding="utf-8")
        self.run_cli(source, expected=1)
        self.assertEqual(source.read_text(encoding="utf-8"), content)

    def test_directory_input_does_not_overwrite_preexisting_reserved_user_files(self):
        for name, content in [
            ("full_text.txt", "THIS_IS_AN_ORIGINAL_BOOK_NOT_GENERATED_OUTPUT"),
            ("metadata.json", '{"personal_notes": "Preserve this source-side metadata"}'),
        ]:
            with self.subTest(name=name):
                directory = self.root / name.replace(".", "-")
                directory.mkdir()
                source = directory / "chapter.txt"
                source.write_text("可以提取的章节，但不能覆盖旁边的用户文件。", encoding="utf-8")
                protected = directory / name
                protected.write_text(content, encoding="utf-8")
                self.run_cli(directory, workdir=directory, expected=1)
                self.assertEqual(protected.read_text(encoding="utf-8"), content)
                self.assertEqual(source.read_text(encoding="utf-8"), "可以提取的章节，但不能覆盖旁边的用户文件。")

    def test_output_symlink_does_not_overwrite_its_target(self):
        good = self.document("source.txt", "可以正常提取的正文。")
        target = self.document("precious.txt", "PRESERVE_THIS_UNRELATED_FILE")
        self.out.mkdir()
        (self.out / "full_text.txt").symlink_to(target)
        self.run_cli(good, expected=1)
        self.assertEqual(target.read_text(encoding="utf-8"), "PRESERVE_THIS_UNRELATED_FILE")

    def test_pdf_without_dependencies_fails_with_actionable_diagnostic(self):
        path = self.root / "valid.pdf"
        make_pdf(path, ["Evidence before conclusion."])
        with patch.object(extractor, "_try_import", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "pypdf|pdfminer"):
                extractor.extract_pdf(path, technical=False)

    def test_technical_pdf_fallback_discloses_degradation_with_stub_parser(self):
        path = self.root / "technical.pdf"
        content = "Plain text loses the visual table layout."
        make_pdf(path, [content])
        fake_page = types.SimpleNamespace(extract_text=lambda: content)
        fake_pypdf = types.SimpleNamespace(
            PdfReader=lambda filename: types.SimpleNamespace(pages=[fake_page])
        )
        with patch.object(extractor, "_try_import", side_effect=lambda name: name == "pypdf"):
            with patch.dict(sys.modules, {"pypdf": fake_pypdf}):
                result = extractor.extract_result(path, technical=True)
        self.assertEqual(result["text"], content)
        self.assertEqual(result["extractor"], "pypdf")
        self.assertEqual(result["pages"], 1)
        warnings = " ".join(result["warnings"]).lower()
        self.assertIn("docling", warnings)
        self.assertIn("degraded", warnings)
        self.assertIn("table", warnings)

    @unittest.skipUnless(
        importlib.util.find_spec("pypdf") or importlib.util.find_spec("pdfminer"),
        "optional PDF parser not installed",
    )
    def test_real_two_page_pdf_preserves_order_and_reports_page_count(self):
        path = self.root / "two-pages.pdf"
        first, second = "FIRST: ask for evidence.", "SECOND: revise the claim."
        make_pdf(path, [first, second])
        self.run_cli(path)
        meta = self.metadata()
        self.assertEqual(meta["pages"], 2)
        self.assertEqual(meta["sources"][0]["pages"], 2)
        full = (self.out / "full_text.txt").read_text(encoding="utf-8")
        self.assertEqual(full.count(first), 1)
        self.assertEqual(full.count(second), 1)
        self.assertLess(full.index(first), full.index(second))


if __name__ == "__main__":
    unittest.main()
