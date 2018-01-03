from appmetrics.metrics import REGISTRY, metrics_by_name_list
from flasgger import swag_from

from app.controllers.response_builder import ok


class MetricsController(object):
    @swag_from('../swagger/metrics.yml')
    def get_metrics_data(self):
        keys_list =  list(REGISTRY.keys())
        return ok(metrics_by_name_list(keys_list))
