
import permit

ACCESS_MAP = {
    'user': permit.USER,
    'trusted': permit.USER | permit.TRUSTED,
    'cheef': permit.USER | permit.TRUSTED | permit.CHEEF
}

def acceptHandler(connection, message, params):
    usersList = params.users

    # We wouldn't be here if params missing
    userName = params.args[0]

    usersList.create(userName)
    usersList.save()

    return "User created: %s" % userName

def accessHandler(connection, message, params):
    usersList = params.users

    # We wouldn't be here if params missing
    userName = params.args[0]
    userAccess = params.args[1]

    user = usersList.get(userName)

    if userAccess not in ACCESS_MAP:
        return "Access level not found: %s" % userAccess

    if not user:
        return "User not found: %s" % userName

    if user.guest:
        return "User not known: %s" % userName

    user.access = ACCESS_MAP[userAccess]
    user.save()

    return "Access '%s' set for: %s" % (userAccess, userName)

def hook(store):
    store.register(acceptHandler, "^[Aa]ccept ([\w\.\@\!\$]+)$", "Accept guest to known users", store.access.CHEEF)
    store.register(accessHandler, "^[Aa]ccess ([\w\.\@\!\$]+) (\w+)$", "Set access level for user", store.access.CHEEF)
