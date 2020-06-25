import sys

try:
    from utime import time, sleep
except:
    print('ERROR: missing dependency `utime`')
    sys.exit(1)

import ubinascii
import hashlib

from .constants import IoTCConnectType
from .hmac import new as hmac
try:
    import urequests
except:
    import upip
    upip.install('micropython-urequests')
    import urequests

import json


class Credentials:

    def __init__(self, host, user, password):
        self._host=host
        self._user=user
        self._password=password

    @property
    def host(self):
        return self._host
    
    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

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
        self._username = '{}/registrations/{}/api-version=2019-03-31'.format(
            scope_id, registration_id)
        resource_uri = '{}/registrations/{}'.format(
            scope_id, registration_id)
        expiry = time() + 946706400   # 6 hours from now in epoch
        signature = encode_uri_component(self._compute_key(
            self._device_key, '{}\n{}'.format(resource_uri, expiry)))
        self._password = 'SharedAccessSignature sr={}&sig={}&se={}&skn=registration'.format(
            resource_uri, signature, expiry)
        self._request_id = int(time())
    

    def _on_message(self, topic, message):
        print(topic.decode('utf-8'))

    def register(self):
        headers = {"content-type": "application/json; charset=utf-8",
                   "user-agent": "iot-central-client/1.0", "Accept": "*/*", 'authorization': self._password}

        body = "{{\"registrationId\":\"{}\"}}".format(self._registration_id)
        uri = "https://{}/{}/registrations/{}/register?api-version={}".format(
            self._endpoint, self._scope_id, self._registration_id, '2019-03-31')
        response = urequests.put(uri, data=body, headers=headers)

        operation_id = json.loads(response.text)['operationId']
        sleep(2)
        uri = "https://{}/{}/registrations/{}/operations/{}?api-version={}".format(
            self._endpoint, self._scope_id, self._registration_id, operation_id, '2019-03-31')
        response = urequests.get(uri, headers=headers)
        if response.status_code == 200:
            assigned_hub = json.loads(response.text)[
                'registrationState']['assignedHub']
            expiry = time() + 946706400
            resource_uri = '{}/devices/{}'.format(
                assigned_hub, self._registration_id)
            signature = encode_uri_component(self._compute_key(
                self._device_key, '{}\n{}'.format(resource_uri, expiry)))
            print('Got hub details')
            return Credentials(assigned_hub,'{}/{}/?api-version=2019-03-30'.format(assigned_hub, self._registration_id),'SharedAccessSignature sr={}&sig={}&se={}'.format(resource_uri, signature, expiry))

    def _compute_key(self, key, payload):
        try:
            secret = ubinascii.a2b_base64(key)
        except:
            print("ERROR: broken base64 secret => `" + key + "`")
            sys.exit()

        ret = ubinascii.b2a_base64(hmac(secret, msg=payload.encode(
            'utf8'), digestmod=hashlib.sha256).digest()).decode('utf-8')
        ret = ret[:-1]
        return ret


unsafe = {
    '?': '%3F',
    ' ': '%20',
    '$': '%24',
    '%': '%25',
    '&': '%26',
    "\'": '%27',
    '/': '%2F',
    ':': '%3A',
    ';': '%3B',
    '+': '%2B',
    '=': '%3D',
    '@': '%40'
}


def encode_uri_component(string):
    ret = ''
    for char in string:
        if char in unsafe:
            char = unsafe[char]
        ret = '{}{}'.format(ret, char)
    return ret
