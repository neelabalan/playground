from marshmallow import Schema
from marshmallow import fields
from marshmallow import validate

from schemas.pagination import PaginationSchema
from schemas.user import UserSchema


class BookmarkSchema(Schema):
    class Meta:
        ordered = True

    id = fields.Integer(dump_only=True)
    url = fields.String(
        required=True,
        validate=[validate.Length(max=1000), validate.URL(relative=False)],
    )
    description = fields.String(validate=[validate.Length(max=200)])
    category = fields.String()
    author = fields.Nested(UserSchema, attribute="user", dump_only=True, exclude=("email",))

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BookmarkPaginationSchema(PaginationSchema):
    data = fields.Nested(BookmarkSchema, attribute="items", many=True)
