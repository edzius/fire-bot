
import json

from datetime import datetime

import table
import permit

def readJson(fileName):
    try:
        fp = open(fileName)
    except IOError as e:
        return {}
    try:
        return json.load(fp)
    except ValueError as e:
        return {}

def writeJson(fileName, data):
    try:
        fp = open(fileName, "w")
    except IOError as e:
        pass
    try:
        return json.dump(data, fp)
    except ValueError as e:
        pass

class UserInfo(table.Table):

    def __init__(self, users, data):
        table.Table.__init__(self, data)
        self.__users = users

    def save(self):
        if not self.__users:
            return

        self.__users.save()

class UserStore:

    def __init__(self, dataFile):
        self.dataFile = dataFile
        self.data = readJson(dataFile)

    def __get_known(self, user):
        return UserInfo(self, user)

    def __get_guest(self, user):
        guest = {
            'guest': True,
            'noticed': user
        }
        return UserInfo(None, guest)

    def save(self):
        writeJson(self.dataFile, self.data)

    def has(self, uid):
        return uid in self.data

    def isGuest(self, uid):
        return self.has(uid) and type(self.data[uid]) != dict

    def isKnown(self, uid):
        return self.has(uid) and type(self.data[uid]) == dict

    def items(self):
        return self.data.keys()

    def get(self, uid):
        if self.isGuest(uid):
            return self.__get_guest(self.data[uid])
        elif self.isKnown(uid):
            return self.__get_known(self.data[uid])
        else:
            return None

    def create(self, uid):
        if self.isKnown(uid):
            return

        user = {
            'created': datetime.now().strftime("%Y%m%d-%H%M%S"),
            'access': permit.USER
        }
        self.data[uid] = user
        return self.__get_known(user)

    def remove(self, uid):
        if not self.has(uid):
            return

        del self.data[uid]

    def notice(self, uid):
        if self.isGuest(uid):
            return

        self.data[uid] = datetime.now().strftime("%Y%m%d-%H%M%S")
        # AUTOsave
        self.save()
        return self.__get_guest(self.data[uid])
