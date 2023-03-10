from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """Registered users in the system"""

    __tablename__ = "users"

    id = db.Column(db.Integer,
                   primary_key=True)

    username = db.Column(db.Text,
                         nullable=False,
                         unique=True,
                         )

    password = db.Column(db.Text,
                         nullable=False)

    email = db.Column(db.Text,
                      nullable=False,
                      unique=True)

    reviews = db.relationship('Review', backref='user')

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.
        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, email, password):
        """Find user with `email` and `password`.
        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.
        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(email=email).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Review(db.Model):
    """User reviews of breweries"""

    __tablename__ = "reviews"

    id = db.Column(db.Integer,
                   primary_key=True)

    review = db.Column(db.String(200),
                       nullable=False)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='cascade')
                        )

    brewery_id = db.Column(db.Integer,
                           db.ForeignKey('breweries.id', ondelete='cascade')
                           )

    star_rating = db.Column(db.Integer,
                            nullable=False)

    brewery = db.relationship('Brewery', backref='reviews')


class Brewery(db.Model):
    """Breweries pulled from API that users can review"""

    __tablename__ = "breweries"

    id = db.Column(db.Integer,
                   primary_key=True)

    name = db.Column(db.Text,
                     nullable=False)


def connect_db(app):
    """Connect this database to provided Flask app."""

    db.app = app
    db.init_app(app)
