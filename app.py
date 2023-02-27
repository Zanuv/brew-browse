from flask import Flask, redirect, render_template, request
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///brew'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "CatsAreGoingCrazy"

toolbar = DebugToolbarExtension(app)

app.app_context().push()
