from appmetrics.metrics import REGISTRY, metrics_by_name_list
from flasgger import swag_from

from app.controllers.response_builder import ok


class GitController(object):
    @swag_from('../swagger/git.yml')
    def get_top_tests_for_repo(self):
        keys_list =  list(REGISTRY.keys())
        return ok(metrics_by_name_list(keys_list))
