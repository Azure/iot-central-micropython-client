from iotc import IoTCClient, IoTCEvents, IoTCConnectType,Credentials
from utime import sleep
import sys
from ntptime import settime
settime()
del sys.modules['ntptime']
client = IoTCClient('0ne0011423C', 'upy2', IoTCConnectType.SYMM_KEY,
                    'r0mxLzPr9gg5DfsaxVhOwKK2+8jEHNclmCeb9iACAyb2A7yHPDrB2/+PTmwnTAetvI6oQkwarWHxYbkIVLybEg==')


def on_properties(name, value):
    print('Received property {} with value {}'.format(name, value))
    return value


def on_commands(command, ack):
    print('Received command {}.'.format(command.name))
    ack(command, command.payload)


client.on(IoTCEvents.PROPERTIES, on_properties)
client.on(IoTCEvents.COMMANDS, on_commands)
client.set_model_id('urn:testapplucaM3:TestC2D_7f7:5')
from iotc import Credentials
client.connect(Credentials(host='iotc-1f9e162c-eacc-408d-9fb2-c9926a071037.azure-devices.net',user='iotc-1f9e162c-eacc-408d-9fb2-c9926a071037.azure-devices.net/upy2/?api-version=2019-03-30',password='SharedAccessSignature sr=iotc-1f9e162c-eacc-408d-9fb2-c9926a071037.azure-devices.net%2Fdevices%2Fupy2&sig=f3xRC%2BzBHuv04snPJ5ox2bg2fopv6f7AjXvw%2FZB5mFo%3D&se=1593194370'))

while client.is_connected():
    print('Sending telemetry')
    client.send_telemetry({'temperature':20,'pressure':40,'humidity':10})
    client.listen()
    sleep(3)
    print('here')
