from appmetrics.reporter import register, fixed_interval_scheduler

from app.lib.performance_metrics.microcosm_metrics_reporter import *
from app.lib.performance_metrics.metrics import *

def register_metrics_reporter(interval=60, **reporter_config):
        microcosm_reporter = MetricsReporter(**reporter_config)
        register(microcosm_reporter.report_metrics,
                 fixed_interval_scheduler(interval))
