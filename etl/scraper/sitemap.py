"""Scraper: fetch Cannondale sitemap and extract pt-br bike URLs.

Uses requests + regex. Output: raw URL list.
"""
import re
import requests

SITEMAP_INDEX = "https://a304077.sitemaphosting6.com/4356448/sitemap.xml"


def get_sitemap_urls(index_url: str = SITEMAP_INDEX) -> list[str]:
    idx = requests.get(index_url, timeout=30).text
    sitemaps = re.findall(r"<loc>(.*?)</loc>", idx)
    urls = []
    for sm in sitemaps:
        try:
            txt = requests.get(sm, timeout=30).text
            urls.extend(re.findall(r"<loc>(.*?)</loc>", txt))
        except Exception as exc:  # noqa: BLE001
            print(f"warn: falha ao baixar {sm}: {exc}")
    return urls


def filter_pt_br_bikes(urls: list[str]) -> list[str]:
    return sorted({u for u in get_sitemap_urls() if "pt-br" in u and "/bikes/" in u})


if __name__ == "__main__":
    bikes = filter_pt_br_bikes()
    print(f"URLs pt-br de bikes: {len(bikes)}")
    for u in bikes[:20]:
        print(u)
