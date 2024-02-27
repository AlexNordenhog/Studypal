from flask import Blueprint, request, render_template, jsonify
from .search import search
from db.database import d


views = Blueprint("views", __name__)

universities = d._get_keys('documents')
subjects = []
for university in universities: # Vi kanske borde göra det till en metod i databasen att få ut alla subjects istället
    uni_subjects = d._get_keys(str('documents/' + university))
    for subject in uni_subjects:
        if subject not in subjects:
            subjects.append(subject)

@views.route("/")
def home():
    universities = d._get_keys('documents')
    subjects = []
    for university in universities: # Vi kanske borde göra det till en metod i databasen att få ut alla subjects istället
        uni_subjects = d._get_keys(str('documents/' + university))
        for subject in uni_subjects:
            if subject not in subjects:
                subjects.append(subject)
    return render_template("home.html",
                           universities=universities,
                           subjects=subjects)
                           

@views.route("/search")
def search_results():
    if request.args.get('university') != 'Choose a university...':
        university = request.args.get('university')
    else:
        print('A')
        university = None
    if request.args.get('subject') != 'Choose a subject...':
        subject = request.args.get('subject')
    else:
        print('B')
        subject = None
    if request.args.get('course') != 'Choose a course...':
        course = request.args.get('course')
    else:
        print('C')
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