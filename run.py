#!/usr/bin/env python
import json
import os

from app import create_app, db
from app.models import User, Company, Country, State, City
from app.decorators import UserType

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))


def add_country():
    filename = os.path.join(os.getcwd(), 'misc/nigeria.json')
    file_content = ''
    with open(filename, 'r') as rb:
        for line in rb:
            file_content += line
    obj = json.loads(file_content)
    country = Country(name='Nigeria')
    for i in obj:
        state = State(name=i)
        for k in obj[i]:
            city = City(name=k)
            state.cities.append(city)
        country.states.append(state)
    db.session.add(country)
    db.session.commit()


@app.before_first_request
def first_request():
    db.create_all()
    if Country.query.get(1) is None:
        add_country()
    if User.query.get(1) is None:
        company = Company(name='Tragel Group', address='Orita-Iloko',
                          city_id=1)
        super_user = User(fullname='Joshua', username='iamOgunyinka',
                          personal_email='ogunyinkajoshua@yahoo.com',
                          password='password', role=UserType.SuperUser)
        company.staffs.append(super_user)
        db.session.add(company)
        db.session.add(super_user)
        db.session.commit()


if  __name__ == '__main__':
    # create a development user
    app.run(debug=True, port=6000)
