from datetime import datetime

from flask import render_template, redirect, flash, request, jsonify
from flask_login import logout_user, login_user, current_user

from . import admin
from .forms import AdminLoginForm, CompanyRegistrationForm
from ..decorators import sudo_required, UserType
from ..models import User, Country, State, City, Company, db, Product
from ..utils import https_url_for


@admin.route('/', methods=['GET', 'POST'])
def login_route():
    form = AdminLoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user is None or user.verify_password(password) is False:
            flash('Invalid username or password')
            return redirect(https_url_for('admin.login_route'))
        login_user(user)
        return redirect(https_url_for('admin.admin_dashboard'))
    else:
        return render_template('login.html', form=form)


@admin.route('/dashboard', methods=['GET'])
@sudo_required
def admin_dashboard():
    name = current_user.fullname
    return render_template('dashboard.html', name=name)


@admin.route('/list_companies', methods=['GET', 'POST'])
@sudo_required
def list_companies():
    companies = [company.to_json() for company in Company.query.all()]
    return render_template('all_companies.html', companies=companies,
                           total=len(companies))


@admin.route('/create_company', methods=['GET', 'POST'])
@sudo_required
def create_company():
    form = CompanyRegistrationForm()
    form.country.choices = [(country.id, country.name) for country in
                            Country.query.all()]
    form.state.choices = [(state.id, state.name) for state in State.query.all()]
    form.city.choices = [(city.id, city.name) for city in City.query.all()]
    if form.validate_on_submit():
        company_name, email = form.name.data, form.email.data
        address,city_id = form.address.data, form.city.data
        admin_name, admin_username = form.admin.data, form.admin_username.data
        admin_email, password = form.admin_email.data, form.admin_password.data
        new_company = Company(name=company_name, official_email=email,
                              address=address, city_id=city_id,
                              date_of_creation=datetime.now())
        company_admin = User(fullname=admin_name, username=admin_username,
                             personal_email=admin_email, address=address,
                             password=password, role=UserType.Administrator)
        new_company.staffs.append(company_admin)
        try:
            db.session.add(new_company)
            db.session.add(company_admin)
            db.session.commit()
            company_admin.username += ("@" + str(company_admin.id))
            db.session.add(company_admin)
            db.session.commit()
            flash('Company added successfully')
            return redirect(https_url_for('admin.create_company'))
        except Exception as e:
            db.session.rollback()
            flash(str(e))
    return render_template('create_company.html', form=form)


@admin.route('/_get_states', methods=['GET'])
@sudo_required
def _get_states():
    country_id = request.args.get('country_id', 1, type=int)
    country = Country.query.filter_by(id=country_id).first()
    states = [(state.id, state.name) for state in country.states]
    return jsonify(states)


@admin.route('/_products/', methods=['GET'])
@sudo_required
def _get_products():
    company_id = request.args.get('company_id', 1, type=int)
    products = [product.to_json() for product in
                Product.query.with_deleted().filter_by(
        company_id=company_id).all()]
    return jsonify(products)


@admin.route('/_staffs/', methods=['GET'])
@sudo_required
def _get_staffs():
    company_id = request.args.get('staff_id', 1, type=int)
    staffs = [staff.to_json() for staff in User.query.with_deleted().filter_by(
        company_id=company_id).all()]
    return jsonify(staffs)


@admin.route('/_get_cities', methods=['GET'])
@sudo_required
def _get_cities():
    state_id = request.args.get('state_id', 1, type=int)
    state = State.query.filter_by(id=state_id).first()
    cities = [(city.id, city.name) for city in state.cities]
    return jsonify(cities)


@admin.route('/logout')
@sudo_required
def logout_route():
    logout_user()
    return redirect(https_url_for('admin.login_route'))
