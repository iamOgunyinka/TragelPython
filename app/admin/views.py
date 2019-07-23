from datetime import datetime

from flask import render_template, redirect, flash, request, jsonify
from flask_login import logout_user, login_user, current_user, login_required

from . import admin
from .forms import AdminLoginForm, CompanyRegistrationForm, \
    CreateSubscriptionForm, BranchAddForm
from ..decorators import sudo_required, UserType
from ..models import User, Country, State, City, Company, db, Product, \
    Subscription
from ..utils import https_url_for, cache_companies_result


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


@admin.route('/suspend_company', methods=['GET'])
@sudo_required
def suspend_company(): # to-do
    name = ''
    return render_template('dashboard.html', name=name)


@admin.route('/list_companies', methods=['GET'])
@sudo_required
def list_companies():
    query = Company.query.filter_by(headquarter_id=None)
    companies = [company.to_json() for company in query.all()]
    return render_template('all_companies.html', companies=companies,
                           total=len(companies))


@admin.route('/list_branches', methods=['GET'])
@sudo_required
def list_branches():
    hq_id = request.args.get('hqid', type=int)
    hq = Company.query.filter_by(id=hq_id).first()
    branches = [branch.to_json() for branch in hq.branches]
    return render_template('all_branches.html', companies=branches,
                           total=len(branches), company_name=hq.name)


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
            company_admin.username += ("@" + str(new_company.id))
            db.session.add(company_admin)
            db.session.commit()
            city = City.query.get(city_id)
            query = city.state.name + '~' + city.name
            cache_companies_result(new_company, query)
            flash('Company added successfully')
            return redirect(https_url_for('admin.create_company'))
        except Exception as e:
            db.session.rollback()
            flash(str(e))
    return render_template('create_company.html', form=form)


@admin.route('/create_branch', methods=['GET', 'POST'])
@sudo_required
def create_branch():
    form = BranchAddForm()
    form.country.choices = [(country.id, country.name) for country in
                            Country.query.all()]
    form.state.choices = [(state.id, state.name) for state in State.query.all()]
    form.city.choices = [(city.id, city.name) for city in City.query.all()]
    hq_id = request.args.get('hqid', -1, type=int)
    if hq_id == -1:
        flash('Please select a company to add branch to')
        return redirect(https_url_for('admin.list_companies'))
    hq = Company.query.get(hq_id)
    if form.validate_on_submit():
        address,city_id = form.address.data, form.city.data
        admin_name, admin_username = form.admin.data, form.admin_username.data
        admin_email, password = form.admin_email.data, form.admin_password.data
        branch = Company(name=hq.name, official_email=hq.official_email,
                              address=address, city_id=city_id,
                              date_of_creation=datetime.utcnow())
        branch_admin = User(fullname=admin_name, username=admin_username,
                             personal_email=admin_email, address=address,
                             password=password, role=UserType.Administrator)
        branch.staffs.append(branch_admin)
        hq.branches.append(branch)
        try:
            db.session.add(hq)
            db.session.commit()
            branch_admin.username += ("@" + str(branch.id))
            db.session.add(branch_admin)
            db.session.commit()

            city = City.query.get(city_id)
            query = city.state.name + '~' + city.name
            cache_companies_result(branch, query)

            flash('Branch added successfully')
            return redirect(https_url_for('admin.list_companies'))
        except Exception as e:
            db.session.rollback()
            flash(str(e))
    return render_template('create_branch.html', form=form,
                           company_name=hq.name)


@admin.route('/subscribe/', methods=['GET'])
@login_required
def add_subscription():
    form = CreateSubscriptionForm()
    form.company_name.choices = [(company.id, company.name) for company in
                                 Company.query.filter_by(headquarter_id=None
                                                         ).all()]
    return render_template('create_subscription.html', form=form)


@admin.route('/_get_states', methods=['GET'])
@login_required
def _get_states():
    country_id = request.args.get('country_id', 1, type=int)
    country = Country.query.filter_by(id=country_id).first()
    states = [(state.id, state.name) for state in country.states]
    return jsonify(states)


@admin.route('/_get_countries', methods=['GET'])
@login_required
def _get_countries():
    countries = [(country.id, country.name) for country in Country.query.all()]
    return jsonify(countries)


@admin.route('/_get_key', methods=['GET'])
@sudo_required
def _get_key():
    company_id = request.args.get('company_id', 1, type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    start_date = datetime.strptime(start, '%m/%d/%Y').date()
    end_date = datetime.strptime(end, '%m/%d/%Y').date()
    now = datetime.utcnow().date()
    if not all((start_date, end_date, start_date >= end_date, start_date <now)):
        return jsonify({'error': 'Please check that the dates are valid'})
    company_name = Company.query.get(company_id).name
    key = Subscription.generate_subscription_token(company_id, company_name,
                                                   start_date, end_date)
    return jsonify({'key': key})


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
    company_id = request.args.get('company_id', 1, type=int)
    staffs = [staff.to_json() for staff in User.query.with_deleted().filter_by(
        company_id=company_id).all()]
    return jsonify(staffs)


@admin.route('/_subscriptions/', methods=['GET'])
@sudo_required
def _get_subscriptions():
    company_id = request.args.get('company_id', 1, type=int)
    last_subscription = Subscription.query.filter_by(
        company_id=company_id).order_by(Subscription.id.desc()).first()
    if last_subscription is None:
        text = 'No subscriptions yet'
    else:
        start_date = last_subscription.begin_date.date()
        to_date = last_subscription.end_date.date()
        text = 'Between {} and {}'.format(start_date, to_date)
    return jsonify({'last': text})


@admin.route('/_get_cities', methods=['GET'])
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
