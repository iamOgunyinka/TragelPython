from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import JSONWebSignatureSerializer as JSONSerializer, \
    base64_decode, base64_encode
from werkzeug.security import generate_password_hash, check_password_hash

from .utils import log_activity, https_url_for

login_manager = LoginManager()
db = SQLAlchemy()

login_manager.session_protection = 'strong'
login_manager.login_view = 'login.login_route'


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

    def __repr__(self):
        return '<Company: NAME -> {}, ID -> {}>'.format(self.name, self.id)

    def generate_auth_token(self):
        s = JSONSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = JSONSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        company = User.query.get(data['id'])
        return company.id if company is not None else None

    @staticmethod
    def import_json(json_object):
        try:
            return Company(name=json_object.get('name'),
                           date_of_creation=datetime.now())
        except Exception as e:
            log_activity('EXCEPTION[create_company]', 'SuperUser', 'New Company',
                         str(e))
            return None


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    personal_email = db.Column(db.String(128), index=True, unique=True)
    address = db.Column(db.String(128), index=False, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    role = db.Column(db.SmallInteger, nullable=False)

    def __repr__(self):
        return '<User {}, {}, {}>'.format(self.fullname, self.username, self.company)

    @property
    def password(self):
        raise AttributeError('Cannot get password in plain text')

    @password.setter
    def password(self, new_password):
        self.password_hash = generate_password_hash(new_password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Anonymous(AnonymousUserMixin):
    def verify_password(self):
        return False

    def __repr__(self):
        return '<Anonymous>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False, unique=False)
    thumbnail = db.Column(db.String(128), nullable=True, unique=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    @staticmethod
    def from_json(json_data, company_id):
        items = []
        if json_data is None: return json_data
        for json_object in json_data:
            product_name = json_object.get('name')
            product_price = json_object.get('price')
            thumbnail_url = json_object.get('thumbnail', '')
            items.append(Product(name=product_name, price=product_price,
                                 thumbnail=thumbnail_url, company_id=company_id))
        return items

    def to_json(self):
        return {
            'name': self.name, 'price': self.price,
            'thumbnail': self.thumbnail, 'id': self.id,
            'url': https_url_for('api.get_product', product_id=self.id),
        }

    def __repr__(self):
        return '<Product: Company -> {}, Name -> {}, Price -> {}>'\
            .format(self.company_id, self.name, self.price)


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           index=True)
    quantity = db.Column(db.Integer, default=lambda: 1)

    def to_json(self):
        product = Product.query.get(self.product_id)
        return {
            'product': product.name, 'quantity': self.quantity,
            'price': product.price
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    date_of_order = db.Column(db.DateTime, default=datetime.now)
    payment_reference = db.Column(db.Text, unique=True, index=False, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    items = db.relationship('Item', backref='order', lazy='dynamic',
                            cascade='all, delete-orphan')

    @staticmethod
    def import_data(order_data):
        try:
            payment_reference_id = order_data.get('payment_reference_id')
            order_list = []
            for item in order_data.get('items'):
                new_item = Item(quantity=item.get('quantity'),
                                product_id=item.get('product_id'))
                order_list.append(new_item)
            return payment_reference_id, order_list
        except:
            return None, None

    def to_json(self):
        return {
            'id': self.id, 'staff': User.query.get(self.staff_id).fullname,
            'payment_reference': self.payment_reference,
            'date': self.date_of_order.isoformat(),
            'items': [item.to_json() for item in self.items]
        }


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    begin_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    # we need these builtin functions in order to use the min-max functions
    # see the decorator implementation: `subscribed`
    def __lt__(self, other):
        return self.end_date < other.end_date

    def __gt__(self, other):
        return self.end_date > other.end_date

    def __le__(self, other):
        return self.end_date <= other.end_date

    def __ge__(self, other):
        return self.end_date >= other.end_date

    def __eq__(self, other):
        return (self.begin_date, self.end_date) == (other.begin_date, other.end_date)

    @staticmethod
    def generate_subscription_token(company_id, company_name, from_date, to_date):
        serializer = JSONSerializer(current_app.config['SECRET_KEY'])
        obj = {'id': company_id, 'company': company_name, 'from': str(from_date),
               'to': str(to_date)}
        return base64_encode(serializer.dumps(obj)).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = JSONSerializer(current_app.config['SECRET_KEY'])
        try:
            data_object = base64_decode(s.loads(token).decode('utf-8'))
        except:
            return None, None, None
        return data_object.get('id'), data_object.get('from'), data_object.get('to')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


login_manager.anonymous_user = Anonymous
