from telegram import *

import signal
import sys


def main():
    while True:
        telegram_run()
        time.sleep(2)


if __name__ == '__main__':
    #signal.signal(signal.SIGTERM, sys.exit())
    main()