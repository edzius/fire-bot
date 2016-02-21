.PHONY: all clean

#CFLAGS += -DDEBUG_ARGS
#CFLAGS += -DIPTABLES_IPTV=\"INPUT\"

all: iptv

iptv: iptv.c

clean:
	rm -f iptv
	rm -rf dist/

dist: iptv
	mkdir -p dist/
	cp iptv dist/
	cp *.py dist/
	mkdir -p dist/actions/
	cp actions/*.py dist/actions/
