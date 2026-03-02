import time, threading
import os

class Logger:
    def __init__(self, prefix="", log_file=None):
        """
        初始化 Logger
        :param prefix: 日志前缀
        :param log_file: 日志文件路径（可选），如果提供则同时写入文件和控制台
        """
        self.prefix = prefix
        # 若未显式传入，则尝试使用环境变量 TASK_LOG_FILE，方便将所有日志汇总到同一文件
        self.log_file = log_file or os.environ.get('TASK_LOG_FILE')
        self.file_lock = threading.Lock() if self.log_file else None
        
        # 如果指定了日志文件，确保目录存在
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

    def log(self, msg):
        thread = threading.current_thread().name
        log_msg = f"[{time.strftime('%H:%M:%S')}] [{self.prefix}] [{thread}] {msg}"
        
        # 始终输出到控制台
        print(log_msg)
        
        # 如果指定了日志文件，同时写入文件
        if self.log_file and self.file_lock:
            try:
                with self.file_lock:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(log_msg + '\n')
            except Exception as e:
                # 如果写入文件失败，只输出到控制台，不中断程序
                print(f"[Logger Error] 写入日志文件失败: {e}")
