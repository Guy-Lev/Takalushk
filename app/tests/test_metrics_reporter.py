import uuid

import appmetrics
import pytest
from appmetrics.metrics import REGISTRY, new_gauge, new_histogram
from flask import Flask
from mock import Mock

from app.controllers.metrics_controller import MetricsController
from app.lib.performance_metrics import *


class TestMetricsReporter(object):
    @pytest.fixture
    def app(request):
        app = Flask('dummy')

        with app.app_context():
            yield app

    @pytest.fixture(autouse=True)
    def all_test_wrapper(self, request):
        clear_counters()
        self.metrics_reporter = MetricsReporter()
        request.addfinalizer(clear_counters)

    @pytest.fixture()
    def counter(self):
        name = random_string()
        new_counter(name)
        yield name

    @pytest.fixture()
    def timer(self):
        name = random_string() + 't'
        new_histogram(name)
        yield name

    @pytest.fixture()
    def gauge(self):
        new_gauge('unsupported_metric_kind')
        yield

    @pytest.fixture()
    def logger(self):
        logger.debug = Mock()
        logger.exception = Mock()
        yield logger

    @pytest.fixture()
    def udp(self):
        mock_udp = Mock()
        socket.socket = Mock()
        socket.socket.return_value = mock_udp
        yield mock_udp

    @pytest.fixture()
    def registry_call_back_parameter(self):
        registry = {name: metric_obj.get() for name, metric_obj in REGISTRY.items()}
        yield registry

    def test_should_return_an_existing_counter(self, counter):
        none_safe_existing_counter = metric(counter)
        existing_counter = get_or_create_counter(counter)

        assert none_safe_existing_counter is existing_counter
        assert type(existing_counter) is appmetrics.simple_metrics.Counter

    def test_should_return_a_new_counter(self):
        assert not REGISTRY
        new_counter = get_or_create_counter(random_string())
        assert type(new_counter) is appmetrics.simple_metrics.Counter

    def test_should_register_decorated_method_with_timer_name(self):
        @TimerMetric(name="name_will_be_wrapped")
        def will_be_wrapped():
            return "timer is wrapping me"

        return_val = will_be_wrapped()
        assert return_val == "timer is wrapping me"
        assert "name_will_be_wrapped" in REGISTRY

    def test_should_register_decorated_method_with_timer(self):
        @TimerMetric()
        def will_be_wrapped():
            return "timer is wrapping me"

        return_val = will_be_wrapped()
        assert return_val == "timer is wrapping me"
        assert "will_be_wrapped" in REGISTRY

    def test_should_register_decorated_method_with_counter(self):
        @report_success_metric
        def counter_will_be_wrapped():
            return Result(status_code=200, msg="ok")

        counter_will_be_wrapped()
        counter = get_or_create_counter("counter_will_be_wrapped_success")
        val_before = counter.get()["value"]
        counter_will_be_wrapped()
        assert val_before + 1 == counter.get()["value"]

    def test_should_register_decorated_method_with_counter_failed(self):
        @report_success_metric
        def counter_will_be_wrapped():
            return Result(status_code=500, msg="fail")

        counter_will_be_wrapped()
        counter = get_or_create_counter("counter_will_be_wrapped_fail")
        val_before = counter.get()["value"]
        counter_will_be_wrapped()
        assert val_before + 1 == counter.get()["value"]

    def test_should_parse_counter_metrics_registered(self,
                                                     counter,
                                                     registry_call_back_parameter):
        registerd_counter_metrics = self.metrics_reporter.build_metric_data(
                                                        registry_call_back_parameter)
        assert counter in registerd_counter_metrics[0]

    def test_should_log_unsupported_metrics(self,
                                            gauge,
                                            logger,
                                            registry_call_back_parameter):
        built_metric_data = self.metrics_reporter.build_metric_data(
                                                        registry_call_back_parameter)
        assert not built_metric_data
        logger.debug.assert_called_with('Unsupported metric type: gauge')

    def test_should_parse_timer_metrics_producing_a_line_per_wanted_metric_point(self,
                                                            timer,
                                                            registry_call_back_parameter):
        registerd_counter_metrics = self.metrics_reporter.build_metric_data(
                                                        registry_call_back_parameter)
        lines_of_timer_metrics = registerd_counter_metrics[0]
        assert timer in lines_of_timer_metrics
        assert all(metric_point in lines_of_timer_metrics
                   for metric_point in WANTED_TIMER_METRICS)
        metric_points_parsed = lines_of_timer_metrics.split('\n')
        assert len(metric_points_parsed) == len(WANTED_TIMER_METRICS)

    def test_should_extract_each_timer_percentile_as_its_own_metric_point(self,
                                                          timer,
                                                          registry_call_back_parameter):
        registerd_counter_metrics = self.metrics_reporter.build_metric_data(
                                                        registry_call_back_parameter)
        lines_of_timer_metrics = registerd_counter_metrics[0]
        assert all(percentile_metric_point in lines_of_timer_metrics
                    for percentile_metric_point in PERCENTILE_METRIC_NAMES)
    
    def test_should_passively_handle_and_log_metric_report_errors(self, logger):
        error_causing_data = 1
        self.metrics_reporter.report_metrics(error_causing_data)
        assert logger.exception.called

    def test_should_send_metric_reports_to_hosted_graphite(self,
                                                           counter,
                                                           timer,
                                                           udp,
                                                           registry_call_back_parameter):
        self.metrics_reporter.report_metrics(registry_call_back_parameter)
        text_report = str(udp.sendto.call_args[0][0])
        assert all(metric in text_report for metric in (counter, timer))



    def test_metrics_controller(self, app):
        with app.app_context():
            get_or_create_counter("metrics")
            data = MetricsController().get_metrics_data()
            import json
            body = data.data.decode("utf-8")
            assert json.loads(body)["metrics"]["kind"] == "counter"
####################
### Test Helpers ###
####################

def clear_counters():
    REGISTRY.clear()

def random_string():
    return str(uuid.uuid4())[0:8]

class Result:
    def __init__(self, status_code, msg):
        self.status_code = status_code
        self.msg = msg

