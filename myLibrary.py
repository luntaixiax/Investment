import logging
import os

logging.basicConfig(
    level = logging.INFO,
    format="[%(levelname)s]:  %(module)s\\%(funcName)s\n%(message)s",
)

MAIN_PATH = os.path.dirname(__file__)