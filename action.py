
import re
import os
import sys

import permit

# Workaround for python premature modules GC
MODULES = []

def unknownAction(*a):
    return "Idantaundastandfh"

class ActionStore:

    def __init__(self):
        self.handlers = []
        # Exported ACCESS variables for registration
        self.access = permit

        self.register(unknownAction, ".*", access=(permit.USER | permit.TRUSTED | permit.CHEEF))

    def __iter__(self):
        return iter(self.handlers)

    def load(self, directory):
        global MODULES

        if not os.path.isdir(directory):
            raise ValueError("Invalid handlers directory: %s" % directory)

        imports = []
        for fileName in os.listdir(directory):
            if not re.search("\.py$", fileName):
                continue
            moduleName = fileName[:fileName.rfind('.')]
            imports.append(moduleName)

        MODULES = []

        sys.path.append(directory)
        for moduleName in imports:
            try:
                module = __import__(moduleName)
                MODULES.append(module)
                del sys.modules[moduleName]             #remove it form modules registry
            except ImportError as e:
                # TODO(edzius): do not keep quiet, log warning
                pass
        sys.path.remove(directory)

        for module in MODULES:
            if 'hook' not in dir(module):
                continue

            try:
                module.hook(self)
            except Exception as e:
                # TODO(edzius): do not keep quiet, log warning
                pass

    def register(self, fn, pattern, about=None, access=None):
        item = {
            'execute': fn,
            'matcher': re.compile(pattern),
            'about': about,
            'access': access or permit.USER
        }
        self.handlers.insert(0, item)

    def select(self, data, permit=255):
        for handler in self.handlers:
            if not (handler['access'] & permit):
                continue

            result = handler['matcher'].match(data)
            if not result:
                continue
            return handler['execute'], result

        return None, None
