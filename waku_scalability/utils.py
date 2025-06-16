# Util and format functions
# -----------------------------------------------------------


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def sizeof_fmt(num):
    return "%.1f%s" % (num, "MB")


def sizeof_fmt_kb(num):
    return "%.2f%s" % (num * 1024, "KB")


def magnitude_fmt(num):
    for x in ["", "k", "m"]:
        if num < 1000:
            return "%2d%s" % (num, x)
        num /= 1000


# Color format based on daily bandwidth usage
# <10mb/d = good, <30mb/d ok, <100mb/d bad, 100mb/d+ fail.
def load_color_prefix(load):
    if load < (10):
        color_level = bcolors.OKBLUE
    elif load < (30):
        color_level = bcolors.OKGREEN
    elif load < (100):
        color_level = bcolors.WARNING
    else:
        color_level = bcolors.FAIL
    return color_level


def load_color_fmt(load, string):
    return load_color_prefix(load) + string + bcolors.ENDC


def get_header(string) -> str:
    return bcolors.HEADER + string + bcolors.ENDC + "\n"
