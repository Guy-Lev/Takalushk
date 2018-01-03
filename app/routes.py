import logging

logger = logging.getLogger(__name__)

def create_routes(app, **controllers):
    metrics_app = controllers["metrics"]
    git_app = controllers["git"]
    # static rule
    app.add_url_rule('/metrics', endpoint=None, view_func=metrics_app.get_metrics_data)
    app.add_url_rule('/git/init', endpoint=None, view_func=git_app.init_db)
    app.add_url_rule('/git/get_top', endpoint=None, view_func=git_app.init_db)

    logger.info(app.url_map)
