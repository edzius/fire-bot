
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>              /* Obtain O_* constant definitions */
#include <unistd.h>
#include <arpa/inet.h>

#define STRING_MAX 64
#define BUFFER_MAX 8096
#define IPADDR_MAX 16
#define IPTABLES_BIN "/sbin/iptables"
#ifndef IPTABLES_IPTV
#define IPTABLES_IPTV "IPTV"
#endif

struct ipt_rule {
	int index;
	char addr[IPADDR_MAX];
};

#ifdef DEBUG_ARGS
static void dump_args(char *args[], int count)
{
	printf("ARGS: ");
	for (int i = 0; i < count; i++) {
		printf("%s ", args[i]);
	}
	printf("\n");
}
#endif

static void usage(const char *exec)
{
	printf("Usage: %s [-l] [-c] [-r OLD_IP] [NEW_IP]\n", exec);
	printf("Examples:\n");
	printf("\t%s -l -- list available rules\n", exec);
	printf("\t%s -c 0.0.0.0 -- create rule for given IP address\n", exec);
	printf("\t%s -r 0.0.0.0 -- remove rule for given IP address\n", exec);
	printf("\t%s -r 0.0.0.0 1.1.1.1 -- replace rule for given IP address\n", exec);
}

static void die(const char *format, ...)
{
	char buffer[STRING_MAX];
	int saved = errno;

	if (format != NULL) {
		va_list ap;

		va_start(ap, format);
		vsnprintf(buffer, STRING_MAX, format, ap);
		va_end(ap);
	}

	fprintf(stderr, "%s (%d)\n", buffer, saved);
	exit(1);
}

static int iptv_rule_split(char *line, struct ipt_rule *rule) {
	char *token;

	token = strtok(line, " ");
	rule->index = atoi(token);
	strtok(NULL, " ");
	strtok(NULL, " ");
	strtok(NULL, " ");
	token = strtok(NULL, " ");
	strncpy(rule->addr, token, IPADDR_MAX);

	// Remove subnet prefixes
	char *slash = strchr(rule->addr, '/');
	if (slash) {
		*slash = 0;
	}

	return 0;
}

static int iptv_rules_parse(char *buffer, struct ipt_rule **found) {
	int count = 0;
	char *token;
	char *lines[128];

	struct ipt_rule *rules;

	token = strtok(buffer, "\n");	// Chain name
	token = strtok(NULL, "\n");	// Header row
	while ((token = strtok(NULL, "\n"))) {
		lines[count] = token;
		count += 1;
	}

	rules = calloc(count, sizeof(struct ipt_rule));

	int i, s = 0;
	for (i = 0; i < count; i++) {
		if (iptv_rule_split(lines[i], &rules[s]))
			continue;
		s += 1;
	}

	*found = rules;

	return count;
}

static int iptv_rules_read(char *buffer, int size)
{
	int pipefd[2];

	if (pipe(pipefd))
		die("pipe(): failed");

	int pid = fork();
	if (pid == -1) {
		die("fork(): failed");
	} else if (pid == 0) {
		char *argv[] = { IPTABLES_BIN, "--line-numbers", "-n", "-L", IPTABLES_IPTV, NULL };
#ifndef DEBUG_ARGS
		dup2(pipefd[1], STDOUT_FILENO);
		close(pipefd[0]);
		close(pipefd[1]);
		execv(IPTABLES_BIN, argv);
		/* We don't get here */
		die("execv(): failed");
#else
		dump_args(argv, 6);
		exit(EXIT_SUCCESS);
#endif
	} else {
		int cnt = 0;
		*buffer = 0;
#ifndef DEBUG_ARGS
		close(pipefd[1]);
		cnt = read(pipefd[0], buffer, size);
		close(pipefd[0]);
#endif
		return cnt;
	}
}

static int iptv_rules_exec(const char *cliargs)
{
	int pid = fork();
	if (pid == -1) {
		die("fork(): failed");
	} else if (pid == 0) {
		char *token;
		char *args[16];
		int argind = 0;
		args[argind++] = IPTABLES_BIN;
		args[argind++] = strtok(strdup(cliargs), " ");
		while ((args[argind++] = strtok(NULL, " "))) { }
#ifndef DEBUG_ARGS
		execv(IPTABLES_BIN, args);
		/* We don't get here */
		die("execv(): failed");
#else
		dump_args(args, argind);
		exit(EXIT_SUCCESS);
#endif
	}
}

static int validate_ip(const char *addr)
{
	struct in_addr dst;
	if (inet_pton(AF_INET, addr, &dst) <= 0) {
		return 0;
	}
	return 1;
}

static int iptv_rule_find(struct ipt_rule *rules, int count, const char *addr)
{
	int i;
	for (i = 0; i < count; i++) {
		if (!strcmp(rules[i].addr, addr)) {
			return rules[i].index;
		}
	}
	return -1;
}

static void iptv_rules_list(struct ipt_rule *rules, int count)
{
	int i;
	for (i = 0; i < count; i++) {
		printf("%u: %s\n", rules[i].index, rules[i].addr);
	}
}

static void iptv_rule_create(const char *addr)
{
	char buffer[64];
	if (snprintf(buffer, sizeof(buffer), "-I "IPTABLES_IPTV" -s %s -j ACCEPT", addr) < 0) {
		die("snprinf(): failed");
	}
	iptv_rules_exec(buffer);
}

static void iptv_rule_delete(int index)
{
	char buffer[64];
	if (snprintf(buffer, sizeof(buffer), "-D "IPTABLES_IPTV" %i", index) < 0) {
		die("snprinf(): failed");
	}
	iptv_rules_exec(buffer);
}

static void iptv_rule_replace(const char *addr, int index)
{
	char buffer[64];
	if (snprintf(buffer, sizeof(buffer), "-R "IPTABLES_IPTV" %i -s %s -j ACCEPT", index, addr) < 0) {
		die("snprinf(): failed");
	}
	iptv_rules_exec(buffer);
}

int main(int argc, char *argv[])
{
	struct ipt_rule *rules;
	int count;
	char buffer[BUFFER_MAX];

	char *prog = argv[0];
	char c;
	int rules_list = 0;
	int rule_create = 0;
	char *rule_replace = NULL;
	char *rule_address = NULL;

	while ((c = getopt(argc, argv, "hlcr:")) != -1) {
		switch (c) {
		case 'l':
			rules_list = 1;
			break;
		case 'c':
			rule_create = 1;
			break;
		case 'r':
			if (!validate_ip(optarg)) {
				printf("Invalid IP address: %s\n", optarg);
				exit(EXIT_FAILURE);
			}
			rule_replace = strdup(optarg);
			break;
		case 'h':
		default: /* '?' */
			usage(prog);
			exit(EXIT_FAILURE);
		}
	}

	argc -= optind;
	argv += optind;

	if (!*argv) {
		if (rule_create) {
			usage(prog);
			exit(EXIT_FAILURE);
		}
	} else {
		if (!validate_ip(*argv)) {
			printf("Invalid IP address: %s\n", *argv);
			exit(EXIT_FAILURE);
		}
		rule_address = strdup(*argv);
	}

	// Execution

	iptv_rules_read(buffer, sizeof(buffer));
	count = iptv_rules_parse(buffer, &rules);

	if (rules_list) {
		iptv_rules_list(rules, count);
	} else if (rule_create) {
		int rule_index = iptv_rule_find(rules, count, rule_address);
#ifndef DEBUG_ARGS
		if (rule_index != -1) {
			printf("Rule exists for IP: %s\n", rule_address);
			exit(EXIT_FAILURE);
		}
#endif
		iptv_rule_create(rule_address);
	} else if (rule_replace) {
		int rule_index = iptv_rule_find(rules, count, rule_replace);
#ifndef DEBUG_ARGS
		if (rule_index == -1) {
			printf("No rule for IP: %s\n", rule_replace);
			exit(EXIT_FAILURE);
		}
#endif
		if (!rule_address) {
			iptv_rule_delete(rule_index);
		} else {
			iptv_rule_replace(rule_address, rule_index);
		}
	}

	exit(EXIT_SUCCESS);
}

