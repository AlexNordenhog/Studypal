from flask import Blueprint, request, render_template, jsonify
from .search import s, SearchError
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

    results = s.search(query, university, subject, course)  
    return render_template('search.html', query=query, results=results)

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
    courses = d.get_courses_from_subject_at_university(university, subject)
    return jsonify(courses)

@views.route('/get-subjects')
def get_subjects():
    university = request.args.get('university')
    uni_subjects = d.get_all_subjects_from_university(university)
    return jsonify(uni_subjects)
    
@views.route('/get-universities')
def get_universities():
    subject = request.args.get('subject')
    subject_unis = d.get_subject_universities(subject)
    return jsonify(subject_unis)

@views.route("/document")
def document():

    id = 1
    document = d.get_document(id)

    votes = d.get_document_votes(id)
    upvotes = votes['upvotes']
    downvotes = votes['downvotes']

    upload_comment = d.get_document_upload_comment(id)
    comments = d.get_document_comments(id)

    header = document['upload']['header']
    author = document['upload']['author']
    date = document['timestamp']['date']
    time = document['timestamp']['time']

    file_storage = d.file_storage
    download_url = file_storage.generate_download_url(id) 

    return render_template("document.html", votes=votes, upload_comment=upload_comment, comments=comments, header=header, author=author, date=date, time=time, upvotes=upvotes, downvotes=downvotes, download_url=download_url)


@views.route('course_page/<course_name>')
def course_page(course_name):
    course_page_dict = d.get_course_data(course_name)
    return render_template("course_page.html", course_page_dict=course_page_dict)

@views.app_errorhandler(SearchError)
def handle_search_error(error):
    '''
    Redirects the user to the search_error page if there is an issue with 
    executing the search() function when they press on the search button.
    '''
    return render_template('search_error.html')

@views.route("/add_user", methods=["POST"])
def add_user():
    data = request.json
    uid = data.get("uid")
    username = data.get("username")
    
    # Add the user to the database
    d.add_user(uid, username)
    
    return jsonify({"message": "User added successfully"})