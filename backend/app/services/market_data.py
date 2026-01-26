from typing import List, Dict, Any, Optional
from app.storage import RedisClient

class MarketDataService:
    @staticmethod
    async def get_merged_market_data() -> List[Dict[str, Any]]:
        """
        Merge base market state (CoinGecko Snapshot) with live prices (Binance).
        Returns list of rich ticker dicts.
        """
        # 1. Fetch Snapshot (Base: Rich metadata, 5m old)
        snapshot = await RedisClient.get_json("market:snapshot") or []
        
        # 2. Fetch Live (Overlay: Fast prices, 30s old)
        live_tickers = await RedisClient.get_json("market:tickers") or []
        live_map = {t['symbol']: t for t in live_tickers}
        
        merged = []
        processed_symbols = set()
        
        # 3. Process Snapshot (Base)
        for coin in snapshot:
            symbol = coin.get('symbol')
            if not symbol: continue
            
            # Prevent duplicates from CoinGecko
            if symbol in processed_symbols:
                continue
            
            processed_symbols.add(symbol)
            
            # Overlay live data if available
            if symbol in live_map:
                live = live_map[symbol]
                coin['price'] = live.get('price', coin['price'])
                coin['change_24h'] = live.get('change_24h', coin.get('change_24h'))
                coin['volume_24h'] = live.get('volume_24h', coin.get('volume_24h'))
                coin['high_24h'] = live.get('high_24h')
                coin['low_24h'] = live.get('low_24h')
                
            merged.append(coin)
            
        # 4. Add Live Orphans (Tickers in Binance not in CoinGecko snapshot)
        for symbol, live in live_map.items():
            if symbol not in processed_symbols:
                merged.append({
                    "symbol": symbol,
                    "name": symbol.split('/')[0],
                    "price": live.get('price', 0),
                    "change_24h": live.get('change_24h', 0),
                    "volume_24h": live.get('volume_24h', 0),
                    "high_24h": live.get('high_24h', 0),
                    "low_24h": live.get('low_24h', 0),
                    "market_cap": 0,
                    "rank": 9999,
                    "image": None
                })
                
        return merged

    @staticmethod
    async def get_top_symbols(limit: int = 100, sort_by: str = "market_cap") -> List[str]:
        """
        Get list of top symbols based on market cap or volume.
        Auto-filters stablecoins and other non-speculative assets.
        """
        # Blacklist of stablecoins and non-tradeable assets
        BLACKLIST = {
            "USDT/USDT", "USDC/USDT", "DAI/USDT", "FDUSD/USDT", "TUSD/USDT",
            "USDP/USDT", "EUR/USDT", "BUSD/USDT", "USDD/USDT", "PYUSD/USDT",
            "WBTC/USDT", "USDE/USDT", "USD1/USDT", "BFUSD/USDT",
            "LUSD/USDT", "FRAX/USDT", "USTC/USDT"
        }
        data = await MarketDataService.get_merged_market_data()
        
        # Filter symbols that are active on Binance Futures might be useful here, 
        # but for now we just return the top ones from the merged list.
        # Merged list already contains only USDT pairs (see worker.py sync_market_summary)
        
        if sort_by == "volume":
            data.sort(key=lambda x: x.get('volume_24h', 0), reverse=True)
        else: # Default market_cap
            data.sort(key=lambda x: x.get('market_cap' or 0) or 0, reverse=True)
            
        # Filter against active Binance symbols to ensure we only return tradeable assets
        from app.providers.binance_provider import BinanceProvider
        provider = BinanceProvider()
        try:
            active_symbols_info = await provider.get_symbols()
            active_symbols = {s.symbol for s in active_symbols_info}
            
            # Filter data
            filtered_data = [
                item for item in data 
                if item['symbol'] in active_symbols 
                and item['symbol'] not in BLACKLIST
                and not item['symbol'].endswith("DOWN/USDT") # Filter leveraged tokens
                and not item['symbol'].endswith("UP/USDT")
            ]
            
            # If filtration emptied the list (e.g. provider error), fallback to raw data
            # but ideally we want strict filtering.
            if filtered_data:
                data = filtered_data
                
        except Exception as e:
            # excessive logging might be noisy, but good for debugging
            pass
        finally:
            await provider.close()
            
        return [item['symbol'] for item in data[:limit]]
