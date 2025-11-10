import logging
import sys


def setup_logging():
    """
        Configures the root logger for the entire application.
        this function should be called once at the application starting point. 
    """
    if not logging.getLogger().hasHandlers():

        logging.basicConfig(
            level=logging.DEBUG,
            stream=sys.stdout,
            format='%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logging.getLogger().info("Logging system configured.")

def set_external_log_levels():
    """
        adjust the logging level for external libraries to prevent noise
    """
    logging.getLogger("requests").setLevel(logging.WARNING)

