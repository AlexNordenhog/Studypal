from flask import Blueprint, request, render_template, jsonify
from .search import s, SearchError
from db.database import d
from .categorization import c

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
    universities = d.get_all_universities()
    subjects = d.get_all_unique_subjects()
    return render_template("upload.html", universities=universities, subjects=subjects)


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


@views.route("document/<document_id>")
def document(document_id):
    document_dict = d.get_document(document_id)
    if document_dict is None:
        return "Document dict doesnt work", 404
    else:
        pass

    comments = d.get_document_comments(document_id)
    
    for comment in comments:
        if "uid" in comment.keys():
            uid = comment["uid"]
            comment["username"] = d.get_user(uid)["username"]
        
    download_url = document_dict['upload']['pdf_url']
    
    # pdf id instead of download url
    if 'https://' not in download_url:
        file_storage = d.file_storage
        download_url = file_storage.generate_download_url(document_id)

    return render_template("document.html", document_dict=document_dict, download_url=download_url, comments=comments)


@views.route('course_page/<course_name>')
def course_page(course_name):
    course_page_dict = d.get_course_data(course_name)

    comments = d.get_course_comments(course_name)
    
    for comment in comments:
        if "uid" in comment.keys():
            uid = comment["uid"]
            comment["username"] = d.get_user(uid)["username"]    

    return render_template("course_page.html", course_page_dict=course_page_dict, comments=comments)


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


@views.route("/create_profile")
def create_profile():
    return render_template("create_profile.html")


@views.route("/get_document", methods=["POST"])
def get_document():
    data = request.json
    document_id = data.get("document_id")
    
    # Get the document from the database
    document = d.get_document(document_id)
    
    if document:
        categorization = document.get("categorization", {})
        comments = document.get("comments", {})
        upload = document.get("upload", {})
        votes = document.get("votes", {})
        timestamp = document.get("timestamp", {})
        
        # Return specific values from the document
        return jsonify({
            "course": categorization.get("course"),
            "school": categorization.get("school"),
            "subject": categorization.get("subject"),
            "tags": categorization.get("tags"),
            "upload_comment": comments.get("upload_comment"),
            "author": upload.get("author"),
            "header": upload.get("header"),
            "pdf_url": upload.get("pdf_url"),
            "upvotes": votes.get("upvotes"),
            "downvotes": votes.get("downvotes"),
            "date":timestamp.get("date"),
            "time":timestamp.get("time"),
            "validated":upload.get("validated")
        })
    else:
        return jsonify({"error": "Document not found"})


@views.route("/add_document_comment", methods=["POST"])
def add_document_comment():
    data = request.json
    uid = data.get("uid")
    document_id = data.get("document_id")
    text = data.get("text")

    # Add the comment to the document in the database
    d.add_document_comment(document_id, uid, text)

    return jsonify({"message": "Comment added to document successfully"})


@views.route("/add_document_report", methods=["POST"])
def add_document_report():
    data = request.json
    uid = data.get("uid")
    document_id = data.get("document_id")
    text = data.get("text")
    reason = data.get("reason")

    d.add_document_report(document_id, uid, reason, text)

    return jsonify({"message": "Comment added to document successfully"})


@views.route("/add_course_comment", methods=["POST"])
def add_course_comment():
    data = request.json
    uid = data.get("uid")
    course_name = data.get("course_name")
    text = data.get("text")
    
    # Add the comment to the document in the database
    d.add_course_comment(course_name, uid, text)
    
    return jsonify({"message": "Comment added to document successfully"})


@views.route("/test-comment")
def comment():
    return render_template("test-comment.html")


@views.route("/vote_document", methods=["POST"])
def vote_document():
    data = request.json
    uid = data.get("uid")
    document_id = data.get("document_id")
    is_upvote = data.get("is_upvote")
    
    # Add vote to the document in the database
    d.add_document_vote(document_id, uid, is_upvote)
    
    return jsonify({"message": "Vote added successfully"})


@views.route("/get_user", methods=["POST"])
def get_user():
    data = request.json
    uid = data.get("uid")

    user = d.get_user(uid)

    if user != None:
        return jsonify({"username":user["username"],"creation_date":user["creation_date"],"role":user["role"]})
    else:
        return jsonify({"username":'unregistered user', "creation_date":"none"})


@views.route("/test-vote")
def test_comment():
    return render_template("/test-vote.html")


@views.route('/upload_document', methods=['POST'])
def upload_document():
    if 'pdf_file' not in request.files:
        return "No file part"
    
    pdf_file = request.files['pdf_file']

    # Check if the file is selected
    if pdf_file.filename == '':
        return "No selected file"

    # Add document to db
    d.add_document(
        pdf_url=request.form['downloadURL'],
        course=request.form['course'],
        school=request.form['school'],
        upload_comment=request.form['upload_comment'],
        subject=request.form['subject'],
        uid=request.form['uid'],
        header=request.form['header'],
        type_of_document=request.form['type_of_document'],
        tags=request.form.getlist('tags')
    )
    
    return "Document uploaded successfully"

@views.route('/upload_document_v2', methods=['POST'])
def upload_document_v2():
    #if 'tempURL' not in request.files:
    #    return "No file part"
    
    #pdf_file = request.files['pdf_file']

    # Check if the file is selected
    #if pdf_file.filename == '':
    #    return "No selected file"
    course = request.form["uploadCourse"]
    if course == "Choose a course...":
        course = request.form["manualUploadCourse"]

    # Add document to db
    status = (
        d.add_document(
        pdf_url=request.form['tempURL'],
        course=course,
        school=request.form['uploadUniversity'],
        upload_comment=request.form['documentComment'],
        subject=request.form['uploadSubject'],
        uid=request.form['uid'],
        header='none',
        type_of_document=request.form['documentType'],
        tags=[],
        document_date=request.form["documentDate"]
    ))

    return render_template("thank_you.html")

@views.route("/get_user_documents", methods=["POST"])
def get_user_documents_view():
    data = request.json
    uid = data.get("uid")

    if uid is None:
        return jsonify({"error": "UID is required"}), 400

    documents = d.get_user_documents(uid)

    if documents is not None:
        # Format the list of IDs into a list of dictionaries
        formatted_documents = [{"id": doc_id} for doc_id in documents]
        return jsonify(formatted_documents)
    else:
        return jsonify([])  # Return an empty list if no documents are found


@views.route("/upload_v2")
def upload_v2():
    return render_template("upload_v2.html")


@views.route("/upload/temp", methods=["POST"])
def upload_temp_pdf():
    temp_url = request.json.get('temp_url')
    temp_id = request.json.get('temp_id')
    uid = request.json.get('uid')

    if temp_url and temp_id and uid:
        d.add_temp_pdf(temp_id=temp_id, temp_url=temp_url, uid=uid)
        return "Success"
    else:
        return "Missing parameters", 400


@views.route('upload/specifications/<temp_id>', methods=["GET"])
def upload_specificatoins(temp_id):
    temp_url = d.get_temp_pdf(temp_id)

    universities = [
        'Blekinge Institute of Technology', 'Chalmers University of Technology', 'Dalarna University', 'GIH - the Swedish School of Sport and Health Sciences', 'Halmstad University', 
        'Jönköping University', 'KMH - Royal College of Music in Stockholm', 'KTH Royal Institute of Technology', 'Karlstad University', 'Karolinska Institutet', 'Konstfack', 
        'Kristianstad University', 'Linköping University', 'Linneaus University', 'Luleå University of Technology', 'Lund University', 'Malmö University', 'Maria Cederschiöld University',
        'Mid Sweden University', 'Mälardalen University', 'Royal Institute of Art', 'SLU - Swedish University of Agricultural Sciences', 'SMI - University College of Music Education in Stockholm', 
        'Sophiahemmet University College', 'Stockholm School of Economics', 'Stockholm University', 'Stockholm University of the Arts', 'Swedish Defence University', 'Södertörn University', 
        'The Swedish Red Cross University College', 'Umeå University', 'University College Stockholm', 'University West', 'University of Borås', 'University of Gothenburg', 
        'University of Gävle', 'University of Skövde', 'Uppsala University', 'Örebro University'
    ]
    subjects = [
        'Accounting', 'Aerospace Engineering', 'Anthropology', 'Archaeology', 'Art History', 'Astronomy', 'Bioengineering',
        'Biology', 'Business Administration', 'Chemical Engineering', 'Chemistry', 'Civil Engineering', 'Civil Law',
        'Classics', 'Communication Studies', 'Computer Science', 'Criminology', 'Culinary Arts', 'Curriculum and Instruction',
        'Cybersecurity', 'Data Science', 'Dentistry', 'Economics', 'Educational Leadership', 'Educational Psychology',
        'Electrical Engineering', 'English Literature', 'Entrepreneurship', 'Environmental Policy', 'Environmental Science',
        'Fashion Design', 'Finance', 'Geographical Information Systems (GIS)', 'Geography', 'Geology', 'Graphic Design',
        'History', 'Hotel Management', 'Human Resources', 'Information Systems', 'International Business', 'International Law',
        'Languages and Linguistics', 'Law', 'Marine Biology', 'Marketing', 'Mathematics', 'Mechanical Engineering',
        'Medicine', 'Music', 'Network Engineering', 'Nursing', 'Operations Management', 'Patent Law', 'Pharmacy',
        'Philosophy', 'Photography', 'Physics', 'Political Science', 'Psychology', 'Public Health', 'Real Estate',
        'Religious Studies', 'Software Development', 'Software Engineering', 'Special Education', 'Systems Engineering',
        'Tax Law', 'Teaching and Learning', 'Theater and Performance Studies', 'Tourism Management', 'Veterinary Medicine', 'Visual Arts'
    ]
    document_types = ['Assignment', 'Exam', 'Graded Exam (not part of MVP)', 'Lecture Materials', 'Other Document']

    return render_template("upload_specifications.html", url=temp_url, 
                           universities=universities,
                           subjects=subjects,
                           document_types=document_types)

@views.route('/submit-document', methods=['POST'])
def submit_document():
    pdf_url = request.form.get('tempURL')
    uid = int(0)
    document_type = request.form.get('documentType')
    document_date = request.form.get('documentDate')
    university = request.form.get('uploadUniversity')
    subject = request.form.get('uploadSubject')
    course = request.form.get('uploadCourse')
    if course == 'Choose a course...':
        course = request.form.get('manualUploadCourse')
    comment = request.form.get('documentComment', '')
    if document_type == 'Assignment':
        grading_system = request.form.get('gradingSystem', '')
        document_grade = request.form.get('documentGrade', '')
        c.categorize(pdf_url, uid, document_type, document_date, university, subject, course, comment)
    else:
        c.categorize(pdf_url, uid, document_type, document_date, university, subject, course, comment)

    return render_template("thank_you.html")


@views.route("/documents_awaiting_validation")
def get_waiting_documents():
    document_ids = d._get_id_lst(waiting=True)
    reported_ids = d.get_reported_document_ids()

    return render_template("documents_awaiting_validation.html",
                           documents_ids=document_ids, reported_ids=reported_ids)


@views.route("validate_document/<document_id>", methods=["POST"])
def validate_document(document_id):
    data = request.get_json()
    approve = data.get("approve")

    if approve not in [True, False]:
        return "Error: Approve/Disapprove not provided."
    else:
        d.validate_document(document_id, approve)
    
    return jsonify({"status":"success"})


@views.route("validation/<document_id>")
def validation(document_id):
    document_dict = d.get_document(document_id)
    if document_dict is None:
        return "Document dict doesnt work", 404
    else:
        pass

    download_url = document_dict['upload']['pdf_url']
    
    # pdf id instead of download url
    if 'https://' not in download_url:
        file_storage = d.file_storage
        download_url = file_storage.generate_download_url(document_id)

    return render_template("validation.html", document_dict=document_dict, download_url=download_url)


@views.route("/get_document_reports/<document_id>")
def get_document_reports(document_id):
    reports = d.get_document_reports(document_id)
    return jsonify(reports)

@views.route('/status')
def status_view():
    return render_template('status.html')

@views.route('/team')
def team_view():
    return render_template('team.html')

@views.route('/developement_perspective')
def developement_perspective_view():
    return render_template('developement_perspective.html')

@views.route('/timeline')
def timeline_view():
    return render_template('timeline.html')