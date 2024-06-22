import os
import redis
from rq import Worker, Queue, Connection
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

listen = ['default', 'high', 'low']

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
print(redis_url)

if not redis_url:
    raise ValueError("REDIS_URL is not set")

logging.debug(f"Connecting to Redis at {redis_url}")

try:
    conn = redis.from_url(redis_url)
    print(conn.ping())
except Exception as e:
    logging.error(f"Failed to connect to Redis: {e}")
    raise

if __name__ == '__main__':
    logging.debug("Starting worker")
    try:
        worker = Worker(list(map(Queue, listen)), connection=conn)
        worker.work()
    except Exception as e:
        logging.error(f"Worker crashed: {e}")
        raise
