import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from settings import settings

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if settings.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


create_directory('./logs')

handlers = [
    RotatingFileHandler(
        filename='./logs/log.txt',
        mode='w',
        maxBytes=512000,
        backupCount=4,
        encoding='utf-8',
    ),
    logging.StreamHandler(stream=sys.stdout),
]

logging.basicConfig(
    handlers=handlers,
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(name)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z',
)

logger = logging.getLogger('postgres_to_es')
