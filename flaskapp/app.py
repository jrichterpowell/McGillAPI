from flask import Flask, jsonify
from flaskapp.dbmodels import Course
from flaskapp.dbaccess import DBSession
from collections import OrderedDict
import json
#from sqlalchemy import 

app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome to the (unofficial) McGill Course API, please check the README at https://github.com/jrichterpowell/McGillAPI to get started!"

#endpoint to return the whole course data
@app.route("/latest/<course>")
def courseData(course):
    course = course.replace('-', ' ').replace('_', ' ')
    session = DBSession()
    courseQuery = session.query(Course).filter(Course.code==course).first()

    #if the url was improperly formatted or the course does not exist
    if not courseQuery:
        return "Unable to locate course. Please try formating the code as SUBJECT-NUMBER, i.e. MATH-141"

    else:
        courseReturn = courseQuery.__dict__
        #del courseReturn._sa_instance_state
        return jsonify({
            'code':courseQuery.code,
            'terms':courseQuery.terms,
            'profs':json.loads(courseQuery.profs),
            'prereqs':courseQuery.prereqs,
            'credits':courseQuery.credits
        })