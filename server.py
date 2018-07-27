from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask import jsonify
from flask_debugtoolbar import DebugToolbarExtension

from model import Event, Location, Type, connect_to_db, db

from os import environ

app = Flask(__name__)

app.secret_key = "SERVER_APP_SECRET_KEY"

app.jinja_env.undefined = StrictUndefined

###############################################################################


@app.route('/')
def index():
    """Homepage"""

    return render_template('homepage.html')


@app.route('/users')
def user_list():
    """Show a list of all users"""

    users = User.query

    return render_template('user-list.html',
                           users=users)


@app.route('/users/<user_id>')
def show_user_page():
    """Show user info page with saved queries"""

    user = User.query.get(user_id)

    if not user:
        flash('User does not exist')
        return redirect('/login')

    user_saved_searches = db.session.query(Event.id,
                                           Event.fema_id,
                                           Location.state,
                                           Location.county,
                                           Type.name
                                           ).join(
                                               Location,
                                               Type
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

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    occupation = request.form.get('occupation')
    username = User.query.filter_by(username=username).first()
    email = User.query.filter_by(email=email).first()

    if username:
        flash('Username is taken')
        return redirect('/registration')

    if email:
        flash('Email is already in use')
        return redirect('/registration')

    new_user = User(username=username,
                    email=email,
                    password=password,
                    occupation=occupation)
    db.session.add(new_user)
    db.session.commit()

    flash("New User Registeration Complete")

    return redirect('/login')


@app.route('login')
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
        flask('Invalid password')
        return redirect('/login')

    session['user_id'] = user.user_id

    flash("Logged In")

    return redirect(f'/users/{user.user_id}')


@app.route('/logout')
def process_logout():
    """User logout and provide message upon success"""

    session.pop('user_id')
    flash('Logout Successful')

    return redirect('/')


@app.route('/events')
def events_list():
    """Show events list ordered by date"""

    events = Event.query.order_by('start_date').all()

    return render_template('event-list.html',
                           events=events)


@app.route('/events/<int:user_event>')
def show_user_events_info():
    """Show information about the event"""

    event = Event.query.get(fema_id)

    if not event:
        flash('This event does not exist or this datebase is incomplete.')
        return redirect('/')

    return render_template('event-info.html',
                           event=event)


@app.route('/types.json')
def types_list():
    """Display a list of disaster types"""

    types = {
        types.id: {
            "Type ID": types.id,
            "Type Name": types.name
        }
        for types in Type.query}

    return jsonify(types)


@app.route('/type/<user_type>')
def show_user_type():
    """Display all events with that type"""

    user_type = Type.query.get(id)

    if not user_type:
        flash('This type does not exist in this datebase.')
        return redirect('/')

    return render_template('type-info.html',
                           user_type=user_type)


@app.route('/locations/<user_state>')
def show_ulocation_by_state():
    """Show user queried location by state selected"""

    user_state = Location.query.get(state)

    if not user_state:
        flash('This is not a state in the United States.')
        return redirect('/')

    return render_template('user-state.html',
                           user_state=user_state)


@app.route('/locations/<user_county>')
def show_ulocation_by_county():
    """Show user queried location by county selected via zipcode/city"""

    user_county = Location.query.get(county)

    if not user_county:
        flash('This is not a county is not in this datebase')
        return redirect('/')

    return render_template('user-county.html',
                           user_county=user_county)


@app.route('/about')
def show_about_page():
    """Show the about page"""

    return render_template('about.html')


@app.route('/contact')
def show_contact_page():
    """Show contact page"""

    return render_template('contact.html')


@app.route('/us_map')
def us_map():
    """Show a map of the entire United States without markers"""

    return render_template('us-map.html')


@app.route('geolocate')
def geolocate():
    """Zoom in on the location queried by the user with markers"""

    return render_template('geolocate.html')


###############################################################################


if __name__ == "__main__":
    app.debug = True
    connect_to_db(app)
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
