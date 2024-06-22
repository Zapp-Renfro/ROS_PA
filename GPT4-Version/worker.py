import os
import redis
from rq import Worker, Queue, Connection
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

listen = ['default', 'high', 'low']

# Fetch the Redis URL from the environment variables
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise ValueError("REDIS_URL is not set")

logging.debug(f"Connecting to Redis at {redis_url}")

try:
    conn = redis.from_url(redis_url)
    logging.debug(f"Connected to Redis: {conn.ping()}")
except Exception as e:
    logging.error(f"Failed to connect to Redis: {e}")
    raise

if __name__ == '__main__':
    logging.debug("Starting worker")
    try:
        queues = list(map(Queue, listen))
        worker = Worker(queues, connection=conn)  # Explicitly pass the connection
        worker.work()
    except Exception as e:
        logging.error(f"Worker crashed: {e}")
        raise
