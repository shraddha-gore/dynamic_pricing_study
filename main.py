import logging
import os
from config import LOGS_PATH

def setup_logging():
    os.makedirs(LOGS_PATH, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(LOGS_PATH, "experiment.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def main():
    setup_logging()
    logging.info("Dynamic Pricing Study initialised.")
    print("Dynamic Pricing Study initialised.")

if __name__ == "__main__":
    main()