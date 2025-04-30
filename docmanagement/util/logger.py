import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from core.config import settings
from util.constants import ENV_SWITCH


class Logger:
    def __init__(self):
        # Initiate logger
        self.logger = logging.getLogger()
        # switch handler
        if ENV_SWITCH.LOG_STORE == 'AZURE_APP_INSIGHTS':
            self.logger.addHandler(AzureLogHandler(connection_string=settings.APPINSIGHTS_CONNECTION_STRING))
        # Log prefix
        self.log_prefix = ': API LOGS :: DOCUMENT MANAGEMENT :: '
    
    def add_azure_handler(self):
        # Add azure handler to store log statements in app insights
        self.handler = AzureLogHandler(connection_string=settings.APPINSIGHTS_CONNECTION_STRING)

    def log(self, message, log_level = 'ERROR'):
        # Log message according to the levels
        if log_level == 'INFO':
            self.logger.info(self.log_prefix + message)
        elif log_level == 'ERROR':
            self.logger.error(self.log_prefix + message)
        elif log_level == 'WARNING':
            self.logger.warning(self.log_prefix + message)
        elif log_level == 'DEBUG':
            self.logger.debug(self.log_prefix + message)
        elif log_level == 'CRITICAL':
            self.logger.critical(self.log_prefix + message)

logger = Logger()