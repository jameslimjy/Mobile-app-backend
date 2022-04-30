from datetime import datetime
from app import db
from sqlalchemy import ForeignKey, UniqueConstraint, ForeignKeyConstraint


class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.Integer, primary_key = True)
    email_address = db.Column(db.String(100), unique = True, nullable = False)
    name = db.Column(db.String(100), unique = False, nullable = False)
    country_code = db.Column(db.String(10), unique = False, nullable = True)
    phone_number = db.Column(db.Integer, unique = False, nullable = True)
    postal_code = db.Column(db.Integer, unique = False, nullable = False)
    password = db.Column(db.String(100), unique = False, nullable = False)
    latitude = db.Column(db.Float, unique = False, nullable = False)
    longitude = db.Column(db.Float, unique = False, nullable = False)

	# one-to-many model
    wrote_report = db.relationship('Report', back_populates = 'from_user', uselist = True, lazy = True)

    # one-to-many model
    wrote_suggestion = db.relationship('Suggestion', back_populates = 'by_user', uselist = True, lazy = True)

    def __init__(self, email_address, name, country_code, phone_number, postal_code, password, latitude, longitude):
        self.email_address = email_address
        self.name = name
        self.country_code = country_code
        self.phone_number = phone_number
        self.postal_code = postal_code
        self.password = password
        self.latitude = latitude
        self.longitude = longitude


class Report(db.Model):
    __tablename__ = 'Report'
    report_id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255), unique = False, nullable = True)
    description = db.Column(db.String(255), unique = False, nullable = True)
    street_name = db.Column(db.String(255), unique = False, nullable = True)
    postal_code = db.Column(db.Integer, unique = False, nullable = True)
    nearby_landmarks = db.Column(db.String(255), unique = False, nullable = True)
    latitude = db.Column(db.Float, unique = False, nullable = False)
    longitude = db.Column(db.Float, unique = False, nullable = False)
    photo1 = db.Column(db.String(255), unique = False, nullable = True)
    photo2 = db.Column(db.String(255), unique = False, nullable = True)
    photo3 = db.Column(db.String(255), unique = False, nullable = True)
    submitted_by_user = db.Column(db.Integer(), db.ForeignKey('User.user_id'), unique = False, nullable = True)
    submit_to_tc = db.Column(db.Integer(), db.ForeignKey('TownCouncil.tcid'), unique = False, nullable = True)
    # feedback = db.Column(db.Integer(), db.ForeignKey('Feedback.feedback_id'), unique = True, nullable = True)
    timestamp = db.Column(db.DateTime, default = datetime.now, onupdate = datetime.now)

    # one-to-many model
    from_user = db.relationship('User', back_populates = 'wrote_report')

    # one-to-many model
    allocated_tc = db.relationship('TownCouncil', back_populates = 'has_reports')

    # one-to-many model
    has_status = db.relationship('Status', back_populates = 'belongs_to_report', uselist = True, lazy = True)

    # one-to-one model
    has_feedback = db.relationship('Feedback', uselist = False, backref = 'Report')

    def __init__(self, title, description, street_name, postal_code, nearby_landmarks, latitude, longitude, submitted_by_user = None, submit_to_tc = None, photo1 = None, photo2 = None, photo3 = None):
        self.title = title
        self.description = description
        self.street_name = street_name
        self.postal_code = postal_code
        self.nearby_landmarks = nearby_landmarks
        self.latitude = latitude
        self.longitude = longitude
        self.photo1 = photo1
        self.photo2 = photo2
        self.photo3 = photo3
        self.submitted_by_user = submitted_by_user
        self.submit_to_tc = submit_to_tc


class TownCouncil(db.Model):
    __tablename__ = 'TownCouncil'
    tcid = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), unique = True, nullable = False)
    phone_number = db.Column(db.BigInteger, unique = True, nullable = False)
    location = db.Column(db.String(100), unique = True, nullable = False)
    operating_hours = db.Column(db.String(100), unique = False, nullable = False)
    facebook = db.Column(db.String(50), unique = False, nullable = True)
    instagram = db.Column(db.String(50), unique = False, nullable = True)
    website = db.Column(db.String(50), unique = False, nullable = True)
    logo = db.Column(db.String(255), unique = True, nullable = True)

    # one-to-many model
    has_reports = db.relationship('Report', back_populates = 'allocated_tc', uselist = True, lazy = True)

    # one-to-many model
    received_suggestion = db.relationship('Suggestion', back_populates = 'to_tcid', uselist = True, lazy = True)

    def __init__(self, name, phone_number, location, operating_hours, facebook = None, instagram = None, website = None, logo = None):
        self.name = name
        self.phone_number = phone_number
        self.location = location
        self.operating_hours = operating_hours
        self.facebook = facebook
        self.instagram = instagram
        self.website = website
        self.logo = logo


class Status(db.Model):
    __tablename__ = 'Status'
    status_id = db.Column(db.Integer, primary_key = True)
    status_name = db.Column(db.String(50), unique = False, nullable = False)
    comments = db.Column(db.String(255), unique = False, nullable = True)
    from_report_id = db.Column(db.Integer, db.ForeignKey('Report.report_id'), unique = False, nullable = False)
    timestamp = db.Column(db.DateTime, default = datetime.now, onupdate = datetime.now)

    # one-to-many model
    belongs_to_report = db.relationship('Report', back_populates = 'has_status')

    def __init__(self, status_name, comments, from_report_id):
        self.status_name = status_name
        self.comments = comments
        self.from_report_id = from_report_id


class Suggestion(db.Model):
    __tablename__ = 'Suggestion'
    suggestion_id = db.Column(db.Integer, primary_key = True)
    category = db.Column(db.String(50), unique = False, nullable = False)
    description = db.Column(db.String(255), unique = False, nullable = False)
    photo1 = db.Column(db.String(255), unique = False, nullable = True)
    photo2 = db.Column(db.String(255), unique = False, nullable = True)
    photo3 = db.Column(db.String(255), unique = False, nullable = True)
    submission_timestamp = db.Column(db.DateTime, default = datetime.now)
    tc_response = db.Column(db.String(255), unique = False, nullable = True)
    tc_response_timestamp = db.Column(db.DateTime)
    from_user = db.Column(db.Integer, db.ForeignKey('User.user_id'), unique = False, nullable = False)
    to_tc = db.Column(db.Integer, db.ForeignKey('TownCouncil.tcid'), unique = False, nullable = False)

    # one-to-many model
    by_user = db.relationship('User', back_populates = 'wrote_suggestion')

    # one-to-many model
    to_tcid = db.relationship('TownCouncil', back_populates = 'received_suggestion')

    def __init__(self, category, description, from_user, to_tc, photo1 = None, photo2 = None, photo3 = None, tc_response = None, tc_response_timestamp = None):
        self.category = category
        self.description = description
        self.from_user = from_user
        self.to_tc = to_tc
        self.photo1 = photo1
        self.photo2 = photo2
        self.photo3 = photo3
        self.tc_response = tc_response
        self.tc_response_timestamp = tc_response_timestamp


class Feedback(db.Model):
    __tablename__ = 'Feedback'
    feedback_id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.String(255), unique = False, nullable = True)
    rating = db.Column(db.Integer, unique = False, nullable = False)
    submission_timestamp = db.Column(db.DateTime, default = datetime.now)
    tc_response = db.Column(db.String(255), unique = False, nullable = True)
    tc_response_timestamp = db.Column(db.DateTime)
    from_report = db.Column(db.Integer, db.ForeignKey('Report.report_id'))

    def __init__(self, description, rating, from_report, tc_response = None, tc_response_timestamp = None):
        self.description = description
        self.rating = rating
        self.from_report = from_report
        self.tc_response = tc_response
        self.tc_response_timestamp = tc_response_timestamp
