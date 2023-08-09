from itertools import islice


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
    '@': '%40',
    '*': '%2A'
}


def encode_uri_component(string):
    ret = ''
    for char in string:
        if char in unsafe:
            char = unsafe[char]
        ret = '{}{}'.format(ret, char)
    return ret


def window(seq, width):
    it = iter(seq)
    result = tuple(islice(it, width))
    if len(result) == width:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


def decode_uri_component(string):
    res = ""
    skip = 0
    for chars in window(string, 3):
        if skip > 0:
            skip -= 1
            continue
        if chars[0] == '%':
            unescaped = None
            char_code = "{}{}{}".format(chars[0], chars[1], chars[2])
            for k, v in unsafe.items():
                if v.lower() == char_code.lower():
                    unescaped = k
            if unescaped:
                res = "{}{}".format(res, unescaped)
                skip = 2
                continue

        res = "{}{}".format(res, chars[0])

    # add last two characters which are skipped from the loop
    if skip == 1:
        res = "{}{}".format(res, string[len(string)-1])
    elif skip == 0:
        res = "{}{}{}".format(
            res, string[len(string)-2], string[len(string)-1])
    return res
