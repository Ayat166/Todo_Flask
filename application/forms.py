from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired ,Email

class ToDoForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    completed = SelectField('Completed', choices=[('True', 'True'), ('False', 'False')],default="False", validators=[DataRequired()])
    submit = SubmitField('Add Task')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(),Email()])
    password = StringField('Password', validators=[DataRequired()])
    confirm_password  = StringField('Confirm Password', validators=[DataRequired()]) 
    submit = SubmitField('Register')
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')