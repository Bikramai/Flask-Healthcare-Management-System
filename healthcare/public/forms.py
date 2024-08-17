from flask_wtf import FlaskForm
from healthcare.models import User
from wtforms import StringField, PasswordField, SubmitField, EmailField, TimeField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
