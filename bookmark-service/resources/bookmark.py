from http import HTTPStatus

from extensions import cache
from extensions import limiter
from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_optional
from flask_jwt_extended import jwt_required
from flask_restx import Resource
from loguru import logger
from marshmallow.exceptions import ValidationError
from models.bookmark import Bookmark
from schemas.bookmark import BookmarkPaginationSchema
from schemas.bookmark import BookmarkSchema
from utils import clear_cache
from webargs import fields
from webargs.flaskparser import use_kwargs

bookmark_schema = BookmarkSchema()
bookmark_pagination_schema = BookmarkPaginationSchema()


class BookmarkListResource(Resource):
    decorators = [limiter.limit('2 per minute', methods=['GET'], error_message='Too Many Requests')]

    @use_kwargs(
        {
            'q': fields.Str(missing=''),
            'page': fields.Int(missing=1),
            'per_page': fields.Int(missing=20),
            'sort': fields.Str(missing='created_at'),
            'order': fields.Str(missing='desc'),
        }
    )
    @cache.cached(timeout=60, query_string=True)
    def get(self, q, page, per_page, sort, order):
        logger.info('Getting bookmarks')

        if sort not in ['created_at']:
            sort = 'created_at'

        if order not in ['asc', 'desc']:
            order = 'desc'

        paginated_recipes = Bookmark.get_all_bookmarks(q, page, per_page, sort, order)
        return bookmark_pagination_schema.dump(paginated_recipes), HTTPStatus.OK

    @jwt_required
    def post(self):
        json_data = request.get_json()
        current_user = get_jwt_identity()

        try:
            data = bookmark_schema.load(data=json_data)

        except ValidationError as ex:
            return {
                'message': 'Validation errors',
                'errors': str(ex),
            }, HTTPStatus.BAD_REQUEST
        bookmark = Bookmark(**data)
        bookmark.user_id = current_user
        bookmark.save()

        return bookmark_schema.dump(bookmark), HTTPStatus.CREATED


class BookmarkResource(Resource):
    @jwt_optional
    def get(self, recipe_id):
        bookmark = Bookmark.get_by_id(recipe_id=recipe_id)

        if bookmark is None:
            return {'message': 'Bookmark not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if bookmark.is_publish == False and bookmark.user_id != current_user:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN

        return bookmark_schema.dump(bookmark), HTTPStatus.OK

    @jwt_required
    def patch(self, recipe_id):
        json_data = request.get_json()
        try:
            data = bookmark_schema.load(data=json_data, partial=('name',))
        except ValidationError as ex:
            return {
                'message': 'Validation errors',
                'errors': str(ex),
            }, HTTPStatus.BAD_REQUEST
        bookmark = Bookmark.get_by_id(recipe_id=recipe_id)

        if bookmark is None:
            return {'message': 'Bookmark not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != bookmark.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN

        bookmark.url = data.get('url') or bookmark.url
        bookmark.description = data.get('description') or bookmark.description
        bookmark.save()
        clear_cache('/bookmarks')

        return bookmark_schema.dump(bookmark), HTTPStatus.OK

    @jwt_required
    def delete(self, recipe_id):
        bookmark = Bookmark.get_by_id(recipe_id=recipe_id)

        if bookmark is None:
            return {'message': 'Bookmark not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != bookmark.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN

        bookmark.delete()
        clear_cache('/bookmarks')

        return {}, HTTPStatus.NO_CONTENT


class BookmarkPublishResource(Resource):
    @jwt_required
    def put(self, recipe_id):
        bookmark = Bookmark.get_by_id(recipe_id=recipe_id)

        if bookmark is None:
            return {'message': 'Bookmark not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != bookmark.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN

        bookmark.is_publish = True
        bookmark.save()

        clear_cache('/bookmarks')

        return {}, HTTPStatus.NO_CONTENT

    @jwt_required
    def delete(self, recipe_id):
        bookmark = Bookmark.get_by_id(recipe_id=recipe_id)

        if bookmark is None:
            return {'message': 'Bookmark not found'}, HTTPStatus.NOT_FOUND

        current_user = get_jwt_identity()

        if current_user != bookmark.user_id:
            return {'message': 'Access is not allowed'}, HTTPStatus.FORBIDDEN

        bookmark.is_publish = False
        bookmark.save()
        clear_cache('/bookmarks')

        return {}, HTTPStatus.NO_CONTENT
