
def helloHandler(connection, message, params):
    userName = params.user
    userData = params.self

    name = userData.name or userName

    return "Hello %s. How can i help you?" % name

def helpHandler(connection, message, params):
    userLevel = params.self.access or 0

    helpLines = []
    for handler in params.actions:
        if not (userLevel & handler['access']):
            continue

        about = handler['about']
        matcher = handler['matcher']
        if about:
            helpLines.append("%s -- %s" % (matcher.pattern, about))
        else:
            helpLines.append("%s" % matcher.pattern)

    if not len(helpLines):
        return "Feeling lonely?"

    # Remove last one as default handler
    del helpLines[-1]

    helpBlock = "\n".join(helpLines)
    return "Available command patterns:\n%s" % helpBlock

def hook(store):
    store.register(helpHandler, "^[Hh]elp$", "Shows this help menu", store.access.USER | store.access.TRUSTED | store.access.CHEEF)
    store.register(helloHandler, "^[Hh]ello$", "Say HELLO", store.access.USER | store.access.TRUSTED | store.access.CHEEF)
    store.register(helloHandler, "^[Hh]i$", "Say HELLO", store.access.USER | store.access.TRUSTED | store.access.CHEEF)
