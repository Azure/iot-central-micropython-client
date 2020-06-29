from constants import IoTCLogLevel,IoTCEvents,encode_uri_component,HubTopics
from utime import time,sleep
import json

class Command():
    def __init__(self, cmd_name, request_id):
        self._cmd_name = cmd_name
        self._request_id = request_id

    @property
    def name(self):
        return self._cmd_name
    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self,value):
        self._payload=value

    @property
    def request_id(self):
        return self._request_id


class DeviceClient():
    def __init__(self,device_id, credentials, logger):
        self._device_id=device_id
        self._credentials = credentials
        self._content_type='application%2Fjson'
        self._content_encoding='utf-8'
        self._connected=False
        self._events = {}
        self._logger = logger
        self._twin_request_id = time()

        import ure
        self._commands_regex=ure.compile('\$iothub\/methods\/POST\/(.+)\/\?\$rid=(.+)')


    def set_content_type(self,content_type):
        self._content_type = encode_uri_component(content_type)

    def set_content_encoding(self,content_encoding):
        self._content_encoding = content_encoding


    def _on_message(self, topic, message):
        topic = topic.decode('utf-8')
        if topic == HubTopics.TWIN_RES.format(200, self._twin_request_id):
            self._logger.info('Received twin: {}'.format(message))

        if topic.startswith(HubTopics.PROPERTIES):
            # desired properties
            self._logger.info(
                'Received desired property message: {}'.format(message))
            message = json.loads(message.decode('utf-8'))
            self.on_properties_update(message)

        elif topic.startswith(HubTopics.COMMANDS):
            # commands
            self._logger.info('Received command {} with message: {}'.format(topic,message))
            match=self._commands_regex.match(topic)
            if match is not None:
                if all(m is not None for m in [match.group(1),match.group(2)]):
                    command_name=match.group(1)
                    command_req=match.group(2)
                    command=Command(command_name,command_req)
                    if message is not None:
                        command.payload=message
                        self._on_commands(command)

    def connect(self,credentials=None):
        if credentials is not None:
            self._credentials = credentials
            
        # clean up modules
        try:
            import sys
            del sys.modules['provision']
        except:
            pass

        try:
            from umqtt.robust import MQTTClient
        except:
            print('Mqtt library not found. Installing...')
            import upip
            upip.install('micropython-umqtt.robust')
            from umqtt.robust import MQTTClient
        
        self._logger.debug('Hub username: {}'.format(self._credentials.user))
        self._logger.debug('Hub Password: {}'.format(self._credentials.password))
        self._mqtt_client = MQTTClient(self._device_id, self._credentials.host, 8883, self._credentials.user.encode(
            'utf-8'), self._credentials.password.encode('utf-8'), ssl=True,keepalive=60)
        sleep(3)
        self._mqtt_client.connect(False)
        self._connected = True
        self._logger.info('Device connected!')
        self._mqtt_client.set_callback(self._on_message)
        self._mqtt_client.subscribe(HubTopics.TWIN)
        self._mqtt_client.subscribe('{}/#'.format(HubTopics.PROPERTIES))
        self._mqtt_client.subscribe('{}/#'.format(HubTopics.COMMANDS))
        self._mqtt_client.subscribe(
            '{}/#'.format(HubTopics.C2D.format(self._device_id)))

        self._logger.debug(self._twin_request_id)
        self._mqtt_client.publish(
            HubTopics.TWIN_REQ.format(self._twin_request_id).encode('utf-8'), '{{}}')

    def is_connected(self):
        if self._connected == True:
            return True
        return False

    def set_model_id(self,model):
        self._model_id=model

    def send_property(self, payload):
        self._logger.debug('Sending properties {}'.format(json.dumps(payload)))
        self._mqtt_client.publish(
            HubTopics.PROP_REPORT.format(time()).encode('utf-8'), json.dumps(payload))

    def send_telemetry(self,payload,properties=None):
        topic = 'devices/{}/messages/events/?$.ct={}&$.ce={}'.format(self._device_id,self._content_type,self._content_encoding)
        if properties is not None:
            for prop in properties:
                topic+='{}={}&'.format(encode_uri_component(prop),encode_uri_component(properties[prop]))

            topic=topic[:-1]
        self._mqtt_client.publish(topic.encode('utf-8'),json.dumps(payload).encode('utf-8'))

    def on(self, event, callback):
        self._events[event] = callback

    def listen(self):
        if not self.is_connected():
            return
        self._mqtt_client.ping()
        self._mqtt_client.wait_msg()
        sleep(1)

    def on_properties_update(self, patch):
        try:
            prop_cb = self._events[IoTCEvents.PROPERTIES]
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

    def _cmd_resp(self, command:Command,value):
        self._logger.debug('Responding to command "{}" request'.format(command.name))
        self.send_property({
            '{}'.format(command.name): {
                'value': value,
                'requestId': command.request_id
            }
        })

    def _cmd_ack(self,command:Command):
        self._logger.debug('Acknowledging command {}'.format(command.name))
        self._mqtt_client.publish('$iothub/methods/res/{}/?$rid={}'.format(200,command.request_id).encode('utf-8'),'')

    def _on_commands(self,command:Command):
        try:
            cmd_cb = self._events[IoTCEvents.COMMANDS]
        except KeyError:
            return
        
        self._logger.debug(
                'Received command {}'.format(command.name))
        self._cmd_ack(command)

        cmd_cb(command, self._cmd_resp)
