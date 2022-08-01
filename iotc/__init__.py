from iotc.constants import *
from iotc.provision import ProvisioningClient, Credentials
from sys import exit
import ure
import json
from utime import time, sleep
import gc
try:
    from umqtt.robust import MQTTClient
except:
    print('Mqtt library not found. Installing...')
    import upip
    upip.install('micropython-umqtt.robust')
    from umqtt.robust import MQTTClient
gc.collect()


class Command(object):
    def __init__(self, command_name, command_value, component_name=None):
        self._command_name = command_name
        self._command_value = command_value
        if component_name is not None:
            self._component_name = component_name
        else:
            self._component_name = None
        self.reply = None

    @property
    def name(self):
        return self._command_name

    @property
    def value(self):
        return self._command_value

    @property
    def component_name(self):
        return self._component_name


class IoTCClient():
    def __init__(self, id_scope, device_id, credentials_type: IoTCConnectType, credentials, logger=None, storage=None):
        self._device_id = device_id
        self._id_scope = id_scope
        self._credentials_type = credentials_type
        self._content_type = 'application%2Fjson'
        self._content_encoding = 'utf-8'
        self._connected = False
        self._credentials = credentials
        self._storage = storage
        self._events = {}
        self._model_id = None
        if logger is not None:
            self._logger = logger
        else:
            self._logger = ConsoleLogger(IoTCLogLevel.API_ONLY)
        self._twin_request_id = time()

    def set_content_type(self, content_type):
        self._content_type = encode_uri_component(content_type)

    def set_content_encoding(self, content_encoding):
        self._content_encoding = content_encoding

    def set_log_level(self, log_level: IoTCLogLevel):
        self._logger.set_log_level(log_level)

    def _on_message(self, topic, message):
        topic = topic.decode('utf-8')
        self._logger.debug(topic)
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
            match = self._commands_regex.match(topic)
            if match is not None:
                if all(m is not None for m in [match.group(1), match.group(2)]):
                    command_name = match.group(1)
                    command_req = match.group(2)
                    command = Command(command_name, message)
                    try:
                        command_name_with_components = command_name.split("*")

                        if len(command_name_with_components) > 1:
                            # In a component
                            self._logger.debug("Command in a component")
                            command = Command(
                                command_name_with_components[1],
                                message,
                                component_name=command_name_with_components[0],
                            )

                        def reply_fn():
                            self._logger.debug(
                                'Acknowledging command {}'.format(command.name))
                            self._mqtt_client.publish(
                                '$iothub/methods/res/{}/?$rid={}'.format(200, command_req).encode('utf-8'), '')
                            if command.component_name is not None:
                                self.send_property({"{}".format(command.component_name): {"{}".format(
                                    command.name): {"value": command.value, "requestId": command_req}}})
                            else:
                                self.send_property({"{}".format(command.name): {
                                                   "value": command.value, "requestId": command_req}})

                        command.reply = reply_fn
                        self._on_commands(command)
                        sleep(0.1)
                    except:
                        pass

        elif topic.startswith(HubTopics.ENQUEUED_COMMANDS.format(self._device_id)):
            params = topic.split(
                "devices/{}/messages/devicebound/".format(self._device_id), 1)[1].split('&')
            for param in params:
                p = param.split('=')
                if p[0] == "method-name":
                    command_name = decode_uri_component(p[1])
                    command = Command(command_name, message)
                    try:
                        command_name_with_components = command_name.split("*")

                        if len(command_name_with_components) > 1:
                            # In a component
                            self._logger.debug("Command in a component")
                            command = Command(
                                command_name_with_components[1],
                                message,
                                component_name=command_name_with_components[0],
                            )
                    except:
                        pass

                    self._logger.debug(
                        'Received enqueued command {} with message: {}'.format(command.name, command.value))
                    self._on_enqueued_commands(command)

    def connect(self, force_dps=False):
        creds = None

        if force_dps:
            self._logger.info("Refreshing credentials...")

        if self._storage is not None and force_dps is False:
            creds = self._storage.retrieve()

        if creds is None:
            prov = ProvisioningClient(
                self._id_scope, self._device_id, self._credentials_type, self._credentials, self._logger, self._model_id)
            creds = prov.register()

        self._mqtt_client = MQTTClient(
            self._device_id, creds.host, 8883, creds.user, creds.password, ssl=True, keepalive=60)
        self._commands_regex = ure.compile(
            '\$iothub\/methods\/POST\/(.+)\/\?\$rid=(.+)')
        try:
            self._mqtt_client.connect(False)
            self._connected = True
            self._logger.info('Device connected!')
            if self._storage:
                self._storage.persist(creds)
            self._mqtt_client.set_callback(self._on_message)
            self._mqtt_client.subscribe(HubTopics.TWIN)
            self._mqtt_client.subscribe('{}/#'.format(HubTopics.PROPERTIES))
            self._mqtt_client.subscribe('{}/#'.format(HubTopics.COMMANDS))
            self._mqtt_client.subscribe(
                '{}/#'.format(HubTopics.ENQUEUED_COMMANDS.format(self._device_id)))

            self._logger.debug(self._twin_request_id)
            self._mqtt_client.publish(
                HubTopics.TWIN_REQ.format(self._twin_request_id).encode('utf-8'), '{{}}')
        except:
            self._logger.info("ERROR: Failed to connect to Hub")
            if force_dps is True:
                exit(1)
            self.connect(True)

    def is_connected(self):
        if self._connected == True:
            return True
        return False

    def set_model_id(self, model):
        self._model_id = model

    def send_property(self, payload):
        self._logger.debug('Sending properties {}'.format(json.dumps(payload)))
        self._mqtt_client.publish(
            HubTopics.PROP_REPORT.format(time()).encode('utf-8'), json.dumps(payload))

    def send_telemetry(self, payload, properties=None):
        topic = 'devices/{}/messages/events/?$.ct={}&$.ce={}'.format(
            self._device_id, self._content_type, self._content_encoding)
        if properties is not None:
            for prop in properties:
                topic += '&{}={}'.format(prop, properties[prop])

        self._mqtt_client.publish(topic.encode(
            'utf-8'), json.dumps(payload).encode('utf-8'))

    def on(self, event, callback):
        self._events[event] = callback

    def listen(self):
        if not self.is_connected():
            return
        self._mqtt_client.ping()
        self._mqtt_client.wait_msg()
        sleep(0.5)

    def _handle_property_ack(
        self,
        callback,
        property_name,
        property_value,
        property_version,
        component_name=None,
    ):
        if callback is not None:
            ret = callback(property_name, property_value, component_name)
        else:
            ret = True
        if ret:
            if component_name is not None:
                self._logger.debug("Acknowledging {}".format(property_name))
                self.send_property(
                    {
                        "{}".format(component_name): {
                            "{}".format(property_name): {
                                "ac": 200,
                                "ad": "Property received",
                                "av": property_version,
                                "value": property_value,
                            }
                        }
                    }
                )
            else:
                self._logger.debug("Acknowledging {}".format(property_name))
                self.send_property(
                    {
                        "{}".format(property_name): {
                            "ac": 200,
                            "ad": "Property received",
                            "av": property_version,
                            "value": property_value,
                        }
                    }
                )
        else:
            self._logger.debug(
                'Property "{}" unsuccessfully processed'.format(property_name)
            )

    def on_properties_update(self, patch):
        try:
            prop_cb = self._events[IoTCEvents.PROPERTIES]
        except:
            return
        # Set component at false by default
        is_component = False

        for prop in patch:
            is_component = False
            if prop == "$version":
                continue

            # check if component
            try:
                is_component = patch[prop]["__t"]
            except KeyError:
                pass
            if is_component:
                for component_prop in patch[prop]:
                    if component_prop == "__t":
                        continue
                    self._logger.debug(
                        'In component "{}" for property "{}"'.format(
                            prop, component_prop
                        )
                    )
                    self._handle_property_ack(
                        prop_cb,
                        component_prop,
                        patch[prop][component_prop]["value"],
                        patch["$version"],
                        prop,
                    )
            else:
                self._handle_property_ack(
                    prop_cb, prop, patch[prop]["value"], patch["$version"]
                )

    def _cmd_resp(self, command: Command, value):
        self._logger.debug(
            'Responding to command "{}" request'.format(command.name))
        self.send_property({
            '{}'.format(command.name): {
                'value': value,
                'requestId': command.request_id
            }
        })

    def _on_commands(self, command: Command):
        try:
            cmd_cb = self._events[IoTCEvents.COMMANDS]
        except KeyError:
            return

        self._logger.debug(
            'Received command {}'.format(command.name))
        cmd_cb(command)

    def _on_enqueued_commands(self, command: Command):
        try:
            cmd_cb = self._events[IoTCEvents.ENQUEUED_COMMANDS]
        except KeyError:
            return

        self._logger.debug(
            'Received enqueued command {}'.format(command.name))

        cmd_cb(command)
