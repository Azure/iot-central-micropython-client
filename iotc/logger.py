class IoTCLogLevel:
    DISABLED = 1
    API_ONLY = 2
    ALL = 3


class ConsoleLogger:
    def __init__(self, log_level=IoTCLogLevel.API_ONLY):
        self._log_level = log_level

    def _log(self, message):
        print(message)

    def info(self, message):
        if self._log_level != IoTCLogLevel.DISABLED:
            self._log(message)

    def debug(self, message):
        if self._log_level == IoTCLogLevel.ALL:
            self._log(message)

    def set_log_level(self, log_level):
        self._log_level = log_level
