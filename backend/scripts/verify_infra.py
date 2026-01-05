import asyncio
import redis.asyncio as redis
import asyncpg
import sys

async def check_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        await r.ping()
        print("✅ Redis: Connected!")
        await r.close()
        return True
    except Exception as e:
        print(f"❌ Redis: Failed ({e})")
        return False

async def check_postgres():
    try:
        conn = await asyncpg.connect(user='argus', password='argus_password', database='argus_db', host='localhost', port=5433)
        await conn.close()
        print("✅ Postgres: Connected!")
        return True
    except Exception as e:
        print(f"❌ Postgres: Failed ({e})")
        return False

async def main():
    print("--- Verifying Infrastructure ---")
    r_ok = await check_redis()
    db_ok = await check_postgres()
    
    if r_ok and db_ok:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
