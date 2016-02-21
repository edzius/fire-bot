
def infoHandler(connection, message, params):
    usersList = params.users

    if not params.args or len(params.args) < 1:
        userName = params.user
    else:
        userName = params.args[0]

    if not usersList.has(userName):
        return "user: %s\nInformation bot found" % userName

    userData = usersList.get(userName)
    infoLines = []
    infoLines.append("User: %s" % userName)
    for k, v in userData:
        infoLines.append("%s: %s" % (k, v,))

    infoBlock = "\n".join(infoLines)
    return infoBlock

def listHandler(connection, message, params):
    usersList = params.users

    infoLines = []
    for userName in usersList.items():
        if usersList.isKnown(userName):
            infoLines.append("* %s" % userName)

    infoBlock = "\n".join(infoLines)
    return "Accepted users:\n%s" % infoBlock

def guestHandler(connection, message, params):
    usersList = params.users

    infoLines = []
    for userName in usersList.items():
        if usersList.isGuest(userName):
            user = usersList.get(userName)
            infoLines.append("* %s: %s" % (user.noticed, userName))

    infoBlock = "\n".join(infoLines)
    return "Guest users:\n%s" % infoBlock

def nameHandler(connection, message, params):
    user = params.self
    userName = params.args[0]

    user.name = userName
    user.save()

    return "You are now: %s" % userName

def hook(store):
    store.register(infoHandler, "^[Mm]e$", "Show collected information about current user", store.access.USER | store.access.TRUSTED | store.access.CHEEF)
    store.register(nameHandler, "^[Mm]y name is ([\w]+)$", "Set the real user name", store.access.USER | store.access.TRUSTED | store.access.CHEEF)
    store.register(infoHandler, "^[Ii]nfo ([\w\.\@\!\$]+)$", "Show collected information about user", store.access.TRUSTED)
    store.register(listHandler, "^[Ll]ist users$", "Show list of users", store.access.TRUSTED)
    store.register(guestHandler, "^[Ll]ist guests$", "Show list of guest attempts", store.access.TRUSTED)
