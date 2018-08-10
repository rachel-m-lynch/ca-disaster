from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask import jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import Event, Grant, User, UserSearch
from model import connect_to_db, db

from bs4 import BeautifulSoup
# import request
from urllib.request import Request, urlopen
from sqlalchemy import distinct
import os
# import pdb; pdb.set_trace()
app = Flask(__name__)

app.secret_key = os.environ["SERVER_APP_SECRET_KEY"]
google_api_key = os.environ["GOOGLE_API_KEY"]

app.jinja_env.undefined = StrictUndefined

###############################################################################


@app.route('/')
def index():
    """Homepage"""

    return render_template('homepage.html', google_api_key=google_api_key)


@app.route('/users')  # Need to remove eventually
def show_users():
    """Show a list of all users"""

    users = User.query

    return render_template('users-list.html',
                           users=users)


@app.route('/users/<int:user_id>')
def show_user_page(user_id):
    """Show user info page with saved queries"""

    user = User.query.get(user_id)

    if not user:
        flash('User does not exist')
        return redirect('/login')

    user_saved_searches = db.session.query(UserSearch.id,
                                           UserSearch.users_id,
                                           UserSearch.events_id
                                           ).join(
                                                Event
                                           ).filter_by(
                                                user_id=user_id
                                           ).all()

    return render_template('user-info.html',
                           user=user,
                           user_saved_searches=user_saved_searches)


@app.route('/registration')
def show_registration_form():
    """Show registration form"""

    return render_template('registration.html')


@app.route('/registration', methods=['POST'])
def register_user():
    """Register a new user after checking db to make sure it does not exist"""

    print(request.form)
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    occupation = request.form.get('occupation')
    user = User.query.filter_by(username=username).first()
    user_email = User.query.filter_by(email=email).first()

    if user:
        flash('Username is taken')
        return redirect('/registration')

    if user_email:
        flash('Email is already in use')
        return redirect('/registration')

    new_user = User(username=username,
                    email=email,
                    password=password,
                    occupation=occupation)
    db.session.add(new_user)
    db.session.commit()

    flash("New User Registration Complete")

    return redirect('/login')


@app.route('/login')
def show_login_form():
    """Show login form"""

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def process_login():
    """Complete login process"""

    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
        flash('Invalid password')
        return redirect('/login')

    session['user_id'] = user.id

    flash("Logged In")

    return redirect(f'/users/{user.id}')


@app.route('/logout')
def process_logout():
    """User logout and provide message upon success"""

    session.pop('user_id')
    flash('Logout Successful')

    return redirect('/')


@app.route('/events')
def events_list():
    """Show events list ordered by date"""

    disasters = set()
    for row in open('seed_data/event.txt'):
        row = row.rstrip().replace('\t', '').split('|')
        incident = row[1]
        disasters.add(incident)    
    disaster = len(disasters)
    
    page_size = 50
    pages = int(disaster / page_size)
    page = request.args.get('page')  # returns args['page'] if exists, default to None
    if page is None:
        page = 0

    events = Event.query.order_by('fema_id'
                                  ).limit(page_size
                                  ).offset(int(page)*page_size
                                  ).distinct('fema_id'
                                  ).all()
    
    return render_template('event-list.html',
                           events=events,
                           disaster=disaster,
                           pages=pages)


@app.route('/events/<fema_id>')
def show_user_events_info(fema_id):
    """Find an event"""

    event = Event.query.filter_by(fema_id=fema_id).first()
    counties = Event.query.filter_by(fema_id=fema_id
                                     ).order_by(Event.county).all()
    counties_affected = Event.query.filter_by(fema_id=fema_id
                                     ).order_by(Event.county).count()

    print(counties)
    if not event:
        flash('This event does not exist or this datebase is incomplete.')
        return redirect('/')

    return render_template('event-info.html',
                           counties=counties,
                           counties_affected=counties_affected,
                           event=event,
                           fema_id=fema_id)


@app.route('/search')
def show_search_options():
    """Show user the filter options available to look up an event"""
    
    disasters = set()
    for row in open('seed_data/event.txt'):
        row = row.rstrip().replace('\t', '').split('|')
        incident = row[1]
        disasters.add(incident)    
    disaster = len(disasters)
    
    return render_template('user-search.html',
                           disaster=disaster)
    # Try to add this one with the google places search
    # Try to add more search options with google places


@app.route('/search/results')
def show_search_results():
    """Show user query filtered by options selected"""

    state_id = request.args.get('state')
    disaster_type = request.args.get('disaster-type')
    declaration_id = request.args.get('declaration-id')
    month = request.args.get('month')
    year = request.args.get('year')                               

    user_choice = Event.query.distinct('fema_id')
    
    if state_id != 'all':
        user_choice = Event.query.filter_by(state_id=state_id)
    if disaster_type != 'all':
        user_choice = Event.query.filter_by(disaster_type=disaster_type)
    if declaration_id != 'all':
        user_choice = Event.query.filter_by(declaration_id=declaration_id)
    if state_id != 'all' and disaster_type != 'all':
        user_choice = Event.query.filter_by(state_id=state_id,
                                            disaster_type=disaster_type)
    if state_id != 'all' and declaration_id != 'all':
        user_choice = Event.query.filter_by(state_id=state_id,
                                            declaration_id=declaration_id)
    if disaster_type != 'all' and declaration_id != 'all':
        user_choice = Event.query.filter_by(disaster_type=disaster_type,
                                            declaration_id=declaration_id)
    if state_id != 'all' and disaster_type != 'all' and declaration_id != 'all':
        user_choice = Event.query.filter_by(state_id=state_id,
                                            disaster_type=disaster_type,
                                            declaration_id=declaration_id)
       
    num_choices = user_choice.distinct('fema_id'
                                       ).count()                                      
    page_size = 50
    pages = int(num_choices / page_size)
    page = request.args.get('page')  # returns args['page'] if exists, default to None
    if page is None:
        page = 0

    user_choice = user_choice.order_by('fema_id'
                                       ).limit(page_size
                                       ).offset(int(page)*page_size
                                       ).distinct('fema_id'
                                       ).all()
    
    if not user_choice:
        flash('There are no events of this type that are in this datebase.')
        return redirect('/search')

    return render_template('user-results.html',
                           state_id=state_id,
                           disaster_type=disaster_type,
                           declaration_id=declaration_id,
                           month=month,
                           year=year,
                           user_choice=user_choice,
                           num_choices=num_choices,
                           pages=pages)


@app.route('/about')
def show_about_page():
    """Show the about page"""

    return render_template('about.html')


@app.route('/contact')
def show_contact_page():
    """Show contact page"""

    return render_template('contact.html')


@app.route('/us-map')
def us_map():
    """Show a map of the entire United States without markers"""

    return render_template('us-map.html', google_api_key=google_api_key)


@app.route('/geolocate')
def geolocate():
    """Zoom in on the location queried by the user with markers"""

    return render_template('geolocate.html', google_api_key=google_api_key)


@app.route('/places_locate')
def places_locate():
    """Find a location with a query using Google Places API"""

    return render_template('location-search.html',
                           google_api_key=google_api_key)


###############################################################################


if __name__ == "__main__":
    app.debug = True
    connect_to_db(app)
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
