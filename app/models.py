from datetime import datetime
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from . import db, auth


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    date_of_creation = db.Column(db.DateTime, nullable=False, default=datetime.now)
    staffs = db.relationship('User', backref='company')
    orders = db.relationship('Order', backref='company')
    subscriptions = db.relationship('Subscription', backref='company',
                                    lazy='dynamic')
    products = db.relationship('Product', backref='company')

    def generate_auth_token(self, expires_in=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(64), index=True)
    personal_email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    role = db.Column(db.SmallInteger, nullable=False)

    @property
    def password(self):
        raise AttributeError('Cannot get password in plain text')

    @password.setter
    def password(self, new_password):
        self.password_hash = generate_password_hash(new_password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Anonymous(AnonymousUserMixin):
    pass


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False)
    price = db.Column(db.Float, nullable=False, unique=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    date = db.Column(db.DateTime, default=datetime.now)
    payment_reference = db.Column(db.Text, unique=True, index=False, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    items = db.relationship('Item', backref='order', lazy='dynamic',
                            cascade='all, delete-orphan')


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           index=True)
    quantity = db.Column(db.Integer, default=lambda: 1)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    def generate_subscription_token(self, company_name, expires_in=3600000):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
        return s.dumps({'id': self.company_id, 'company': company_name}) \
            .decode('utf-8')

    @staticmethod
    def verify_auth_token(token, company_id):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=3600000)
        try:
            data = s.loads(token)
        except:
            return None
        company = Company.query.get(data['id'])
        return company and company.id == company_id


@auth.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


auth.anonymous_user = Anonymous()


















