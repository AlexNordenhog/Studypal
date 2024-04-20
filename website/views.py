from flask import Blueprint, request, render_template, jsonify
from db.data import Main
from db.data import SearchController
from .categorization import c

views = Blueprint("views", __name__)

main = Main()
search_controller = SearchController()

@views.route("/")
def home():
    universities = main.get_universities()
    subjects = main.get_subjects()
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

    results = search_controller.search(query, university, subject, course)  
    return render_template('search.html', query=query, results=results)


@views.route("/upload")
def upload():
    universities = main.get_universities()
    subjects = main.get_subjects()
    return render_template("upload.html", universities=universities, subjects=subjects)


@views.route("/profile")
def profile():
    
    return render_template("profile.html")


@views.route('/get-courses')
def get_courses():
    university = request.args.get('university')
    subject = request.args.get('subject')
    courses = search_controller.get_courses_from_subject_at_university(university, subject)
    return jsonify(courses)


@views.route('/get-subjects')
def get_subjects():
    university = request.args.get('university')
    uni_subjects = search_controller.get_all_subjects_from_university(university)
    return jsonify(uni_subjects)


@views.route('/get-universities')
def get_universities():
    subject = request.args.get('subject')
    subject_unis = search_controller.get_subject_universities(subject)
    return jsonify(subject_unis)


@views.route("document/<document_id>")
def document(document_id):
    document_dict = main.to_json('document', document_id)
    if document_dict is None:
        return "Document dict doesnt work", 404
    else:
        pass

    #
    # Detta med kommentarer och grejer måste vi lösa här
    #
    comments = main.to_json("document_comments", document_id) #document_dict[document_id]["comment_section"]["comments"]
        
    download_url = document_dict['upload']['pdf_url']
    
    # pdf id instead of download url
    if 'https://' not in download_url:
        #file_storage = d.file_storage
        download_url = ''#file_storage.generate_download_url(document_id)

    return render_template("document.html", document_dict=document_dict, download_url=download_url, comments=comments)


@views.route('course_page/<course_name>')
def course_page(course_name):
    course_page_dict = main.to_json('course', course_name)

    # Example: {1: {'user_id': 'GrG6hgFUKHbQtNxKpSpGM6Sw84n2', 'text': 'first', 'timestamp': {'date': '2024-04-13', 'time': '17:18:37'}, 'username': 'hampus'}}
    comments = main.get_course(course_name=course_name).get_comments()

    return render_template("course_page.html", course_page_dict=course_page_dict, comments=comments)

@views.route("/add_user", methods=["POST"])
def add_user():
    data = request.json
    user_id = data.get("uid")
    username = data.get("username")
    
    # Add the user to the database
    main.add_user(user_id=user_id,
                  username=username)
    
    return jsonify({"message": "User added successfully"})


@views.route("/create_profile")
def create_profile():
    return render_template("create_profile.html")


@views.route("/get_document", methods=["POST"])
def get_document():
    data = request.json
    document_id = data.get("document_id")
    
    document_dict = main.to_json('document', document_id)
    
    if document:
        categorization = document_dict.get("categorization", {})
        comments = document_dict.get("comments", {})
        upload = document_dict.get("upload", {})
        votes = document_dict.get("votes", {})
        timestamp = document_dict.get("timestamp", {})
        
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
    document = main.get_document(document_id) # The document object
    document.add_comment(user_id=uid, text=text)

    return jsonify({"message": "Comment added to document successfully"})


@views.route("/add_document_report", methods=["POST"])
def add_document_report():
    data = request.json
    uid = data.get("uid")
    document_id = data.get("document_id")
    text = data.get("text")
    reason = data.get("reason")

    main.add_document_report(document_id=document_id, user_id=uid, reason=reason, text=text)

    return jsonify({"message": "Comment added to document successfully"})


@views.route("/add_course_comment", methods=["POST"])
def add_course_comment():
    data = request.json
    uid = data.get("uid")
    course_name = data.get("course_name")
    text = data.get("text")
    
    # Add the comment to the document in the database
    main.get_course(course_name=course_name).add_comment(user_id=uid, text=text)
    
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
    main.get_document(document_id=document_id).add_document_vote(user_id=uid, upvote=is_upvote)
    
    return jsonify({"message": "Vote added successfully"})


@views.route("/get_user", methods=["POST"])
def get_user():
    data = request.json
    uid = data.get("uid")

    user = main.to_json('user', uid)

    if user != None:
        return jsonify(
            {
                "username":user["username"],
                "creation_date":user["creation_date"]["date"],
                "role":user["role"]
            })
    else:
        return jsonify({"username":'unregistered user', "creation_date":"none"})


@views.route("/test-vote")
def test_comment():
    return render_template("/test-vote.html")

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
        main.add_document(
        pdf_url=request.form['tempURL'],
        document_type=request.form['documentType'],
        user_id=request.form['uid'],
        university=request.form['uploadUniversity'],
        course_name=course,
        subject=request.form['uploadSubject'],
        write_date=request.form["documentDate"],
        grade = 'ungraded' # should be what user specified
    ))

    return render_template("thank_you.html")

@views.route("/get_user_documents", methods=["POST"])
def get_user_documents_view():
    data = request.json
    uid = data.get("uid")

    if uid is None:
        return jsonify({"error": "UID is required"}), 400

    try:
        documents = main.get_user_documents(uid)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle unexpected errors from the database call

    if documents is not None:
        # Transforming the documents into a more accessible format
        formatted_documents = []
        for document in documents:
            for doc_id, details in document.items():
                formatted_documents.append({
                    "id": doc_id,
                    "header": details.get('header', 'No Title'),
                    "validated": details.get('validated', 'False')
                })
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

    #
    # Temp pdf??
    #

    if temp_url and temp_id and uid:
        #d.add_temp_pdf(temp_id=temp_id, temp_url=temp_url, uid=uid)
        print("temp pdf not implemented")
        return "Success"
    else:
        return "Missing parameters", 400


@views.route('upload/specifications/<temp_id>', methods=["GET"])
def upload_specificatoins(temp_id):


    #
    # Temp pdf???
    #

    temp_url = ''#d.get_temp_pdf(temp_id)

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

@views.route("/documents_awaiting_validation")
def get_waiting_documents():
    document_ids = main.get_waiting_documents()
    reported_ids = main.get_reported_documents()

    return render_template("documents_awaiting_validation.html",
                           documents_ids=document_ids, reported_ids=reported_ids)


@views.route("validate_document/<document_id>", methods=["POST"])
def validate_document(document_id):
    data = request.get_json()
    approve = data.get("approve")

    if approve not in [True, False]:
        return "Error: Approve/Disapprove not provided."
    else:
        main.validate_document(document_id)
    
    return jsonify({"status":"success"})


@views.route("validation/<document_id>")
def validation(document_id):
    document_dict = main.to_json(document, document_id)
    if document_dict is None:
        return "Document dict doesnt work", 404
    else:
        pass

    download_url = document_dict['upload']['pdf_url']
    
    # pdf id instead of download url
    if 'https://' not in download_url:
        #file_storage = d.file_storage
        download_url = ''#file_storage.generate_download_url(document_id)

    return render_template("validation.html", document_dict=document_dict, download_url=download_url)

@views.route("/get_document_reports/<document_id>")
def get_document_reports(document_id):
    reports = ''
    print("get document reports not implemented")
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