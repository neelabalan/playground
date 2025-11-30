from extensions import db
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import or_


class Bookmark(db.Model):
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.String(200))
    # tags =
    category = db.Column(db.String(200), nullable=False)

    created_at = db.Column(db.DateTime(), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))

    @classmethod
    def get_all_bookmarks(cls, q, page, per_page, sort, order):
        keyword = '%{keyword}%'.format(keyword=q)

        if order == 'asc':
            sort_logic = asc(getattr(cls, sort))
        else:
            sort_logic = desc(getattr(cls, sort))

        return (
            cls.query.filter(
                or_(
                    cls.name.ilike(keyword),
                    cls.description.ilike(keyword),
                    cls.ingredients.ilike(keyword),
                ),
                cls.is_publish.is_(True),
            )
            .order_by(sort_logic)
            .paginate(page=page, per_page=per_page)
        )

    @classmethod
    def get_all_by_user(cls, user_id, page, per_page):
        query = cls.query.filter_by(user_id=user_id)
        return query.order_by(desc(cls.created_at)).paginate(page=page, per_page=per_page)

    @classmethod
    def get_by_id(cls, bookmark_id):
        return cls.query.filter_by(id=bookmark_id).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
