from aio_pika import connect_robust, IncomingMessage
import datetime
import logging
import asyncio
import asyncpg
import ujson
import os


POSTGRES_DB   = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASS = os.environ["POSTGRES_PASS"]
RABBITMQ_USER = os.environ.get("RABBITMQ_USER") or "rabbit"
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS") or "password"
POSTGRES_HOST = os.environ.get("POSTGRES_HOST") or "kpi-postgres"
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST") or "kpi-rabbitmq"


async def main():
    postgres = await asyncpg.create_pool(
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}/{POSTGRES_DB}',
        command_timeout = 60
    )
    # If table doesn't exist - create new
    try:
        con = await postgres.acquire()
        await con.execute('''
            CREATE TABLE visits(
                id serial PRIMARY KEY,
                domain VARCHAR (64) NOT NULL,
                path VARCHAR (255) NOT NULL,
                unique_id VARCHAR (32) NOT NULL,
                date timestamp NOT NULL
            )
        ''')
        logging.info("Created table 'visits'..")
    except asyncpg.exceptions.DuplicateTableError:
        logging.info("Table 'visits' already exists.. skipping..")
    finally:
        await postgres.release(con)

    connection = await connect_robust(
        f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672"
    )
    # Creating channel
    channel = await connection.channel()

    # Maximum message count which will be
    # processing at the same time.
    await channel.set_qos(prefetch_count=50)

    # Declaring queue
    queue = await channel.declare_queue("statistics_visits_new")

    async def process_view(message: IncomingMessage):
        nonlocal postgres
        async with message.process():
            data = ujson.loads(message.body.decode())
            try:
                con = await postgres.acquire()
                await con.execute(
                    '''
                        INSERT INTO visits(domain, path, unique_id, date)
                        VALUES($1, $2, $3, $4)
                    ''',
                    data["domain"], data["path"], data["unique_id"],
                    datetime.datetime.fromisoformat(data["date"])
                )

                amount = await con.fetch("SELECT * FROM visits")
                # [DEBUG]
                logging.info(f"Total in db: {len(amount)}")
            finally:
                await postgres.release(con)

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
