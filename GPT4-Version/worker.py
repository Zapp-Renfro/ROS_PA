import os
import redis
from rq import Worker, Queue, Connection
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

listen = ['default', 'high', 'low']

# Set the Redis URL directly for testing
redis_url = 'redis://:pc26bcac62e4cbc350ac192fe4b5bedee252c6aa82bbf45e29ed574216da19536@ec2-52-45-177-80.compute-1.amazonaws.com:12479'
os.environ['REDIS_URL'] = redis_url

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
        worker = Worker(list(map(Queue, listen)), connection=conn)
        worker.work()
    except Exception as e:
        logging.error(f"Worker crashed: {e}")
        raise
