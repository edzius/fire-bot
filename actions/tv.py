
import re
import base64
import hashlib

from datetime import datetime

import iptv

def ipListHandler(connection, message, params):
    usersList = params.users

    result = iptv.listAddresses()
    if not result:
        return 'Failed!'

    result = result.strip()
    matches = re.findall("[0-9]+: ([0-9\.]+)", result)
    # Guard for mocks
    if not matches:
        return result

    mapping = {}
    for ip in matches:
        mapping[ip] = None

    for userName in usersList.items():
        user = usersList.get(userName)
        if not user.ip:
            continue

        mapping[user.ip] = userName

    found = []
    for ip, name in mapping.items():
        if not name:
            found.append("%s - <NONE>" % (ip,))
            continue

        user = usersList.get(name)
        if not user.name:
            found.append("%s - %s" % (ip, name, user.name,))
        else:
            found.append("%s - %s (%s)" % (ip, name, user.name,))

    return "\n".join(found)

def ipDeleteHandler(connection, message, params):
    usersList = params.users

    if not params.args or len(params.args) < 1:
        userName = params.user
    else:
        userName = params.args[0]

    if not usersList.has(userName):
        return "No user"

    user = usersList.get(userName)

    if not user.ip:
        return 'No IP'

    if not iptv.removeAddress(user.ip):
        return 'Failed!'

    user.ip = None
    user.save()

    return 'Done!'

def ipChangeHandler(connection, message, params):
    usersList = params.users

    if not params.args or len(params.args) < 2:
        userName = params.user
        ip = params.args[0]
    else:
        userName = params.args[0]
        ip = params.args[1]

    if not usersList.has(userName):
        return "No user"

    if not iptv.validateIp(ip):
        return 'Invalid IP'

    user = usersList.get(userName)

    if not user.ip:
        result = iptv.insertAddress(ip)
    else:
        result = iptv.changeAddress(ip, user.ip)

    if not result:
        return 'Failed!'

    user.ip = newIp
    user.save()

    return 'Done!'

def ipRequestHandler(connection, message, params):
    m = hashlib.sha512()
    m.update(params.user)
    m.update(datetime.now().strftime("%Y%m%d-%H%M%S"))
    checkhash = base64.b32encode(m.digest())

    if not params.public.iptvChangeRequest:
        params.public.iptvChangeRequest = {}

    ipRequest = params.public.iptvChangeRequest

    # Check whether user has change request
    hashash = None
    for pending, user in ipRequest.items():
        if user == params.user:
            hashash = pending
    # Delete old if user has change request
    if hashash:
        del ipRequest[hashash]

    ipRequest[checkhash] = params.user

    return "Click URL to change IP: http://%s:9000/iptv?hash=%s" % (iptv.currentIp(), checkhash,)

def hook(store):
    store.register(ipRequestHandler, "^[Ii]ptv$", "Request URL to change user IP", store.access.USER)
    store.register(ipListHandler, "^[Ii]ptv list$", "List available IPTV IPs for users", store.access.TRUSTED | store.access.CHEEF)
    store.register(ipDeleteHandler, "^[Ii]ptv del$", "Unregister IPTV IP for current user", store.access.USER)
    store.register(ipChangeHandler, "^[Ii]ptv set ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)$", "Change IPTV IP for current user", store.access.USER)
    store.register(ipDeleteHandler, "^[Ii]ptv del ([\w\.\@\!\$]+)$", "Unregister IPTV IP for user", store.access.CHEEF)
    store.register(ipChangeHandler, "^[Ii]ptv set ([\w\.\@\!\$]+) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)$", "Change IPTV IP for user", store.access.CHEEF)
