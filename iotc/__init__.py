from .provision import ProvisioningClient
from .constants import IoTCConnectType

def run():
    prov = ProvisioningClient('0ne00052362', 'smartd', IoTCConnectType.SYMM_KEY,
                            '68p6zEjwVNB6L/Dz8Wkz4VhaTrYqkndPrB0uJbWr2Hc/AmB+Qxz/eJJ9MIhLZFJ6hC0RmHMgfaYBkNTq84OCNQ==')
    print(prov._mqtt_password)
    print(prov._mqtt_username)
    prov.register()