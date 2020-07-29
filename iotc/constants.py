class IoTCLogLevel:
    DISABLED = 1
    API_ONLY = 2
    ALL = 3

class IoTCConnectType:
    SYMM_KEY = 1
    DEVICE_KEY = 2

class IoTCEvents:
    PROPERTIES = 1
    COMMANDS = 2
    ENQUEUED_COMMANDS = 3

class HubTopics:
    TWIN = '$iothub/twin/res/#'
    TWIN_REQ = '$iothub/twin/GET/?$rid={}'
    TWIN_RES = '$iothub/twin/res/{}/?$rid={}'
    PROPERTIES = '$iothub/twin/PATCH/properties/desired'
    PROP_REPORT = '$iothub/twin/PATCH/properties/reported/?$rid={}'
    COMMANDS = '$iothub/methods/POST'
    ENQUEUED_COMMANDS = 'devices/{}/messages/devicebound'

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

unsafe = {
    '?': '%3F',
    ' ': '%20',
    '$': '%24',
    '%': '%25',
    '&': '%26',
    "\'": '%27',
    '/': '%2F',
    ':': '%3A',
    ';': '%3B',
    '+': '%2B',
    '=': '%3D',
    '@': '%40'
}

def encode_uri_component(string):
    ret = ''
    for char in string:
        if char in unsafe:
            char = unsafe[char]
        ret = '{}{}'.format(ret, char)
    return ret