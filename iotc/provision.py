import sys
import gc
gc.collect()
import json
from iotc.constants import IoTCConnectType,encode_uri_component,ConsoleLogger,IoTCLogLevel
import ubinascii
import hashlib
from iotc.hmac import new as hmac
gc.collect()
try:
    from utime import time, sleep
except:
    print('ERROR: missing dependency `utime`')
    sys.exit(1)
gc.collect()

try:
    import urequests
except:
    import upip
    upip.install('micropython-urequests')
    import urequests
gc.collect()


class Credentials:

    def __init__(self, host, user, password):
        self._host = host
        self._user = user
        self._password = password

    @property
    def host(self):
        return self._host

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    def __str__(self):
        return 'Host={};User={};Password={}'.format(self._host,self._user,self._password)


class ProvisioningClient():

    def __init__(self, scope_id, registration_id, credentials_type: IoTCConnectType, credentials, logger, model_id=None, endpoint='global.azure-devices-provisioning.net'):
        self._endpoint = endpoint
        self._scope_id = scope_id
        self._registration_id = registration_id
        self._credentials_type = credentials_type
        self._api_version = '2019-01-15'
        if logger is not None:
            self._logger=logger
        else:
            self._logger=ConsoleLogger(IoTCLogLevel.DISABLED)

        if model_id is not None:
            self._model_id = model_id

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
        self._username = '{}/registrations/{}/api-version={}'.format(
            scope_id, registration_id, self._api_version)
        resource_uri = '{}/registrations/{}'.format(
            scope_id, registration_id)
        try:
            from ntptime import settime
            settime()
            gc.collect()
            del sys.modules['ntptime']
            gc.collect()
        except:
            pass
        
        expiry = time() + 946706400   # 6 hours from now in epoch
        signature = encode_uri_component(self._compute_key(
            self._device_key, '{}\n{}'.format(resource_uri, expiry)))
        self._password = 'SharedAccessSignature sr={}&sig={}&se={}&skn=registration'.format(
            resource_uri, signature, expiry)
        del expiry
        del signature
        gc.collect()
        self._logger.debug(self._username)
        self._logger.debug(self._password)
        self._headers = {"content-type": "application/json; charset=utf-8",
                         "user-agent": "iot-central-client/1.0", "Accept": "*/*", 'authorization': self._password}

    def _on_message(self, topic, message):
        print(topic.decode('utf-8'))

    def register(self):
        gc.collect()
        self._logger.debug('Registering...')
        body = {'registrationId': self._registration_id}
        try:
            body['data'] = {'iotcModelId': self._model_id}
        except:
            pass

        uri = "https://{}/{}/registrations/{}/register?api-version={}".format(
            self._endpoint, self._scope_id, self._registration_id, self._api_version)
        response = urequests.put(
            uri, data=json.dumps(body), headers=self._headers)
        operation_id = json.loads(response.text)['operationId']
        response.close()
        sleep(5)
        creds = self._loop_assignment(operation_id)
        self._clean_imports()
        self._logger.debug(creds)
        return creds

    def _loop_assignment(self, operation_id):
        gc.collect()
        self._logger.debug('Quering registration...')
        uri = "https://{}/{}/registrations/{}/operations/{}?api-version={}".format(
            self._endpoint, self._scope_id, self._registration_id, operation_id, self._api_version)
        response = urequests.get(uri, headers=self._headers)
        if response.status_code == 202:
            self._logger.debug('Assigning...')
            response.close()
            sleep(3)
            return self._loop_assignment(operation_id)
        elif response.status_code == 200:
            self._logger.debug('Assigned. {}'.format(response.text))
            assigned_hub = json.loads(response.text)[
                'registrationState']['assignedHub']
            response.close()
            expiry = time() + 946706400
            resource_uri = '{}/devices/{}'.format(
                assigned_hub, self._registration_id)
            signature = encode_uri_component(self._compute_key(
                self._device_key, '{}\n{}'.format(resource_uri, expiry)))
            self._logger.debug('Got hub details')
            return Credentials(assigned_hub, '{}/{}/?api-version=2019-03-30'.format(assigned_hub, self._registration_id), 'SharedAccessSignature sr={}&sig={}&se={}'.format(resource_uri, signature, expiry))
        else:
            return None

    def _compute_key(self, key, payload):
        try:
            secret = ubinascii.a2b_base64(key)
        except:
            self._logger.info("ERROR: broken base64 secret => `" + key + "`")
            sys.exit()

        ret = ubinascii.b2a_base64(hmac(secret, msg=payload.encode(
            'utf8'), digestmod=hashlib.sha256).digest()).decode('utf-8')
        ret = ret[:-1]
        return ret

    def _clean_imports(self):
        try:
            del sys.modules['ubinascii']
            del ubinascii
        except:
            pass
        try:
            del sys.modules['hashlib']
            del hashlib
        except:
            pass
        try:
            del sys.modules['iotc.hmac']
            del hmac
        except:
            pass
        try:
            del sys.modules['urequests']
            del urequests
        except:
            pass
