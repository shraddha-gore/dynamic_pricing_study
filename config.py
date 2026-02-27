# Data paths
RAW_DATA_PATH = "data/raw/"
PROCESSED_DATA_PATH = "data/processed/"
RESULTS_PATH = "results/"
LOGS_PATH = "logs/"

# Experimental constants (frozen)
TRAIN_SPLIT_RATIO = 0.8

PRICE_GRID_PERCENTAGE = 0.05      # ±5% candidate grid
MAX_DAILY_CHANGE = 0.03           # ±3% clamp constraint
HYBRID_SMOOTHING_ALPHA = 0.3      # 30% weight on ML price