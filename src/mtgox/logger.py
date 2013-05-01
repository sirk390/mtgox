import logging
import sys

def make_logger(name="mtgox", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fmt1 = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fmt2 = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #Stdout
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(fmt1)
    stdout.setLevel(logging.INFO)
    logger.addHandler(stdout)
    file_handler = logging.FileHandler("mtgox.log")
    file_handler.setFormatter(fmt2)
    logger.addHandler(file_handler)
    return logger

log = make_logger()
