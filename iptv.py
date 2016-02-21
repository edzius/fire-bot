
import socket
import subprocess

def currentIp():
    # FIXME(edzius): avoid hardcoding in code!
    return "78.58.172.68"

def validateIp(addr):
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False

def listAddresses():
    try:
        result = subprocess.check_output('./iptv -l', stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        return None

    return result

def removeAddress(ip):
    if not ip:
        return False

    try:
        subprocess.check_call('./iptv -r %s' % (ip,), stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        return False

    return True

def insertAddress(ip):
    if not ip:
        return False

    try:
        subprocess.check_call('./iptv -c %s' % (ip,), stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        return False

    return True

def changeAddress(newIp, oldIp):
    if not newIp or not oldIp:
        return False

    try:
        subprocess.check_call('./iptv -r %s %s' % (oldIp, newIp,), stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        return False

    return True
