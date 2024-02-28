from flask import Blueprint, request, render_template, jsonify
from .search import search
from db.database import d

views = Blueprint("views", __name__)

@views.route("/")
def home():
    universities = d.get_all_universities()
    subjects = d.get_all_unique_subjects()
    return render_template("home.html",
                           universities=universities,
                           subjects=subjects)
                           
@views.route("/search")
def search_results():
    if request.args.get('university') != 'Choose a university...':
        university = request.args.get('university')
    else:
        university = None
    if request.args.get('subject') != 'Choose a subject...':
        subject = request.args.get('subject')
    else:
        subject = None
    if request.args.get('course') != 'Choose a course...':
        course = request.args.get('course')
    else:
        course = None
    query = request.args.get('query', '')
    
    results = search(query, university, subject, course)  
    return render_template('search_results.html', query=query, results=results)

@views.route("/upload")
def upload():
    return render_template("upload.html")

@views.route("/profile")
def profile():
    return render_template("profile.html")

@views.route('/get-courses')
def get_courses():
    university = request.args.get('university')
    subject = request.args.get('subject')
    courses = search(query="", university=university, subject=subject)
    return jsonify(courses)

@views.route('/get-subjects')
def get_subjects():
    university = request.args.get('university')
    uni_subjects = d.get_all_subjects_from_university(university)
    return jsonify(uni_subjects)

@views.route("/document")
def document():
    return render_template("document.html")
