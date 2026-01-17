#!/usr/bin/env python3
"""
CoinGecko Coin Data Sync Script

Downloads coin metadata and images from CoinGecko API and stores them locally.
Run this script periodically (e.g., every 3 days via cron) to keep data fresh.

Usage:
    python scripts/sync_coins.py [--limit 250] [--force]

Output:
    - data/coins/coins.json - Coin metadata (id, symbol, name, image path, market_cap)
    - data/coins/images/{symbol}.png - Coin logos
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

# Configuration
COINGECKO_API = "https://api.coingecko.com/api/v3"
# Output to frontend/public for Next.js static serving
DATA_DIR = Path(__file__).parent.parent / "frontend" / "public" / "data" / "coins"
COINS_JSON = DATA_DIR / "coins.json"
IMAGES_DIR = DATA_DIR / "images"

# Rate limiting (CoinGecko free tier: 10-30 calls/min)
RATE_LIMIT_DELAY = 2.0  # seconds between requests


async def fetch_coins(limit: int = 250) -> list:
    """Fetch top coins by market cap from CoinGecko."""
    coins = []
    per_page = 100
    pages = (limit + per_page - 1) // per_page
    
    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(1, pages + 1):
            url = f"{COINGECKO_API}/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": "false",
            }
            
            print(f"Fetching page {page}/{pages}...")
            response = await client.get(url, params=params)
            
            if response.status_code == 429:
                print("Rate limited! Waiting 60s...")
                await asyncio.sleep(60)
                response = await client.get(url, params=params)
            
            response.raise_for_status()
            page_data = response.json()
            coins.extend(page_data)
            
            if page < pages:
                await asyncio.sleep(RATE_LIMIT_DELAY)
    
    return coins[:limit]


async def download_image(client: httpx.AsyncClient, url: str, path: Path) -> bool:
    """Download an image from URL to local path."""
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        return True
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return False


async def sync_images(coins: list, force: bool = False) -> dict:
    """Download coin images that don't exist locally."""
    downloaded = 0
    skipped = 0
    failed = 0
    
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient(timeout=30) as client:
        for i, coin in enumerate(coins):
            symbol = coin["symbol"].lower()
            image_url = coin.get("image", "")
            local_path = IMAGES_DIR / f"{symbol}.png"
            
            # Skip if already exists and not forcing
            if local_path.exists() and not force:
                skipped += 1
                continue
            
            if not image_url:
                continue
            
            print(f"  [{i+1}/{len(coins)}] Downloading {symbol}...")
            success = await download_image(client, image_url, local_path)
            
            if success:
                downloaded += 1
            else:
                failed += 1
            
            # Rate limiting for image downloads
            await asyncio.sleep(0.5)
    
    return {"downloaded": downloaded, "skipped": skipped, "failed": failed}


def save_coins_json(coins: list):
    """Save coin metadata to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Transform to our format - only static metadata
    coin_data = []
    for coin in coins:
        symbol = coin["symbol"].lower()
        coin_data.append({
            "id": coin["id"],
            "symbol": symbol.upper(),
            "name": coin["name"],
            "image": f"/data/coins/images/{symbol}.png",
        })
    
    output = {
        "updated_at": datetime.now().astimezone().isoformat(),
        "count": len(coin_data),
        "coins": coin_data,
    }
    
    COINS_JSON.write_text(json.dumps(output, indent=2))
    print(f"Saved {len(coin_data)} coins to {COINS_JSON}")


async def main():
    parser = argparse.ArgumentParser(description="Sync coin data from CoinGecko")
    parser.add_argument("--limit", type=int, default=250, help="Number of coins to fetch")
    parser.add_argument("--force", action="store_true", help="Force re-download all images")
    args = parser.parse_args()
    
    print(f"=== CoinGecko Sync ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    print(f"Fetching top {args.limit} coins...")
    
    # Fetch coin data
    coins = await fetch_coins(args.limit)
    print(f"Fetched {len(coins)} coins from CoinGecko")
    
    # Save JSON metadata
    save_coins_json(coins)
    
    # Download images
    print(f"\nSyncing images (force={args.force})...")
    stats = await sync_images(coins, force=args.force)
    print(f"\nImage sync complete:")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")
    
    print("\n✓ Sync complete!")


if __name__ == "__main__":
    asyncio.run(main())
