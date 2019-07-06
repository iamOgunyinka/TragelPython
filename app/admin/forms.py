from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError, \
    SelectField
from wtforms.validators import DataRequired, InputRequired, Email, EqualTo, \
    Length

from ..models import Company, User


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                                   InputRequired()])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     InputRequired()])
    submit = SubmitField('Submit')

    def validate_password(self, field):
        if len(field.data) < 8:
            raise ValidationError('Incorrect password')


class CompanyRegistrationForm(FlaskForm):
    name = StringField('Company name', validators=[InputRequired()])
    email = StringField('Company\'s official email', validators=[Email(),
        Length(5, 128, message='Email address too short')])
    address = StringField('Company\'s address', validators=[InputRequired()])
    country = SelectField('Country', coerce=int, validators=[DataRequired()],
                          id='select_country')
    state = SelectField('State', coerce=int, validators=[DataRequired()],
                        id='select_state')
    city = SelectField('City', coerce=int, validators=[DataRequired()],
                       id='select_city')
    admin = StringField('Administrator\'s name', validators=[InputRequired()])
    admin_username = StringField('Admin\'s username',
                                 validators=[InputRequired()])
    admin_email = StringField('Admin\'s email', validators=[InputRequired(),
                                                            Email()])
    admin_password = PasswordField('Password', validators=[DataRequired(),
            InputRequired(), EqualTo('confirm_password', message='Password '
                'must match'), Length(8, max=-1, message='Must be at least 8 '
                                                         'characters long')])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), InputRequired()])
    submit = SubmitField('Submit')


    def validate_email(self, field):
        if Company.query.filter_by(official_email=field.data).first():
            raise ValidationError('There\'s a company with this official '
                                   'email')

    def validate_admin_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username registered already')

    def validate_admin_email(self, field):
        if User.query.filter_by(personal_email=field.data).first():
            raise ValidationError('Email registered already')
