# Coin Data

This directory contains coin metadata and images synced from CoinGecko.

## Files

- `coins.json` - Coin metadata (symbol, name, image path, market_cap, rank)
- `images/` - Downloaded coin logos (PNG format)

## Sync Script

Run the sync script to update data:

```bash
# From project root
cd backend
./venv/bin/python3 ../scripts/sync_coins.py --limit 250
```

### Options

- `--limit N` - Number of coins to fetch (default: 250)
- `--force` - Force re-download all images

## Automation (Cron)

To run every 3 days at 2am:

```bash
# Add to crontab -e
0 2 */3 * * cd /path/to/argus && backend/venv/bin/python3 scripts/sync_coins.py --limit 250 >> logs/coin_sync.log 2>&1
```

## JSON Format

```json
{
  "updated_at": "2026-01-17T12:00:00",
  "count": 250,
  "coins": [
    {
      "id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "image": "/data/coins/images/btc.png"
    }
  ]
}
```
