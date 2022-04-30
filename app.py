# Import Libraries
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from random import randint

import os, json, datetime
import pandas as pd

# Initialize Flask App
app = Flask(__name__)
app.debug = True

# Connect to Database
ubuntuUsername = 'user123'
ubuntuPassword = 'password123'

UPLOAD_FOLDER = './uploads'
FAQ = 'sample_faq.csv'

non_pap_tc = ['Aljunied - Hougang', 'Sengkang']
default_status = 'Pending Review'
non_pap_status = 'Other Agencies'
draft_status = 'Draft'
cancelled_status = 'Cancelled'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@localhost:5432/fyp'.format(ubuntuUsername, ubuntuPassword)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

# Import Helper Functions
from helper_functions import readable_date, readable_time, assigned_to_tc, assigned_to_constituency
from send_email import send_email_otp
from send_sms import send_phone_otp

# Import Database Models
from models import User, Report, TownCouncil, Status, Feedback, Suggestion


### API & ROUTES ###
@app.route('/checkaccountexist', methods = ['GET'])
def check_account_exist():
	try:
		email_address = request.args.get('email_address')

		# Check if email_address exists in DB
		this_user = User.query.filter_by(email_address = email_address).first()
		if this_user == None:
			output = (jsonify(code = 200, body = {'exist': False, 'country_code': '', 'phone_number': '', 'name': '', 'user_id': ''}), 200)
			return output
		
		country_code = this_user.country_code
		phone_number = this_user.phone_number
		name = this_user.name

		output = (jsonify(code = 200, body = {'exist': True, 'country_code': country_code, 'phone_number': phone_number, 'name': name, 'user_id': this_user.user_id}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/phoneotp', methods = ['GET'])
def phone_otp():
	try:
		country_code = request.args.get('country_code')
		phone_number = int(request.args.get('phone_number'))

		country_code = country_code.strip()
		if country_code[0] != '+':
			country_code = '+' + country_code

		otp = ''.join([str(randint(0, 9)) for _ in range(6)])
		send_phone_otp(f'{country_code}{phone_number}', otp) # Send OTP to user
		output = (jsonify(code = 200, body = {'otp': otp}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/createnewuser', methods = ['POST'])
def create_new_user():
	try:
		email_address = request.form['email_address']
		country_code = request.form['country_code']
		phone_number = request.form['phone_number']
		name = request.form['name']
		password = request.form['password'] # FE will encrypt password before sending to BE
		postal_code = request.form['postal_code']
		latitude = request.form['latitude']
		longitude = request.form['longitude']

		new_user = User(email_address = email_address, country_code = country_code, phone_number = phone_number, name = name, password = password, postal_code = postal_code, latitude = latitude, longitude = longitude)
		db.session.add(new_user)
		db.session.commit()
		output = (jsonify(code = 201, body = {'user_id': new_user.user_id}), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/login', methods = ['GET'])
def login():
	try:
		email_address = request.args.get('email_address')
		password = request.args.get('password')
		this_user = User.query.filter_by(email_address = email_address).first()

		# Email not found in DB
		if this_user == None:
			output = (jsonify(code = 404), 404)
			return output
		
		# Password entered does not match DB's password
		if password != this_user.password:
			output = (jsonify(code = 401), 401)
			return output

		# Login success
		output = (jsonify(code = 200, body = {'user_id': this_user.user_id}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/emailotp', methods = ['GET'])
def email_otp():
	try:
		email_address = request.args.get('email_address')
		this_user = User.query.filter_by(email_address = email_address).first()

		if this_user == None:
			output = (jsonify(code = 404, body = 'Email address not found'), 404)
			return output

		otp = ''.join([str(randint(0,9)) for _ in range(6)]) # Generate OTP
		send_email_otp(email_address, otp) # Send OTP to user 

		output = (jsonify(code = 200, body = {'otp': otp}), 200)
		return output
	
	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/gethomepage', methods = ['GET'])
def get_homepage():
	try:
		user_id = request.args.get('user_id')
		reports_found = Report.query.filter_by(submitted_by_user = user_id).all()

		reports_found = sorted(reports_found, key = lambda x: (x.report_id), reverse = True)
		result = []
		for r in reports_found:
			r_statuses = Status.query.filter_by(from_report_id = r.report_id).all()
			most_recent_status = sorted(r_statuses, key = lambda x: (x.status_id))[-1] 
			result.append({'report_id': r.report_id, 'title': r.title, 'status': most_recent_status.status_name, 'pict_name': r.photo1})

		output = (jsonify(code = 200, body = {'user_id': user_id, 'result': result}), 200)
		return output

	except Exception as e:
		return (str(e), 500)


@app.route('/getpict', methods = ['GET'])
def get_pict():
	try:
		pict_name = request.args.get('pict_name')
		pict_path = f'{UPLOAD_FOLDER}/{pict_name}'
		return(send_file(pict_path, as_attachment = True))

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/getreportdetails', methods = ['GET'])
def get_report_details():
	try:
		user_id = request.args.get('user_id')
		report_id = request.args.get('report_id')
		this_report = Report.query.filter_by(report_id = report_id).first()
		
		if this_report.submitted_by_user != int(user_id):
			output = (jsonify(code = 404, body = 'Report not submitted by this user'), 404)
			return output

		# Report Info
		result = {'report_id': this_report.report_id, 'title': this_report.title, 'description': this_report.description, 'nearby_landmarks': this_report.nearby_landmarks, 
				'pict_paths': [this_report.photo1, this_report.photo2, this_report.photo3], 'street_name': this_report.street_name, 'postal_code': this_report.postal_code}

		# Statuses Info
		these_statuses = Status.query.filter_by(from_report_id = report_id).all()
		sorted_statuses = sorted(these_statuses, key = lambda x: (x.timestamp)) # sort in ascending timestamp before returning FE
		status = []
		for s in sorted_statuses:
			if s.status_name != 'Draft':
				status.append({'status_name': s.status_name, 'comments': s.comments, 'date': readable_date(s.timestamp), 'time': readable_time(s.timestamp)})

		# Town Council Info
		this_tc = TownCouncil.query.filter_by(tcid = this_report.submit_to_tc).first()
		tc = {'tc_name': this_tc.name, 'tc_operating_hours': this_tc.operating_hours, 'tc_phone_number': this_tc.phone_number, 'tc_location': this_tc.location, 'logo': this_tc.logo}

		# Feedback Info
		this_feedback = Feedback.query.filter_by(from_report = report_id).first()
		if this_feedback == None:
			feedback = None
		else:
			fb_user = {'timestamp': this_feedback.submission_timestamp, 'description': this_feedback.description, 'rating': this_feedback.rating}
			fb_tc = {'timestamp': this_feedback.tc_response_timestamp, 'tc_response': this_feedback.tc_response}
			feedback = {'user': fb_user, 'tc': fb_tc}
		
		output = (jsonify(code = 200, body = {'user_id': user_id, 'result': result, 'status': status, 'tc': tc, 'feedback': feedback}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output
		

@app.route('/getdraftreport', methods = ['GET'])
def get_draft_report():
	try:
		user_id = request.args.get('user_id')
		report_id = request.args.get('report_id')
		this_report = Report.query.filter_by(report_id = report_id).first()

		if this_report.submitted_by_user != int(user_id):
			output = (jsonify(code = 404, body = 'Report not submitted by this user'), 404)
			return output

		has_statuses = Status.query.filter_by(from_report_id = report_id).all()
		most_recent_status = sorted(has_statuses, key = lambda x: (x.status_id))[-1]
		if most_recent_status.status_name != 'Draft':
			output = (jsonify(code = 404, body = "This is no longer a draft report"), 404)
			return output

		report = {'report_id': report_id, 'title': this_report.title, 'description': this_report.description, 'street_name': this_report.street_name,
				  'postal_code': this_report.postal_code, 'nearby_landmarks': this_report.nearby_landmarks, 'latitude': this_report.latitude, 'longitude': this_report.longitude,
				  'pict_paths': [this_report.photo1, this_report.photo2, this_report.photo3]}
		
		output = (jsonify(code = 200, body = {'user_id': user_id, 'report': report}))
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/gethomelocation', methods = ['GET'])
def get_home_location():
	try:
		user_id = request.args.get('user_id')
		this_user = User.query.filter_by(user_id = user_id).first()

		output = (jsonify(code = 200, body = {'postal_code': this_user.postal_code, 'latitude': this_user.latitude, 'longitude': this_user.longitude}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/getlatlon', methods = ['GET']) # For development purposes only
def getlatlon():
	'''
	Takes in latitude and longitude
	Returns town council assigned to that location
	'''
	lat = request.args.get('lat')
	lon = request.args.get('lon')
	tc = assigned_to_tc(float(lat), float(lon))
	return tc


@app.route('/submitnewreport', methods = ['POST'])
def submit_new_report():
	try:
		submitted_by_user = request.form['user_id']
		title = request.form['title']
		description = request.form['description']
		nearby_landmarks = request.form['nearby_landmarks']
		street_name = request.form['street_name']
		postal_code = request.form['postal_code']
		is_draft = request.form['is_draft']
		is_draft = True if is_draft == 'True' else False
		latitude = request.form['latitude']
		longitude = request.form['longitude']

		# Create new report
		new_report = Report(title = title, description = description, street_name = street_name, postal_code = postal_code, nearby_landmarks = nearby_landmarks, 
							submitted_by_user = submitted_by_user, latitude = latitude, longitude = longitude)
		db.session.add(new_report)
		db.session.commit()

		if is_draft: # If its a draft, save it as new status
			new_status = Status(status_name = draft_status, comments = '', from_report_id = new_report.report_id)

		else: # If its not a draft, check if assigned TC is under PAP's charge
			
			# Assign to town council
			assigned_tc_name = assigned_to_tc(float(latitude), float(longitude))
			assigned_tc = TownCouncil.query.filter_by(name = assigned_tc_name).first()

			if assigned_tc == None:
				# output = (jsonify(code = 404, body = 'Could not map to any town council'), 404)
				# return output
				submit_to_tc = 1
				assigned_tc = TownCouncil.query.filter_by(tcid = submit_to_tc).first()
				print('Could not map to any town council :/ arbitarily mapped to Aljunied - Hougang')
			else:
				submit_to_tc = assigned_tc.tcid

			new_report.submit_to_tc = submit_to_tc
			db.session.commit()

			if assigned_tc.name in non_pap_tc:
				new_status = Status(status_name = non_pap_status, comments = '', from_report_id = new_report.report_id)
			else:
				new_status = Status(status_name = default_status, comments = '', from_report_id = new_report.report_id)
		
		db.session.add(new_status)
		db.session.commit()

		# Save photos to uploads folder
		if request.files:
			if request.files['photo1']:
				photo1 = request.files['photo1']
				if photo1.filename != '':
					photo1_secure_filename = secure_filename(photo1.filename)
					save_in_folder_as = f"{new_report.report_id}_{photo1_secure_filename}"
					photo1.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					new_report.photo1 = save_in_folder_as
					db.session.commit()

			if request.files['photo2']:
				photo2 = request.files['photo2']
				if photo2.filename != '':
					photo2_secure_filename = secure_filename(photo2.filename)
					save_in_folder_as = f'{new_report.report_id}_{photo2_secure_filename}'
					photo2.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					new_report.photo2 = save_in_folder_as
					db.session.commit()

			if request.files['photo3']:
				photo3 = request.files['photo3']
				if photo3.filename != '':
					photo3_secure_filename = secure_filename(photo3.filename)
					save_in_folder_as = f'{new_report.report_id}_{photo3_secure_filename}'
					photo3.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					new_report.photo3 = save_in_folder_as
					db.session.commit()

		output = (jsonify(code = 201, body = {'user_id': submitted_by_user, 'report_id': new_report.report_id}), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/cancelreport', methods = ['POST'])
def cancel_report():
	try:
		user_id = request.form['user_id']
		report_id = request.form['report_id']
		reason = request.form['reason']
		this_report = Report.query.filter_by(report_id = report_id).first()

		if this_report.submitted_by_user != int(user_id):
			output = (jsonify(code = 404, body = 'Report not submitted by this user'), 404)
			return output

		# Check if report has already been cancelled or completed
		has_statuses = Status.query.filter_by(from_report_id = report_id).all()
		for i in has_statuses:
			if (i.status_name == 'Cancelled') or (i.status_name == 'Completed'):
				output = (jsonify(code = 404, body = 'This report has either been cancelled or completed already'), 404)
				return output

		new_status = Status(status_name = cancelled_status, comments = reason, from_report_id = report_id)
		db.session.add(new_status)
		db.session.commit()

		output = (jsonify(code = 201, body = {'user_id': user_id, 'report_id': report_id}), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/canceldraft', methods = ['POST'])
def cancel_draft():
	try:
		user_id = request.form['user_id']
		report_id = request.form['report_id']
		this_report = Report.query.filter_by(report_id = report_id).first()

		if this_report == None:
			output = (jsonify(code = 404, body = 'Report does not exist'), 404)
			return output

		if this_report.submitted_by_user != int(user_id):
			output = (jsonify(code = 404, body = 'Report not submitted by this user'), 404)
			return output

		has_statuses = Status.query.filter_by(from_report_id = report_id).all()
		for i in has_statuses:
			if i.status_name != 'Draft':
				output = (jsonify(code = 404, body = 'This report has progressed from being a Draft'), 404)
				return output

		for i in has_statuses:
			db.session.delete(i)
			db.session.commit()

		db.session.delete(this_report)
		db.session.commit()

		output = (jsonify(code = 203, body = {'user_id': user_id}), 203)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/submitdraftreport', methods = ['POST'])
def submit_draft_report():
	try:
		report_id = request.form['report_id']
		submitted_by_user = request.form['user_id']
		title = request.form['title']
		description = request.form['description']
		nearby_landmarks = request.form['nearby_landmarks']
		street_name = request.form['street_name']
		postal_code = request.form['postal_code']
		is_draft = request.form['is_draft']
		is_draft = True if is_draft == 'True' else False
		latitude = request.form['latitude']
		longitude = request.form['longitude']

		# Find original draft report
		this_report = Report.query.filter_by(report_id = report_id).first()
		if this_report == None:
			output = (jsonify(code = 404, body = 'Draft report not found'), 404)
			return output

		elif this_report.submitted_by_user != int(submitted_by_user):
			output = (jsonify(code = 404, body = 'Report not submitted by this user'), 404)
			return output

		# Check if report is still in Draft status
		has_statuses = Status.query.filter_by(from_report_id = report_id).all()
		for i in has_statuses:
			if i.status_name != 'Draft':
				output = (jsonify(code = 404, body = 'This report has progressed from being a Draft'), 404)
				return output
		
		# Assign to town council
		assigned_tc_name = assigned_to_tc(float(latitude), float(longitude))
		assigned_tc = TownCouncil.query.filter_by(name = assigned_tc_name).first()

		if assigned_tc == None:
			# output = (jsonify(code = 404, body = 'Could not map to any town council'), 404)
			# return output
			submit_to_tc = 1
			print('Could not map to any town council :/ arbitarily mapped to Aljunied - Hougang')
			assigned_tc = TownCouncil.query.filter_by(tcid = submit_to_tc).first()
		else:
			submit_to_tc = assigned_tc.tcid

		# Update report details
		this_report.title = title
		this_report.description = description
		this_report.nearby_landmarks = nearby_landmarks
		this_report.street_name = street_name
		this_report.postal_code = postal_code
		this_report.latitude = latitude
		this_report.longtitude = longitude
		this_report.submit_to_tc = submit_to_tc
		db.session.commit()

		# Remove previous photos from uploads folder
		try:
			os.remove(app.config['UPLOAD_FOLDER'] + '/' + this_report.photo1)
		except:
			pass
		try:
			os.remove(app.config['UPLOAD_FOLDER'] + '/' + this_report.photo2)
		except:
			pass
		try:
			os.remove(app.config['UPLOAD_FOLDER'] + '/' + this_report.photo3)
		except:
			pass

		this_report.photo1 = None
		this_report.photo2 = None
		this_report.photo3 = None

		# Save photos to uploads folder
		if request.files:
			if request.files['photo1']:
				photo1 = request.files['photo1']
				if photo1.filename != '':
					photo1_secure_filename = secure_filename(photo1.filename)
					save_in_folder_as = f"{report_id}_{photo1_secure_filename}"
					photo1.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					this_report.photo1 = save_in_folder_as
					db.session.commit()

			if request.files['photo2']:
				photo2 = request.files['photo2']
				if photo2.filename != '':
					photo2_secure_filename = secure_filename(photo2.filename)
					save_in_folder_as = f'{report_id}_{photo2_secure_filename}'
					photo2.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					this_report.photo2 = save_in_folder_as
					db.session.commit()

			if request.files['photo3']:
				photo3 = request.files['photo3']
				if photo3.filename != '':
					photo3_secure_filename = secure_filename(photo3.filename)
					save_in_folder_as = f'{report_id}_{photo3_secure_filename}'
					photo3.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					this_report.photo3 = save_in_folder_as
					db.session.commit()

		if is_draft: # If its a draft, save it as new status
			new_status = Status(status_name = draft_status, comments = '', from_report_id = report_id)

		else: # If its not a draft, check if assigned TC is under PAP's charge
			if assigned_tc.name in non_pap_tc:
				new_status = Status(status_name = non_pap_status, comments = '', from_report_id = report_id)
			else:
				new_status = Status(status_name = default_status, comments = '', from_report_id = report_id)
		db.session.add(new_status)
		db.session.commit()

		output = (jsonify(code = 201, body = {'user_id': submitted_by_user, 'report_id': report_id}), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/getuserinfo', methods = ['GET'])
def get_user_info():
	try:
		user_id = request.args.get('user_id')
		this_user = User.query.filter_by(user_id = user_id).first()

		output = (jsonify(code = 200, body = {'name': this_user.name, 'email_address': this_user.email_address, 'country_code': this_user.country_code, 'phone_number': this_user.phone_number, 'postal_code': this_user.postal_code}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output

@app.route('/edituserinfo', methods = ['PUT'])
def edit_user_info():
	try:
		user_id = request.form['user_id']
		name = request.form['name']
		country_code = request.form['country_code']
		phone_number = request.form['phone_number']
		postal_code = request.form['postal_code']
		latitude = request.form['latitude']
		longitude = request.form['longitude']

		this_user = User.query.filter_by(user_id = user_id).first()
		this_user.name = name
		this_user.country_code = country_code
		this_user.phone_number = phone_number
		this_user.postal_code = postal_code
		this_user.latitude = latitude
		this_user.longitude = longitude
		db.session.commit()

		output = (jsonify(code = 201, body = {'user_id': user_id}), 201)
		return output

	except Exception as e:
		return (str(e), 500)


@app.route('/changepassword', methods = ['PUT'])
def change_password():
	try:
		user_id = request.form['user_id']
		curr_password = request.form['curr_password']
		new_password = request.form['new_password']
		this_user = User.query.filter_by(user_id = user_id).first()

		if curr_password != this_user.password: # If password entered does not match DB's password
			output = (jsonify(code = 401), 401)
			return output

		this_user.password = new_password
		db.session.commit()
		output = (jsonify(code = 201), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/resetpassword', methods = ['POST'])
def reset_password():
	try:
		user_id = request.form['user_id']
		new_password = request.form['new_password']
		this_user = User.query.filter_by(user_id = user_id).first()

		this_user.password = new_password
		db.session.commit()
		output = (jsonify(code = 201, user_id = this_user.user_id), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/submitfeedback', methods = ['POST'])
def submit_feedback():
	try:
		user_id = request.form['user_id']
		report_id = request.form['report_id']
		description = request.form['description']
		rating = request.form['rating']

		# Check if report was submitted by user
		this_report = Report.query.filter_by(report_id = report_id).first()
		if this_report.submitted_by_user != int(user_id):
			output = (jsonify(code = 404, body = 'Report not submitted by this user'), 404)
			return output

		# Check if report is completed
		report_completed = False
		has_statuses = Status.query.filter_by(from_report_id = report_id).all()
		for i in has_statuses:
			if i.status_name == 'Completed':
				report_completed = True
		if not report_completed:
			output = (jsonify(code = 404, body = 'Submit feedback function not available as report is not completed'), 404)
			return output

		new_feedback = Feedback(description = description, rating = rating, from_report = report_id)
		db.session.add(new_feedback)
		db.session.commit()

		output = (jsonify(code = 201, body = {'user_id': user_id, 'report_id': report_id}), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/submitsuggestion', methods = ['POST'])
def submit_suggestion():
	try:
		user_id = request.form['user_id']
		category = request.form['category']
		description = request.form['description']
		this_user = User.query.filter_by(user_id = user_id).first()

		# Assign to town council
		assigned_tc_name = assigned_to_tc(float(this_user.latitude), float(this_user.longitude))
		assigned_tc = TownCouncil.query.filter_by(name = assigned_tc_name).first()

		if assigned_tc == None:
			# output = (jsonify(code = 404, body = 'Could not map to any town council'), 404)
			# return output
			submit_to_tc = 1
			print('Could not map to any town council :/ arbitarily mapped to Aljunied - Hougang')
			assigned_tc = TownCouncil.query.filter_by(tcid = submit_to_tc).first()
		else:
			submit_to_tc = assigned_tc.tcid

		new_suggestion = Suggestion(category = category, description = description, from_user = user_id, to_tc = submit_to_tc)
		db.session.add(new_suggestion)
		db.session.commit()

		# Save photos to uploads folder
		if request.files:
			if request.files['photo1']:
				photo1 = request.files['photo1']
				if photo1.filename != '':
					photo1_secure_filename = secure_filename(photo1.filename)
					save_in_folder_as = f"{new_suggestion.suggestion_id}_{photo1_secure_filename}"
					photo1.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					new_suggestion.photo1 = save_in_folder_as
					db.session.commit()

			if request.files['photo2']:
				photo2 = request.files['photo2']
				if photo2.filename != '':
					photo2_secure_filename = secure_filename(photo2.filename)
					save_in_folder_as = f'{new_suggestion.suggestion_id}_{photo2_secure_filename}'
					photo2.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					new_suggestion.photo2 = save_in_folder_as
					db.session.commit()

			if request.files['photo3']:
				photo3 = request.files['photo3']
				if photo3.filename != '':
					photo3_secure_filename = secure_filename(photo3.filename)
					save_in_folder_as = f'{new_suggestion.suggestion_id}_{photo3_secure_filename}'
					photo3.save(os.path.join(app.config['UPLOAD_FOLDER'],
								save_in_folder_as))
					new_suggestion.photo3 = save_in_folder_as
					db.session.commit()

		output = (jsonify(code = 201, body = {'user_id':user_id}), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/readsuggestions', methods = ['GET'])
def read_suggestions():
	try:
		user_id = request.args.get('user_id')

		suggestions = []
		has_suggestions = Suggestion.query.filter_by(from_user = user_id).all()

		if len(has_suggestions) == 0:
			output = (jsonify(code = 200, body = {'result': None, 'tc_info': None}), 200)
			return output

		for i in has_suggestions:
			this_tc = TownCouncil.query.filter_by(tcid = i.to_tc).first()
			suggestions.append({'user': {'suggestion_id': i.suggestion_id, 'category': i.category, 'description': i.description, 'submission_timestamp': i.submission_timestamp, 'pict_paths': [i.photo1, i.photo2, i.photo3]},
								'tc': {'tc_response_timestamp': i.tc_response_timestamp, 'tc_response': i.tc_response}})
		
		suggestions = sorted(suggestions, key = lambda x: x['user']['submission_timestamp'], reverse = True)
		output = (jsonify(code = 200, body = {'result': suggestions, 'tc_info': {'logo': this_tc.logo, 'name': this_tc.name}}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/mytowncouncil', methods = ['GET'])
def my_towncouncil():
	try:
		user_id = request.args.get('user_id')
		this_user = User.query.filter_by(user_id = user_id).first()

		# Assign to town council and constituency
		assigned_tc_name = assigned_to_tc(float(this_user.latitude), float(this_user.longitude))
		assigned_tc = TownCouncil.query.filter_by(name = assigned_tc_name).first()

		if assigned_tc == None:
			# output = (jsonify(code = 404, body = 'Could not map to any town council'), 404)
			# return output
			submit_to_tc = 1
			arbitary_constituency = 'Aljunied'
			print('Could not map to any town council :/ arbitarily mapped to Aljunied - Hougang')
			assigned_tc = TownCouncil.query.filter_by(tcid = submit_to_tc).first()
			assigned_constituency = arbitary_constituency
		else:
			submit_to_tc = assigned_tc.tcid
			assigned_constituency = assigned_to_constituency(float(this_user.latitude), float(this_user.longitude))

		# Prepare FAQ
		faq = []
		df = pd.read_csv(FAQ)
		for _, row in df.iterrows():
			faq.append({'question': row['question'], 'answer': row['answer']})

		body = {'constituency': assigned_constituency, 'name': assigned_tc.name, 'location': assigned_tc.location, 'operating_hours': assigned_tc.operating_hours,
				'instagram': assigned_tc.instagram, 'facebook': assigned_tc.facebook, 'website': assigned_tc.website, 'logo': assigned_tc.logo, 'faq':faq, 'phone_number': assigned_tc.phone_number}
		
		output = (jsonify(code = 200, body = body), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/tcgetallreports', methods = ['GET']) # TCP facing
def tc_get_all_reports():
	try:
		tc_id = request.args.get('tc_id')
	
		tc_reports = Report.query.filter_by(submit_to_tc = tc_id).all()
		tc_suggestions = Suggestion.query.filter_by(to_tc = tc_id).all()
		result = []

		for i in tc_reports:
			statuses = Status.query.filter_by(from_report_id = i.report_id).all()
			statuses = [i for i in statuses if i.status_name != 'Draft']			
			if len(statuses) > 0:
				latest_status = sorted(statuses, key = lambda x: (x.timestamp))[-1] # Only return latest status for each report
				sub = [i.timestamp, {'id': i.report_id, 'title': i.title, 'status': latest_status.status_name}]
				result.append(sub)

		for i in tc_suggestions:
			sub = [i.submission_timestamp, {'id': i.suggestion_id, 'title': i.category, 'status': 'Suggestion'}]
			result.append(sub)

		result = sorted(result, key = lambda x: x[0], reverse=True)
		output = (jsonify(code = 200, body = {'tc_id': tc_id, 'result': result}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/tcgetreportdetails', methods = ['GET']) # TCP facing
def tc_get_report_details():
	try:
		tcid = request.args.get('tc_id')
		report_id = request.args.get('report_id')

		this_report = Report.query.filter_by(report_id = report_id).first()
		if this_report == None:
			output = (jsonify(code = 404, body = 'Report does not exist'), 404)
			return output

		if this_report.submit_to_tc != int(tcid):
			output = (jsonify(code = 404, body = 'Report tagged to another town council'), 404)
			return output

		# Report Info
		result = {'report_id': this_report.report_id, 'title': this_report.title, 'description': this_report.description, 'nearby_landmarks': this_report.nearby_landmarks, 
				'pict_paths': [this_report.photo1, this_report.photo2, this_report.photo3], 'street_name': this_report.street_name, 'postal_code': this_report.postal_code, 'timestamp': this_report.timestamp}

		# Statuses Info
		these_statuses = Status.query.filter_by(from_report_id = report_id).all()
		sorted_statuses = sorted(these_statuses, key = lambda x: (x.timestamp)) # sort in ascending timestamp before returning FE
		status = []
		for s in sorted_statuses:
			if s.status_name != 'Draft':
				status.append({'status_name': s.status_name, 'comments': s.comments, 'date': readable_date(s.timestamp), 'time': readable_time(s.timestamp)})

		# User info
		this_user = User.query.filter_by(user_id = this_report.submitted_by_user).first()
		user = {'name': this_user.name, 'phone_number': this_user.phone_number, 'postal_code': this_user.postal_code, 'email_address': this_user.email_address, 'country_code': this_user.country_code}

		# Feedback info
		this_feedback = Feedback.query.filter_by(from_report = report_id).first()
		if this_feedback == None:
			feedback = None
		else:
			feedback = {'description': this_feedback.description, 'timestamp': this_feedback.submission_timestamp, 'rating': this_feedback.rating, 
					'tc_response': {'response': this_feedback.tc_response, 'timestamp': this_feedback.tc_response_timestamp}}

		output = (jsonify(code = 200, body = {'tc_id': tcid, 'result': result, 'status': status, 'user': user, 'feedback': feedback}), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/tcgetsuggestiondetails', methods = ['GET']) # TCP facing
def tc_get_suggestion_details():
	try:
		tc_id = request.args.get('tc_id')
		suggestion_id = request.args.get('suggestion_id')

		this_suggestion = Suggestion.query.filter_by(suggestion_id = suggestion_id).first()
		if this_suggestion == None:
			output = (jsonify(code = 404, body = 'This suggestion does not exist'), 404)
			return output

		if this_suggestion.to_tc != int(tc_id):
			output = (jsonify(code = 404, body = 'This suggestion is assigned to another town council'), 404)
			return output

		this_user = User.query.filter_by(user_id = this_suggestion.from_user).first()
		user_info = {'country_code': this_user.country_code, 'email_address': this_user.email_address, 'name': this_user.name,
					 'phone_number': this_user.phone_number, 'postal_code': this_user.postal_code}
		
		body = {'user': {'suggestion_id': suggestion_id, 'category': this_suggestion.category, 'description': this_suggestion.description, 
						 'submission_timestamp': this_suggestion.submission_timestamp, 'photo1': this_suggestion.photo1, 'photo2': this_suggestion.photo2, 'photo3': this_suggestion.photo3},
				'tc': {'tc_response_timestamp': this_suggestion.tc_response_timestamp, 'tc_response': this_suggestion.tc_response},
				'user_info': user_info}
		
		output = (jsonify(code = 200, body = body), 200)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/tcupdatereportstatus', methods = ['POST']) # TCP facing
def update_report_status():
	try:
		tc_id = int(request.form['tc_id'])
		report_id = request.form['report_id']
		status_name = request.form['status_name']
		comments = request.form['comments']

		# Check if report belongs to this TC, this case shouldn't occur as FE will check this
		this_report = Report.query.filter_by(report_id = report_id).first()
		if this_report.submit_to_tc != tc_id:
			output = (jsonify(code = 404, body = 'This report is assigned to another town council'), 404)
			return output

		new_status = Status(status_name = status_name, comments = comments, from_report_id = report_id)
		db.session.add(new_status)
		db.session.commit()

		output = (jsonify(code = 201), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/tcreplyfeedback', methods = ['POST']) # TCP facing
def tc_reply_feedback():
	try:
		tc_id = int(request.form['tc_id'])
		report_id = request.form['report_id']
		response = request.form['response']

		this_report = Report.query.filter_by(report_id = report_id).first()
		if this_report.submit_to_tc != tc_id:
			output = (jsonify(code = 404, body = 'This report is assigned to another town council'), 404)
			return output

		this_feedback = Feedback.query.filter_by(from_report = report_id).first()
		this_feedback.tc_response = response
		this_feedback.tc_response_timestamp = datetime.datetime.now()
		db.session.commit()
		output = (jsonify(code = 201), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output


@app.route('/tcreplysuggestion', methods = ['POST']) # TCP facing
def tc_reply_suggestion():
	try:
		tc_id = int(request.form['tc_id'])
		suggestion_id = request.form['suggestion_id']
		response = request.form['response']

		this_suggestion = Suggestion.query.filter_by(suggestion_id = suggestion_id).first()
		if this_suggestion.to_tc != tc_id:
			output = (jsonify(code = 404, body = 'This suggestion is assigned to another town council'), 404)
			return output

		this_suggestion.tc_response = response
		this_suggestion.tc_response_timestamp = datetime.datetime.now()
		db.session.commit()
		output = (jsonify(code = 201), 201)
		return output

	except Exception as e:
		output = (jsonify(code = 500, body = str(e)), 500)
		return output