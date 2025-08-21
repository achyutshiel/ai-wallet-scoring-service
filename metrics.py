from collections import deque

class Metrics:
    def __init__(self):
        self.processed_wallets = 0
        self.total_processing_ms = 0.0
        self.avg_processing_ms = 0.0
        self.last_errors = deque(maxlen=50)

    def record_success(self, processing_ms: float):
        self.processed_wallets += 1
        self.total_processing_ms += processing_ms
        if self.processed_wallets > 0:
            self.avg_processing_ms = self.total_processing_ms / self.processed_wallets

    def record_error(self, msg: str):
        self.last_errors.append(msg)
