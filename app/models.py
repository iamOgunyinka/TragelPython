from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from itsdangerous import JSONWebSignatureSerializer as JSONSerializer, \
    base64_decode, base64_encode
from werkzeug.security import generate_password_hash, check_password_hash

from .decorators import role_to_string
from .utils import log_activity, https_url_for, PaymentType, \
    generate_payment_id

login_manager = LoginManager()
db = SQLAlchemy()

login_manager.session_protection = 'strong'
login_manager.login_view = 'login.login_route'


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    official_email = db.Column(db.String(128), nullable=True)
    address = db.Column(db.String(256), nullable=False)
    city_id = db.Column(db.Integer, nullable=False)
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

    def to_json(self):
        city = City.query.filter_by(id=self.city_id).first()
        country = city.state.country.name if city else ''
        city = city.name if city else ''
        return {'name': self.name, 'id': self.id, 'city': city,
                'country': country, 'staffs': len(self.staffs),
                'products': len(self.products),
                'date': self.date_of_creation}

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


class SoftDeletedQuery(BaseQuery):
    _with_deleted = False

    def __new__(cls, *args, **kwargs):
        obj = super(SoftDeletedQuery, cls).__new__(cls)
        obj._with_deleted = kwargs.pop('_with_deleted', False)
        if len(args) > 0:
            super(SoftDeletedQuery, obj).__init__(*args, **kwargs)
            return obj.filter_by(deleted=False) if not obj._with_deleted else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_deleted(self):
        return self.__class__(db.class_mapper(self._mapper_zero().class_),
                              session=db.session(), _with_deleted=True)

    def _get(self, *args, **kwargs):
        return super(SoftDeletedQuery, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        obj = self.with_deleted()._get(*args, **kwargs)
        return obj if obj is None or self._with_deleted or not obj.deleted \
            else None


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
    deleted = db.Column(db.Boolean(), default=False, nullable=False)

    query_class = SoftDeletedQuery

    def __repr__(self):
        return '<User {}, {}, {}>'.format(self.fullname, self.username, self.company)

    def to_json(self):
        return {
            'id': self.id, 'name': self.fullname, 'username': self.username,
            'role': self.role, 'email': self.personal_email,
            'is_deleted': self.deleted, 'role_name': role_to_string(self.role)
        }

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

    @property
    def role(self):
        return 0

    def __repr__(self):
        return '<Anonymous>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False, unique=False)
    price = db.Column(db.Float, nullable=False, unique=False)
    thumbnail = db.Column(db.String(128), nullable=True, unique=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    deleted = db.Column(db.Boolean(), default=False, nullable=False)

    query_class = SoftDeletedQuery

    @staticmethod
    def from_json(json_data, company_id):
        items = []
        if json_data is None: return json_data
        for json_object in json_data:
            product_name = json_object.get('name', '')
            product_price = json_object.get('price', 0.0)
            thumbnail_url = json_object.get('thumbnail', '')
            new_product = Product(name=product_name, price=product_price,
                                  company_id=company_id, thumbnail=thumbnail_url)
            product_id = int(json_object.get('id', 0))
            existing_product = Product.query.get(product_id)
            if existing_product is not None:
                if not existing_product == new_product:
                    existing_product.deleted = True
                    items.append(existing_product)
                    items.append(new_product)
            else:
                items.append(new_product)
        return items

    def __eq__(self, other):
        return self.name == other.name and self.price == other.price and\
            self.thumbnail == other.thumbnail

    def to_json(self):
        return {
            'name': self.name, 'price': self.price, 'deleted': self.deleted,
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
        product = Product.query.with_deleted().get(self.product_id)
        return {
            'product': product.name, 'quantity': self.quantity,
            'price': product.price
        }


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    date_of_order = db.Column(db.DateTime, default=datetime.now)
    payment_type = db.Column(db.Integer, unique=False, nullable=False,
                             default=PaymentType.EBanking)
    payment_reference = db.Column(db.Text, unique=True, index=False, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    items = db.relationship('Item', backref='order', lazy='dynamic',
                            cascade='all, delete-orphan')
    payment_confirmed = db.relationship('Confirmation', backref='order',
                                        uselist=False)
    deleted = db.Column(db.Boolean(), default=False, nullable=False)

    query_class = SoftDeletedQuery

    @staticmethod
    def import_data(order_data):
        try:
            payment_ref_id = order_data.get('payment_reference_id')
            paid_in_cash = payment_ref_id == 'cash'
            if paid_in_cash:
                payment_ref_id = generate_payment_id()
            order_list = []
            for item in order_data.get('items'):
                new_item = Item(quantity=item.get('quantity'),
                                product_id=item.get('product_id'))
                order_list.append(new_item)
            pay_type = PaymentType.Cash if paid_in_cash else PaymentType.EBanking
            return payment_ref_id, pay_type, order_list
        except:
            return None

    def to_json(self):
        result = {
            'id': self.id, 'staff': User.query.get(self.staff_id).fullname,
            'payment_type': self.payment_type,
            'payment_reference': self.payment_reference,
            'date': self.date_of_order.isoformat(),
            'items': [item.to_json() for item in self.items],
        }
        if self.payment_confirmed is not None:
            result['confirmation'] = self.payment_confirmed.to_json()
        return result


class Confirmation(db.Model):
    __tablename__ = 'confirmations'

    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Boolean(), default=False, nullable=False)
    admin_id = db.Column(db.Integer, unique=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True)
    date = db.Column(db.DateTime, unique=False)

    def to_json(self):
        result = {'confirmed': self.confirmed}
        if self.confirmed == 1:
            result['by'] = User.query.with_deleted().get(self.admin_id).fullname
            result['date'] = self.date.isoformat()
        return result


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False)
    begin_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    def to_json(self):
        return {'from': self.begin_date.isoformat(), 'to':
            self.end_date.isoformat()}

    # we need these builtin functions in order to use the min-max functions
    # see the decorator implementation: `subscribed`
    def __lt__(self, other):
        return self.begin_date < other.begin_date or self.end_date < \
               other.end_date

    def __gt__(self, other):
        return not (self < other)

    def __le__(self, other):
        return (self < other) or (self == other)

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __eq__(self, other):
        return (self.begin_date == other.begin_date) and (self.end_date ==
                                                    other.end_date)

    @staticmethod
    def generate_subscription_token(company_id, company_name, from_date, to_date):
        serializer = JSONSerializer(current_app.config['SECRET_KEY'])
        obj = {'id': company_id, 'company': company_name,
               'from': from_date.isoformat(), 'to': to_date.isoformat() }
        return base64_encode(serializer.dumps(obj)).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = JSONSerializer(current_app.config['SECRET_KEY'])
        try:
            data_object = s.loads(base64_decode(token).decode())
            return data_object.get('id'), data_object.get('from'), data_object.get('to')
        except Exception as e:
            return None


class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    states = db.relationship('State', backref='country')

    def to_json(self):
        return {'name': self.name,
                'states': [state.to_json() for state in self.states]}


class State(db.Model):
    __tablename__ = 'states'
    id= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    cities = db.relationship('City', backref='state')
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))

    def to_json(self):
        return {'name': self.name,
                'cities': [city.to_json() for city in self.cities] }


class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=False)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'))

    def to_json(self):
        return self.name


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


login_manager.anonymous_user = Anonymous
