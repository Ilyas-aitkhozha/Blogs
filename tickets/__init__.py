import sys
import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    stream=sys.stdout,
)