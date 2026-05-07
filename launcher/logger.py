import logging
import sys

def setup_logger():
    logger = logging.getLogger("CatLauncher")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    try:
        fh = logging.FileHandler("launcher.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    return logger

log = setup_logger()
