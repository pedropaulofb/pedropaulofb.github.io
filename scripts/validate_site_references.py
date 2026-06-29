#!/usr/bin/env python3
"""Validate website metadata, semantic profiles, publication entries, and references.

This repository intentionally keeps the website small and manually curated. The
validator adds lightweight, dependency-free safeguards around that model:
metadata consistency, selected-publication structure, internal links, semantic
profile exposure, and optional external HTTP reference checks.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as _dt
import html.parser
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

EXPECTED_SITE_URL = "https://pedropaulofb.github.io/"
EXPECTED_PERSON_ID = "https://pedropaulofb.github.io/profile.jsonld#person"
EXPECTED_PROFILE_JSONLD = "docs/profile.jsonld"
EXPECTED_PROFILE_TTL = "docs/profile.ttl"
EXPECTED_MAIN_PAGES = {
    "index.md": "https://pedropaulofb.github.io/#profile-page",
    "about.md": "https://pedropaulofb.github.io/about/#webpage",
    "expertise.md": "https://pedropaulofb.github.io/expertise/#webpage",
    "projects.md": "https://pedropaulofb.github.io/projects/#webpage",
    "publications.md": "https://pedropaulofb.github.io/publications/#webpage",
    "contact.md": "https://pedropaulofb.github.io/contact/#webpage",
}
EXPECTED_IDENTITY_URLS = {
    "https://orcid.org/0000-0003-2736-7817",
    "https://dblp.org/pid/96/8280",
    "https://scholar.google.com/citations?user=1kF9FGwAAAAJ",
    "https://www.linkedin.com/in/pedro-paulo-favato-barcelos/",
    "https://github.com/pedropaulofb/",
    "https://w3id.org/pedropaulofb/orcid",
    "https://w3id.org/pedropaulofb/scholar",
    "https://w3id.org/pedropaulofb/linkedin",
    "https://w3id.org/pedropaulofb/github",
}
EXPECTED_PUBLICATION_PROFILE_URLS = {
    "https://w3id.org/pedropaulofb/scholar",
    "https://w3id.org/pedropaulofb/orcid",
    "https://dblp.org/pid/96/8280",
}
STATUS_SENSITIVE_URL_MARKERS = (
    "accepted-submissions",
    "programme/accepted-submissions",
)
REQUIRED_PUBLICATION_FIELDS = ("**Citation:**", "**Link:**", "**Technical relevance:**")

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MARKDOWN_LINK_WITH_LABEL_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RAW_HTTP_RE = re.compile(r"(?<!\()https?://[^\s<>)\]\"'`]+")
PUBLICATION_ENTRY_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
DOI_URL_RE = re.compile(r"^https://doi\.org/10\.\S+/.+", re.IGNORECASE)
YEAR_RE = re.compile(r"\((?:19|20)\d{2}\)")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b", re.IGNORECASE)


@dataclasses.dataclass(frozen=True)
class Finding:
    level: str
    category: str
    path: str
    line: int | None
    message: str

    def sort_key(self) -> tuple[str, str, int, str]:
        order = {"error": "0", "warning": "1", "info": "2"}
        return (order.get(self.level, "9"), self.path, self.line or 0, self.message)


@dataclasses.dataclass(frozen=True)
class LinkRef:
    source_path: Path
    line: int
    url: str


@dataclasses.dataclass(frozen=True)
class PublicationEntry:
    title: str
    body: str
    start_line: int


class LinkHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key.lower() in {"href", "src"} and value:
                self.urls.append(value)


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def add(findings: list[Finding], level: str, category: str, path: str, message: str, line: int | None = None) -> None:
    findings.append(Finding(level=level, category=category, path=path, line=line, message=message))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def iter_source_files(root: Path) -> Iterable[Path]:
    patterns = (
        "README.md",
        "CITATION.cff",
        "mkdocs.yml",
        "docs/**/*.md",
        "docs/**/*.jsonld",
        "docs/**/*.ttl",
        "overrides/**/*.html",
    )
    for pattern in patterns:
        yield from sorted(root.glob(pattern))


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def is_external(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"}


def is_skipped_scheme(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"mailto", "tel"}


def strip_fragment_and_query(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed._replace(query="", fragment=""))


def collect_links(root: Path, findings: list[Finding]) -> list[LinkRef]:
    links: list[LinkRef] = []
    for path in iter_source_files(root):
        if not path.exists():
            continue
        text = read_text(path)
        path_rel = rel(path, root)
        if path.suffix.lower() in {".md", ".yml", ".yaml", ".jsonld", ".ttl", ".cff"}:
            for match in MARKDOWN_LINK_RE.finditer(text):
                links.append(LinkRef(path, line_number_for_offset(text, match.start(1)), match.group(1)))
            for match in RAW_HTTP_RE.finditer(text):
                links.append(LinkRef(path, line_number_for_offset(text, match.start(0)), match.group(0).rstrip(".,;:`")))
        if path.suffix.lower() == ".html":
            parser = LinkHTMLParser()
            try:
                parser.feed(text)
            except html.parser.HTMLParseError as exc:  # pragma: no cover; defensive for older Python behavior
                add(findings, "warning", "html", path_rel, f"Could not fully parse HTML for link extraction: {exc}")
            for url in parser.urls:
                links.append(LinkRef(path, 1, url))
    return links


def parse_mkdocs_nav_paths(mkdocs_text: str) -> list[str]:
    paths: list[str] = []
    for line in mkdocs_text.splitlines():
        match = re.match(r"\s*-\s+[^:]+:\s+([^#\s]+\.md)\s*$", line)
        if match:
            paths.append(match.group(1))
    return paths


def parse_mkdocs_social_links(mkdocs_text: str) -> set[str]:
    return set(re.findall(r"\blink:\s+(https?://\S+|mailto:\S+)", mkdocs_text))


def validate_required_paths(root: Path, findings: list[Finding]) -> None:
    required = [
        "mkdocs.yml",
        "README.md",
        "docs/index.md",
        "docs/about.md",
        "docs/expertise.md",
        "docs/projects.md",
        "docs/publications.md",
        "docs/contact.md",
        EXPECTED_PROFILE_JSONLD,
        EXPECTED_PROFILE_TTL,
        "overrides/main.html",
        "scripts/generate_profile_ttl.py",
    ]
    for item in required:
        if not (root / item).exists():
            add(findings, "error", "required-file", item, "Required website or validation file is missing.")


def validate_mkdocs(root: Path, findings: list[Finding]) -> dict[str, object]:
    mkdocs_path = root / "mkdocs.yml"
    if not mkdocs_path.exists():
        return {"nav_paths": [], "social_links": set()}

    text = read_text(mkdocs_path)
    nav_paths = parse_mkdocs_nav_paths(text)
    social_links = parse_mkdocs_social_links(text)

    if f"site_url: {EXPECTED_SITE_URL}" not in text:
        add(findings, "error", "mkdocs", "mkdocs.yml", f"Expected site_url to be {EXPECTED_SITE_URL}.")

    for nav_path in nav_paths:
        if not (root / "docs" / nav_path).exists():
            add(findings, "error", "mkdocs", "mkdocs.yml", f"Navigation target does not exist: docs/{nav_path}")

    expected_social = {
        "https://w3id.org/pedropaulofb/linkedin",
        "https://w3id.org/pedropaulofb/email",
        "https://w3id.org/pedropaulofb/github",
        "https://w3id.org/pedropaulofb/scholar",
        "https://w3id.org/pedropaulofb/orcid",
    }
    missing_social = sorted(expected_social - social_links)
    for url in missing_social:
        add(findings, "warning", "mkdocs", "mkdocs.yml", f"Expected stable social/profile redirect missing from MkDocs social links: {url}")

    return {"nav_paths": nav_paths, "social_links": social_links}


def load_profile_jsonld(root: Path, findings: list[Finding]) -> dict | None:
    profile_path = root / EXPECTED_PROFILE_JSONLD
    if not profile_path.exists():
        return None
    try:
        return json.loads(read_text(profile_path))
    except json.JSONDecodeError as exc:
        add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, f"Invalid JSON-LD: {exc}", exc.lineno)
        return None


def graph_nodes(profile: dict) -> list[dict]:
    graph = profile.get("@graph", [])
    return [node for node in graph if isinstance(node, dict)]


def node_by_id(nodes: list[dict], node_id: str) -> dict | None:
    return next((node for node in nodes if node.get("@id") == node_id), None)


def as_url_set(values: object) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {value for value in values if isinstance(value, str)}


def validate_profile_jsonld(root: Path, findings: list[Finding]) -> None:
    profile = load_profile_jsonld(root, findings)
    if profile is None:
        return

    nodes = graph_nodes(profile)
    person = node_by_id(nodes, EXPECTED_PERSON_ID)
    if person is None:
        add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, f"Missing canonical Person node: {EXPECTED_PERSON_ID}")
        return

    for key in ("name", "givenName", "familyName", "jobTitle", "description", "url", "sameAs", "identifier", "knowsAbout", "subjectOf"):
        if key not in person:
            add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, f"Person node is missing required property: {key}")

    same_as = as_url_set(person.get("sameAs"))
    for url in sorted(EXPECTED_IDENTITY_URLS - same_as):
        add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, f"Person sameAs is missing expected identity URL: {url}")

    website = node_by_id(nodes, "https://pedropaulofb.github.io/#website")
    if website is None:
        add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, "Missing WebSite node.")
    elif website.get("url") != EXPECTED_SITE_URL:
        add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, f"WebSite URL should be {EXPECTED_SITE_URL}.")

    node_ids = {node.get("@id") for node in nodes}
    for source_page, expected_id in EXPECTED_MAIN_PAGES.items():
        if expected_id not in node_ids:
            add(findings, "error", "jsonld", EXPECTED_PROFILE_JSONLD, f"Missing page entity for docs/{source_page}: {expected_id}")


def validate_profile_ttl(root: Path, findings: list[Finding]) -> None:
    ttl_path = root / EXPECTED_PROFILE_TTL
    if not ttl_path.exists():
        add(findings, "error", "semantic-profile", EXPECTED_PROFILE_TTL, "Turtle profile is missing.")
        return

    text = read_text(ttl_path)
    required_snippets = [
        "@prefix schema:",
        "@prefix foaf:",
        "@prefix dcterms:",
        f"<{EXPECTED_PERSON_ID}>",
        "<https://pedropaulofb.github.io/profile.ttl>",
        "@prefix schema:",
        "@prefix foaf:",
        "@prefix dcterms:",
        "@prefix xsd:",
        "schema:Person",
        "foaf:Person",
        "schema:sameAs",
        "Generated from docs/profile.jsonld by scripts/generate_profile_ttl.py",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            add(findings, "error", "semantic-profile", EXPECTED_PROFILE_TTL, f"Turtle profile is missing required snippet: {snippet}")

    for url in sorted(EXPECTED_IDENTITY_URLS):
        if f"<{url}>" not in text:
            add(findings, "warning", "semantic-profile", EXPECTED_PROFILE_TTL, f"Turtle profile does not contain expected identity URL: {url}")


def validate_template_metadata(root: Path, findings: list[Finding]) -> None:
    template_path = root / "overrides/main.html"
    if not template_path.exists():
        return
    text = read_text(template_path)
    checks = [
        ("profile.jsonld", "JSON-LD alternate profile link"),
        ("application/ld+json", "JSON-LD alternate content type or homepage JSON-LD script type"),
        ("profile.ttl", "Turtle alternate profile link"),
        ("text/turtle", "Turtle alternate content type"),
    ]
    for snippet, description in checks:
        if snippet not in text:
            add(findings, "error", "template", "overrides/main.html", f"Template does not expose {description}.")


def extract_publication_entries(markdown: str) -> list[PublicationEntry]:
    entries: list[PublicationEntry] = []
    matches = list(PUBLICATION_ENTRY_RE.finditer(markdown))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        entries.append(
            PublicationEntry(
                title=match.group(1).strip(),
                body=markdown[start:end].strip(),
                start_line=line_number_for_offset(markdown, match.start()),
            )
        )
    return entries


def extract_markdown_links(markdown: str) -> list[tuple[str, str]]:
    return [(match.group(1).strip(), match.group(2).strip()) for match in MARKDOWN_LINK_WITH_LABEL_RE.finditer(markdown)]


def validate_publications(root: Path, findings: list[Finding]) -> list[PublicationEntry]:
    path = root / "docs/publications.md"
    path_label = "docs/publications.md"
    if not path.exists():
        return []

    text = read_text(path)
    entries = extract_publication_entries(text)

    if "# Publications" not in text:
        add(findings, "error", "publications", path_label, "Missing top-level `# Publications` heading.")
    if "## Selection focus" not in text:
        add(findings, "error", "publications", path_label, "Missing `## Selection focus` section explaining the selection logic.")
    if "It is not a complete publication list" not in text:
        add(findings, "warning", "publications", path_label, "Publication page should explicitly state that it is a selected, not complete, list.")

    for url in sorted(EXPECTED_PUBLICATION_PROFILE_URLS):
        if url not in text:
            add(findings, "error", "publications", path_label, f"Publication page is missing external publication-record link: {url}")

    if not entries:
        add(findings, "error", "publications", path_label, "No selected-publication entries found. Expected level-3 headings (`###`).")
        return []

    titles_seen: dict[str, int] = {}
    for entry in entries:
        title_key = entry.title.casefold()
        if title_key in titles_seen:
            add(
                findings,
                "error",
                "publications",
                path_label,
                f"Duplicate publication heading: {entry.title!r}; first occurrence at line {titles_seen[title_key]}.",
                entry.start_line,
            )
        else:
            titles_seen[title_key] = entry.start_line

        for label in REQUIRED_PUBLICATION_FIELDS:
            if label not in entry.body:
                add(findings, "error", "publications", path_label, f"Publication entry '{entry.title}' is missing {label}", entry.start_line)

        if PLACEHOLDER_RE.search(entry.body):
            add(findings, "error", "publications", path_label, f"Publication entry '{entry.title}' contains a placeholder marker such as TODO/TBD/FIXME.", entry.start_line)

        if not YEAR_RE.search(entry.body):
            add(findings, "warning", "publications", path_label, f"Publication entry '{entry.title}' has no parenthesized publication year in its citation block.", entry.start_line)

        links = extract_markdown_links(entry.body)
        if not links:
            add(findings, "error", "publications", path_label, f"Publication entry '{entry.title}' has no Markdown link in its link block.", entry.start_line)

        has_doi_link = False
        has_status_sensitive_link = False
        for label, url in links:
            if not is_external(url):
                add(findings, "warning", "publications", path_label, f"Publication entry '{entry.title}' has a non-external link target: {url}", entry.start_line)
            if label.casefold() == "doi":
                has_doi_link = True
                if not DOI_URL_RE.match(url):
                    add(findings, "error", "publications", path_label, f"Publication entry '{entry.title}' labels a link as DOI but the target is not a DOI URL: {url}", entry.start_line)
            if any(marker in url for marker in STATUS_SENSITIVE_URL_MARKERS):
                has_status_sensitive_link = True

        if not has_doi_link:
            if has_status_sensitive_link:
                add(findings, "warning", "publications", path_label, f"Publication entry '{entry.title}' uses a status-sensitive non-DOI link; review after venue publication.", entry.start_line)
            else:
                add(findings, "warning", "publications", path_label, f"Publication entry '{entry.title}' does not use a DOI link.", entry.start_line)

    structured_sources = [
        "publications.bib",
        "docs/publications.bib",
        "publications.csl.json",
        "docs/publications.csl.json",
        "publications.yml",
        "docs/publications.yml",
        "publications.yaml",
        "docs/publications.yaml",
        "publications.json",
        "docs/publications.json",
    ]
    for candidate in structured_sources:
        if (root / candidate).exists():
            add(findings, "warning", "publications", candidate, "Local structured publication source exists; confirm this is intentional and does not duplicate the curated Markdown source of truth.")

    return entries


def candidate_internal_paths(root: Path, source_path: Path, url: str) -> list[Path]:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    if not path or path == "/":
        return [root / "docs" / "index.md"]
    if path.startswith("/"):
        raw = path.lstrip("/")
        base = root / "docs" / raw
    else:
        base = (source_path.parent / path).resolve()

    candidates = [base]
    if base.suffix == "":
        candidates.extend([
            base.with_suffix(".md"),
            base / "index.md",
            base.with_suffix(".jsonld"),
            base.with_suffix(".ttl"),
        ])
    if str(base).endswith(os.sep):
        candidates.append(base / "index.md")
    return candidates


def validate_internal_links(root: Path, links: list[LinkRef], findings: list[Finding]) -> None:
    for link in links:
        url = link.url.strip()
        if not url or url.startswith("#") or is_external(url) or is_skipped_scheme(url):
            continue
        if url.startswith("{") or url.startswith("{{") or url.startswith("{%"):
            continue
        if url.startswith("javascript:"):
            continue
        candidates = candidate_internal_paths(root, link.source_path, strip_fragment_and_query(url))
        if not any(candidate.exists() for candidate in candidates):
            add(
                findings,
                "error",
                "internal-link",
                rel(link.source_path, root),
                f"Internal link target does not resolve to a repository file: {url}",
                link.line,
            )


def external_urls(links: list[LinkRef]) -> list[str]:
    urls: set[str] = set()
    for link in links:
        url = link.url.rstrip(".,;:`")
        if is_external(url):
            urls.add(url)
    return sorted(urls)


def check_url(url: str, timeout: int) -> tuple[str, str, int | None, str]:
    headers = {
        "User-Agent": "pedropaulofb-site-maintenance-validator/1.0 (+https://pedropaulofb.github.io/)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return (url, "ok", response.status, response.geturl())
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in {405, 501, 403, 429}:
                continue
            return (url, "warning", exc.code, str(exc))
        except Exception as exc:  # noqa: BLE001 - network variability is reported, not hidden
            if method == "HEAD":
                continue
            return (url, "warning", None, str(exc))
    return (url, "warning", None, "No supported HTTP method succeeded.")


def validate_external_links(urls: list[str], findings: list[Finding], timeout: int, max_workers: int, fail_on_external_error: bool) -> None:
    if not urls:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda target: check_url(target, timeout), urls))
    for url, status, http_status, detail in results:
        if status == "ok":
            continue
        level = "error" if fail_on_external_error else "warning"
        status_text = f"HTTP {http_status}" if http_status else "no HTTP status"
        add(findings, level, "external-link", "external references", f"External reference check returned {status_text} for {url}: {detail}")


def validate_status_sensitive_links(root: Path, links: list[LinkRef], findings: list[Finding]) -> None:
    for link in links:
        # Publication entries already receive a publication-specific warning that
        # includes the entry title and review rationale. Avoid reporting the same
        # URL twice in normal validation output.
        if rel(link.source_path, root) == "docs/publications.md":
            continue
        if any(marker in link.url for marker in STATUS_SENSITIVE_URL_MARKERS):
            add(
                findings,
                "warning",
                "external-link",
                rel(link.source_path, root),
                f"Status-sensitive external reference should be reviewed periodically: {link.url}",
                link.line,
            )


def render_report(findings: list[Finding], links: list[LinkRef], publication_entries: list[PublicationEntry], checked_external: bool) -> str:
    now = _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat()
    counts = {level: sum(1 for finding in findings if finding.level == level) for level in ("error", "warning", "info")}
    unique_external = external_urls(links)
    publication_findings = [finding for finding in findings if finding.category == "publications"]
    status_sensitive = sorted({link.url for link in links if any(marker in link.url for marker in STATUS_SENSITIVE_URL_MARKERS)})

    lines = [
        "# Site maintenance validation report",
        "",
        f"Generated: `{now}`",
        "",
        "## Summary",
        "",
        f"- Errors: {counts['error']}",
        f"- Warnings: {counts['warning']}",
        f"- Informational notes: {counts['info']}",
        f"- Selected publication entries: {len(publication_entries)}",
        f"- Publication-specific findings: {len(publication_findings)}",
        f"- External URLs inventoried: {len(unique_external)}",
        f"- External URLs checked over HTTP: {'yes' if checked_external else 'no'}",
        "",
        "## Publication maintenance model",
        "",
        "`docs/publications.md` remains the manually curated source of truth. External scholarly profiles and DOI/publisher/conference pages are authority checks, not generation sources.",
        "",
        "| Option | Decision | Reason |",
        "|---|---|---|",
        "| Manual Markdown | Keep as source of truth | Preserves selection logic, hand-written context, and low maintenance overhead. |",
        "| BibTeX-backed generation | Defer | Would add a bibliography dependency and duplicate external scholarly metadata for a small curated page. |",
        "| ORCID-backed import | Defer | Useful as an authority check, but too broad for selected-publication curation. |",
        "| YAML/JSON-backed local data | Defer | Could improve consistency later, but currently duplicates visible Markdown content without enough benefit. |",
        "| Hybrid curated model | Use lightly | Keep manual Markdown and add validation/reporting for repeated citation, link, DOI, and relevance structure. |",
        "",
        "## Selected publication entries",
        "",
    ]

    if publication_entries:
        for entry in publication_entries:
            lines.append(f"- Line {entry.start_line}: {entry.title}")
    else:
        lines.append("None found.")
    lines.append("")

    for level in ("error", "warning", "info"):
        selected = sorted([finding for finding in findings if finding.level == level], key=lambda item: item.sort_key())
        title = level.capitalize() + "s"
        lines.extend([f"## {title}", ""])
        if not selected:
            lines.extend(["None.", ""])
            continue
        for finding in selected:
            loc = finding.path
            if finding.line:
                loc += f":{finding.line}"
            lines.append(f"- **{finding.category}** `{loc}` - {finding.message}")
        lines.append("")

    lines.extend(["## Status-sensitive references", ""])
    if status_sensitive:
        for url in status_sensitive:
            lines.append(f"- {url}")
    else:
        lines.append("None identified.")
    lines.append("")

    lines.extend(["## External URL inventory", ""])
    if unique_external:
        for url in unique_external:
            lines.append(f"- {url}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    findings: list[Finding] = []

    if not root.exists():
        print(f"Repository root does not exist: {root}", file=sys.stderr)
        return 2

    validate_required_paths(root, findings)
    validate_mkdocs(root, findings)
    validate_profile_jsonld(root, findings)
    validate_profile_ttl(root, findings)
    validate_template_metadata(root, findings)
    publication_entries = validate_publications(root, findings)

    links = collect_links(root, findings)
    validate_internal_links(root, links, findings)
    validate_status_sensitive_links(root, links, findings)

    if args.check_external:
        validate_external_links(
            external_urls(links),
            findings,
            timeout=args.external_timeout,
            max_workers=args.max_workers,
            fail_on_external_error=args.fail_on_external_error,
        )
    else:
        add(findings, "info", "external-link", "external references", "External HTTP checks were skipped. Use --check-external to run them.")

    report = render_report(findings, links, publication_entries=publication_entries, checked_external=args.check_external)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    if not args.quiet:
        print(report)

    return 1 if any(finding.level == "error" for finding in findings) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root to validate. Default: current directory.")
    parser.add_argument("--report", help="Optional Markdown report output path.")
    parser.add_argument("--quiet", action="store_true", help="Do not print the Markdown report to stdout.")
    parser.add_argument("--check-external", action="store_true", help="Check external HTTP(S) links. External failures are warnings by default.")
    parser.add_argument("--fail-on-external-error", action="store_true", help="Treat external-link failures as errors.")
    parser.add_argument("--external-timeout", type=int, default=15, help="Timeout in seconds for each external URL check.")
    parser.add_argument("--max-workers", type=int, default=6, help="Maximum number of parallel external URL checks.")
    return parser


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
