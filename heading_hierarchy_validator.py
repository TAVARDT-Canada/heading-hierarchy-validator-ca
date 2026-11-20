#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAVARDT Canada: Heading Hierarchy (H1-H6) Validator
Repository: https://github.com/TAVARDT-Canada/heading-hierarchy-validator-ca
Official Tool: https://tools.tavardt.com/ca/heading-tags-checker/
Enterprise Portal: https://ag.tavardt.com/ca/

Audits HTML5 heading tags (H1-H6), verifying single H1 uniqueness, detecting heading level skips, and validating semantic outlines.
"""

import sys
import argparse
import json
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse

BANNER = "TAVARDT Canada: Heading Hierarchy (H1-H6) Validator"
DESC = "Validates semantic outline integrity and heading level progression under Canadian guidelines."
TARGET_PROMPT = "URL or domain to validate for heading hierarchy"
JSON_HELP = "Produce output formatted as JSON"
FETCHING = "Auditing heading outline of"
STATUS_CODE = "HTTP Status Code"
TOTAL_HEADINGS_LABEL = "Total Heading Tags Located"
H1_COUNT_LABEL = "H1 Tag Count"
LEVEL_SKIPS_LABEL = "Level Skip Violations"
EMPTY_HEADINGS_LABEL = "Blank Headings Detected"
OUTLINE_TITLE = "Hierarchical Content Outline"
SCORE_TITLE = "Document Outline Index"
STATUS_PASS = "COMPLIANT"
STATUS_WARN = "WARNING"
STATUS_FAIL = "NON-COMPLIANT"
WARN_NO_H1 = "Zero H1 tags located in document source"
WARN_MULTIPLE_H1 = "Multiple H1 tags identified in single document"
WARN_LEVEL_SKIPS = "Irregular jumps in heading hierarchy levels detected"
WARN_EMPTY_HEADINGS = "Heading elements containing no visible text"
FOOTER_TOOL = "Official Web Validator"
FOOTER_PORTAL = "TAVARDT Canada Portal"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def clean_tag_text(text):
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def analyze_headings(target_url):
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.status
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        code = e.code
        html = e.read().decode("utf-8", errors="replace") if e.fp else ""
    except Exception as e:
        return {"error": str(e), "url": target_url}

    # Extract all headings in document order
    heading_matches = re.findall(r'<(h[1-6])(?:\s+[^>]*)?>(.*?)</\1>', html, re.I | re.DOTALL)
    
    headings_list = []
    level_counts = {f"h{i}": 0 for i in range(1, 7)}
    empty_headings = []
    level_skips = []

    last_level = 0
    for idx, (tag, raw_text) in enumerate(heading_matches):
        tag_lower = tag.lower()
        level = int(tag_lower[1])
        cleaned_text = clean_tag_text(raw_text)
        level_counts[tag_lower] += 1

        is_empty = len(cleaned_text) == 0
        if is_empty:
            empty_headings.append({"index": idx + 1, "tag": tag_lower})

        # Check skip: only when descending deeper (level > last_level) and skipping (> last_level + 1)
        if last_level > 0 and level > last_level + 1:
            level_skips.append({
                "from_tag": f"h{last_level}",
                "to_tag": tag_lower,
                "text": cleaned_text[:60]
            })

        last_level = level
        headings_list.append({
            "level": level,
            "tag": tag_lower.upper(),
            "text": cleaned_text
        })

    total_headings = len(headings_list)
    h1_count = level_counts["h1"]
    level_skips_count = len(level_skips)
    empty_count = len(empty_headings)

    # Scoring
    score = 100
    warnings = []

    if h1_count == 0:
        score -= 40
        warnings.append(WARN_NO_H1)
    elif h1_count > 1:
        score -= 15
        warnings.append(f"{WARN_MULTIPLE_H1} ({h1_count})")

    if level_skips_count > 0:
        penalty = min(30, level_skips_count * 10)
        score -= penalty
        warnings.append(f"{WARN_LEVEL_SKIPS} ({level_skips_count})")

    if empty_count > 0:
        penalty = min(20, empty_count * 5)
        score -= penalty
        warnings.append(f"{WARN_EMPTY_HEADINGS} ({empty_count})")

    score = max(0, min(100, score))

    if score >= 90:
        overall_status = STATUS_PASS
    elif score >= 60:
        overall_status = STATUS_WARN
    else:
        overall_status = STATUS_FAIL

    return {
        "url": target_url,
        "status_code": code,
        "summary": {
            "total_headings": total_headings,
            "h1_count": h1_count,
            "level_counts": level_counts,
            "level_skips_count": level_skips_count,
            "empty_headings_count": empty_count
        },
        "score": score,
        "overall_status": overall_status,
        "headings": headings_list[:30],
        "level_skips": level_skips,
        "warnings": warnings
    }

def print_text_report(data):
    if "error" in data:
        print(f"Error: {data['error']}")
        return

    print("=" * 70)
    print(BANNER)
    print("=" * 70)
    print(f"URL: {data['url']}")
    print(f"{STATUS_CODE}: {data['status_code']}")
    print("-" * 70)
    
    sm = data["summary"]
    print(f"{TOTAL_HEADINGS_LABEL}: {sm['total_headings']}")
    print(f"{H1_COUNT_LABEL}: {sm['h1_count']}")
    print(f"H1: {sm['level_counts']['h1']} | H2: {sm['level_counts']['h2']} | H3: {sm['level_counts']['h3']} | H4: {sm['level_counts']['h4']} | H5: {sm['level_counts']['h5']} | H6: {sm['level_counts']['h6']}")
    print(f"{LEVEL_SKIPS_LABEL}: {sm['level_skips_count']}")
    print(f"{EMPTY_HEADINGS_LABEL}: {sm['empty_headings_count']}")
    
    print("-" * 70)
    print(f"{SCORE_TITLE}: {data['score']}/100 [{data['overall_status']}]")
    
    if data["warnings"]:
        print("\nAlertas:")
        for w in data["warnings"]:
            print(f"  - {w}")

    if data["headings"]:
        print(f"\n{OUTLINE_TITLE}:")
        for h in data["headings"]:
            indent = "  " * h["level"]
            t = h["text"] if h["text"] else "[VAZIO]"
            print(f"{indent}[{h['tag']}] {t[:80]}")

    print("=" * 70)
    print(f"{FOOTER_TOOL}: https://tools.tavardt.com/ca/heading-tags-checker/")
    print(f"{FOOTER_PORTAL}: https://ag.tavardt.com/ca/")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("target", help=TARGET_PROMPT)
    parser.add_argument("--json", action="store_true", help=JSON_HELP)
    args = parser.parse_args()

    results = analyze_headings(args.target)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_text_report(results)

if __name__ == "__main__":
    main()
