from appmetrics.metrics import timer
from appmetrics.metrics import metric, new_counter

class TimerMetric(object):
    def __init__(self, name=None):
        self.timer_name = name

    def __call__(self, wrapped_method):
        name = self.timer_name if self.timer_name else wrapped_method.__name__
        def wrapping_timer(*args, **kwargs):
            with timer(name):
                return wrapped_method(*args, **kwargs)

        return wrapping_timer


def get_or_create_counter(name):
    try:
        return metric(name)
    except KeyError:
        return new_counter(name)

def report_success_metric(func):
    def metrics_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result.status_code >= 300:
            get_or_create_counter("{}_fail".format(func.__name__)).notify(1)
        else:
            get_or_create_counter("{}_success".format(func.__name__)).notify(1)

        return result

    return metrics_wrapper
