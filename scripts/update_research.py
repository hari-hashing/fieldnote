#!/usr/bin/env python3
"""Incrementally ingest embodied-AI papers and write dated daily snapshots.

Sources:
  * arXiv Atom API (primary preprint metadata)
  * OpenReview API 2 (public venue/review records)
  * OpenAlex Works API (discovery only; primary-source verification required)

No credentials or third-party Python packages are required.
"""
from __future__ import annotations
import argparse
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
USER_AGENT = "Fieldnote-EmbodiedAI-ResearchAtlas/1.0 (academic research index; contact: repository maintainer)"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
WARNINGS: list[str] = []
RELEVANCE = re.compile(r"\b(robot|robotic|robotics|embodied|manipulation|vision.language.action|\bvla\b|world.action|world model|physical ai|humanoid|tactile|dexterous|navigation|autonomous driving|robot learning)\b", re.I)


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return ""


def request_text(url: str, timeout: int = 35, headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def request_json(url: str, timeout: int = 35) -> dict[str, Any]:
    return json.loads(request_text(url, timeout=timeout, headers={"Accept": "application/json"}))


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN: could not parse {path}: {exc}", file=sys.stderr)
        return fallback


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", value).strip()


def date_window(days: int) -> tuple[dt.date, dt.date]:
    end = utcnow().date()
    start = end - dt.timedelta(days=max(1, days) - 1)
    return start, end


def arxiv_query(category: str, start: dt.date, end: dt.date) -> list[dict[str, Any]]:
    """Fetch a paginated arXiv query, respecting a modest request interval."""
    lo, hi = start.strftime("%Y%m%d0000"), end.strftime("%Y%m%d2359")
    date_expr = f"submittedDate:[{lo} TO {hi}]"
    query_map = {
        "cs.RO": f"cat:cs.RO AND {date_expr}",
        "cs.CV": f"cat:cs.CV AND (all:robot OR all:robotics OR all:embodied OR all:manipulation) AND {date_expr}",
        "cs.AI": f"cat:cs.AI AND (all:robot OR all:robotics OR all:embodied) AND {date_expr}",
        "cs.LG": f'cat:cs.LG AND (all:robot OR all:robotics OR all:embodied OR all:VLA OR all:"world model") AND {date_expr}',
        "all_vla": f'all:"vision-language-action" AND {date_expr}',
        "all_wam": f'all:"world action model" AND {date_expr}',
        "all_robot_world": f'all:"robot world model" AND {date_expr}',
    }
    query = query_map.get(category, f"cat:{category} AND {date_expr}")
    results: list[dict[str, Any]] = []
    page_size = 200
    max_results = 1000  # Per query; the rolling window keeps the normal volume far below this cap.
    for page_start in range(0, max_results, page_size):
        params = urllib.parse.urlencode({
            "search_query": query,
            "start": page_start,
            "max_results": page_size,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        url = "https://export.arxiv.org/api/query?" + params
        try:
            xml = request_text(url, timeout=60)
            root = ET.fromstring(xml)
            entries = root.findall("a:entry", NS)
            for entry in entries:
                raw_id = (entry.findtext("a:id", default="", namespaces=NS)).strip()
                match = re.search(r"abs/([^/?]+)", raw_id)
                if not match:
                    continue
                paper_id = re.sub(r"v\d+$", "", match.group(1))
                title = clean_text(entry.findtext("a:title", default="", namespaces=NS))
                abstract = clean_text(entry.findtext("a:summary", default="", namespaces=NS))
                published = entry.findtext("a:published", default="", namespaces=NS)
                updated = entry.findtext("a:updated", default="", namespaces=NS)
                authors = [clean_text(x.findtext("a:name", default="", namespaces=NS)) for x in entry.findall("a:author", NS)]
                categories = [x.attrib.get("term", "") for x in entry.findall("a:category", NS)]
                journal_ref = clean_text(entry.findtext("arxiv:journal_ref", default="", namespaces=NS))
                doi = clean_text(entry.findtext("arxiv:doi", default="", namespaces=NS))
                links = entry.findall("a:link", NS)
                pdf = next((x.attrib.get("href") for x in links if x.attrib.get("title") == "pdf"), f"https://arxiv.org/pdf/{paper_id}")
                results.append({
                    "id": paper_id, "title": title, "authors": ", ".join(authors[:8]) + (", et al." if len(authors) > 8 else ""),
                    "first_published": iso_date(published), "latest_revision": iso_date(updated),
                    "year": int(published[:4]) if published[:4].isdigit() else None,
                    "abstract": abstract, "paper_url": f"https://arxiv.org/abs/{paper_id}", "pdf_url": pdf,
                    "doi": doi, "journal_ref": journal_ref, "categories": categories,
                    "source": "arXiv", "source_type": "primary", "status": "preprint",
                    "venue": f"Journal reference: {journal_ref}" if journal_ref else "Preprint",
                })
            if len(entries) < page_size:
                break
            if page_start + page_size >= max_results:
                msg = f"arXiv {category} query reached pagination cap ({max_results}); further records may exist."
                WARNINGS.append(msg)
                print(f"WARN: {msg}", file=sys.stderr)
                break
        except Exception as exc:
            msg = f"arXiv {category} query failed at start={page_start}: {exc}"
            WARNINGS.append(msg)
            print(f"WARN: {msg}", file=sys.stderr)
            break
        time.sleep(3)  # arXiv asks clients to be considerate between consecutive calls.
    return results


def openreview_notes(start: dt.date, end: dt.date) -> list[dict[str, Any]]:
    """Discover recent public OpenReview notes; filter by original cdate locally."""
    found: list[dict[str, Any]] = []
    for offset in range(0, 1000, 100):
        params = urllib.parse.urlencode({"limit": 100, "offset": offset, "details": "replyCount"})
        try:
            payload = request_json("https://api2.openreview.net/notes?" + params, timeout=45)
        except Exception as exc:
            msg = f"OpenReview API query failed at offset {offset}: {exc}"
            WARNINGS.append(msg)
            print(f"WARN: {msg}", file=sys.stderr)
            break
        notes = payload.get("notes", [])
        if not notes:
            break
        for note in notes:
            content = note.get("content") or {}
            def val(key: str) -> Any:
                v = content.get(key, "")
                return v.get("value", "") if isinstance(v, dict) else v
            title = clean_text(str(val("title")))
            abstract = clean_text(str(val("abstract")))
            authors = val("authors")
            if isinstance(authors, list):
                authors = ", ".join(map(str, authors[:8]))
            cdate = note.get("cdate") or note.get("tmdate")
            try:
                published = dt.datetime.fromtimestamp(float(cdate) / 1000, tz=dt.timezone.utc).date().isoformat()
            except Exception:
                published = ""
            if published and not (start.isoformat() <= published <= end.isoformat()):
                continue
            if not (title and RELEVANCE.search(title + " " + abstract)):
                continue
            note_id = note.get("forum") or note.get("id") or ""
            invitation = note.get("invitation", "")
            decision = str(val("decision") or "")
            status = "accepted" if re.search(r"accept", decision, re.I) else "needs_verification"
            found.append({
                "id": f"openreview:{note_id}", "title": title, "authors": str(authors or "Authors not indexed"),
                "first_published": published, "year": int(published[:4]) if published else None,
                "abstract": abstract, "paper_url": f"https://openreview.net/forum?id={note_id}" if note_id else "https://openreview.net/",
                "code_url": "", "source": "OpenReview", "source_type": "primary", "status": status,
                "venue": invitation or "OpenReview record", "openreview_id": note_id,
            })
        if len(notes) < 100:
            break
    return found


def inverted_abstract(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    pairs: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions or []:
            pairs.append((int(pos), word))
    return " ".join(w for _, w in sorted(pairs))


def openalex_discovery(start: dt.date, end: dt.date) -> list[dict[str, Any]]:
    """Aggregator discovery only. Results remain flagged until verified at source."""
    found: list[dict[str, Any]] = []
    searches = [
        'vision language action robotics',
        'world action model robot embodied',
        'world model robot manipulation',
        'embodied foundation model humanoid robot',
    ]
    for search in searches:
        params = urllib.parse.urlencode({
            "search": search,
            "filter": f"from_publication_date:{start.isoformat()},to_publication_date:{end.isoformat()}",
            "per-page": 100,
            "sort": "publication_date:desc",
            "select": "id,doi,display_name,publication_date,authorships,primary_location,biblio,abstract_inverted_index,type",
        })
        try:
            payload = request_json("https://api.openalex.org/works?" + params, timeout=40)
        except Exception as exc:
            msg = f"OpenAlex discovery failed for {search!r}: {exc}"
            WARNINGS.append(msg)
            print(f"WARN: {msg}", file=sys.stderr)
            continue
        for work in payload.get("results", []):
            title = clean_text(work.get("display_name", ""))
            abstract = clean_text(inverted_abstract(work.get("abstract_inverted_index")))
            if not (title and RELEVANCE.search(title + " " + abstract)):
                continue
            date = work.get("publication_date", "")
            if date and not (start.isoformat() <= date <= end.isoformat()):
                continue
            authorships = work.get("authorships") or []
            authors = ", ".join((a.get("author") or {}).get("display_name", "") for a in authorships[:8])
            loc = work.get("primary_location") or {}
            source = loc.get("source") or {}
            venue = source.get("display_name", "") if isinstance(source, dict) else ""
            landing = loc.get("landing_page_url") or work.get("doi") or work.get("id")
            found.append({
                "id": work.get("doi") or work.get("id"), "title": title, "authors": authors,
                "first_published": date, "year": int(date[:4]) if date[:4].isdigit() else None,
                "abstract": abstract, "paper_url": landing, "doi": work.get("doi", ""),
                "source": "OpenAlex discovery", "source_type": "aggregator_discovery",
                "status": "needs_verification", "venue": venue or "Venue needs verification",
                "notes": "Discovery record only. Verify title, date, venue and claims at the publisher/preprint source before treating as confirmed.",
            })
        time.sleep(0.5)
    return found


def load_taxonomy() -> list[dict[str, Any]]:
    return read_json(DATA / "taxonomy.json", [])


def classify(paper: dict[str, Any], taxonomy: list[dict[str, Any]]) -> dict[str, Any]:
    text = " ".join([
        paper.get("title", ""), paper.get("abstract", ""), paper.get("venue", ""),
        " ".join(paper.get("categories", []) or []),
    ]).lower()
    scores: list[tuple[int, str]] = []
    for b in taxonomy:
        score = sum(1 for kw in b.get("keywords", []) if kw.lower() in text)
        scores.append((score, b["id"]))
    scores.sort(reverse=True)
    existing = paper.get("primary_bin")
    if existing in {b["id"] for b in taxonomy}:
        primary = existing
    else:
        primary = scores[0][1] if scores and scores[0][0] else "embodiment"
    secondary = [bid for score, bid in scores if score > 0 and bid != primary][:5]
    paper["primary_bin"] = primary
    paper["secondary_bins"] = sorted(set((paper.get("secondary_bins") or []) + secondary))
    if not paper.get("tags"):
        paper["tags"] = ["auto-classified"]
    if not paper.get("limitations"):
        paper["limitations"] = "Not extracted automatically. Read the full paper before drawing conclusions."
    if not paper.get("datasets"):
        paper["datasets"] = []
    if not paper.get("embodiments"):
        paper["embodiments"] = []
    if not paper.get("real_robot"):
        paper["real_robot"] = "Not established; verify full text."
    if not paper.get("code_url"):
        m = re.search(r"https?://github\.com/[\w.-]+/[\w.-]+", paper.get("abstract", ""))
        paper["code_url"] = m.group(0).rstrip(".,)") if m else ""
    return paper


def paper_key(p: dict[str, Any]) -> str:
    pid = str(p.get("id", "")).strip().lower()
    if pid:
        return pid
    doi = str(p.get("doi", "")).strip().lower()
    if doi:
        return doi
    return re.sub(r"[^a-z0-9]+", "", p.get("title", "").lower())


def merge_papers(existing: list[dict[str, Any]], incoming: list[dict[str, Any]], taxonomy: list[dict[str, Any]], today: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    index = {paper_key(p): p for p in existing if paper_key(p)}
    title_index = {re.sub(r"[^a-z0-9]+", "", p.get("title", "").lower()): paper_key(p) for p in existing if p.get("title") and paper_key(p)}
    newly_added: list[dict[str, Any]] = []
    for raw in incoming:
        if not RELEVANCE.search(raw.get("title", "") + " " + raw.get("abstract", "")):
            continue
        p = classify(dict(raw), taxonomy)
        key = paper_key(p)
        if not key:
            continue
        title_key = re.sub(r"[^a-z0-9]+", "", p.get("title", "").lower())
        # Cross-source duplicate guard: OpenReview and arXiv often index the same title under different IDs.
        if key not in index and title_key in title_index:
            key = title_index[title_key]
        if key in index:
            old = index[key]
            # Preserve curated annotations while refreshing source metadata.
            for field in ("title", "authors", "abstract", "latest_revision", "venue", "doi", "paper_url", "pdf_url", "code_url"):
                if p.get(field) and (not old.get(field) or field in ("latest_revision", "venue")):
                    old[field] = p[field]
            old["last_seen"] = today
            old["sources_seen"] = sorted(set(old.get("sources_seen", [old.get("source", "")])) | {p.get("source", "")})
            index[key] = old
            title_index[title_key] = key
        else:
            p["added_at"] = today
            p["last_seen"] = today
            p["sources_seen"] = [p.get("source", "")]
            index[key] = p
            title_index[title_key] = key
            newly_added.append(p)
    all_papers = list(index.values())
    all_papers.sort(key=lambda x: (x.get("first_published") or "", x.get("title", "")), reverse=True)
    return all_papers, newly_added


def update_opportunities(all_papers: list[dict[str, Any]]) -> dict[str, Any]:
    path = DATA / "opportunities.json"
    obj = read_json(path, {"opportunities": []})
    opps = obj.get("opportunities", [])
    for o in opps:
        bins = o.get("bins", [])
        coverage = 0
        for p in all_papers:
            p_bins = set([p.get("primary_bin")] + (p.get("secondary_bins") or []))
            if len(set(bins) & p_bins) >= min(2, len(bins)):
                coverage += 1
        # Explicitly an index-coverage heuristic, not a novelty estimate.
        gap = max(8, min(98, 100 - 7 * coverage))
        feasibility = int(o.get("feasibility", 65))
        o["coverage_count"] = coverage
        o["gap_score"] = gap
        o["score"] = round(0.55 * gap + 0.45 * feasibility)
    obj["generated_at"] = utcnow().isoformat()
    obj["method"] = "Rule-based intersection scoring using paper coverage in primary and secondary taxonomy bins. Scores indicate underrepresentation in this local index, not verified novelty."
    return obj


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="Look-back window in days (default: 7).")
    parser.add_argument("--skip-openalex", action="store_true", help="Skip OpenAlex discovery if rate-limited or unavailable.")
    parser.add_argument("--skip-openreview", action="store_true", help="Skip OpenReview discovery.")
    args = parser.parse_args()

    start, end = date_window(args.days)
    today = end.isoformat()
    taxonomy = load_taxonomy()
    current = read_json(DATA / "papers.json", {"papers": [], "sources": {}})
    existing = current.get("papers", [])
    incoming: list[dict[str, Any]] = []
    source_counts = {"arxiv": 0, "openreview": 0, "openalex_discovery": 0}
    warnings = WARNINGS

    for cat in ("cs.RO", "cs.CV", "cs.AI", "cs.LG", "all_vla", "all_wam", "all_robot_world"):
        rows = arxiv_query(cat, start, end)
        source_counts["arxiv"] += len(rows)
        incoming.extend(rows)
    if not args.skip_openreview:
        rows = openreview_notes(start, end)
        source_counts["openreview"] = len(rows)
        incoming.extend(rows)
    if not args.skip_openalex:
        rows = openalex_discovery(start, end)
        source_counts["openalex_discovery"] = len(rows)
        incoming.extend(rows)

    all_papers, new_papers = merge_papers(existing, incoming, taxonomy, today)
    now = utcnow().isoformat()
    current["schema_version"] = 1
    current["generated_at"] = now
    current["last_ingestion"] = now
    current["sources"] = source_counts
    current["papers"] = all_papers
    write_json(DATA / "papers.json", current)

    # Archive is a dated seven-day snapshot, not merely the delta, so it remains interpretable later.
    in_window = [p for p in all_papers if p.get("first_published") and start.isoformat() <= p["first_published"] <= end.isoformat()]
    in_window.sort(key=lambda x: (x.get("first_published") or "", x.get("title", "")), reverse=True)
    archive = {
        "snapshot_date": today,
        "generated_at": now,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "paper_count": len(in_window),
        "new_to_index_count": len(new_papers),
        "source_counts": source_counts,
        "coverage_note": "Snapshot of records first published within the preceding window. Aggregator-discovered records remain marked for primary-source verification.",
        "warnings": warnings,
        "papers": in_window,
    }
    write_json(DATA / "archives" / f"{today}.json", archive)

    opp_obj = update_opportunities(all_papers)
    write_json(DATA / "opportunities.json", opp_obj)

    archive_paths = sorted((DATA / "archives").glob("*.json"), reverse=True)
    manifest = {"generated_at": now, "archives": []}
    for p in archive_paths:
        item = read_json(p, {})
        manifest["archives"].append({"date": item.get("snapshot_date", p.stem), "file": f"data/archives/{p.name}", "paper_count": item.get("paper_count", len(item.get("papers", []))), "period": f"{item.get('period_start','')} → {item.get('period_end','')}"})
    write_json(DATA / "manifest.json", manifest)

    print(f"Window: {start} to {end}")
    print(f"New to index: {len(new_papers)} | Indexed total: {len(all_papers)}")
    print(f"Source discovery counts: {json.dumps(source_counts)}")
    print("Archive and opportunity scores updated.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
