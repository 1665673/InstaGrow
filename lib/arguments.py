import argparse


def amend_arguments(argv, amendments, upsert=False):
    argv = argv.copy()
    for key in amendments:
        value = amendments[key]
        if value is not None and not isinstance(value, list):
            value = [value]
        i = 0
        updated = False
        while i < len(argv):
            if key == argv[i]:
                # amend values of this argument
                j = i + 1
                # firstly, delete original associated sub arguments
                while j < len(argv) and argv[j][0] != '-':
                    del argv[j]
                # delete whole arguments, or append new sub arguments
                if value is None:
                    del argv[i]
                else:
                    for k in range(len(value)):
                        argv.insert(j + k, value[k])
                # break the inner loop. amendments for current key is done
                updated = True
                break
            i += 1
        if not updated and upsert:
            argv += [key] + (value if value is not None else [])
    return argv


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?', type=str)
    parser.add_argument("password", nargs='?', type=str)
    parser.add_argument("proxy", nargs='?', type=str)
    parser.add_argument("-w", "--worker", action="store_true")
    parser.add_argument("-user", "--username1", type=str)
    parser.add_argument("-pass", "--password1", type=str)
    parser.add_argument("-px", "--proxy1", type=str)
    parser.add_argument("-di", "--disable-image", action="store_true")
    parser.add_argument("-c", "--chrome", action="store_true")
    parser.add_argument("-g", "--gui", action="store_true")
    parser.add_argument("-o", "--owner", type=str)
    parser.add_argument("-i", "--instance", type=str)
    parser.add_argument("-v", "--version", type=str)
    parser.add_argument("-n", "--name", type=str)
    parser.add_argument("-t", "--tasks", nargs="+", type=str)
    parser.add_argument("-rt", "--remote-tasks", nargs="+", type=str)
    parser.add_argument("-ct", "--customer-tasks", nargs="+", type=str)
    parser.add_argument("-tg", "--tag", type=str)
    parser.add_argument("-p", "--pull", nargs="*", type=str)
    parser.add_argument("-pe", "--pull-exclude", nargs="*", type=str)
    parser.add_argument("-pb", "--pull-by", nargs="+", type=str)
    parser.add_argument("-ap", "--allocate-proxy", nargs="*", type=str)
    parser.add_argument("-q", "--query", action="store_true")
    parser.add_argument("-rp", "--retry-proxy", nargs="?", type=int, const=-1, default=0)
    parser.add_argument("-rc", "--retry-credentials", nargs="?", type=int, const=-1, default=0)
    parser.add_argument("-rl", "--retry-login", nargs="?", type=int, const=-1, default=0)
    parser.add_argument("-nc", "--no-cookies", action="store_true")
    parser.add_argument("-m", "--merge", nargs="?", type=str, const="")
    parser.add_argument("-s", "--silent", action="store_true")
    parser.add_argument("-wp", "--warm-up", nargs="*", type=str)
    return parser
