from .provision import ProvisioningClient
from .constants import IoTCConnectType, IoTCLogLevel, HubTopics, IoTCEvents
from utime import time
import json

try:
    from umqtt.simple import MQTTClient
except:
    print('Mqtt library not found. Installing...')
    import upip
    upip.install('micropython-umqtt.simple')
    from umqtt.simple import MQTTClient


class ConsoleLogger:
    def __init__(self, log_level):
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


class IoTCClient():
    def __init__(self, scope_id, device_id, key):
        self._logger = ConsoleLogger(IoTCLogLevel.ALL)
        self._scope_id = scope_id
        self._device_id = device_id
        self._device_key = key
        self._events = {}

    def _on_message(self, topic, message):
        topic = topic.decode('utf-8')
        # if topic == HubTopics.TWIN_RES.format(200, self._twin_request_id):
        #     self._logger.info('Received twin: {}'.format(message))

        # try:
        #     cb = self._events['topic']
        #     cb(message)
        # except:
        #     pass
        if topic.startswith(HubTopics.PROPERTIES):
            # desired properties
            self._logger.info(
                'Received desired property message: {}'.format(message))
            message=json.loads(message.decode('utf-8'))
            self.on_properties_update(message)

        elif topic.startswith(HubTopics.COMMANDS):
            # commands
            self._logger.info('Received command message: {}'.format(message))
        #     const match = message.destinationName.match(/\$iothub\/ methods\/ POST\/ (.+)\/\?\$rid=(.+)/)
        #     if (match & & match.length === 3) {
        #         let cmd: Partial < IIoTCCommand > = {
        #             name: match[1],
        #             requestId: match[2]
        #         };
        #         if (message.payloadString) {
        #             cmd['requestPayload'] = message.payloadString; }
        #         this.onCommandReceived(cmd); }

        # }

    def connect(self):
        provisioning_client = ProvisioningClient(
            self._scope_id, self._device_id, IoTCConnectType.DEVICE_KEY, self._device_key)
        credentials=provisioning_client.register()
        self._mqtt_client=MQTTClient(self._device_id, credentials.host, 8883, credentials.user.encode(
            'utf-8'), credentials.password.encode('utf-8'), ssl = True, keepalive = 4000)
        self._mqtt_client.connect()
        self._connected=True
        self._logger.info('Device connected!')
        self._mqtt_client.set_callback(self._on_message)
        self._mqtt_client.subscribe(HubTopics.TWIN)
        self._mqtt_client.subscribe('{}/#'.format(HubTopics.PROPERTIES))
        self._mqtt_client.subscribe('{}/#'.format(HubTopics.COMMANDS))
        self._mqtt_client.subscribe(
            '{}/#'.format(HubTopics.C2D.format(self._device_id)))

        self._twin_request_id=time()
        self._mqtt_client.publish(
            HubTopics.TWIN_REQ.format(self._twin_request_id), '{{}}')

    def is_connected(self):
        if self._connected == True:
            return True
        return False

    def send_property(self, payload):
        self._mqtt_client.publish(HubTopics.PROP_REPORT.format(time()),json.dumps(payload))

    def on(self, event, callback):
        self._events[event]=callback

    def listen(self):
        self._mqtt_client.wait_msg()

    def on_properties_update(self,patch):
        print(patch)
        try:
            prop_cb=self._events[IoTCEvents.PROPERTIES]
        except:
            return

        for prop in patch:
            if prop == '$version':
                continue
            ret = prop_cb(prop, patch[prop]['value'])
            if ret:
                self._logger.debug('Acknowledging {}'.format(prop))
                self.send_property({
                    '{}'.format(prop): {
                        "value": patch[prop]["value"],
                        'status': 'completed',
                        'desiredVersion': patch['$version'],
                        'message': 'Property received'}
                })
            else:
                self._logger.debug(
                    'Property "{}" unsuccessfully processed'.format(prop))
