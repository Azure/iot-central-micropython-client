class IoTCConnectType:
    SYMM_KEY = 1
    DEVICE_KEY = 2
    x509_CERT = 3


class IoTCLogLevel:
    DISABLED = 1
    API_ONLY = 2
    ALL = 3


class HubTopics:
    TWIN = '$iothub/twin/res/#'
    TWIN_REQ = '$iothub/twin/GET/?$rid={}'
    TWIN_RES = '$iothub/twin/res/{}/?$rid={}'
    PROPERTIES = '$iothub/twin/PATCH/properties/desired'
    PROP_REPORT = '$iothub/twin/PATCH/properties/reported/?$rid={}'
    COMMANDS = '$iothub/methods/POST'
    C2D = 'devices/{}/messages/devicebound'


class IoTCEvents:
    PROPERTIES = 1
    COMMANDS = 2
    C2D = 3
