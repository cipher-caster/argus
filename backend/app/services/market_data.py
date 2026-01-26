from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import select
from app.storage import RedisClient, Database
from app.schemas.candle import Candle as DbCandle
from app.schemas.market_data import CoinInfo
from app.providers import Candle as ProviderCandle

class MarketDataService:
    @staticmethod
    async def fetch_and_sync_ohlcv(
        symbol: str, 
        timeframe: str, 
        limit: int = 100, 
        end_timestamp: Optional[int] = None
    ) -> Tuple[List[ProviderCandle], str]:
        """
        Fetch OHLCV data from DB, fallback to Binance/Provider if stale or missing.
        Returns (candles, provider_name).
        """
        from app.providers.binance_provider import BinanceProvider
        
        async with Database.get_session() as session:
            # Base query
            query = select(DbCandle).where(
                DbCandle.symbol == symbol,
                DbCandle.timeframe == timeframe
            )
            
            # Apply pagination (historical data)  
            if end_timestamp:
                query = query.where(DbCandle.timestamp < end_timestamp)
                
            # Order and limit
            statement = query.order_by(DbCandle.timestamp.desc()).limit(limit)
            
            results = await session.execute(statement)
            db_candles = results.scalars().all()
            
            # Helper for timeframe ms
            timeframe_ms = {
                '1m': 60 * 1000,
                '5m': 5 * 60 * 1000,
                '15m': 15 * 60 * 1000,
                '30m': 30 * 60 * 1000,
                '1h': 60 * 60 * 1000,
                '4h': 4 * 60 * 60 * 1000,
                '12h': 12 * 60 * 60 * 1000,
                '1d': 24 * 60 * 60 * 1000,
                '3d': 3 * 24 * 60 * 60 * 1000,
                '1w': 7 * 24 * 60 * 60 * 1000,
            }.get(timeframe, 60 * 60 * 1000)

            # Check staleness
            import time
            now_ms = int(time.time() * 1000)
            is_stale = False
            if db_candles and not end_timestamp:
                latest_ts = db_candles[0].timestamp
                if (now_ms - latest_ts) > timeframe_ms:
                    is_stale = True
                    print(f"I: Data stale for {symbol} {timeframe}. Latest: {latest_ts}, Now: {now_ms}")

            # --- Direct Fetch if Missing or Stale ---
            if not db_candles or len(db_candles) < limit // 2 or is_stale:
                print(f"I: Fetching from Binance... (Reason: Missing={not db_candles}, Sparse={len(db_candles) < limit//2 if db_candles else False}, Stale={is_stale})")
                try:
                    provider = BinanceProvider()
                    try:
                        # Calculate 'since' timestamp
                        if end_timestamp:
                            since_ts = end_timestamp - (1000 * timeframe_ms)
                        else:
                            since_ts = None  # Fetch latest
                        
                        print(f"I: Fetching from Binance with since={since_ts}")
                        fresh_candles = await provider.get_ohlcv(symbol, timeframe=timeframe, limit=1000, since=since_ts)
                        
                        # Save to DB
                        for c in fresh_candles:
                            candle_db = DbCandle(
                                symbol=symbol,
                                provider="binance",
                                timeframe=timeframe,
                                timestamp=c.timestamp,
                                open=c.open,
                                high=c.high,
                                low=c.low,
                                close=c.close,
                                volume=c.volume
                            )
                            await session.merge(candle_db)
                        await session.commit()
                        print(f"I: Saved {len(fresh_candles)} candles to DB")
                        
                        # Re-query
                        results = await session.execute(statement)
                        db_candles = results.scalars().all()
                        
                    finally:
                        await provider.close()
                        
                except Exception as e:
                    print(f"E: Failed to fetch from Binance: {e}")
            
            # Sort ascending for frontend
            db_candles = sorted(db_candles, key=lambda x: x.timestamp)
            
            # Convert to response format
            candles = [
                ProviderCandle(
                    timestamp=c.timestamp,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume
                ) for c in db_candles
            ]
            
            return candles, ("postgres-db" if db_candles else "empty")

    @staticmethod
    def filter_and_sort_coins(
        raw_data: List[Dict[str, Any]],
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        sort_by: str = "market_cap",
        sort_order: str = "desc"
    ) -> Tuple[List[CoinInfo], int]:
        """
        Process raw market data: Convert to CoinInfo, Filter, Sort, Paginate.
        Returns (page_coins, total_count).
        """
        # Convert to CoinInfo objects
        coins = []
        for t in raw_data:
            coins.append(CoinInfo(
                rank=0, # will resolve later
                symbol=t['symbol'],
                name=t['name'] or t['symbol'].split('/')[0],
                price=t['price'],
                change_1h=t.get('change_1h'),
                change_24h=t.get('change_24h'),
                change_7d=t.get('change_7d'),
                volume_24h=t.get('volume_24h'),
                high_24h=t.get('high_24h'),
                low_24h=t.get('low_24h'),
                market_cap=t.get('market_cap') or (t.get('volume_24h', 0) * 15.5), # Heuristic fallback
                image=t.get('image'),
                sparkline_in_7d=t.get('sparkline_in_7d')
            ))
            
        # Filter (Search)
        if search:
            s_upper = search.upper()
            coins = [c for c in coins if s_upper in c.symbol.upper()]
            
        # Sort
        reverse = sort_order == "desc"
        # Helper to safely get value or 0
        def get_val(obj, attr):
            v = getattr(obj, attr, 0)
            return v if v is not None else 0

        coins.sort(key=lambda x: get_val(x, sort_by if hasattr(x, sort_by) else 'market_cap'), reverse=reverse)
            
        # Rerank
        for idx, c in enumerate(coins):
            c.rank = idx + 1
            
        # Paginate
        total = len(coins)
        start = (page - 1) * page_size
        end = start + page_size
        page_coins = coins[start:end]
        
        return page_coins, total

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
