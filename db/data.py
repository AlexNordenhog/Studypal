import firebase_admin, os
from firebase_admin import db, credentials, storage
import datetime
from pathlib import Path
import uuid
#import json

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
    _votes = {}

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

class CommentSection():
    _comments = {}
    _comment_section_id = uuid.uuid4().hex

    def add_comment(self, user_id:str, text:str, reply_to=None):
        comment = Comment(user_id=user_id, text=text, reply_to=reply_to)
        ref = self._get_new_comment_ref()
        self._comments[ref] = comment

    def _get_new_comment_ref(self) -> int:
        try:
            ref = max(self._comments.keys())
        except:
            ref = 1
        
        return ref

class Comment:
    _vote_dir = VoteDirectory()
    _db_ref = None
    _comment_id = uuid.uuid4().hex

    def __init__(self, user_id, text, reply_to = None):
        """
        :reply_to: id of the parent document
        """
        self._user_id = user_id
        self._text = text
        self._parent = reply_to # comment id
        self._timestamp = Timestamp().timestamp

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
        return self._comment_id

class Document:

    _document_id = uuid.uuid4().hex
    _validated = False
    _comments = {}
    _votes = {}

    def __init__(self, pdf_url, header, document_id, user_id) -> None:
        
        # document content
        self._header = header
        self._pdf_url = pdf_url
        
        # ids
        self._user_id = user_id
        self._timestamp = Timestamp().timestamp
    
    def add_vote(self, user_id, upvote):
        # Overwrites old vote, if it exists
        self.votes[user_id] = upvote

    def add_comment(self, user_id, text):
        comment = Comment(user_id, text)
        self.comments.append(comment)

    def get_id(self) -> int:
        return self._id

    def get():
        return

    def get_header(self) -> str:
        return self._header()

    def get_validation(self) -> bool:
        return self._validated

    def to_json(self):
        json = {
            self.document_id:{
                "upload":{
                    "header":self._header,
                    "pdf_url":self._pdf_url,
                    "validated":self._validated,
                    "user_id":self._user_id
                },

                "categorization":self._categorization,

                "votes":self._votes,

                "timestamp":self._timestamp
                
            }
        }
    
        return json
    
    def get_votes(self):
        """Returns a dictionary with upvote and downvote count."""
        values = list(self.votes.values())
        upvotes = values.count(True)
        downvotes = values.count(False)

        return {
            "upvotes":upvotes,
            "downvotes":downvotes
        }
    
    def get_user_vote(self, user_id):
        """
        Returns user vote type;
        
        If user vote is an upvote: -> True
        If user vote is an upvote: -> True
        If there is no user vote -> None
        """
        
        if user_id in self.votes.keys():
            
            # User vote is recorded
            if self.votes[user_id] == True:

                return True
            
            return False

        return None

    def get_comments(self):
        return self.comments

class GradedExam(Document):
    def __init__(self, pdf_url, header, document_id, user_id, grade) -> None:
        super().__init__(pdf_url, header, document_id, user_id, grade)

class Course:
    _documents = {}
    _comments = {}
    _course_id = uuid.uuid4().hex
    _validated = False
    
    def __init__(self, course_name, university) -> None:
        self._university = university
        self._course_name = course_name

    def change_validation_status(self, approve):
        self._validated = approve

    def get_id(self) -> str:
        return self._course_id

    def add(self, subject, document: Document):
        
        # sorting without subject
        #self.documents[document.id] = document
        
        # with subject

        # Add subject
        if subject not in self.documents.keys():
            self.documents[subject] = {}

        self.documents[subject][document.id] = document

    def get(self, document_id: int, subject: str):
        return self.documents[subject][document_id]

class User:
    def __init__(self, user_id, username, role = "student", sign_up_timestamp=Timestamp().timestamp) -> None:
        self._id = user_id
        self._username = username
        self._sign_up_timestamp = sign_up_timestamp
        self._documents = {}
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

    def add_document_link(self, document: Document):
        document_id = document.get_id()
        document_name = document.get_header()
        document_validated = document.get_validation()
        
        #append
        #self._documents[document_id] = 

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
    
    _pending_courses = {}
    _courses = {}

    def get_course_names(self) -> list:
        pass

    def get(self, course_name):
        return self._courses[course_name]

    def add(self, course: Course):
        self._courses[course.course_name] = course

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

class SearchController:
    def __init__(self) -> None:
        pass

    def search(self):
        pass

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
    
    def _initialize_firebase(self):
        self._firebase_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + "/cert.json")
        self._firebase_url = {"databaseURL":"https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/"}
        self._app = firebase_admin.initialize_app(self._firebase_cert, self._firebase_url, "database")
    
    def get_users(self):

        users_dct = {}

        # Fetch all users from database
        db_user_ref = db.reference("/Users", self._app)
        db_users = db_user_ref.get()
        
        for user_id in db_users:
            users_dct[user_id] = User(user_id=user_id,
                                      username=db_users[user_id]["username"],
                                      sign_up_timestamp=db_users[user_id]["creation_date"])
        
        return users_dct
    
    def get_documents(self):

        documents_dct = {}

        # Fetch all documents from databae

        universities = self._get_keys(f'/Universities/', self._app)
        
        for university in universities:
            subjects = self._get_keys(f'/Universities/{university}')
            
            for subject in subjects:
                courses = self._get_keys(f'/Universities/{university}/{subject}')
                    
                for course in courses:
                    if 'Documents' in self._get_keys(f'/Universities/{university}/{subject}/{course}'):
                        document_types = self._get_keys(f'/Universities/{university}/{subject}/{course}/Documents')

                        for document_type in document_types:
                            document_ids = self._get_keys(f'/Universities/{university}/{subject}/{course}/Documents/{document_type}')
                        
                            for id in document_ids:
                                # add document here to dict
                                pass
        
        return documents_dct

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

    def _set_from_firebase(self):
        
        users = {}
        db_users = self._database.get_users()

        for user in db_users:
            self._user_dir.add(users[user])

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

    def add_document(self, document: Document, user: User, course: Course):
        document.to_json()

    def add_course(self, course_id, university):
        self.course_directory.add()

    def _add_to_db(self, ref, json):
        db.reference(ref).update(json)

class Main:
    _main = None
    _course_dir = CourseDirectory()
    _user_dir = UserDirectory()

    def __new__(cls):
        if cls._main == None:
            cls._main = super(Main, cls).__new__(cls)

        return cls._main

    def _set_from_firebase(self):
        users = self._database.get_users()

        for user in users:
            self._user_dir.add(users[user])
