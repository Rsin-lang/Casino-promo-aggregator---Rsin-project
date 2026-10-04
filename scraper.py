import asyncio
import json
import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

VENUES = [
    {
        "id": "crown-sydney",
        "name": "Crown Sydney",
        "url": "https://www.crownsydney.com.au/whats-on#casino",
        "location": "Sydney, NSW, Australia",
        "badgeColor": "bg-red-500/10 text-red-400 border-red-500/20"
    },
    {
        "id": "crown-melbourne",
        "name": "Crown Melbourne",
        "url": "https://www.crownmelbourne.com.au/whats-on",
        "location": "Melbourne, VIC, Australia",
        "badgeColor": "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
    },
    {
        "id": "star-brisbane",
        "name": "The Star Brisbane",
        "url": "https://www.star.com.au/brisbane",
        "location": "Brisbane, QLD, Australia",
        "badgeColor": "bg-amber-500/10 text-amber-400 border-amber-500/20"
    },
    {
        "id": "star-goldcoast",
        "name": "The Star Gold Coast",
        "url": "https://www.star.com.au/goldcoast",
        "location": "Broadbeach, QLD, Australia",
        "badgeColor": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    },
    {
        "id": "star-sydney",
        "name": "The Star Sydney",
        "url": "https://www.star.com.au/sydney/whats-on",
        "location": "Pyrmont, Sydney, NSW, Australia",
        "badgeColor": "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
    },
    {
        "id": "christchurch",
        "name": "Christchurch Casino",
        "url": "https://christchurchcasino.co.nz/whats-on/",
        "location": "Christchurch, New Zealand",
        "badgeColor": "bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/20"
    }
]

async def scrape_venue(page, venue: Dict[str, Any]) -> List[Dict[str, Any]]:
    logging.info(f"Crawling {venue['name']}...")
    promos = []
    await page.goto(venue['url'], wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(3000)

    cards = await page.query_selector_all("article, .promo-card, .event-card, div:has(h3)")
    for idx, card in enumerate(cards):
        text = await card.inner_text()
        if any(term in text.lower() for term in ["win", "cash", "rewards", "poker", "jackpot", "car", "multiplier", "table"]):
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if lines:
                promos.append({
                    "id": f"{venue['id']}-{idx}",
                    "venue": venue["name"],
                    "location": venue["location"],
                    "badgeColor": venue["badgeColor"],
                    "title": lines[0],
                    "schedule": lines[1] if len(lines) > 1 else "Active Season",
                    "category": "Cash & Vehicles" if "win" in text.lower() or "car" in text.lower() else "Member Rewards",
                    "description": " ".join(lines[1:4]),
                    "sourceUrl": venue["url"],
                    "tags": ["Gaming", venue["name"].split()[0]]
                })
    return promos

async def main():
    all_promotions = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for venue in VENUES:
            try:
                res = await scrape_venue(page, venue)
                all_promotions.extend(res)
            except Exception as e:
                logging.error(f"Failed to scrape {venue['name']}: {e}")

        await browser.close()

    with open("promotions.json", "w", encoding="utf-8") as f:
        json.dump(all_promotions, f, indent=2, ensure_ascii=False)
    logging.info(f"Scraped {len(all_promotions)} promotions into promotions.json")

if __name__ == "__main__":
    asyncio.run(main())