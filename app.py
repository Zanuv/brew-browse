from flask import Flask, redirect, render_template, request, session, g, flash, abort
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Review, Brewery
from forms import SignupForm, LoginForm, BrewerySearchForm
from sqlalchemy.exc import IntegrityError
import requests

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///brew'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "CatsAreGoingCrazy"

toolbar = DebugToolbarExtension(app)

app.app_context().push()
connect_db(app)

#############################
# User Login and Signup


@app.before_request
def add_user_to_g():
    """"""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle User Signup"""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    form = SignupForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )

            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.email.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Welcome, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


#############################
# Home page and brewery search

@app.route('/', methods=['GET', 'POST'])
def home():
    form = BrewerySearchForm()
    if form.validate_on_submit():
        city = form.city.data
        state = form.state.data
        url = f'https://api.openbrewerydb.org/breweries?by_city={city}&by_state={state}'
        response = requests.get(url)
        breweries = response.json()
        return render_template('home.html', form=form, breweries=breweries)
    return render_template('home.html', form=form)


@app.route('/brewery/<brewery_name>')
def brewery_details(brewery_name):
    url = f'https://api.openbrewerydb.org/breweries?by_name={brewery_name}'
    response = requests.get(url)
    breweries = response.json()
    if breweries:
        brewery = next(
            (brewery for brewery in breweries if brewery['name'] == brewery_name), None)
    if brewery:
        return render_template('detail.html', brewery=brewery)
    else:
        return abort(404)
