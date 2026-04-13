#!/usr/bin/env python3
"""Simple crawling agent that collects emails and phone numbers from web pages.

Usage:
  python contact_collector_agent.py --start-url https://example.com --max-pages 20
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4})")
FACEBOOK_PROFILE_RE = re.compile(
    r"(?:facebook\.com/(?:profile\.php\?id=\d+|user/\d+|people/[^/?]+/\d+|[A-Za-z0-9.]{3,}))/?$"
)


@dataclass
class CrawlResult:
    url: str
    emails: Set[str]
    phones: Set[str]
    is_profile: bool


def normalize_phone(value: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", value)
    if cleaned.startswith("1") and len(cleaned) == 11:
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+") and len(cleaned) == 10:
        cleaned = "+1" + cleaned
    return cleaned


def extract_contacts(text: str) -> tuple[Set[str], Set[str]]:
    emails = {match.lower() for match in EMAIL_RE.findall(text)}
    phones = {normalize_phone(match) for match in PHONE_RE.findall(text)}
    phones = {p for p in phones if 10 <= len(re.sub(r"\D", "", p)) <= 15}
    return emails, phones


def extract_contacts_from_soup(soup: BeautifulSoup) -> tuple[Set[str], Set[str]]:
    emails: Set[str] = set()
    phones: Set[str] = set()
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        if href.startswith("mailto:"):
            emails.add(href.replace("mailto:", "").split("?", 1)[0].strip().lower())
        if href.startswith("tel:"):
            phones.add(normalize_phone(href.replace("tel:", "").split("?", 1)[0].strip()))
    return emails, {p for p in phones if 10 <= len(re.sub(r"\D", "", p)) <= 15}


def same_domain(start_url: str, candidate_url: str) -> bool:
    return urlparse(start_url).netloc == urlparse(candidate_url).netloc


def is_facebook_profile_url(url: str) -> bool:
    parsed = urlparse(url)
    query = f"?{parsed.query}" if parsed.query else ""
    return bool(FACEBOOK_PROFILE_RE.search(f"{parsed.netloc}{parsed.path}{query}"))


def discover_links(url: str, html: str) -> Iterable[str]:
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.select("a[href]"):
        joined = urljoin(url, anchor.get("href", ""))
        parsed = urlparse(joined)
        if parsed.scheme in {"http", "https"}:
            yield joined.split("#", 1)[0]


def read_cookies_json(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(content, dict):
        return {str(k): str(v) for k, v in content.items()}
    if isinstance(content, list):
        parsed: dict[str, str] = {}
        for cookie in content:
            if isinstance(cookie, dict) and cookie.get("name") and cookie.get("value"):
                parsed[str(cookie["name"])] = str(cookie["value"])
        return parsed
    return {}


def crawl(start_url: str, max_pages: int, timeout: int, stay_on_domain: bool, profile_only: bool, cookies_json: str | None) -> list[CrawlResult]:
    seen: Set[str] = set()
    queue = deque([start_url])
    results: list[CrawlResult] = []

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ContactCollectorBot/1.0 (+https://example.com/bot-info)",
        }
    )
    cookie_map = read_cookies_json(cookies_json)
    if cookie_map:
        session.cookies.update(cookie_map)

    while queue and len(seen) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        text_emails, text_phones = extract_contacts(response.text)
        link_emails, link_phones = extract_contacts_from_soup(soup)
        emails = text_emails | link_emails
        phones = text_phones | link_phones
        is_profile = is_facebook_profile_url(url)
        if not profile_only or is_profile:
            results.append(CrawlResult(url=url, emails=emails, phones=phones, is_profile=is_profile))

        for link in discover_links(url, response.text):
            if link in seen:
                continue
            if stay_on_domain and not same_domain(start_url, link):
                continue
            if profile_only:
                if is_facebook_profile_url(link):
                    queue.appendleft(link)
                else:
                    queue.append(link)
            else:
                queue.append(link)

    return results


def write_csv(results: list[CrawlResult], output_file: str) -> None:
    with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["url", "is_profile", "emails", "phones"])
        for row in results:
            writer.writerow(
                [
                    row.url,
                    "yes" if row.is_profile else "no",
                    ";".join(sorted(row.emails)),
                    ";".join(sorted(row.phones)),
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl links and collect emails + phone numbers."
    )
    parser.add_argument("--start-url", required=True, help="First URL to crawl")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum pages to visit")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument(
        "--all-domains",
        action="store_true",
        help="Follow links across any domain (default is same-domain only)",
    )
    parser.add_argument("--output", default="contacts.csv", help="Output CSV file")
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Save contacts only from profile pages (helpful for Facebook group/user crawls)",
    )
    parser.add_argument(
        "--cookies-json",
        help="Path to JSON cookies for authenticated pages. Accepts {name:value} object or browser-style cookie list.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = crawl(
        start_url=args.start_url,
        max_pages=args.max_pages,
        timeout=args.timeout,
        stay_on_domain=not args.all_domains,
        profile_only=args.profile_only,
        cookies_json=args.cookies_json,
    )
    write_csv(results, args.output)

    total_emails = len({email for result in results for email in result.emails})
    total_phones = len({phone for result in results for phone in result.phones})
    print(f"Visited {len(results)} pages")
    print(f"Collected {total_emails} unique emails")
    print(f"Collected {total_phones} unique phone numbers")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
