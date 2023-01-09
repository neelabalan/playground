from flask.cli import FlaskGroup

from app import app
from app import db

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()
    print("Completed executing create_db command")


if __name__ == "__main__":
    cli()
