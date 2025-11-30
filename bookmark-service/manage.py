import os
import sys

from flask.cli import FlaskGroup
from flask_migrate import Migrate
from loguru import logger

probable_par_dir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]), os.pardir, os.pardir))
if os.path.exists(os.path.join(probable_par_dir, '__init__.py')):
    sys.path.insert(0, probable_par_dir)

from app import app
from app import db

cli = FlaskGroup(app)


@cli.command('create_db')
def create_db():
    db.init_app(app)
    db.drop_all()
    migrate = Migrate(app, db)
    db.create_all()
    db.session.commit()
    logger.info('completed executing create_db command')


if __name__ == '__main__':
    cli = cli()
