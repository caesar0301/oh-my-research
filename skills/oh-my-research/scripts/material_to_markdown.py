#!/usr/bin/env python3
"""Convert collected research materials to full-text Markdown.

Pipeline (per source):
  1. Resolve to a local file:
     - arxiv URL  → download PDF via arxiv API (preferred) or http fallback
     - DOI        → resolve to publisher PDF (best-effort http)
     - http(s) PDF → download
     - local path → use directly
     - HTML page  → fetch and save as .html
  2. Convert to GitHub-Flavored Markdown:
     - Preferred: `@firecrawl/anydoc` CLI (Node 20+, no install)
     - Fallback: `pymupdf` (PDF), `pdfplumber` (PDF), `markdownify`+`bs4` (HTML)
     - Last resort: record `.failed.txt` with the reason
  3. Write `materials/<bucket>/<ID>.md` (full-text) next to the `.source.txt`.

The script is mechanical: no semantic analysis, no summarization. It only turns
bytes on disk into Markdown text that ANALYZE then reads in full.

Usage:
  python3 material_to_markdown.py <source> --id P-001 [--workspace .]
  python3 material_to_markdown.py <source> --id P-001 --bucket papers
  python3 material_to_markdown.py --index            # convert all indexed sources
  python3 material_to_markdown.py --convert-dir materials/papers  # (v1.4) batch convert existing files

Exit codes: 0 success, 1 conversion failed (see .failed.txt), 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# macOS Python often lacks CA certs in the stdlib store; fall back to a permissive
# context only when the default verify fails. curl is tried first for downloads.
_SSL_CTX = ssl.create_default_context()


def _ssl_fallback_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# --- arxiv parsing (stdlib only — no external dependency) --------------------
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query?id_list={id}"
ARXIV_ABS_RE = re.compile(r"arxiv\.org/abs/([^/?#]+)", re.I)
ARXIV_PDF_RE = re.compile(r"arxiv\.org/pdf/([^/?#]+)", re.I)
DOI_RE = re.compile(r"^10\.\d{4,}/\S+$")

# File extensions anydoc can convert directly
ANYDOC_EXTS = {
    ".pdf",
    ".doc",
    ".docx",
    ".docm",
    ".odt",
    ".rtf",
    ".epub",
    ".ppt",
    ".pps",
    ".pot",
    ".pptx",
    ".pptm",
    ".ppsx",
    ".ppsm",
    ".odp",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".xlsb",
    ".ods",
    ".csv",
}
ANYDOC_EXTS_TUPLE = tuple(sorted(ANYDOC_EXTS))
MARKDOWN_EXTS = {".md", ".markdown", ".txt"}

# Fallback converters (imported lazily so the script runs even if missing)
PDF_FALLBACK_LIBS = ["pymupdf", "pdfplumber"]
HTML_FALLBACK_LIBS = ["markdownify", "bs4"]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --- Source resolution -------------------------------------------------------


def _http_get(url: str, timeout: int = 60) -> bytes:
    """Download bytes. Prefer curl (handles macOS CA store), fall back to urllib."""
    # curl is ubiquitous and uses the system CA store on macOS
    if shutil.which("curl"):
        try:
            result = subprocess.run(
                ["curl", "-fsSL", "--max-time", str(timeout), url],
                capture_output=True,
                timeout=timeout + 10,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    # urllib with permissive fallback for environments lacking CA certs
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "oh-my-research/1.0 (material collector)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as r:  # noqa: S310
            return r.read()
    except urllib.error.URLError:
        with urllib.request.urlopen(
            req, timeout=timeout, context=_ssl_fallback_ctx()
        ) as r:  # noqa: S310
            return r.read()


def resolve_arxiv_pdf(url: str) -> tuple[bytes, str]:
    """Download an arxiv PDF. Returns (pdf_bytes, title)."""
    m = ARXIV_ABS_RE.search(url) or ARXIV_PDF_RE.search(url)
    if not m:
        raise ValueError(f"not an arxiv URL: {url}")
    arxiv_id = m.group(1)
    # Direct PDF is fastest
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    try:
        return _http_get(pdf_url), arxiv_id
    except urllib.error.URLError:
        pass
    # Fallback: arxiv API for metadata + pdf link
    api = ARXIV_API.format(id=arxiv_id)
    xml = _http_get(api)
    title = arxiv_id
    try:
        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        if entry is not None:
            t = entry.find("atom:title", ns)
            if t is not None and t.text:
                title = " ".join(t.text.split())
    except ET.ParseError:
        pass
    return _http_get(pdf_url), title


def resolve_doi_pdf(doi: str) -> tuple[bytes, str]:
    """Best-effort DOI → PDF. Many publishers block automated download, so this
    may raise; the caller records a failure and continues."""
    # Try doi.org redirect, then look for a PDF link in the landing page.
    url = f"https://doi.org/{doi}"
    landing = _http_get(url)
    # Naive: scan for a PDF link
    text = landing.decode("utf-8", errors="ignore")
    pdf_match = re.search(r'href="(https?://[^"]+\.pdf)"', text, re.I)
    if pdf_match:
        return _http_get(pdf_match.group(1)), doi
    raise ValueError(f"DOI landing page had no obvious PDF link: {doi}")


def download_to_temp(url: str) -> tuple[Path, str]:
    """Download a URL to a temp file, return (path, title_or_name)."""
    data = _http_get(url)
    suffix = _guess_suffix(url)
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    Path(tmp).write_bytes(data)
    return Path(tmp), url.rsplit("/", 1)[-1]


def _guess_suffix(url: str) -> str:
    low = url.lower().split("?")[0]
    for ext in ANYDOC_EXTS | {".html", ".htm"}:
        if low.endswith(ext):
            return ext
    return ".pdf"  # default for paper-like URLs


# --- Conversion --------------------------------------------------------------


def anydoc_available() -> bool:
    return shutil.which("npx") is not None


def convert_with_anydoc(src: Path, dst: Path) -> bool:
    """Use `npx -y @firecrawl/anydoc` to convert. Returns True on success."""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # anydoc requires absolute paths for reliable -o output resolution
        result = subprocess.run(
            [
                "npx",
                "-y",
                "@firecrawl/anydoc",
                str(src.resolve()),
                "-o",
                str(dst.resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode == 0 and dst.exists()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_pdf_fallback(src: Path) -> str | None:
    """Try pymupdf / pdfplumber. Returns Markdown text or None."""
    # pymupdf
    try:
        import fitz  # type: ignore

        doc = fitz.open(src)
        parts = []
        for page in doc:
            parts.append(page.get_text("text"))
        doc.close()
        if parts:
            return "\n\n".join(parts)
    except ImportError:
        pass
    except Exception:
        pass
    # pdfplumber
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(src) as pdf:
            parts = [p.extract_text() or "" for p in pdf.pages]
        if any(parts):
            return "\n\n".join(parts)
    except ImportError:
        pass
    except Exception:
        pass
    return None


def convert_html_fallback(src: Path) -> str | None:
    """Try markdownify+bs4. Returns Markdown text or None."""
    try:
        from markdownify import markdownify as md  # type: ignore

        html = src.read_text(encoding="utf-8", errors="ignore")
        out = md(html)
        return out or None
    except ImportError:
        return None
    except Exception:
        return None


def convert(src: Path, dst: Path, source_url: str) -> tuple[bool, str]:
    """Convert `src` to Markdown at `dst`. Returns (success, method_or_reason)."""
    suffix = src.suffix.lower()
    # 1. anydoc (preferred)
    if anydoc_available():
        if convert_with_anydoc(src, dst):
            return True, "anydoc"
    # 2. fallbacks
    if suffix == ".pdf":
        text = convert_pdf_fallback(src)
        if text:
            write_text(dst, text)
            return True, "pymupdf/pdfplumber"
    elif suffix in (".html", ".htm"):
        text = convert_html_fallback(src)
        if text:
            write_text(dst, text)
            return True, "markdownify"
    # 3. failure
    return False, "all converters failed (anydoc + fallbacks)"


# --- Orchestration -----------------------------------------------------------


def process_source(
    workspace: Path,
    source: str,
    material_id: str,
    bucket: str = "papers",
    title: str | None = None,
) -> dict[str, Any]:
    """Download + convert one source. Returns a result record."""
    bucket_dir = workspace / "materials" / bucket
    md_path = bucket_dir / f"{material_id}.md"
    failed_path = workspace / "materials" / "failed" / f"{material_id}.failed.txt"
    low = source.lower()

    # Already converted? skip
    if md_path.exists() and md_path.stat().st_size > 0:
        return {
            "id": material_id,
            "status": "exists",
            "path": str(md_path.relative_to(workspace)),
        }

    local_file: Path | None = None
    cleanup = False
    resolved_title = title or source

    try:
        # --- resolve to a local file ---
        if ARXIV_ABS_RE.search(low) or ARXIV_PDF_RE.search(low):
            pdf_bytes, resolved_title = resolve_arxiv_pdf(source)
            local_file = _save_temp(pdf_bytes, ".pdf")
            cleanup = True
        elif DOI_RE.match(source.strip()):
            pdf_bytes, resolved_title = resolve_doi_pdf(source.strip())
            local_file = _save_temp(pdf_bytes, ".pdf")
            cleanup = True
        elif low.startswith(("http://", "https://")) and low.endswith(
            ANYDOC_EXTS_TUPLE
        ):
            local_file, resolved_title = download_to_temp(source)
            cleanup = True
        elif low.startswith(("http://", "https://")):
            # generic web page — fetch as HTML
            data = _http_get(source)
            local_file = _save_temp(data, ".html")
            cleanup = True
        elif Path(source).exists():
            local_file = Path(source).resolve()
        else:
            raise ValueError(f"cannot resolve source: {source}")

        # --- convert (markdown/txt passthrough; anydoc preferred; fallbacks) ---
        if local_file.suffix.lower() in MARKDOWN_EXTS:
            write_text(md_path, local_file.read_text(encoding="utf-8", errors="ignore"))
            ok, method = True, "passthrough"
        else:
            ok, method = convert(local_file, md_path, source)
        if not ok:
            write_text(
                failed_path, f"source: {source}\nid: {material_id}\nreason: {method}\n"
            )
            return {
                "id": material_id,
                "status": "failed",
                "reason": method,
                "failed_path": str(failed_path.relative_to(workspace)),
            }

        return {
            "id": material_id,
            "status": "converted",
            "method": method,
            "path": str(md_path.relative_to(workspace)),
            "title": resolved_title,
        }
    except Exception as e:
        write_text(
            failed_path,
            f"source: {source}\nid: {material_id}\nreason: {type(e).__name__}: {e}\n",
        )
        return {
            "id": material_id,
            "status": "failed",
            "reason": f"{type(e).__name__}: {e}",
            "failed_path": str(failed_path.relative_to(workspace)),
        }
    finally:
        if cleanup and local_file and local_file.exists():
            try:
                local_file.unlink()
            except OSError:
                pass


def _save_temp(data: bytes, suffix: str) -> Path:
    fd, tmp = tempfile.mkstemp(suffix=suffix)
    Path(tmp).write_bytes(data)
    return Path(tmp)


def process_index(workspace: Path) -> list[dict[str, Any]]:
    """Convert every indexed source that lacks a .md file."""
    idx_path = workspace / "docs" / "index" / "papers-index.json"
    if not idx_path.exists():
        print("no papers-index.json found", file=sys.stderr)
        return []
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    results = []
    for bucket in ("papers", "web", "github"):
        for item in data.get(bucket, []):
            mid = item.get("id", "")
            if not mid:
                continue
            b = bucket if bucket != "papers" else "papers"
            r = process_source(workspace, item["source"], mid, b, item.get("title"))
            results.append(r)
    return results


def process_dir(
    workspace: Path, directory: Path, bucket: str | None = None
) -> list[dict[str, Any]]:
    """Batch-convert existing files in a directory (v1.4).

    Scans a directory for convertible files (.pdf, .docx, .html, etc.) that
    don't yet have a corresponding .md file, and converts them. The material ID
    is derived from the filename stem (e.g. 2506.23852.pdf → ID 2506.23852).

    This handles the common use case where a user has already downloaded a batch
    of PDFs (e.g. via curl/wget) and needs them converted to Markdown without
    re-downloading or manually scripting the conversion.

    Args:
        workspace: workspace root path
        directory: directory containing source files (e.g. materials/papers/)
        bucket: override bucket name; if None, inferred from directory name

    Returns:
        List of result dicts (one per file)
    """
    directory = directory.resolve()
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return []

    # Infer bucket from directory name if not specified
    if bucket is None:
        # materials/papers/ → "papers", materials/web/ → "web"
        try:
            rel = directory.relative_to(workspace / "materials")
            bucket = rel.parts[0] if rel.parts else "papers"
        except ValueError:
            bucket = "papers"

    # Find convertible files (exclude .md, .txt, .source.txt, .failed.txt)
    convertible_exts = ANYDOC_EXTS | {".html", ".htm"}
    skip_exts = MARKDOWN_EXTS | {".source.txt", ".failed.txt", ".json", ".ds_store"}

    results: list[dict[str, Any]] = []
    for src_file in sorted(directory.iterdir()):
        if not src_file.is_file():
            continue
        suffix = src_file.suffix.lower()
        # Skip already-markdown, text, and metadata files
        if suffix in skip_exts or src_file.name.startswith("."):
            continue
        if suffix not in convertible_exts:
            continue

        # Derive material ID from filename stem
        material_id = src_file.stem
        # For arXiv PDFs named like "2506.23852.pdf", the ID is "2506.23852"
        # For files named "P-001.pdf", the ID is "P-001"
        # Either way, the stem is the ID

        # Determine output path: materials/<bucket>/<ID>.md
        md_path = workspace / "materials" / bucket / f"{material_id}.md"

        # Skip if already converted
        if md_path.exists() and md_path.stat().st_size > 0:
            results.append(
                {
                    "id": material_id,
                    "status": "exists",
                    "path": str(md_path.relative_to(workspace)),
                    "source": str(src_file),
                }
            )
            continue

        # Convert using the existing convert() function
        failed_path = workspace / "materials" / "failed" / f"{material_id}.failed.txt"
        ok, method = convert(src_file, md_path, str(src_file))

        if ok:
            results.append(
                {
                    "id": material_id,
                    "status": "converted",
                    "method": method,
                    "path": str(md_path.relative_to(workspace)),
                    "source": str(src_file),
                }
            )
        else:
            write_text(
                failed_path,
                f"source: {src_file}\nid: {material_id}\nreason: {method}\n",
            )
            results.append(
                {
                    "id": material_id,
                    "status": "failed",
                    "reason": method,
                    "failed_path": str(failed_path.relative_to(workspace)),
                    "source": str(src_file),
                }
            )

    return results


# --- CLI ---------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description="OMR material → Markdown converter")
    p.add_argument("source", nargs="?", help="URL / DOI / arxiv / local path")
    p.add_argument("--id", help="material ID (e.g. P-001)")
    p.add_argument(
        "--bucket", default="papers", help="materials bucket (papers/web/github)"
    )
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    p.add_argument("--title", default=None)
    p.add_argument(
        "--index", action="store_true", help="convert all indexed sources lacking .md"
    )
    p.add_argument(
        "--convert-dir",
        type=Path,
        default=None,
        help="(v1.4) batch convert existing files in a directory (e.g. materials/papers/)",
    )
    args = p.parse_args()

    ws = args.workspace.resolve()

    if args.convert_dir is not None:
        results = process_dir(
            ws, args.convert_dir, args.bucket if args.bucket != "papers" else None
        )
        print(json.dumps({"converted": results}, indent=2))
        return 0

    if args.index:
        results = process_index(ws)
        print(json.dumps({"converted": results}, indent=2))
        return 0

    if not args.source or not args.id:
        p.error("source and --id are required (or use --index / --convert-dir)")

    r = process_source(ws, args.source, args.id, args.bucket, args.title)
    print(json.dumps(r, indent=2))
    return 0 if r["status"] in ("converted", "exists") else 1


if __name__ == "__main__":
    sys.exit(main())
