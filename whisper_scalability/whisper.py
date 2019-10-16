class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# We assume an envelope is 1kb
envelope_size = 1

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

# Case 1: only receiving messages meant for you
load = envelope_size * envelopes_per_message * \
    received_messages_per_day

if load < 10000:
    color_level = bcolors.OKBLUE
elif load < 30000:
    color_level = bcolors.OKGREEN
elif load < 100000:
    color_level = bcolors.WARNING
else:
    color_level = bcolors.FAIL

print bcolors.HEADER + "Case 1. Only receiving messages meant for you" + bcolors.ENDC
print ""
print "Assumptions:"
print "- A1. Envelope size (static): " + str(envelope_size) + "kb"
print "- A2. Envelopes / message (static): " + str(envelopes_per_message)
print "- A3. Received messages / day (static): " + str(received_messages_per_day)
print ""
print color_level + "Receiving bandwidth is " + str(load/1000) + "mb/day" + bcolors.ENDC
print ""

# Case 2: receiving all messages

# print bcolors.WARNING + "Warning: No active frommets remain. Continue?" + bcolors.ENDC
