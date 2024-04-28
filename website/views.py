from flask import Blueprint, request, render_template, jsonify
from db.data import Main
from db.data import SearchController


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

    results = search_controller.search(query=query, course_directory=main._course_dir, university=university, subject=subject, course=course)  
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
    try:
        courses = search_controller.get_courses_from_subject_at_university(university, subject)
    except KeyError:
        courses = []
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




@views.route("/document/<document_id>")
def document(document_id):
    # Fetch the document data
    document_data = main.to_json('document', document_id)
    
    # Check if the document data is found
    if not document_data:
        return "Document not found", 404
    
    # Extract the components you need to pass to the template
    content = document_data.get('content', {})
    categorization = document_data.get('categorization', {})
    comments = main.to_json("document_comments", document_id)
    download_url = content.get('pdf_url', '')
    votes = document_data.get('votes', {})
    timestamp = document_data.get('timestamp', '')

    # Pass the data to the template
    return render_template("document.html", 
                           content=content, 
                           categorization=categorization,
                           comments=comments,
                           download_url=download_url,
                           votes=votes,
                           timestamp=timestamp,
                           document_id=document_id)


@views.route('course_page/<course_name>')
def course_page(course_name):
    course_data = main.to_json('course_page', course_name)

    if not course_data:
        return "Course not found", 404

    content = course_data.get('Content', {})
    documents = course_data.get("Documents", {})
    # Example: {1: {'user_id': 'GrG6hgFUKHbQtNxKpSpGM6Sw84n2', 'text': 'first', 'timestamp': {'date': '2024-04-13', 'time': '17:18:37'}, 'username': 'hampus'}}
    comments = main.to_json("course_comments", course_name)
    print(comments)
    print(content)
    print(documents)

    return render_template("course_page.html", 
                           content=content,
                           documents=documents,
                           comments=comments)

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
        content = document_dict.get("content", {})
        votes = document_dict.get("votes", {})
        timestamp = document_dict.get("timestamp", {})
        
        # Return specific values from the document
        return jsonify({
            "course": categorization.get("course"),
            "school": categorization.get("school"),
            "subject": categorization.get("subject"),
            "tags": categorization.get("tags"),
            "upload_comment": comments.get("upload_comment"),
            "author": content.get("author"),
            "header": content.get("header"),
            "pdf_url": content.get("pdf_url"),
            "upvotes": votes.get("upvotes"),
            "downvotes": votes.get("downvotes"),
            "date":timestamp.get("date"),
            "time":timestamp.get("time"),
            "validated":content.get("validated")
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

@views.route("/vote_course_comment", methods=["POST"])
def vote_course_comment():
    data = request.json
    uid = data.get("uid")
    comment_id = data.get("comment_id")
    course_name = data.get("course_name")
    is_upvote = data.get("is_upvote")

    main.get_course(course_name=course_name).add_comment_vote(comment_id=comment_id, user_id=uid, upvote=is_upvote)

    return jsonify({"message": "Vote added successfully"})

@views.route("/vote_document_comment", methods=["POST"])
def vote_document_comment():
    data = request.json
    uid = data.get("uid")
    comment_id = data.get("comment_id")
    document_id = data.get("document_id")
    is_upvote = data.get("is_upvote")

    main.get_document(document_id=document_id).add_comment_vote(comment_id=comment_id, user_id=uid, upvote=is_upvote)

    return jsonify({"message": "Vote added successfully"})

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
                "creation_date":user["creation_date"],
                "role":user["role"]
            })
    else:
        return jsonify({"username":'unregistered user', "creation_date":"none"})


@views.route("/test-vote")
def test_comment():
    return render_template("/test-vote.html")


@views.route('/upload_document_v2', methods=['POST'])
def upload_document_v2():

    if request.form['uid'] == "":
        return "No user id"

    course = request.form["uploadCourse"]
    if course == "Choose a course...":
        course = request.form["manualUploadCourse"]
        main.add_course(course_name=course,
                        university=request.form['uploadUniversity'],
                        subject=request.form['uploadSubject'])

    is_anonymous = 'anonymous' in request.form

    # Add document to db
    document_data = {
        'pdf_url': request.form['tempURL'],
        'document_type': request.form['documentType'],
        'user_id': request.form['uid'],
        'university': request.form['uploadUniversity'],
        'course_name': course,
        'subject': request.form['uploadSubject'],
        'upload_comment': request.form['documentComment'],
        'write_date': request.form['documentDate'],
        'submitted_anonymously': is_anonymous
    }

    if request.form.get('documentGrade'):
        document_data['grade'] = request.form['documentGrade']

    #if request.form.get('anonymousCheckbox'):
    #    document_data['submitted_anonymously'] = True

    main.add_document(**document_data)

    return render_template("thank_you.html")

@views.route("/get_user_documents", methods=["POST"])
def get_user_documents_view():
    data = request.json
    uid = data.get("uid")

    if uid is None:
        return jsonify({"error": "UID is required"}), 400

    try:
        documents = main.get_user_documents(uid)
        print(documents)
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


@views.route("/upload")
def upload_v2():
    return render_template("upload.html")

@views.route("/upload/pdf", methods=["POST"])
def upload_pdf():
    pdf_url = request.json.get('pdf_url')
    pdf_id = request.json.get('pdf_id')
    uid = request.json.get('uid')

    if pdf_url and pdf_id and uid:
        main.add_user_upload(pdf_id=pdf_id, 
                             pdf_url=pdf_url)
        return "Success"
    else:
        return "Missing parameters", 400

@views.route('upload/specifications/<pdf_id>', methods=["GET"])
def upload_specificatoins(pdf_id):

    pdf_url = main.get_user_upload_pdf(pdf_id=pdf_id)

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
    document_types = ['Assignment', 'Exam', 'Graded Exam (coming soon)', 'Lecture Materials', 'Other Document']

    return render_template("upload_specifications.html", url=pdf_url, 
                           universities=universities,
                           subjects=subjects,
                           document_types=document_types)

@views.route("/moderator_panel")
def get_waiting_documents():
    document_ids = main.get_waiting_documents()
    reported_ids = main.get_reported_documents()

    return render_template("moderator_panel.html",
                           documents_ids=document_ids, reported_ids=reported_ids)


@views.route("validate_course/<course_name>", methods=["POST"])
def validate_course(course_name):
    data = request.get_json()
    approve = data.get("approve")

    if approve not in [True, False]:
        return "Error: Approve/Disapprove not provided."
    else:
        main.validate_course(course_name=course_name)
    
    return jsonify({"status":"success"})


from flask import request, jsonify

@views.route("/validate_document/<document_id>", methods=["POST"])
def validate_document(document_id):
    data = request.get_json()
    approve = data.get("approve")

    if approve not in [True, False]:
        return jsonify({"error": "Approve/Disapprove not provided."}), 400
    else:
        try:
            main.validate_document(document_id, approve)

        except Exception as e:
            print(f"Error validating document {document_id}: {str(e)}")
            return jsonify({"error": "Failed to validate document."}), 500
    
    return jsonify({"status": "success", "approved": approve})


@views.route("validation/<document_id>")
def validation(document_id):
    # Fetch the document data
    document_data = main.to_json('document', document_id)
    
    # Check if the document data is found
    if not document_data:
        return "Document not found", 404
    
    # Extract the components you need to pass to the template
    content = document_data.get('content', {})
    categorization = document_data.get('categorization', {})
    comments = main.to_json("document_comments", document_id)
    download_url = content.get('pdf_url', '')
    votes = document_data.get('votes', {})
    timestamp = document_data.get('timestamp', '')

    return render_template("validation.html", 
                           content=content, 
                           categorization=categorization,
                           comments=comments,
                           download_url=download_url,
                           votes=votes,
                           timestamp=timestamp,
                           document_id=document_id)

@views.route("/get_document_reports/<document_id>")
def get_document_reports(document_id):
    reports = ''
    print("get document reports not implemented")
    return jsonify(reports)