# Util and format functions
#-----------------------------------------------------------

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
# TODO: Get rid of bytes and KB, always print as as MB and above, then %3.1f
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%6.1f%s" % (num, x)
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

def print_header(string):
    print bcolors.HEADER + string + bcolors.ENDC + "\n"

def print_assumptions(xs):
    print "Assumptions:"
    for x in xs:
        print x
    print ""

def usage_str(load_users_fn, n_users):
    load = load_users_fn(n_users)
    return load_color_fmt(load, "For " + magnitude_fmt(n_users) + " users, receiving bandwidth is " + sizeof_fmt(load_users_fn(n_users)) + "/day")

def print_usage(load_users):
    print usage_str(load_users, 100)
    print usage_str(load_users, 100 * 100)
    print usage_str(load_users, 100 * 100 * 100)
    print ""

# Assumptions
#-----------------------------------------------------------

# We assume a node is not relaying messages, but only sending
#
# Goal:
# - make it user-bound, not network-bound
# - reasonable bw and fetch time
# ~1GB per month, ~ 30 mb per day, ~1 mb per hour

envelope_size = 1024 # 1kb

# Due to negotiation, data sync, etc
# Rough assumed overhead, constant factor
envelopes_per_message = 10

received_messages_per_day = 100

# Assume half of all messages are in 1:1 and group chat
# XXX: Implicitly assume message/envelope ratio same for 1:1 and public,
# probably not true due to things like key negotiation and data sync
private_message_proportion = 0.5

# Number of partitions for partition topic
n_partitions = 5000

# On Bloom filter, false positive rate:
#
# Bloom logic
# f: in_set?(s, x) => (maybe, no)
# if false_positive high => lots of maybe => direct hits
# test happens at routing node and depends on what filter preference peer has,
# OR what request mailserver receives

bloom_size = 512     # size of filter, m
bloom_hash_fns = 3   # number of hash functions, k

# This correspond to topics in bloom filter
# Might be a tad too high, assuming roughly maps to conversations
# I.e. public chat + contact code + partition topic (1 topic per convo)
bloom_elements = 100 # elements in set, n

# Assuming optimal number of hash functions, i.e. k=(m/n)ln 2
# (512/100)*math.log(2) ~ 3.46
# Note that this is very sensitive, so if 200 element you want 1 hash fn, and
# if 50 topics you want 7. Understanding the implications using a suboptimal
# number of hash function is left as an exercise to the reader.
#
# Implied false positive rate (https://hur.st/bloomfilter/?n=100&p=&m=512&k=3)
# p=~0.087, roughly.
bloom_false_positive = 0.1 # false positive rate, p
# Sensitivity to n:
# n=50 => p=1%, n=100 => p=10%, n=200 => 30%
#
# Note that false positivity has two faces, one is in terms of extra bandwidth usage
# The other is in terms of anonymity / plausible deniability for listening on topic
# I.e. N envelopes go to node => 1% false positive rate => 1% of N goes to recipient node
# Even if they only wanted 1 message!
#
# The false positive is a factor of total network traffic

# If you are connected to two peers, you often get same message from both peers
# Even though both are acting according to protocol
# E.g. see https://our.status.im/whisper-pss-comparison/
# With mailservers and non perfect queries this might be higher
# On the other hand, with one mailserver it might be lower
benign_duplicate_receives = 2

# 90% time spent offline, i.e. 10% or ~2.5h per day online.
# Also note Whisper TTL, so when coming online you will get more envelopes
offline_time_proportion = 0.9

# Assumption strings
a1 = "- A1. Envelope size (static): " + str(envelope_size) + "kb"
a2 = "- A2. Envelopes / message (static): " + str(envelopes_per_message)
a3 = "- A3. Received messages / day (static): " + str(received_messages_per_day)
a4 = "- A4. Only receiving messages meant for you."
a5 = "- A5. Received messages for everyone."
a6 = "- A6. Proportion of private messages (static): " + str(private_message_proportion)
a7 = "- A7. Public messages only received by relevant recipients (static)."
a8 = "- A8. All private messages are received by everyone (same topic) (static)."
a9 = "- A9. Private messages are partitioned evenly across partition shards (static), n=" + str(n_partitions)
a10 = "- A10. Bloom filter size (m) (static): " + str(bloom_size)
a11 = "- A11. Bloom filter hash functions (k) (static): " + str(bloom_hash_fns)
a12 = "- A12. Bloom filter elements, i.e. topics, (n) (static): " + str(bloom_elements)
a13 = "- A13. Bloom filter assuming optimal k choice (sensitive to m, n)."
a14 = "- A14. Bloom filter false positive proportion of full traffic, p=" + str(bloom_false_positive)
a15 = "- A15. Benign duplicate receives factor (static): " + str(benign_duplicate_receives)
a16 = "- A16. No bad envelopes, bad PoW, expired, etc (static)."
a17 = "- A17. User is offline p% of the time (static) p=" + str(offline_time_proportion)
a18 = "- A18. No bad request, duplicate messages for mailservers, and overlap/retires are perfect (static)."
a19 = "- A19. Mailserver only fetches topic interested in."

# Cases
#-----------------------------------------------------------

# Case 1: only receiving messages meant for you
def case1():
    def load_users(n_users):
        return envelope_size * envelopes_per_message * \
            received_messages_per_day

    print_header("Case 1. Only receiving messages meant for you")
    print_assumptions([a1, a2, a3, a4])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Case 2: receiving all messages
def case2():

    def load_users(n_users):
        return envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users

    print_header("Case 2. Receiving messages for everyone")
    print_assumptions([a1, a2, a3, a5])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Case 3: all private messages go over one discovery topic
def case3():

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

    print_header("Case 3. All private messages go over one discovery topic")
    print_assumptions([a1, a2, a3, a6, a7, a8])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Case 4: all private messages are partitioned into shards
def case4():

    def load_users(n_users):
        if n_users < n_partitions:
            # Assume spread out, not colliding
            factor_load = 1
        else:
            # Assume spread out evenly, collides proportional to users
            factor_load = n_users / n_partitions
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * factor_load
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)
        return total_load

    print_header("Case 4. All private messages are partitioned into shards")
    print_assumptions([a1, a2, a3, a6, a7, a9])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Case 5: all messages are passed through a bloom filter with a certain false positive rate
def case5():

    def load_users(n_users):
        if n_users < n_partitions:
            # Assume spread out, not colliding
            factor_load = 1
        else:
            # Assume spread out evenly, collides proportional to users
            factor_load = n_users / n_partitions
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * factor_load
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)

        # false positive total network traffic, assuming full node relaying
        network_load = envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users
        false_positive_load = network_load * bloom_false_positive

        return total_load + false_positive_load

    print_header("Case 5. Case 4 + All messages are passed through bloom filter with false positive rate")
    print_assumptions([a1, a2, a3, a6, a7, a9, a10, a11, a12, a13, a14])
    print_usage(load_users)
    print("NOTE: Traffic extremely sensitive to bloom false positives")
    print("This completely dominates network traffic at scale.")
    print("With p=1% we get 10k users ~100MB/day and 1m users ~10gb/day)")
    print("------------------------------------------------------------")


# Case 6: Same as case 5 but with duplicate receives
def case6():

    def load_users(n_users):
        if n_users < n_partitions:
            # Assume spread out, not colliding
            factor_load = 1
        else:
            # Assume spread out evenly, collides proportional to users
            factor_load = n_users / n_partitions
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * factor_load
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)

        # false positive total network traffic, assuming full node relaying
        network_load = envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users
        false_positive_load = network_load * bloom_false_positive

        return (total_load + false_positive_load) * benign_duplicate_receives

    print_header("Case 6. Case 5 + Benign duplicate receives")
    print_assumptions([a1, a2, a3, a6, a7, a9, a10, a11, a12, a13, a14, a15, a16])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Case 7: Mailservers case
def case7():

    def load_users(n_users):
        if n_users < n_partitions:
            # Assume spread out, not colliding
            factor_load = 1
        else:
            # Assume spread out evenly, collides proportional to users
            factor_load = n_users / n_partitions
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * factor_load
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)

        # false positive total network traffic, assuming full node relaying
        network_load = envelope_size * envelopes_per_message * \
            received_messages_per_day * n_users

        false_positive_load = network_load * bloom_false_positive

        online_traffic = (total_load + false_positive_load) * benign_duplicate_receives
        # fetching happens with topics, also no duplicates
        offline_traffic = total_load

        total_traffic = (offline_traffic * offline_time_proportion) + \
            (online_traffic * (1 - offline_time_proportion))
        return total_traffic

    print_header("Case 7. Case 6 + Mailserver case under ideal conditions and mostly offline")
    print_assumptions([a1, a2, a3, a6, a7, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Case 8: Waka mode - like Infura but for chat, no metadata connection
def case8():

    def load_users(n_users):
        if n_users < n_partitions:
            # Assume spread out, not colliding
            factor_load = 1
        else:
            # Assume spread out evenly, collides proportional to users
            factor_load = n_users / n_partitions
        load_private = envelope_size * envelopes_per_message * \
            received_messages_per_day * factor_load
        load_public = envelope_size * envelopes_per_message * \
            received_messages_per_day
        total_load = load_private * private_message_proportion + \
            load_public * (1 - private_message_proportion)

        return total_load

    print_header("Case 8. Waka mode - no metadata protection with bloom filter and one node connected; still static shard")
    print("Next step up is to either only use contact code, or shard more aggressively.")
    print("Note that this requires change of other nodes behavior, not just local node.")
    print("")
    print_assumptions([a1, a2, a3, a6, a7, a9])
    print_usage(load_users)
    print("------------------------------------------------------------")

# Run cases
#-----------------------------------------------------------


# Print goals
print("")
print(bcolors.HEADER + "Whisper theoretical model. Attempts to encode characteristics of it." + bcolors.ENDC)
print("")
print("Goals:")
print("1. Ensure network scales by being user or usage bound, as opposed to bandwidth growing in proportion to network size.")
print("2. Staying with in a reasonable bandwidth limit for limited data plans.")
print("3. Do the above without materially impacting existing nodes.")
print("" + bcolors.ENDC)

case1()
case2()
case3()
case4()
case5()
case6()
case7()
case8()

# Notes
#-----------------------------------------------------------

# What did I observe? I observed 15GB/m = 500mb per day. This was with
# discovery topic. After case 6, with case 3 discovery multiplier (x50, and
# maybe tiny bit fewer bloom_n), this roughly checks out. Also heavy user +
# envelope size. And number of users?

# Things left to encode:
# - Bugs / invalid / bad envelopes
# - percentage offline probably impacts data sync overhead
# - as does number of envelopes per message for private/public chats
# - Unknowns?

# Feedback:
# Which of these assumptions are false?
# Any assumptions or conditions not accurately captured?
# Which are most interesting to you?
# Which do we want to verify, and what metrics do we need to verify?

# Misc:
# - If we x100 users tomorrow, how can we move the partition topic?
#   - also relevant for bloom filter p% at event
# - Show: path we are on today, and alternative path
# - Also not captured: fallover of relaying node, if it exceeds bandwidth link
# - It'd be neat if you could encode assumptions set
# - Get secondary out of model confirmation
# - How many unique public keys have we seen in common chats the last month?
