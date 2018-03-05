# Module imports
import os
import time
import sqlite3
import requests
import jenkins
from jenkinsapi.jenkins import Jenkins
from sqlalchemy import *
from sqlalchemy_utils import has_index, has_unique_index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime

Base = declarative_base()
session = scoped_session(sessionmaker())


class Jobs(Base):
    __tablename__ = 'Jobs'

    id = Column(Integer, primary_key = True)
    jenkins_id = Column(Integer, unique=True)
    name = Column(String)
    time_stamp = Column(DateTime)
    result = Column(String)
    build = Column(String)
    edt = Column(String)

    __table_args__ = (
        Index(
            'my_index',
            jenkins_id,
            time_stamp # I can pass in unique=True here but that affects time_stamp. Am not okay with that being unique
        ),
    )


# Initialization
def init_db(dbname='sqlite:///jenkins.sqlite3'):
    engine = create_engine(dbname, echo=False)
    session.remove()
    session.configure(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.drop_all(engine) # This always allows me to drop db and recreate every time I initiate the script.
    Base.metadata.create_all(engine)
    return engine


# Functions to testing Sqlite DB (using Raw SQL, SQLAlchemy's Core and SQLAlchemy's ORM).
def test_sqlalchemy_orm(number_of_records=1):
    """ ORM """
    init_db()
    start = time.time()
    for i in range(number_of_records):
        user = Jobs()
        user.name = 'NAME ' + str(i)
        session.add(user)
    session.commit()
    end = time.time()
    print
    "SQLAlchemy ORM: Insert {0} records in {1} seconds".format(
        str(number_of_records), str(end - start)
    )


def test_sqlalchemy_core(number_of_records=1):
    """ CORE """
    engine = init_db()
    start = time.time()
    engine.execute(
        Jobs.__table__.insert(),
        [{"name": "NAME " + str(i)} for i in range(number_of_records)]
    )
    end = time.time()
    print
    "SQLAlchemy Core: Insert {0} records in {1} seconds".format(
        str(number_of_records), str(end - start)
    )


def init_sqlite3(dbname="sqlite3.sqlite3"):
    """ This initializes sqlite3 before we insertion into it with Raw SQL """
    conn = sqlite3.connect(dbname)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user")
    cursor.execute("CREATE TABLE user (id INTEGER NOT NULL, name VARCHAR(255), PRIMARY KEY(id))")
    conn.commit()
    return conn


def test_sqlite3(number_of_records=1):
    """ SQLITE3 """
    conn = init_sqlite3()
    cursor = conn.cursor()
    start = time.time()
    for i in range(number_of_records):
        cursor.execute("INSERT INTO user (name) VALUES (?)", ("NAME " + str(i),))
    conn.commit()
    end = time.time()
    print
    "sqlite3: Insert {0} records in {1} seconds".format(
        str(number_of_records), str(end - start)
    )


if __name__ == "__main__":
    test_sqlite3()
    test_sqlalchemy_core()
    test_sqlalchemy_orm()

# Decalared input for Username, Password and Jenkins URL
jenkins_url = 'http://localhost:8080'
username = input('Your username: ')
password = input('Password: ')


""" Function to connect the Jenkins API or get server instance"""
def jenkins_connection(jenkins_url, username, password):
    server = Jenkins(jenkins_url, username=username, password=password)
    return server

if __name__ == '__main__':
    print ('You are using Jenkins Version: %s' %jenkins_connection(jenkins_url, username, password).version)


""" Function to add a Job in the job list """
def add_job(session, joblist):
    for job in joblist:
        session.add(job)
    session.commit()


""" Function to get a previous job """
def get_job(session, name):
    job = session.query(Jobs).filter_by(name=name).order_by(Jobs.jenkins_id_desc()).first()
    if (job != None):
        return job.jenkins_id
    else:
        return None


""" Function to create a Job list """
def create_joblist(start, lastname, jobname):
    job_list = []
    for n in range(start + 1, lastname + 1):
        current = server.get_build_info(jobname, n)
        current_as_jobs = Jobs()
        current_as_jobs.jenkins_id = current['id']
        current_as_jobs.build = current['build']
        current_as_jobs.edt = current['edt']
        current_as_jobs.name = jobname
        current_as_jobs.result = current['result']
        current_as_jobs.time_stamp = datetime.datetime.fromtimestamp(long(current['time_stamp'])*0.001)
        job_list.append(current_as_jobs)
    return job_list


# Define authenticated to be false so that our conditional statements/snippets will take effect on it.

try:
    server = jenkins.Jenkins('http://localhost:8080', username=username, password=password)
    user = server.get_whoami()
    print('You are authenticated by Jenkins as %s' % (user['fullName']))
    authenticated = True
except JenkinsException as e:
    print ('There was an error in authentication!')
    authenticated = False


""" If authenticated, we pass in initialized DB into session and we pass in a loop condition to create joblist """
if authenticated:
    session = init_db

    jobs = server.get_all_jobs()
    for job in jobs:
        job_name = job['name']
        prev_job_id = get_job(session, job_name)
        prev_build_number = server.get_job_info(job_name)['lastbuild']['name']

        if prev_job_id == None:
            start = 0
        else:
            start = prev_job_id

        job_list = create_joblist(start, prev_build_number, jobname)
        add_job(session, job_list)

print("The job is successfully updated into Database")