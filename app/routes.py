import logging

logger = logging.getLogger(__name__)

def create_routes(app, **controllers):
    metrics_app = controllers["metrics"]
    # static rule
    app.add_url_rule('/metrics', endpoint=None, view_func=metrics_app.get_metrics_data)

    logger.info(app.url_map)
