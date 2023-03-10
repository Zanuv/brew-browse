from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange


class SignupForm(FlaskForm):
    """Form for signup."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    """Login form."""

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    submit = SubmitField('Log In')


class BrewerySearchForm(FlaskForm):
    """Search form for Breweries."""

    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    submit = SubmitField('Search')


class ReviewForm(FlaskForm):
    """Form for a User to submit a Review."""

    review = StringField('Review', validators=[
                         DataRequired(), Length(max=200)])
    star_rating = IntegerField('Rating', validators=[
                               DataRequired(), NumberRange(min=1, max=5)])
    submit = SubmitField('Submit Review')
