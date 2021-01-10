from aio_pika import connect_robust, IncomingMessage
from collections import Counter
from .utils import send_email
import datetime
import aioredis
import logging
import asyncio
import asyncpg
import ujson
import os


POSTGRES_DB   = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASS = os.environ["POSTGRES_PASS"]
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")   or "rabbit"
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS")   or "password"
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")   or "kpi-postgres"
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")   or "kpi-rabbitmq"
REDIS_HOST    = os.environ.get("REDIS_HOST")      or "kpi-redis"
TIMEOUT       = int(os.environ.get("TIMEOUT", 0)) or 30  # minutes
N_TOP_RESULTS = int(os.environ.get("N_TOP_RESULTS", 0)) or 10  # amount of top popular paths to show


async def main():
    postgres = await asyncpg.create_pool(
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}/{POSTGRES_DB}',
        command_timeout = 60
    )
    redis = await aioredis.create_redis_pool(f"redis://{REDIS_HOST}/0")
    connection = await connect_robust(
        f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672"
    )
    # Creating channel
    channel = await connection.channel()

    # Maximum message count which will be
    # processing at the same time.
    await channel.set_qos(prefetch_count=50)

    # Declaring queue
    queue = await channel.declare_queue("statistics_report")

    async def process_view(message: IncomingMessage):
        nonlocal postgres
        nonlocal redis

        async with message.process():
            data = ujson.loads(message.body.decode())
            email = data["email"]
            cached = await redis.get(email)
            if not cached:
                cached = {
                    "date": datetime.datetime.now().isoformat(),
                    "emails_left": 1,
                    "emails_limit": 1,
                }
            else:
                cached = ujson.loads(cached.decode())

            # If needs renewal - set back to the account's limit
            if cached["date"] < (datetime.datetime.now() - datetime.timedelta(minutes=TIMEOUT)).isoformat():
                cached["emails_left"] = cached["emails_limit"]

            # check whether email can be sent right now
            if cached["emails_left"] > 0:
                cached["emails_left"] -= 1
                domain = data["domain"]
                # collect data
                try:
                    con = await postgres.acquire()
                    rows = await con.fetch(
                        "SELECT * FROM visits WHERE domain = $1 AND date > $2",
                        domain, datetime.datetime.now() - datetime.timedelta(days=30)
                    )
                    logging.info(f"Collected {len(rows)} rows for domain \"{domain}\".")
                    # Compile stats for the domain from all data
                    ctx = {
                        "domain": domain,
                        "emails_left": cached["emails_left"],
                        "total_visits": len(rows),
                        "unique_visitors": len(set(row["unique_id"] for row in rows)),
                        "count": Counter(row["path"] for row in rows).most_common(N_TOP_RESULTS),
                    }
                    # logging.info(f"{ctx}")

                finally:
                    await postgres.release(con)

                await send_email(email, ctx)
                
                logging.error("Something here worked, early termination.. BEEP BOOP")
                # finally commit to db
                await redis.set(email, ujson.dumps(cached).encode())

    await queue.consume(process_view)
    return connection


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    loop = asyncio.get_event_loop()
    connection = loop.run_until_complete(main())

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(connection.close())
