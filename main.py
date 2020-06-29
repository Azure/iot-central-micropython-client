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
device_id='upy3'
key='r0mxLzPr9gg5DfsaxVhOwKK2+8jEHNclmCeb9iACAyb2A7yHPDrB2/+PTmwnTAetvI6oQkwarWHxYbkIVLybEg=='
conn_type=IoTCConnectType.SYMM_KEY

prov=ProvisioningClient(scope_id,device_id,conn_type,key,logger,'urn:testapplucaM3:TestC2D_7f7:5')
creds=prov.register()
from device import DeviceClient
client=DeviceClient(device_id,creds,logger)

def on_properties(name, value):
    print('Received property {} with value {}'.format(name, value))
    return value


def on_commands(command, ack):
    print('Command {}.'.format(command.name))
    ack(command, command.payload)


client.on(IoTCEvents.PROPERTIES, on_properties)
client.on(IoTCEvents.COMMANDS, on_commands)
client.connect()

client.send_property({'devProp':10})


while client.is_connected():
    client.listen()
    print('Sending telemetry')
    client.send_telemetry({'temperature':randint(0,20),'pressure':randint(0,20),'humidity':randint(0,20)})
    sleep(2)

