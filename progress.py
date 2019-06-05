from time import time
import sys

bar_length = 20


def format_time(seconds):
    h, ms = divmod(int(seconds), 3600)
    m, s = divmod(ms, 60)
    return "{}:{:02}:{:02}".format(h, m, s)


def bar(iterator, length):
    start_t = time()

    def update_bar(i):
        if length > 0:
            int_prop = (i * bar_length) // length
        else:
            int_prop = bar_length
        bar = "#" * int_prop + "-" * (bar_length - int_prop)
        if i > 0:
            elasped_t = time() - start_t
            total_t = (elasped_t / i) * length
        else:
            elasped_t = 0
            total_t = 0
        text = '[{bar}] {i}/{len} {elasped_t}/{total_t}\r'.format(bar=bar, i=i, len=length, elasped_t=format_time(elasped_t), total_t=format_time(total_t))
        sys.stdout.write(text)
        sys.stdout.flush()

    for i, obj in enumerate(iterator):
        update_bar(i)
        yield obj
    update_bar(length)
    sys.stdout.write('\n')
    sys.stdout.flush()
