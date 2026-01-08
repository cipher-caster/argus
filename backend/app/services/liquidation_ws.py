"""
Binance Futures WebSocket service for liquidation data

Connects to the forceOrder stream and aggregates liquidation events
into time-bucketed price levels stored in Redis.
"""
import asyncio
import json
import logging
import time
from typing import Dict, Optional
import websockets
from app.storage import RedisClient

logger = logging.getLogger(__name__)

# Configuration
WS_URL = "wss://fstream.binance.com/ws/!forceOrder@arr"
BUCKET_SIZE_SECONDS = 15  # Time bucket granularity
PRICE_BUCKET_SIZE = 50  # $50 price levels for BTC
DATA_TTL_SECONDS = 86400  # 24 hours


class LiquidationAggregator:
    """Aggregates liquidation events into buckets"""
    
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self._running = False
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
    
    def _get_time_bucket(self, timestamp_ms: int) -> int:
        """Round timestamp to nearest bucket"""
        ts_seconds = timestamp_ms // 1000
        return (ts_seconds // BUCKET_SIZE_SECONDS) * BUCKET_SIZE_SECONDS
    
    def _get_price_bucket(self, price: float) -> str:
        """Round price to nearest bucket level"""
        bucket = int(price // PRICE_BUCKET_SIZE) * PRICE_BUCKET_SIZE
        return str(bucket)
    
    async def _process_event(self, data: dict):
        """Process a single liquidation event"""
        try:
            order = data.get("o", {})
            symbol = order.get("s", "")
            
            # Filter for target symbol
            if symbol != self.symbol:
                return
            
            price = float(order.get("p", 0))
            quantity = float(order.get("q", 0))
            trade_time = int(order.get("T", 0))
            side = order.get("S", "")
            
            if price <= 0 or quantity <= 0:
                return
            
            # Calculate bucket keys
            time_bucket = self._get_time_bucket(trade_time)
            price_bucket = self._get_price_bucket(price)
            volume = price * quantity  # USD value
            
            # Store in Redis
            redis_key = f"liquidation:{self.symbol}:buckets"
            
            # Get existing data
            existing = await RedisClient.get_json(redis_key) or {}
            
            # Update bucket
            time_key = str(time_bucket)
            if time_key not in existing:
                existing[time_key] = {}
            
            if price_bucket not in existing[time_key]:
                existing[time_key][price_bucket] = 0
            
            existing[time_key][price_bucket] += volume
            
            # Clean old buckets (keep last 24h)
            cutoff = int(time.time()) - DATA_TTL_SECONDS
            existing = {k: v for k, v in existing.items() if int(k) > cutoff}
            
            # Save back
            await RedisClient.set_json(redis_key, existing, ttl=DATA_TTL_SECONDS)
            
            logger.debug(f"Liquidation: {symbol} {side} {quantity}@{price} -> bucket {time_bucket}/{price_bucket}")
            
        except Exception as e:
            logger.error(f"Error processing liquidation event: {e}")
    
    async def start(self):
        """Start the WebSocket connection"""
        self._running = True
        retry_delay = 1
        event_count = 0
        
        while self._running:
            try:
                print(f"[LiquidationWS] Connecting to {WS_URL}...")
                logger.info(f"Connecting to Binance Futures WebSocket...")
                async with websockets.connect(WS_URL, ping_interval=30) as ws:
                    self._ws = ws
                    retry_delay = 1  # Reset on successful connect
                    print("[LiquidationWS] Connected! Waiting for events...")
                    logger.info("Connected to Binance Futures liquidation stream")
                    
                    async for message in ws:
                        if not self._running:
                            break
                        
                        try:
                            data = json.loads(message)
                            event_count += 1
                            if event_count <= 5 or event_count % 100 == 0:
                                print(f"[LiquidationWS] Event #{event_count}: {data.get('o', {}).get('s')} {data.get('o', {}).get('q')}@{data.get('o', {}).get('p')}")
                            await self._process_event(data)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON: {message[:100]}")
                            
            except websockets.ConnectionClosed as e:
                print(f"[LiquidationWS] Connection closed: {e}")
                logger.warning(f"WebSocket closed: {e}. Reconnecting in {retry_delay}s...")
            except Exception as e:
                print(f"[LiquidationWS] Error: {e}")
                logger.error(f"WebSocket error: {e}. Reconnecting in {retry_delay}s...")
            
            if self._running:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Exponential backoff
    
    async def stop(self):
        """Stop the WebSocket connection"""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info("Liquidation WebSocket stopped")


# Global instance
_aggregator: Optional[LiquidationAggregator] = None


async def start_liquidation_stream(symbol: str = "BTCUSDT"):
    """Start the global liquidation aggregator"""
    global _aggregator
    if _aggregator is None:
        _aggregator = LiquidationAggregator(symbol)
        asyncio.create_task(_aggregator.start())
        logger.info(f"Started liquidation stream for {symbol}")


async def stop_liquidation_stream():
    """Stop the global liquidation aggregator"""
    global _aggregator
    if _aggregator:
        await _aggregator.stop()
        _aggregator = None
