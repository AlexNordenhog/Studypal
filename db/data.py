import firebase_admin, os
from firebase_admin import db, credentials, storage
import datetime
from pathlib import Path
import uuid
import difflib


class IDHandler:
    #_used_ids = []
    _id_handler = None

    def __new__(cls):
        if cls._id_handler == None:
            cls._id_handler = super(IDHandler, cls).__new__(cls)
        return cls._id_handler
    
    def get_new_id(self) -> str:
        id = uuid.uuid4().hex
        #self._used_ids.append(id)
        return id

class Timestamp:
    def __init__(self) -> None:
        datetime_now = datetime.datetime.utcnow()
        self.timestamp = {
            "date":datetime_now.strftime("%Y-%m-%d"),
            "time":datetime_now.strftime("%H:%M:%S")
        }

class VoteDirectory():

    def __init__(self, vote_directory_id = uuid.uuid4().hex, votes = {}):
        self._vote_directory_id = vote_directory_id
        self._votes = votes

    def get(self) -> dict:
        upvotes = sum(vote for vote in self._votes.values())
        downvotes = len(self._votes) - upvotes
        
        votes = {
            "upvotes":upvotes,
            "downvotes":downvotes
        }

        return votes

    def add(self, user_id, upvote):
        try:
            old_vote = self._votes[user_id]

            if old_vote == upvote:
                return "User vote already stored"
            
            else:
                self._votes[user_id] = upvote
                return "User vote updated"
        except:
            self._votes[user_id] = upvote
            return "User vote stored"
        
    def to_json(self):
        return {
            "votes":self._votes,
            "vote_directory_id":self._vote_directory_id
        }

class CommentSection():
    
    def __init__(self, comment_section_id = uuid.uuid4().hex, comments = {}) -> None:
        self._comment_section_id = comment_section_id
        self._comments = comments

    def add_comment(self, user_id:str, text:str, reply_to=None):
        comment = Comment(user_id=user_id, text=text, reply_to=reply_to)
        ref = self._get_new_comment_ref()
        self._comments[ref] = comment
    
    def get_id(self):
        return self._comment_section_id

    def _get_new_comment_ref(self) -> int:
        try:
            ref = max(self._comments.keys())
        except:
            ref = 1
        
        return ref
    
    def to_json(self):
        return {
            "comments":self._comments,
            "comment_section_id":self._comment_section_id
        }

class Comment:

    def __init__(self, user_id, text, reply_to = None, comment_id = uuid.uuid4().hex, vote_dir = VoteDirectory()):
        """
        :reply_to: id of the parent document
        """
        self._user_id = user_id
        self._comment_id = comment_id
        self._text = text
        self._parent = reply_to # comment id
        self._timestamp = Timestamp().timestamp
        self._vote_dir = vote_dir

    def get_json(self) -> str:
        json = {
            "user_id": self._user_id,
            "text":self._text,
            "timestamp":self._timestamp
        }
        return json

    def get_content(self):
        """
        Returns a json string with 

        user_id,
        text,
        timestamp,
        parent
        """

        json = {
            "user_id": self._user_id,
            "text":self._text,
            "timestamp":self._timestamp,
            "parent":self._parent
        }

    def get_parent(self):
        return self._parent

    def add_vote(self, user_id, upvote):
        return self._vote_dir.add(user_id=user_id, upvote=upvote)

    def get_votes(self) -> dict:
        return self._vote_dir.get()

    def get_id(self):
        return self.comment_id

class Document:

    def __init__(self, pdf_url: str, 
                 document_type: str, 
                 user_id: str, 
                 university: str, 
                 course_name: str, 
                 subject: str, 
                 validated: bool = False, 
                 vote_directory: VoteDirectory = VoteDirectory(), 
                 comment_section: CommentSection = CommentSection(), 
                 document_id: str = uuid.uuid4().hex,
                 timestamp = Timestamp().timestamp) -> None:
        
        # document content
        self._user_id = user_id
        self._header = course_name
        self._pdf_url = pdf_url
        self._document_type = document_type
        
        # categorization
        self._university = university
        self._course_name = course_name
        self._subject = subject
        self._validated = validated
        self._document_id = document_id

        self._timestamp = timestamp

        self._vote_directory = vote_directory
        self._comment_section = comment_section

    def add_vote(self, user_id, upvote):
        self._vote_directory.add(user_id=user_id, upvote=upvote)

    def add_comment(self, user_id, text):
        print("Comments not yet implemented")
        pass

    def get_vote_directory_json(self):
        return self._vote_directory.to_json()

    def get_id(self) -> int:
        return self._document_id

    def get_header(self) -> str:
        return self._header()

    def get_validation(self) -> bool:
        return self._validated

    def get_type(self):
        return self._document_type
    
    def to_json(self):
        json = {
            self._document_id:{
                "upload":{
                    "header":self._header,
                    "pdf_url":self._pdf_url,
                    "validated":self._validated,
                    "user_id":self._user_id
                },

                "categorization":{
                    "university":self._university,
                    "course_name":self._course_name,
                    "subject":self._subject,
                    "document_type":self._document_type
                },

                "vote_directory":self._vote_directory.to_json(),

                #"comment_section":self._comment_section.to_json(),

                "timestamp":self._timestamp
                
            }
        }
    
        return json

class GradedExam(Document):
    def __init__(self, pdf_url, document_type, user_id, 
                 university, course_name, subject, 
                 validated=False, vote_directory=None, 
                 comment_section=None, document_id=uuid.uuid4().hex, 
                 timestamp=Timestamp().timestamp) -> None:
        super().__init__(pdf_url, document_type, user_id, 
                         university, course_name, subject, 
                         validated, vote_directory, comment_section, 
                         document_id, timestamp)

class Course:
    _comment_section_id = None
    '''
    A course.
    '''
    def __init__(self, course_name, university, subject, validated = False, comment_section_id = None) -> None:
        self.course_name = course_name # id
        self._university = university
        self._subject = subject
        self._documents = {'Graded Exams' : [], 'Exams' : [], 'Lecture Materials' : [], 'Assignments' : [], 'Other Documents' : []}
        self._validated = validated

        if comment_section_id:
            self._comment_section_id = comment_section_id

    def approve_course(self):
        '''
        Approves the course by changing _validated to True.
        '''
        self._validated = True

    def get_course_name(self) -> str:
        '''
        Returns the course name.
        '''
        return self.course_name

    def add_document(self, document_type, document_id):
        '''
        Adds a document id to the _documents dict.
        '''
        try:
            self._documents[document_type].append(document_id)
        except:
            print('Could not add document.')

    def add_comment(self, comment):
        '''
        Adds a comment to the _comments dict.
        '''
        self._comments.update({comment.comment_id : comment})

    def get_university(self):
        '''
        Returns the university for the course.
        '''
        return self._university
    
    def get_subject(self):
        '''
        Returns the subject for the course.
        '''
        return self._subject

    def get_course_data(self):
        # Kommer vi behöva denna?
        '''
        Returns a dictionary containing all the information needed to display the course in UI.
        '''

    def to_json(self):
        json = {
            self.course_name:{
                "Documents":{
                    "Graded Exams":(self._documents["Graded Exams"]),
                    "Exams":(self._documents["Exams"]),
                    "Lecture Materials":(self._documents["Lecture Materials"]),
                    "Assignments":(self._documents["Assignments"]),
                    "Other Documents":(self._documents["Other Documents"])
                },

                "Course Info":{
                    "course_name":self.course_name,
                    "university":self._university,
                    "subject":self._subject,
                    "validated":self._validated,
                    "comment_section_id":self._comment_section_id
                }
            }
        }
        
        return json

class User:
    def __init__(self, user_id, username, role = "student", sign_up_timestamp=Timestamp().timestamp, documents: list = []) -> None:
        self._id = user_id
        self._username = username
        self._sign_up_timestamp = sign_up_timestamp
        self._documents = documents
        self._role = role

    def get_username(self):
        return self._username
    
    def get_id(self):
        return self._id

    def to_json(self) -> str:
        json = {
            self._user_id:{
                "username":self._username,
                "creation_date":self._sign_up_timestamp
            }
        }

        return json

    def add_document_link(self, document_id):
        self._documents.append(document_id)

class Moderator(User):
    def __init__(self, user_id, username) -> None:
        super().__init__(user_id, username)

class Student(User):
    def __init__(self, user_id, username) -> None:
        super().__init__(user_id, username)

class Directory:

    def add(self):
        pass

    def get(self):
        pass

class CourseDirectory(Directory):
    '''
    A directory containing courses.
    '''

    _pending_courses = {}
    _courses = {}

    def get_course(self, course_name) -> Course:
        return self._courses[course_name] if self.course_exists(course_name=course_name) else None

    def get_course_names(self) -> list:
        '''
        Returns a list of all the course names for all courses in the course directory.
        '''
        return self._courses.keys()

    def get_courses(self):
        '''
        Returns the _courses dict.
        '''
        return self._courses

    def get(self, course_name):
        '''
        Returns the course object for a certain course name.
        '''
        try:
            return self._courses[course_name]
        except KeyError:
            raise ValueError(f'Could not get course for: {course_name}')

    def add_course(self, course: Course):
        '''
        Takes a course object and adds it to the course dictionary.
        '''
        if not self.course_exists(course_name=course.course_name):
            self._courses.update({course.course_name : course})
        else:
            print(f"Failed to add course. The course, {course.course_name}, already exists.")

    def add_pending_course(self, course: Course):
        '''
        Takes a course object and adds it to the pending course dictionary.
        '''
        self._pending_courses.update({course.course_name : course})

    def course_exists(self, course_name: str) -> bool:
        """
        Takes a string and returns a bool wether if course_name is in the courses dict.
        """
        course_names = self.get_course_names()

        return True if course_name in course_names else False

class UserDirectory(Directory):
    _users = {}
    
    def add(self, user: User) -> bool:
        """
        Returns True if the user is successfully added.
        """
        
        if not self._is_unique_username(user.get_username()):
            return False
        
        self._users[user.get_id()] = user

        return True

    def get(self, user_id) -> User:
        """
        Returns the :User.
        """

        if user_id == "all":
            return self._users

        user = self._users[user_id]
        
        return user

    def _is_unique_username(self, username) -> bool:
        """
        Returns bool wether if the username is unique.
        """

        usernames = []

        for user in self._users:
            usernames.append(self._users[user].get_username())

        if username in usernames:
            return False
        
        return True

class DocumentDirectory(Directory):
    
    _documents = {}

    def add(self, document:Document):
        if not self.document_exists(document._document_id):
            self._documents[document.get_id()] = document
        else:
            print("Document already exists.")

    def get(self, document_id) -> Document:
        return self._documents[document_id] if self.document_exists(document_id) else None

    def document_exists(self, document_id: str) -> bool:
        return True if document_id in self._documents.keys() else False

class SearchController:

    def search(self, query, course_directory: CourseDirectory, university=None, subject=None, course=None):
        '''
        Search function to search for courses in the database.
        
        Parameters:
        - query: Search keyword provided by the user. Can be empty, meaning no keyword search.
        - university: Selected university.
        - subject: Selected subject.
        - course: Selected course.

        Returns a list of matching courses based on the search criteria.
        '''
        filtered_courses = []
        all_courses = course_directory.get_course_names()

        if university and subject and course:
            for c in all_courses:
                course_university = c.get_university()
                course_subject = c.get_subject()
                course_name = c.get_course_name()
                if course_university == university and course_subject == subject and course_name == course:
                    filtered_courses.append(c)
                    break

        elif university and subject and not course:
            for c in all_courses:
                course_university = c.get_university()
                course_subject = c.get_subject()
                if course_university == university and course_subject == subject:
                    filtered_courses.append(c)

        elif university and not subject and not course:
            for c in all_courses:
                course_university = c.get_university()
                if course_university == university:
                    filtered_courses.append(c)

        elif not university and subject and not course:
            for c in all_courses:
                course_subject = c.get_subject()
                if course_subject == subject:
                    filtered_courses.append(c)

        elif not university and not subject and not course:
            filtered_courses.extend(all_courses)

        matching_courses = []
        if query:
            lower_filtered_course_names = []
            filtered_course_names = []
            for c in filtered_courses:
                lower_course_name = c.get_course_name().lower()
                course_name = c.get_course_name()
                lower_filtered_course_names.append(lower_course_name)
                filtered_course_names.append(course_name)
            n_matches = max(1, len(filtered_courses))
            if filtered_courses:
                close_matches = difflib.get_close_matches(query.lower(), lower_filtered_course_names, n=n_matches, cutoff=0.5)
                matching_course_names = [filtered_course_names[lower_filtered_course_names.index(match)] for match in close_matches]
                for course_name in matching_course_names:
                    course = course_directory.get(course_name)
                    matching_courses.append(course)
        else:
            matching_courses = filtered_courses

        return matching_courses

    def get_courses_from_subject_at_university(self, university, subject):
        '''
        Returns a list of all courses from a specific subject at a specific university.
        '''

        subject_courses = self._get_keys(f'Universities/{university}/{subject}')

        return subject_courses
    
    def get_all_subjects_from_university(self, university):
        '''
        Returns a list of all subjects for a certain university.
        '''
        university_subjects = self._get_keys(f'Universities/{university}')

        return university_subjects
    
    def get_subject_universities(self, subject):
        '''
        Returns a list of all universities for a certain subject.
        '''
        subject_universities = []
        universities = self.get_all_universities()
        for u in universities:
            university_subjects = self.get_all_subjects_from_university(u)
            for s in university_subjects:
                if s == subject:
                    subject_universities.append(u)
        return subject_universities


class Firebase:
    _firebase = None

    def __new__(cls):
        # Make sure there is only one instance of FirebaseStorage,
        # and that firebase storage is not initialized multiple times.
        if cls._firebase == None:
            # Initialize Firebase Storage
            cls._initialize_firebase(cls)
            cls._firebase = super(Firebase, cls).__new__(cls)
        return cls._firebase
    
    def _initialize_firebase(self):
        pass

class FirebaseStorage(Firebase):
    _firebase_cert = None
    _app = None
    _storage_url = None

    def __new__(cls):
        return super().__new__(cls)
    
    def _initialize_firebase_storage(self):
        self._firebase_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + "/cert.json")
        self._storage_url = {"storageBucket": "studypal-8a379.appspot.com"}
        self._app = firebase_admin.initialize_app(self._firebase_cert, self._storage_url, name = "storage")

    def upload_pdf(self, pdf_file_path: str, document_id: int):
        """
        Save PDF file to firebase storage.
        """
        
        storage_path = f"PDF/{document_id}.pdf"
        bucket = storage.bucket(app=self.app)
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(pdf_file_path)
        
        return storage_path
    
    def download_pdf(self, document_id: int):
        
        download_path = (f"{Path.home()}/Downloads")

        with open(f"{download_path}/{document_id}.pdf", "wb") as f:    
            storage.bucket(app=self.app).get_blob(f"PDF/{document_id}.pdf").download_to_file(f)

    # Generates url to filestorage document
    def generate_download_url(self, document_id: int):
        """Generate a download URL for a document."""
        storage_path = f"PDF/{document_id}.pdf"
        bucket = storage.bucket(app=self.app)
        blob = bucket.blob(storage_path)
        download_url = blob.generate_signed_url(datetime.timedelta(seconds=300), method="GET") # URL expires in 5 minutes
        return download_url

class FirebaseDatabase(Firebase):
    _app = None
    _firebase_cert = None
    _firebase_url = None

    def __new__(cls):
        return super().__new__(cls)

    def get_from_path(self, path):
        try:
            return db.reference(path, self._app).get()
        except:
            print("Error fetching from FirebaseStorage")

    def _initialize_firebase(self):
        self._firebase_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + "/cert.json")
        self._firebase_url = {"databaseURL":"https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/"}
        self._app = firebase_admin.initialize_app(self._firebase_cert, self._firebase_url, "database")
    
    def add_document(self, document: Document, user_id: str, course: Course):
        ref = db.reference("/Documents", self._app)
        ref.update(document.to_json())

        document_id = document.get_id()
        course_name = course.get_course_name()
        university = course.get_university()
        subject = course.get_subject()
        document_type = document.get_type()

        ref = db.reference(f"/Courses/{course_name}/Documents", self._app)

        # get and update course document reference list
        course_documents = ref.get(document_type)
        
        try:
            course_documents.append(document_id)
        
        except:
            course_documents = [document_id]

        ref.update({document_type:course_documents})

        # add document reference to user
        ref = db.reference(f"/Users/{user_id}", self._app)
        user_documents = ref.get("/Documents")
        
        try:
            user_documents.append(document_id)
        
        except:
            user_documents = [document_id]
        
        ref.update({"Documents":user_documents})
    
    def update_document_votes(self, document_id, vote_directory_json):
        try:
            ref = db.reference(f"/Documents/{document_id}/vote_directory", self._app)
            ref.update(vote_directory_json)
            
        except:
            ref = db.reference(f"/Documents/{document_id}/", self._app)
            ref.update({"vote_directory":vote_directory_json})

    def get_users(self) -> list[User]:
        """Returns a list of all users in a list[User]"""
        users = []
        users_dict = self.get_from_path(path="/Users")
        
        if users_dict:
            for user_id in users_dict:
                user = User(user_id=user_id, username=users_dict[user_id]["username"],
                            role=users_dict[user_id]["role"], sign_up_timestamp=users_dict[user_id]["creation_date"])
                
                users.append(user)
        
        return users
    
    def add_course(self, course: Course):
        ref = db.reference("/Courses", self._app)
        ref.update(course.to_json())

    def get_courses(self) -> list[Course]:
        courses = []
        courses_dict = self.get_from_path("/Courses")
        
        if courses_dict:
            for course_name in courses_dict:
                current_course = courses_dict[course_name]["Course Info"]
                course = Course(course_name=course_name,
                                university=current_course["university"],
                                subject=current_course["subject"],
                                validated=current_course["validated"])
                
                courses.append(course)

        return courses
    
    def get_documents(self) -> list[Document]:
        
        documents = []
        documents_dict = self.get_from_path("/Documents")
        if documents_dict:
            for document_id in documents_dict:
                document_dict = documents_dict[document_id]

                try:
                    vote_directory = VoteDirectory(vote_directory_id=document_dict["vote_directory"]["vote_directory_id"],
                                                   votes=document_dict["vote_directory"]["votes"])
                except:
                    vote_directory = VoteDirectory()

                document = Document(document_id=document_id,
                                    pdf_url=document_dict["upload"]["pdf_url"],
                                    user_id=document_dict["upload"]["user_id"],
                                    validated=document_dict["upload"]["validated"],

                                    university=document_dict["categorization"]["university"],
                                    document_type=document_dict["categorization"]["document_type"],
                                    course_name=document_dict["categorization"]["course_name"],
                                    subject=document_dict["categorization"]["subject"],

                                    vote_directory=vote_directory,

                                    timestamp=document_dict["timestamp"])
                
                documents.append(document)

        return documents

class FirebaseManager:
    _firebase_manager = None
    _storage = FirebaseStorage()
    _database = FirebaseDatabase()

    def __new__(cls):
        # Make sure there is only one instance of FirebseManager
        if cls._firebase_manager == None:
            # Sync with firebase
            cls._firebase_manager = super(FirebaseManager, cls).__new__(cls)
        
        return cls._firebase_manager

    def get_from_database_path(self, path):
        data = self._database.get_from_path(path)

        return data if data else None

    def _set_from_firebase(self):
        
        users = {}
        db_users = self._database.get_users()

        for user in db_users:
            self._user_dir.add(users[user])
        
    def get_all_courses(self) -> list[Course]:
        return self._database.get_courses()

    def get_all_documents(self) -> list[Document]:
        return self._database.get_documents()

    def get_all_users(self) -> list[User]:
        return self._database.get_users()

    def add_document(self, document: Document, user_id: str, course: Course):
        self._database.add_document(document=document, user_id=user_id, course=course)
    
    def update_document_votes(self, document_id, vote_directory_json):
        self._database.update_document_votes(document_id=document_id, vote_directory_json=vote_directory_json)

    #methods below needs to move/change
    def add_user(self, user_id, username, add_to_db=True):
        """Create user and add to database."""

        # Create a new user
        user = User(user_id=user_id, username=username)

        # Add user to dict
        self._users[user_id] = user

        # Save user in database
        if add_to_db:
            self._add_to_db(ref="/Users/", json=user.to_json())

    def add_course(self, course: Course):
        self._database.add_course(course=course)

class Main:
    _main = None
    _firebase_manager = FirebaseManager()
    _course_dir = CourseDirectory()
    _user_dir = UserDirectory()
    _document_dir = DocumentDirectory()
    _search_controller = SearchController()

    def __new__(cls):
        if cls._main == None:
            cls._main = super(Main, cls).__new__(cls)
            cls._set_from_firebase(cls)

        return cls._main
    
    def add_document_vote(self, document_id: str, user_id: str, upvote: bool):
        try:
            document = self._document_dir.get(document_id=document_id)
            document.add_vote(user_id=user_id, upvote=upvote)
            vote_directory_json = document.get_vote_directory_json()

            # update to firebase database
            self._firebase_manager.update_document_votes(document_id=document_id,
                                                         vote_directory_json=vote_directory_json)
        except:
            print(f"Failed to add vote to document: {document_id}")

    def search(self, query, university=None, subject=None, course=None):
        return self._search_controller.search(query=query, course_directory=self._course_dir, university=university, subject=subject, course=course)
    
    def get_universities(self):
        return self._firebase_manager.get_from_database_path("/categorization/universities")

    def get_document_types(self):
        return self._firebase_manager.get_from_database_path("/categorization/document_types")
    
    def get_subjects(self):
        return self._firebase_manager.get_from_database_path("/categorization/subjects")

    def get_document(self, document_id: str) -> Document:
        return self._document_dir.get(document_id=document_id)

    def add_document(self, pdf_url, document_type, 
                 user_id, university, course_name, subject,
                 validated = False, vote_directory = None, 
                 comment_section = None, document_id = uuid.uuid4().hex,
                 timestamp = Timestamp().timestamp):
        
        document = Document(pdf_url=pdf_url, document_type=document_type, 
                 user_id=user_id, university=university, course_name=course_name, subject=subject)
        
        if not self._course_dir.course_exists(course_name=course_name):
            print("Course does not exist, please create the course before (for now?)")
        
        else:
            # add to document dir and firebase
            course = self._course_dir.get_course(course_name=course_name)
            self._document_dir.add(document=document)
            self._firebase_manager.add_document(document=document, user_id=user_id, course=course)

            # add reference in course
            course.add_document(document_id=document_id, document_type=document_type)

            # add reference in user
            user = self._user_dir.get(user_id=user_id)
            user.add_document_link(document_id=document_id)

    def old_add_document(self, course_name: str, document: Document, user_id: str):
        """
        Adds a course to the Document Directory and document id to the Course.
        """

        self._firebase_manager.add_document(document=document, course=self._course_dir.get_course(course_name), user_id=user_id)
        try:
            course = self._course_dir.get_course(course_name)

            # Add the document id to the Course
            document_type = document.get_type()
            document_id = document.get_id()
            course.add_document(document_id=document_id, document_type=document_type)
            
            # Add the document to the Document Directory
            self._document_dir.add(document=document)

            # Save to Firebase
            

            print("Success")
        except:
            print("Error storing document")

    def add_course(self, course_name: str, university: str, subject: str) -> bool:
        """
        Adds a course to the Course Directory.
        """

        course = Course(course_name=course_name,
                        university=university,
                        subject=subject
        )

        self._course_dir.add_course(course=course)
        self._firebase_manager.add_course(course=course)

    def _set_user_directory_from_firebase(self):
        users = self._firebase_manager.get_all_users()
        
        for user in users:
            self._user_dir.add(user)

    def _set_cuorse_directory_from_firebase(self):
        courses = self._firebase_manager.get_all_courses()
        
        for course in courses:
            self._course_dir.add_course(course)

    def _set_documents_from_firebase(self):
        documents = self._firebase_manager.get_all_documents()

        for document in documents:
            self._document_dir.add(document=document)

    def _set_from_firebase(self):
        print("FirebaseRealtimeDatabase sync initiated")
        self._set_user_directory_from_firebase(self)
        self._set_cuorse_directory_from_firebase(self)
        self._set_documents_from_firebase(self)
        print("FirebaseRealtimeDatabase sync completed")

def test_document():
    main = Main()

    # create and add a course
    course = Course("IY1422", "BTH", "Economics")
    main._course_dir.add_course(course=course)

    # add document
    doc = Document(pdf_url="https://", header="is generated", document_type="Exams", user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2")

    print(doc.to_json())

    main.add_document(document=doc, course_name=course.get_course_name(), user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2")
    t = main.get_document(doc.get_id())
    if t:
        print(t.get_id())

#test_document()

def test_course_search():

    # Testing testing
    #course_directory = CourseDirectory()
    #search_controller = SearchController()
    m = Main()
    analys1 = Course('Analys 1', 'Blekinge Institute of Technology', 'Mathematics')
    industriell_marknadsföring = Course('Industriell Marknadsföring', 'Blekinge Institute of Technology', 'Marketing')
    inledande_matematisk_analys = Course('Inledande Matematisk Analys', 'Chalmers Institute of Technology', 'Mathematics')
    m.add_course(analys1, analys1.get_university(), analys1.get_subject())
    m.add_course(industriell_marknadsföring, industriell_marknadsföring.get_university(), industriell_marknadsföring.get_subject())
    m.add_course(inledande_matematisk_analys, inledande_matematisk_analys.get_university(), inledande_matematisk_analys.get_subject())
    search_results = m.search('', 'Blekinge Institute of Technology', 'Mathematics')

    if search_results:
        for result in search_results:
            print(result.get_course_name())
    else:
        print('No search results.')

#test_course_search()



main = Main()
main.add_document_vote(document_id="df69c0d511954b7e9a343b65da52f96f", user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2", upvote=True)

#print(main.get_document("df69c0d511954b7e9a343b65da52f96f").get_type())
#main.add_course('Analys 1', 'Blekinge Institute of Technology', 'Mathematics')
#main.add_document(pdf_url="https://", document_type="Exams", user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2",
#                  university="Blekinge Institute of Technology", course_name="Analys 1", 
#                  subject="Mathematics")