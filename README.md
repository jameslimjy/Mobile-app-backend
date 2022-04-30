# iTown2@SG: Back End

This repository contains the *back end system* of iTown2@SG. This includes the database and main Application Programming Interface (API) logic of iTown2@SG.

## Table of contents
1. [Before You Start](#before-you-start)
2. [Technologies](#technologies)
3. [Running the Project on Your Local Device](#run-proj-locally)
    1. [Setting Up a Phone Number for One-Time Password (OTP) Verification](#setup-otp)
    2. [Setting Up the Database](#setup-db)
    3. [Creating a Virtual Environment](#create-virtual-env)
    4. [Activating Virtual Environment](#activate-virtual-env)
    5. [Installing Dependencies](#install)
    6. [Initialising and Updating the Database](#initialise-and-update-db)
    7. [Populating the Database](#load-data)
    8. [Running the App](#run)
    9. [Stopping the App](#stop)

## Before You Start<a name="before-you-start"></a>
Please note that the front end interfaces of this project should be run concurrently with the back end. Check out the front end interfaces of this project, [iTown2@SG](https://github.com/iTown2SG/mobile-frontend) and [Town Council Portal (TCP)](https://github.com/iTown2SG/web).

## Technologies<a name="technologies"></a>
This project is created with the following main technologies and versions:

- [Python](https://www.python.org/downloads/): 3.8.3
- [Flask](https://flask.palletsprojects.com/en/1.1.x/installation/): 1.1.2
- [PostgreSQL](https://www.postgresql.org/download/): 12.2
- [Twillio](https://www.twilio.com/try-twilio)

All other requirements and dependencies needed can be found in ```requirements.txt```.

All commands listed below are run on [Ubuntu](https://ubuntu.com/download/desktop), an operating system on Linux.

## Running the Project on Your Local Device<a name="run-proj-locally"></a>
Two (2) terminals will be used in the system.

Terminal A: To run PostgreSQL database

Terminal B: To run main API back end

**Please take note of the terminals used and use the correct terminals to run each of the commands.**

### Setting Up a Phone Number for One-Time Password (OTP) Verification<a name="setup-otp"></a>
Visit [Twillio](https://www.twilio.com/try-twilio) and sign up for an account. Log in to your account if you already have an existing account.

**Take note of the registered phone number on Twillio. This is the only phone number that you can use to receive an OTP, while performing testing using iTown2@SG.**

Go to the [Twillio Console](https://www.twilio.com/console) and look for "ACCOUNT SID", which typically starts with ```AC```. Copy the ACCOUNT SID, and paste it between the double quotes after "(" and before "," in *Line 4* of ```send_sms.py```.

Look for "AUTH TOKEN" on the Twillio Console, then copy it, and paste it between the double quotes after "," and before ")" in *Line 4* of ```send_sms.py```.

On the Twillio Console, get a TRIAL NUMBER. Copy the number and paste it in  *Line 5* of ```send_sms.py```, between the double quotes. This will be the phone number that will be sending the OTP to your registered phone number on Twillio.

### Setting Up the Database<a name="setup-db"></a>
Start the PostgreSQL service in *Terminal A* using
```
sudo service postgresql start
```
and launch it using 
```
sudo -u postgres psql
```

Create a new database using
```
create database fyp;
```

Then, create a new user using
```
create user user123 with password 'password123';
```
and assign rights of the database to this new user using
```
grant all privileges on database fyp to user123;
```

### Creating a Virtual Environment<a name="create-virtual-env"></a>
In *Terminal B*, navigate into the folder that you wish to set up a new virtual environment.

Create a new virtual environment using
```
virtualenv -p python3 env_<folder_name>
```

You can enter any folder name you like. **If you have already created a virtual environment, please proceed directly to activate the virtual environment.**

### Activating Virtual Environment<a name="activate-virtual-env"></a>

Activate the virtual environment using
```
source env_<folder_name>/bin/activate
```

### Installing Dependencies<a name="install"></a>
Make sure that you are running the command in *Terminal B* in the same directory of the file ```requirements.txt```.

Install the required dependencies to the virtual environment with
```
pip install -r requirements.txt
```

### Initialising and Updating the Database<a name="initialise-and-update-db"></a>
In *Terminal B*, initialise the database using
```
python manage.py db init
```

Update the database using
```
python manage.py db migrate
```
and 
```
python manage.py db upgrade
```

### Populating the Database<a name="load-data"></a>
In *Terminal B*, populate data using
```
python load_data.py
```

This will load the necessary data, such as the information of town councils stored in ```load_sample_data/towncouncil.csv```, and some sample data used for testing, such as user information of iTown2@SG stored in ```load_sample_data/user.csv``` into the database.

In *Terminal A*, check if the data has been loaded correctly using
```
\c fyp;
```
and
```
\dt;
```
and
```
select * from <table_name>
```

You can enter any table name you like that appears on the terminal after entering the command ```\dt;```.

### Running the App<a name="run"></a>
In *Terminal B*, run the app with
```
python manage.py runserver
```

You will see the following lines of code. 
```
* Serving Flask app "app" (lazy loading)
* Environment: production
WARNING: This is a development server. Do not use it in a production deployment.
Use a production WSGI server instead.
* Debug mode: on
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
* Restarting with stat
* Debugger is active!
...
```

The app is running on localhost with port 5000. Please ensure that the database system is running on *Terminal A* while the app is running in *Terminal B*.

**Please note that the front end interfaces of this project should be run concurrently with the back end. Check out the front end interfaces of this project, [iTown2@SG](https://github.com/iTown2SG/mobile-frontend) and [Town Council Portal (TCP)](https://github.com/iTown2SG/web).**

### Stopping the App<a name="stop"></a>
Press ```Ctrl``` + ```C``` in *Terminal B* to stop the app.

You can quit the PostgreSQL interface in *Terminal A* using ```\q;```.
