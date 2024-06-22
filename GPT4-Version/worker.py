import os
import redis
from rq import Worker, Queue  # Modification ici
import logging

# Configure logging
logging.basic(level=logging.DEBUG)

listen = ['default', 'high', 'low']

# Redis URL
redis_url = 'redis://:pc26bcac62e4cbc350ac192fe4b5bedee252c6aa82bbf45e29ed574216da19536@ec2-52-45-177-80.compute-1.amazonaws.com:12479'

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
        # Explicitly set the connection for each queue
        queues = [Queue(name, connection=conn) for name in listen]  # Modification ici
        worker = Worker(queues, connection=conn)  # Modification ici
        worker.work()
    except Exception as e:
        logging.error(f"Worker crashed: {e}")
        raise
