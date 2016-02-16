.PHONY: all clean

#CFLAGS += -DDEBUG_ARGS
#CFLAGS += -DIPTABLES_IPTV=\"INPUT\"

all: iptv

iptv: iptv.c

clean:
	rm -f iptv
