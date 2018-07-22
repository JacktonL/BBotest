from app import db


class User(db.Document):
    email = db.StringField(required=True)
    real_name = db.StringField(min_length=1, max_length=50, required=True)
    username = db.StringField(min_length=4, max_length=50, required=True)
    password = db.StringField(min_length=6, max_length=50, required=True)

