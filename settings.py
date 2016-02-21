
import sys
import ConfigParser

def die(fmt, *arg):
    msg = fmt % arg
    sys.stderr.write("ERROR: %s\n" % msg)
    sys.exit(1)

def load(fileName):
    try:
        fp = open(fileName)
    except IOError as e:
        die('Config file not found')

    config = ConfigParser.RawConfigParser()
    config.readfp(fp)
    return config
