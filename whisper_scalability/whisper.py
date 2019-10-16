class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# https://web.archive.org/web/20111010015624/http://blogmag.net/blog/read/38/Print_human_readable_file_size
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.0f%s" % (num, x)
        num /= 1024.0

def magnitude_fmt(num):
    for x in ['','k','m']:
        if num < 1000:
            return "%2d%s" % (num, x)
        num /= 1000

# We assume an envelope is 1kb
envelope_size = 1024

# 100, 10k, 1m - jumping two orders of magnitude
n_users = 10000

# Due to negotiation, data sync, etc
# Rough assumed overhead, constant factor
envelopes_per_message = 10

# Receiving messages per day
# TODO: Split up by channel, etc
received_messages_per_day = 100

# This means means 10*100*1= 1 MB per day

# oh, it is envelopes per time

# everyone received all messages

def bandwidth_usage(n_users):
    print(n_users)

#print(n_users * envelopes_per_message * received_messages_per_day)

# How much bandwidth does a receiving node waste?

# We assume a node is not relaying messages, but only sending

# Goal:
# - make it user-bound, not network-bound
# - reasonable bw and fetch time

# TODO: Offline take into account

# ~1GB per month, ~ 30 mb per day, ~1 mb per hour

# Offline proportion


def case1():
    # Case 1: only receiving messages meant for you
    load = envelope_size * envelopes_per_message * \
        received_messages_per_day

    if load < (1024 * 1000 * 10):
        color_level = bcolors.OKBLUE
    elif load < 30000:
        color_level = bcolors.OKGREEN
    elif load < 100000:
        color_level = bcolors.WARNING
    else:
        color_level = bcolors.FAIL

    print bcolors.HEADER + "\nCase 1. Only receiving messages meant for you" + bcolors.ENDC
    print ""
    print "Assumptions:"
    print "- A1. Envelope size (static): " + str(envelope_size) + "kb"
    print "- A2. Envelopes / message (static): " + str(envelopes_per_message)
    print "- A3. Received messages / day (static): " + str(received_messages_per_day)
    print "- A4. Only receiving messages meant for you"
    print ""
    print color_level + "For N users, receiving bandwidth is " + sizeof_fmt(load) + "/day" + bcolors.ENDC
    print ""
    print("------------------------------------------------------------")

def case2():
    # Case 2: receiving all messages

    def load_users(n_users):
        return envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users

    def color(n_users):
        load = load_users(n_users)
        if load < 10000:
            color_level = bcolors.OKBLUE
        elif load < 30000:
            color_level = bcolors.OKGREEN
        elif load < 100000:
            color_level = bcolors.WARNING
        else:
            color_level = bcolors.FAIL
        return color_level

    def usage_str(n_users):
        return color(n_users) + "For " + magnitude_fmt(n_users) + " users, receiving bandwidth is " + sizeof_fmt(load_users(n_users)) + "/day" + bcolors.ENDC

    print bcolors.HEADER + "\nCase 2. Receiving messages for everyone" + bcolors.ENDC
    print ""
    print "Assumptions:"
    print "- A1. Envelope size (static): " + str(envelope_size) + "kb"
    print "- A2. Envelopes / message (static): " + str(envelopes_per_message)
    print "- A3. Received messages / day (static): " + str(received_messages_per_day)
    print "- A4. Received messages for everyone"
    print ""
    print usage_str(100)
    print usage_str(100 * 100)
    print usage_str(100 * 100 * 100)
    print ""
    print("------------------------------------------------------------")


case1()
case2()


# Ok, let's get serious. What assumptions do we need to encode?
# Also, what did I observe? I observed 15GB/m = 500mb per day.
