import logging

from app.lib.performance_metrics.metrics import get_or_create_counter


class LogMetricsHandler(logging.Handler):
    def emit(self, record):
            get_or_create_counter(record.levelname).notify(1)
