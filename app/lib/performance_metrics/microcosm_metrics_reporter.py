import threading
import socket
from time import time
from collections import defaultdict
import logging


LOCK = threading.Lock()
COUNTERS_LAST_VALUES = {}
OUT_METRIC_DATA_TEMPLATE = "{token}.microcosm.{app}.{metric_name} {value} {now}"
PERCENTILE_METRIC_NAMES = ('50percentile',
                            '75percentile',
                            '90percentile',
                            '95percentile',
                            '99percentile',
                            '999percentile')
GIVEN_TIMER_METRICS = ('variance',
                        'median',
                        'max',
                        'min',
                        'arithmetic_mean',
                        'standard_deviation')
WANTED_TIMER_METRICS = GIVEN_TIMER_METRICS + PERCENTILE_METRIC_NAMES + ('count',)

logger = logging.getLogger(__name__)

report_build_map = defaultdict(lambda: 'log_unsupported_metric_type', {
    'histogram': 'build_timer_report',
    'counter': 'build_counter_report'})


class MetricsReporter(object):
    def __init__(self, app_prefix=None, endpoint=None, token=None):
        self.app_prefix = app_prefix
        self.endpoint = endpoint
        self.token = token

    def report_metrics(self, metrics):
        try:
            self.local_metrics_report(metrics)
            self.graphite_metrics_report(metrics)
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def local_metrics_report(metrics):
        logger.debug(metrics)

    def graphite_metrics_report(self, metrics):
        data = self.build_metric_data(metrics)
        self.report_to_graphite(data)

    def build_metric_data(self, metrics):
        map_metric_data = (self._parse_metric_row_data(*item) for item in metrics.items())
        return [data for data in map_metric_data if data]

    def report_to_graphite(self, data):
        text_report = '\n'.join(data).encode('utf-8')
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.sendto(text_report, (self.endpoint, 2003))

    def _parse_metric_row_data(self, name, metric):
        metric_type = metric['kind']
        build_report = self.get_metric_report_builder(metric_type)
        return build_report(name, metric)

    def get_metric_report_builder(self, metric_type):
        return getattr(self, report_build_map[metric_type])

    @staticmethod
    def log_unsupported_metric_type(*args):
        metric = args[1]
        logger.debug("Unsupported metric type: {}".format(metric['kind']))

    def build_timer_report(self, name, timer_data):
        relevant_timer_data = _extract_relevant_timer_data(timer_data)
        parsed_data = self._parse_timer_data(name, relevant_timer_data)
        return parsed_data

    def build_counter_report(self, name, counter_data):
        with LOCK:
            last_val = COUNTERS_LAST_VALUES.get(name, 0)
            value = counter_data['value'] - last_val
            COUNTERS_LAST_VALUES[name] = counter_data['value']
        return self._render_report(name, value)

    def _parse_timer_data(self, name, timer_data):
        return '\n'.join(self._render_report('{metric_name}.{metric_key}'.format(
            metric_name=name,
            metric_key=metric_point),
            metric_value)
                         for metric_point, metric_value in timer_data.items())

    def _render_report(self, metric_name, value):
        return OUT_METRIC_DATA_TEMPLATE.format(token=self.token,
                                               app=self.app_prefix,
                                               metric_name=metric_name,
                                               value=value,
                                               now=int(time()))


def _extract_relevant_timer_data(timer_data):
    extracted_data = dict(
        {metric_name: timer_data[metric_name] for metric_name in GIVEN_TIMER_METRICS},
        count=timer_data['n'],
        **_extract_percentile_data(timer_data['percentile']))
    return extracted_data


def _extract_percentile_data(percentiles):
    return {
        '{percentage}percentile'.format(percentage=_remove_decimal_point(percentile)): val
        for percentile, val in percentiles
    }


def _remove_decimal_point(number):
    return str(number).replace('.', '')


