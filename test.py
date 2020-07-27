data="devices/264hjjv1hqf/messages/devicebound/%24.exp=2020-07-25T14%3A14%3A25.1720000Z&%24.mid=Commands%3Ac2d-Fr7guTmpM&%24.to=%2Fdevices%2F264hjjv1hqf%2Fmessages%2Fdevicebound&iothub-ack=none&method-name=Commands%3Ac2d"

params=data.split("devices/264hjjv1hqf/messages/devicebound/",1)[1].split('&')
fields={}
for param in params:
    p=param.split('=')
    if p[0] == "method-name":
        method_name=p[1].split("Commands%3A")[1]

print(method_name)