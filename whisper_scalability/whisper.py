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
            return "%3.1f%s" % (num, x)
        num /= 1024.0

def magnitude_fmt(num):
    for x in ['','k','m']:
        if num < 1000:
            return "%2d%s" % (num, x)
        num /= 1000

# Color format based on daily bandwidth usage
# <10mb/d = good, <30mb/d ok, <100mb/d bad, 100mb/d+ fail.
def load_color_prefix(load):
    if load < (1024 * 1000 * 10):
        color_level = bcolors.OKBLUE
    elif load < (1024 * 1000 * 30):
        color_level = bcolors.OKGREEN
    elif load < (1024 * 1000 * 100):
        color_level = bcolors.WARNING
    else:
        color_level = bcolors.FAIL
    return color_level

def load_color_fmt(load, string):
    return load_color_prefix(load) + string + bcolors.ENDC

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

def bandwidth_usage(n_users):
    print(n_users)

# We assume a node is not relaying messages, but only sending
# Goal:
# - make it user-bound, not network-bound
# - reasonable bw and fetch time
# ~1GB per month, ~ 30 mb per day, ~1 mb per hour

def case1():
    # Case 1: only receiving messages meant for you
    load = envelope_size * envelopes_per_message * \
        received_messages_per_day

    print bcolors.HEADER + "\nCase 1. Only receiving messages meant for you" + bcolors.ENDC
    print ""
    print "Assumptions:"
    print "- A1. Envelope size (static): " + str(envelope_size) + "kb"
    print "- A2. Envelopes / message (static): " + str(envelopes_per_message)
    print "- A3. Received messages / day (static): " + str(received_messages_per_day)
    print "- A4. Only receiving messages meant for you"
    print ""
    print load_color_fmt(load, "For N users, receiving bandwidth is " + sizeof_fmt(load) + "/day")
    print ""
    print("------------------------------------------------------------")

def case2():
    # Case 2: receiving all messages

    def load_users(n_users):
        return envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users

    def usage_str(n_users):
        load = load_users(n_users)
        return load_color_fmt(load, "For " + magnitude_fmt(n_users) + " users, receiving bandwidth is " + sizeof_fmt(load_users(n_users)) + "/day")

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



# Assume half of all messages are in 1:1 and group chat
# XXX: Implicitly assume message/envelope ratio same for 1:1 and public,
# probably not true due to things like key negotiation and data sync
private_message_proportion = 0.5

def case3():
    # Case 3: all private messages go over one discovery topic

    # Public scales per usage, all private messages are received
    # over one discovery topic
    def load_users(n_users):
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)
        return total_load

    def usage_str(n_users):
        load = load_users(n_users)
        return load_color_fmt(load, "For " + magnitude_fmt(n_users) + " users, receiving bandwidth is " + sizeof_fmt(load_users(n_users)) + "/day")

    print bcolors.HEADER + "\nCase 3. All private messages go over one discovery topic" + bcolors.ENDC
    print ""
    print "Assumptions:"
    print "- A1. Envelope size (static): " + str(envelope_size) + "kb"
    print "- A2. Envelopes / message (static): " + str(envelopes_per_message)
    print "- A3. Received messages / day (static): " + str(received_messages_per_day)
    print "- A4. Proportion of private messages (static): " + str(private_message_proportion)
    print "- A5. Public messages only received by relevant recipients (static)"
    print "- A6. All private messages are received by everyone (same topic) (static)"
    print ""
    print usage_str(100)
    print usage_str(100 * 100)
    print usage_str(100 * 100 * 100)
    print ""
    print("------------------------------------------------------------")

def case4():
    # Case 4: all private messages are partitioned into shards

    partitions = 5000

    def load_users(n_users):
        if n_users < partitions:
            # Assume spread out, not colliding
            factor_load = 1
        else:
            # Assume spread out evenly, collides proportional to users
            factor_load = n_users / partitions
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * factor_load
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)
        return total_load

    def usage_str(n_users):
        load = load_users(n_users)
        return load_color_fmt(load, "For " + magnitude_fmt(n_users) + " users, receiving bandwidth is " + sizeof_fmt(load_users(n_users)) + "/day")

    print bcolors.HEADER + "\nCase 4. All private messages are partitioned into shards" + bcolors.ENDC
    print ""
    print "Assumptions:"
    print "- A1. Envelope size (static): " + str(envelope_size) + "kb"
    print "- A2. Envelopes / message (static): " + str(envelopes_per_message)
    print "- A3. Received messages / day (static): " + str(received_messages_per_day)
    print "- A4. Proportion of private messages (static): " + str(private_message_proportion)
    print "- A5. Public messages only received by relevant recipients (static)"
    print "- A6. Private messages are partitioned evenly across partition shards (static), n=" + str(partitions)
    print ""
    print usage_str(100)
    print usage_str(100 * 100)
    print usage_str(100 * 100 * 100)
    print ""
    print("------------------------------------------------------------")

case1()
case2()
case3()
case4()


# Ok, let's get serious. What assumptions do we need to encode?
# Also, what did I observe? I observed 15GB/m = 500mb per day.

# Things to encode:
# - Noisy topic
# - Duplicate messages
# - Bloom filter false positives
# - Bugs / invalid messages
# - Offline case dominant

# Now getting somewhere, still big discrepency though. I.e.
# Case 3. All private messages go over one discovery topic

# Assumptions:
# - A1. Envelope size (static): 1024kb
# - A2. Envelopes / message (static): 10
# - A3. Received messages / day (static): 100
# - A4. Proportion of private messages (static): 0.5
# - A5. All private messages are received by everyone (same topic) (static)
# - A6. Public messages only received by relevant recipients (static)

# For 100 users, receiving bandwidth is  49MB/day
# For 10k users, receiving bandwidth is   5GB/day
# For  1m users, receiving bandwidth is 477GB/day

# 50mb*30 = 1.5GB, I see 15GB so x10. What's missing?
# Heavy user, and duplicate messages (peers), Envelope size?
# Say * 4 (size) * 2 (duplicates) * 2 (usage) then it is within x8-16.
# Also missing bloom filter here

# I am also assuming we are roughly 100 users today, is this accurate?
# How many unique public keys have we seen in common chats the last month?

# TODO: It'd be neat if you could encode assumptions set
