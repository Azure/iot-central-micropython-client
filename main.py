import sys
from utime import sleep

try:
    from random import randint
except:
    import upip
    upip.install('micropython-random')
    from random import randint

from iotc.provision import Credentials,IoTCConnectType,ProvisioningClient
from iotc.logger import ConsoleLogger,IoTCLogLevel
from iotc.device import DeviceClient,IoTCEvents

logger = ConsoleLogger(IoTCLogLevel.ALL)
scope_id='0ne0011423C'
device_id='264hjjv1hqf'
key='S8Zg6NINKgCvNIzSnX/JrYIkd5EuXRy5HKZxVPj6798='
conn_type=IoTCConnectType.DEVICE_KEY
prov=ProvisioningClient(scope_id,device_id,conn_type,key,logger)
creds=prov.register()
client=DeviceClient(device_id,creds,logger)

def on_properties(name, value):
    print('Received property {} with value {}'.format(name, value))
    return value


def on_commands(command, ack):
    print('Command {}.'.format(command.name))
    ack(command, command.payload)

def on_enqueued(command):
    print('Enqueued Command {}.'.format(command.name))


client.on(IoTCEvents.PROPERTIES, on_properties)
client.on(IoTCEvents.COMMANDS, on_commands)
client.connect()

client.send_property({'readOnlyProp':40})

while client.is_connected():
    client.listen()
    print('Sending telemetry')
    client.send_telemetry({'temperature':randint(0,20),'pressure':randint(0,20),'acceleration':{'x':randint(0,20),'y':randint(0,20)}})
    sleep(2)

