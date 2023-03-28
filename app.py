from flask import Flask, redirect, render_template, request, session, g, flash, abort, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask_bcrypt import Bcrypt
from models import db, connect_db, User, Review, Brewery
from forms import SignupForm, LoginForm, BrewerySearchForm, ChangePasswordForm
from sqlalchemy.exc import IntegrityError
import requests

bcrypt = Bcrypt()
CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///brew_9js6'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "CatsAreGoingCrazy"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

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


# Handles user signup

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


# Handles logging the user in

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


# Handles logging the user out

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

    # Get the most recent reviews from the database
    recent_reviews = Review.query.order_by(Review.id.desc()).limit(30).all()

    return render_template('home.html', form=form, recent_reviews=recent_reviews)


# Details page for a selected Brewery

@app.route('/brewery/<brewery_name>', methods=['GET', 'POST'])
def brewery_details(brewery_name):
    # Check if the brewery exists in the database
    brewery = Brewery.query.filter_by(name=brewery_name).first()

    # If it doesn't exist, query the API to get the brewery data
    if not brewery:
        url = f'https://api.openbrewerydb.org/breweries?by_name={brewery_name}'
        response = requests.get(url)
        breweries = response.json()
        if breweries:
            brewery_data = next(
                (brewery for brewery in breweries if brewery['name'] == brewery_name), None)
        else:
            return abort(404)

        # Create a new Brewery object with the name attribute
        brewery = Brewery(name=brewery_data['name'])

        # Add the new Brewery object to the database
        db.session.add(brewery)
        db.session.commit()

        # Redirect the user to the same page to prevent form resubmission
        return redirect(url_for('brewery_details', brewery_name=brewery_name))

    # Handle the review form submission
    if request.method == 'POST':
        review_text = request.form.get('review')
        rating = request.form.get('rating')
        user_id = g.user.id

        # Check if the review is too long
        if len(review_text) > 200:
            flash('Review is too long (maximum 200 characters)')
            return redirect(url_for('brewery_details', brewery_name=brewery_name))

        # Create a new Review object and associate it with the brewery
        review = Review(
            review=review_text,
            star_rating=rating,
            brewery_id=brewery.id,
            user_id=user_id
        )
        db.session.add(review)
        db.session.commit()

        # Redirect the user to the same page to prevent form resubmission
        return redirect(url_for('brewery_details', brewery_name=brewery_name))

    # Query the API to get the brewery data
    url = f'https://api.openbrewerydb.org/breweries?by_name={brewery_name}'
    response = requests.get(url)
    breweries = response.json()
    if breweries:
        brewery_data = next(
            (brewery for brewery in breweries if brewery['name'] == brewery_name), None)
    else:
        return abort(404)

    # Query the reviews associated with the brewery
    reviews = Review.query.filter_by(brewery_id=brewery.id).all()

    # Pass the brewery data to the template
    return render_template('detail.html', brewery=brewery_data, reviews=reviews)


# Handles deleting a Review for a Brewery

@app.route('/breweries/<brewery_name>/delete_review/<int:review_id>', methods=['POST'])
def delete_review(brewery_name, review_id):
    review = Review.query.get_or_404(review_id)
    if g.user and review.user_id == g.user.id:
        db.session.delete(review)
        db.session.commit()
        flash('Your review has been deleted.', 'success')
    else:
        flash('You are not authorized to delete this review.', 'danger')
    return redirect(url_for('brewery_details', brewery_name=brewery_name))


# Handles allowing a user to edit the reviews they have made

@app.route('/review/<int:review_id>/edit', methods=['GET', 'POST'])
def edit_review(review_id):
    # Get the review from the database
    review = Review.query.get(review_id)

    # Make sure the review exists and the user is authorized to edit it
    if not review or (g.user and review.user_id != g.user.id):
        return abort(404)

    # Handle the form submission
    if request.method == 'POST':
        review_text = request.form['review']
        star_rating = request.form['star_rating']
        review.review = review_text
        review.star_rating = star_rating
        db.session.commit()
        flash('Your review has been updated!', 'success')

        # Redirect the user to the brewery detail page
        return redirect(url_for('brewery_details', brewery_name=review.brewery.name))

    # Render the template with the review form
    return render_template('edit_review.html', review=review)


#############################

# Handles the user viewing their account

@app.route('/account/<int:user_id>')
def account(user_id):
    """Show the user account information."""

    user = User.query.get_or_404(user_id)
    change_password_form = ChangePasswordForm()

    # Query the reviews associated with the user
    reviews = Review.query.filter_by(user_id=user_id).all()

    return render_template('users/account.html', user=user, change_password_form=change_password_form, reviews=reviews)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data
        hashed_password = g.user.password

        # Check if the old password is correct
        if bcrypt.check_password_hash(hashed_password, old_password):
            # Hash the new password and update the user's password
            new_password_hash = bcrypt.generate_password_hash(
                new_password).decode('utf-8')
            g.user.password = new_password_hash
            db.session.commit()

            flash('Your password has been updated.', 'success')
            return redirect(url_for('account', user_id=g.user.id))

        else:
            flash('Old password is incorrect.', 'danger')

    return render_template('users/change_password.html', form=form)
