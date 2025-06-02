import logging
def get_log_level(log_level: str) -> int:
    lvl = log_level.upper()
    if lvl in ("DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"):
        return getattr(logging, lvl)
    else:
        print(f"Invalid log level provided: {lvl}, defaulting to info")
        return logging.INFO