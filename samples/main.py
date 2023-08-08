import sys
from utime import sleep
from random import randint
from iotc import IoTCClient,IoTCConnectType,IoTCLogLevel,IoTCEvents

# If your device needs wifi before running uncomment and adapt as necessary
# import network
# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect("SSID","password")
# print(wlan.isconnected())

scope_id=''
device_id=''
key=''
conn_type=IoTCConnectType.DEVICE_KEY

client=IoTCClient(scope_id,device_id,conn_type,key)
client.set_log_level(IoTCLogLevel.ALL)

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

