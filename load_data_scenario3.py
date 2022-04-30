from app import db, SQLAlchemy
from models import User, Report, TownCouncil, Status, Feedback, Suggestion
from datetime import datetime, timedelta
import csv

data_folder_path = 'load_sample_data/'
data_file = {
    'USER': 'user_scenario3.csv',
    'REPORT': 'report_scenario3.csv',
    'STATUS': 'status_scenario3.csv',
    'TOWNCOUNCIL': "towncouncil.csv",
    'FEEDBACK': 'feedback_scenario3.csv',
    'SUGGESTION': 'suggestion.csv'}   

db.session.close()
db.drop_all()
db.create_all()

# Delete independent tables
db.session.query(Status).delete()
db.session.query(Feedback).delete()

# Clear associative tables
user = db.session.query(User).all()
for i in user:
    i.wrote_report = []
    i.wrote_suggestion = []
    db.session.commit()

report = db.session.query(Report).all()
for i in report:
    i.has_status = []
    db.session.commit()

towncouncil = db.session.query(TownCouncil).all()
for i in towncouncil:
    i.has_reports = []
    i.received_suggestion = []
    db.session.commit()

# Delete tables
db.session.query(Report).delete()
db.session.query(Suggestion).delete()
db.session.query(User).delete()
db.session.query(TownCouncil).delete()

# Reset ID
db.session.execute('ALTER SEQUENCE "User_user_id_seq" RESTART WITH 1')
db.session.commit()

db.session.execute('ALTER SEQUENCE "Report_report_id_seq" RESTART WITH 10000')
db.session.commit()

db.session.execute('ALTER SEQUENCE "Status_status_id_seq" RESTART WITH 1')
db.session.commit()

db.session.execute('ALTER SEQUENCE "TownCouncil_tcid_seq" RESTART WITH 1')
db.session.commit()

db.session.execute('ALTER SEQUENCE "Feedback_feedback_id_seq" RESTART WITH 1000')
db.session.commit()

db.session.execute('ALTER SEQUENCE "Suggestion_suggestion_id_seq" RESTART WITH 1000')
db.session.commit()

#### LOAD NEW DATA ####
with open(data_folder_path + data_file['USER'], 'r') as f:
    f.readline()
    for line in f:
        l = line.strip().split(',')
        email_address = l[0]
        name = l[1]
        country_code = l[2]
        phone_number = l[3]
        postal_code = l[4]
        password = l[5]
        latitude = l[6]
        longitude = l[7]
        new_user = User(email_address = email_address, name = name, country_code = country_code, phone_number = phone_number, postal_code = postal_code, password = password, latitude = latitude, longitude = longitude)
        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)


with open(data_folder_path + data_file['TOWNCOUNCIL'], 'r') as f:
    f.readline()
    for line in f:
        l = line.strip().split(',')
        name = l[0]
        phone_number = l[1]
        location = l[2]
        operating_hours = l[3]
        website = l[4]
        facebook = l[5]
        instagram = l[6]
        logo = l[7]
        new_towncouncil = TownCouncil(name = name, phone_number = phone_number, location = location, operating_hours = operating_hours,
                                      website = website, facebook = facebook, instagram = instagram, logo = logo)
        db.session.add(new_towncouncil)
        db.session.commit()
        db.session.refresh(new_towncouncil)


with open(data_folder_path + data_file['REPORT'], 'r') as f:
    f.readline()
    for line in f:
        l = line.strip().split(',')
        title = l[0]
        description = l[1]
        street_name = l[2]
        postal_code = l[3]
        nearby_landmarks = l[4]
        latitude = l[5]
        longitude = l[6]
        submitted_by_user = l[7]
        submit_to_tc = l[8]
        photo1 = l[9] if len(l[9]) else None
        photo2 = l[10] if len(l[10]) else None
        new_report = Report(title = title, description = description, street_name = street_name, postal_code = postal_code, nearby_landmarks = nearby_landmarks, latitude = latitude, longitude = longitude, submitted_by_user = submitted_by_user, submit_to_tc = submit_to_tc, photo1=photo1, photo2=photo2)
        db.session.add(new_report)
        db.session.commit()
        db.session.refresh(new_report)


with open(data_folder_path + data_file['STATUS'], 'r') as f:
    f.readline()
    for line in f:
        l = line.strip().split(',')
        status_name = l[0]
        comments = l[1]
        from_report_id = l[2]
        new_status = Status(status_name = status_name, comments = comments, from_report_id = from_report_id)
        db.session.add(new_status)
        db.session.commit()
        db.session.refresh(new_status)


with open(data_folder_path + data_file['FEEDBACK'], 'r') as f:
    f.readline()
    for line in f:
        l = line.strip().split(',')
        from_report = l[0]
        description = l[1]
        rating = l[2]
        tc_response = l[3]
        dt = datetime.now() + timedelta(seconds = 10)
        new_feedback = Feedback(description = description, rating = rating, from_report = from_report, tc_response = tc_response, tc_response_timestamp = dt)
        db.session.add(new_feedback)
        db.session.commit()
        db.session.refresh(new_feedback)


with open(data_folder_path + data_file['SUGGESTION'], 'r') as f:
    f.readline()
    for line in f:
        l = line.strip().split(',')
        category = l[0]
        description = l[1]
        tc_response = l[2]
        from_user = l[3]
        to_tc = l[4]
        dt = datetime.now() + timedelta(seconds = 10)
        new_suggestion = Suggestion(category = category, description = description, from_user = from_user, to_tc = to_tc, tc_response = tc_response, tc_response_timestamp = dt)
        db.session.add(new_suggestion)
        db.session.commit()
        db.session.refresh(new_suggestion)