#!/usr/bin/env python
import os

from app import create_app, db
from app.models import User, Company
from app.utils import SUPER_USER

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
        if User.query.get(1) is None:
            company = Company(name='Tragel Group')
            super_user = User(fullname='Joshua', username='iamOgunyinka',
                              personal_email='ogunyinkajoshua@yahoo.com',
                              password='password', role=SUPER_USER, )
            company.staffs.append(super_user)
            db.session.add(company)
            db.session.add(super_user)
            db.session.commit()
        # create a development user
    app.run()
