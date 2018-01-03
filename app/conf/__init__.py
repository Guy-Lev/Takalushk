from os import environ

environment = environ.get("ENVIRONMENT_TYPE", "default")

if environment == "production":
    from app.conf.production import config
elif environment == "staging":
    from app.conf.staging import config
else:
    from app.conf.default import config

conf = {"app": {"name": environ['APP_NAME']},
        "rds": {'username': environ['RDS_USERNAME'],
                'password': environ['RDS_PASSWORD'],
                'host': environ['RDS_HOSTNAME'],
                'port': environ['RDS_PORT'],
                'dbname': environ['RDS_DB_NAME'],
                'revid': environ.get("REV_ID", 'head')}
        }
conf.update(config)
