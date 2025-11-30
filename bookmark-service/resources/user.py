from http import HTTPStatus

from extensions import limiter
from flask import request

# from flask import url_for
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_optional
from flask_jwt_extended import jwt_required
from flask_restx import Resource

# from utils import generate_token
from marshmallow.exceptions import ValidationError
from models.bookmark import Bookmark
from models.user import User
from schemas.bookmark import BookmarkPaginationSchema
from schemas.bookmark import BookmarkSchema
from schemas.user import UserSchema
from utils import verify_token
from webargs import fields
from webargs.flaskparser import use_kwargs

user_schema = UserSchema()
user_public_schema = UserSchema(exclude=('email',))
bookmark_list_schema = BookmarkSchema(many=True)
bookmark_pagination_schema = BookmarkPaginationSchema()


class UserListResource(Resource):
    def post(self):
        json_data = request.get_json()

        try:
            data = user_schema.load(data=json_data)
        except ValidationError as ex:
            return {
                'message': 'Validation errors',
                'errors': str(ex),
            }, HTTPStatus.BAD_REQUEST

        if User.get_by_username(data.get('username')):
            return {'message': 'username already used'}, HTTPStatus.BAD_REQUEST

        if User.get_by_email(data.get('email')):
            return {'message': 'email already used'}, HTTPStatus.BAD_REQUEST

        user = User(**data)
        user.save()
        return user_schema.dump(user), HTTPStatus.CREATED


class UserResource(Resource):
    @jwt_optional
    def get(self, username):
        user = User.get_by_username(username=username)

        if user is None:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user == user.id:
            data = user_schema.dump(user).data
        else:
            data = user_public_schema.dump(user)

        return data, HTTPStatus.OK


class MeResource(Resource):
    @jwt_required
    def get(self):
        user = User.get_by_id(id=get_jwt_identity())

        return user_schema.dump(user), HTTPStatus.OK


class UserBookmarkListResource(Resource):
    decorators = [
        limiter.limit(
            '3/minute;30/hour;300/day',
            methods=['GET'],
            error_message='Too Many Requests',
        )
    ]

    @jwt_optional
    @use_kwargs(
        {
            'page': fields.Int(missing=1),
            'per_page': fields.Int(missing=10),
            'visibility': fields.Str(missing='public'),
        }
    )
    def get(self, username, page, per_page, visibility):
        user = User.get_by_username(username=username)

        if user is None:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        paginated_recipes = Bookmark.get_all_by_user(user_id=user.id, page=page, per_page=per_page)

        return bookmark_pagination_schema.dump(paginated_recipes), HTTPStatus.OK


class UserActivateResource(Resource):
    def get(self, token):
        email = verify_token(token, salt='activate')

        if email is False:
            return {'message': 'Invalid token or token expired'}, HTTPStatus.BAD_REQUEST

        user = User.get_by_email(email=email)

        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

        if user.is_active is True:
            return {'message': 'The user account is already activated'}, HTTPStatus.BAD_REQUEST

        user.is_active = True
        user.save()
        return {}, HTTPStatus.NO_CONTENT
