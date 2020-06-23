import sys
try:
    from utime import time
except:
    print('ERROR: missing dependency `utime`')

try:
    from math import floor
except:
    print('ERROR: missing dependency `math`')

try:
    from umqtt.robust import MQTTClient
except:
    print('ERROR: missing dependencies `micropython-umqtt.robust` and `micropython-umqtt.simple`')

try:
    import base64
except:
    print('ERROR: missing dependency `micropython-base64`')

try:
    import hmac
except:
    print('ERROR: missing dependency `micropython-hmac`')

try:
    import hashlib
except:
    print('ERROR: missing dependency `micropython-hashlib`')

try:
    from urllib.parse import quote_plus
except:
    print('ERROR: missing dependency `micropython-urllib.parse`')

try:
    import ssl
except:
    print('ERROR: missing dependency `micropython-ssl`')


from constants import IoTCConnectType


class ProvisioningClient():

    def __init__(self, scope_id, registration_id, credentials_type: IoTCConnectType, credentials, endpoint='global.azure-devices-provisioning.net'):
        self._endpoint = endpoint
        self._scope_id = scope_id
        self._registration_id = registration_id
        self._credentials_type = credentials_type
        if self._credentials_type in (IoTCConnectType.DEVICE_KEY, IoTCConnectType.SYMM_KEY):
            self._device_key = credentials
            if self._credentials_type == IoTCConnectType.SYMM_KEY:
                self._device_key = self._compute_key(
                    credentials, self._registration_id)
                # self._logger.debug('Device key: {}'.format(self._key_or_cert))
        else:
            self._key_file = self.credentials['key_file']
            self._cert_file = self.credentials['cert_file']
            # try:
            #     self._cert_phrase = self.credentials['cert_phrase']
            #     # TODO: x509 = X509(self._cert_file, self._key_file, self._cert_phrase)
            # except:
            #     # self._logger.debug(
            #         'No passphrase available for certificate. Trying without it')
            #     # TODO: x509 = X509(self._cert_file, self._key_file)
        self._mqtt_username = '{}/registrations/{}/api-version=2019-03-31'.format(
            scope_id, registration_id)
        resource_uri = '{}/registrations/{}'.format(
            scope_id, registration_id)
        expiry = floor(time())+21600  # 6 hours from now
        signature = quote_plus(self._compute_key(
            self._device_key, '{}\n{}'.format(resource_uri, expiry)))
        self._mqtt_password = 'SharedAccessSignature sr={}&sig={}&se={}&skn=registration'.format(
            quote_plus(resource_uri), signature, expiry)

        self._request_id = int(time())
        self._client = MQTTClient(self._registration_id, self._endpoint, port=8883,ssl=True, user=self._mqtt_username,
                                  password=self._mqtt_password)

    def register(self):
        self._client.connect()

    def _compute_key(self, key, payload):
        try:
            secret = base64.b64decode(key)
        except:
            print("ERROR: broken base64 secret => `" + secret + "`")
            sys.exit()

        return base64.b64encode(hmac.new(secret, msg=payload.encode('utf8'), digestmod=hashlib._sha256.sha256).digest())

