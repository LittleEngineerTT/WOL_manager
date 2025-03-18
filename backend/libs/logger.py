import logging
import os
import sys

def setup_logger(log_file, time_format="%Y-%m-%d %H:%M:%S") -> logging.Logger:
    """
    Set up a logger that writes to a file and to stdout.

    :param log_file: Path to the log file
    :param time_format: Format for the timestamp. Defaults to "%Y-%m-%d %H:%M:%S".
    return: Logger object
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(log_file)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    # Create logger
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(f'%(asctime)s %(message)s', datefmt=time_format)

    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
