from flask import Flask
from flask_migrate import Migrate
from flask_restx import Api
from loguru import logger

# from config import AppConfig
from extensions import cache
from extensions import db
from extensions import jwt
from extensions import limiter
from resources.bookmark import BookmarkListResource
from resources.bookmark import BookmarkResource
from resources.token import RefreshResource
from resources.token import RevokeResource
from resources.token import TokenResource
from resources.token import black_list
from resources.user import MeResource
from resources.user import UserActivateResource
from resources.user import UserBookmarkListResource
from resources.user import UserListResource
from resources.user import UserResource

app = Flask(__name__)
app.config.from_object("config.AppConfig")


def create_app():
    register_extensions(app)
    register_resources(app)

    return app


def register_extensions(app):
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        jti = decrypted_token["jti"]
        return jti in black_list


def register_resources(app):
    api = Api(app)

    api.add_resource(UserListResource, "/users")
    api.add_resource(UserActivateResource, "/users/activate/<string:token>")
    api.add_resource(UserResource, "/users/<string:username>")
    api.add_resource(UserBookmarkListResource, "/users/<string:username>/bookmarks")

    api.add_resource(MeResource, "/me")

    api.add_resource(TokenResource, "/token")
    api.add_resource(RefreshResource, "/refresh")
    api.add_resource(RevokeResource, "/revoke")

    api.add_resource(BookmarkListResource, "/bookmarks")
    api.add_resource(BookmarkResource, "/bookmarks/<int:bookmark_id>")


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
