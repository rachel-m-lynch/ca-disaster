"""Models and database functions for California Disaster project"""

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

###############################################################################
# Model definitions


class Event(db.Model):
    """The disaster declarations that are in FEMA's database"""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    declaration_id = db.Column(db.String, nullable=False)

    fema_id = db.Column(db.Integer)

    state_id = db.Column(db.String)

    name = db.Column(db.String)

    county = db.Column(db.String)

    start_date = db.Column(db.Date)

    end_date = db.Column(db.Date)

    declared_on = db.Column(db.Date)

    close_out_date = db.Column(db.Date)

    disaster_type = db.Column(db.String)

    grants = db.relationship('Grant', backref='event')

    user_id = db.Column(db.ForeignKey('users.id'))

    damaged_property = db.Column(db.Boolean, default=False)

    def __repr__(self):
        """Display info about the disaster event"""

        return f"""<Event ID: {self.id}
                   Declaration ID: {self.declaration_id}
                   FEMA ID: {self.fema_id}
                   State ID: {self.state_id}
                   Name: {self.name}
                   County:{self.county}
                   Occured On: {self.start_date} - {self.end_date}
                   Declared On: {self.declared_on}
                   Disaster Closed Out On: {self.close_out_date}
                   Disaster Type: {self.disaster_type}>"""


class Grant(db.Model):
    """Money that was awarded for disasters"""

    __tablename__ = "grants"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    total = db.Column(db.Float)

    grant = db.Column(db.String)

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

    def __repr__(self):
        """Display information about funding that was granted"""

        return f"""<Grant Total ID: {self.id}
                   Total: {self.total}
                   Grant Type: {self.grant}
                   Event ID: {self.event_id}>"""
                   

class User(db.Model):
    """Keep user info to save user info"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    username = db.Column(db.String, nullable=False)

    email = db.Column(db.String, unique=True, nullable=False)

    password = db.Column(db.String, nullable=False)

    occupation = db.Column(db.String)

    searches = db.relationship('Event', secondary='user_searches', backref='users')

    def __repr__(self):
        """Display information about the user"""

        return f"""<User ID: {self.id}
                   Username: {self.username}
                   Email: {self.email}
                   Password: {self.password}
                   Occupation: {self.occupation}>"""


class UserSearch(db.Model):
    """Joining the event and location"""

    __tablename__ = "user_searches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    users_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    events_id = db.Column(db.Integer, db.ForeignKey('events.id'))

    def __repr__(self):
        """Display information about the user's saved searches"""

        return f"""<User-Searches ID: {self.id}
                   User ID: {self.users_id}
                   Event ID:{self.events_id}>"""


###############################################################################

def connect_to_db(app, database='postgresql:///disasters'):
    """Connect the database to Flask app."""

    app.config['SQLALCHEMY_DATABASE_URI'] = database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    from server import app
    connect_to_db(app)
    print("Connected to DB.")
    db.create_all()