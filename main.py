from constants import *
from provision import ProvisioningClient
from utime import sleep

try:
    from random import randint
except:
    import upip
    upip.install('micropython-random')
    from random import randint

logger = ConsoleLogger(IoTCLogLevel.ALL)
scope_id='0ne0011423C'
device_id='upy2'
key='r0mxLzPr9gg5DfsaxVhOwKK2+8jEHNclmCeb9iACAyb2A7yHPDrB2/+PTmwnTAetvI6oQkwarWHxYbkIVLybEg=='
conn_type=IoTCConnectType.SYMM_KEY

prov=ProvisioningClient(scope_id,device_id,conn_type,key,logger)
creds=prov.register()
from device import DeviceClient
client=DeviceClient(device_id,creds,logger)

def on_properties(name, value):
    print('Received property {} with value {}'.format(name, value))
    return value


def on_commands(command, ack):
    print('Received command {}.'.format(command.name))
    ack(command, command.payload)


client.on(IoTCEvents.PROPERTIES, on_properties)
client.on(IoTCEvents.COMMANDS, on_commands)
client.set_model_id('urn:testapplucaM3:TestC2D_7f7:5')
client.connect()

while client.is_connected():
    print('Sending telemetry')
    client.listen()
    sleep(3)
    client.send_telemetry({'temperature':randint(0,30),'pressure':randint(0,30),'humidity':randint(0,30)})
