import time, threading

class Logger:
    def __init__(self, prefix=""):
        self.prefix = prefix

    def log(self, msg):
        thread = threading.current_thread().name
        print(f"[{time.strftime('%H:%M:%S')}] [{self.prefix}] [{thread}] {msg}")
