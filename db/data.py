import firebase_admin, os
from firebase_admin import db, credentials, storage
import datetime
from pathlib import Path
#import json

class Timestamp:
    def __init__(self) -> None:
        datetime_now = datetime.datetime.utcnow()
        self.timestamp = {
            "date":datetime_now.strftime("%Y-%m-%d"),
            "time":datetime_now.strftime("%H:%M:%S")
        }

class Comment:
    def __init__(self, user_id, text) -> None:
        self._user_id = user_id
        self._text = text
        self._timestamp = Timestamp().timestamp

    def get_json(self) -> str:
        json = {
            "user_id": self._user_id,
            "text":self._text,
            "timestamp":self._timestamp
        }
        return json

class Document:
    def __init__(self, pdf_url, header, document_id, user_id, categorization) -> None:
        self._header = header
        self._user_id = user_id
        self._pdf_url = pdf_url
        self._id = document_id
        self._categorization = categorization
        self._validated = False
        self._comments = {}
        self._votes = {}
        self._timestamp = Timestamp().timestamp
    
    def add_vote(self, user_id, upvote):
        # Overwrites old vote, if it exists
        self.votes[user_id] = upvote

    def add_comment(self, user_id, text):
        comment = Comment(user_id, text)
        self.comments.append(comment)

    def get():
        return

    def _to_json(self):
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

class Course:
    def __init__(self, course_name, university) -> None:
        self.documents = {}
        self.comments = {}
        self.university = university
        #self.course_id = course_id
        self.course_name = course_name

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
    def __init__(self, user_id, username, sign_up_timestamp=Timestamp().timestamp) -> None:
        self._id = user_id
        self._username = username
        self._sign_up_timestamp = sign_up_timestamp

    def get_username(self):
        return self._username
    
    def get_id(self):
        return self._id

    def _to_json(self) -> str:
        json = {
            self._user_id:{
                "username":self._username,
                "creation_date":self._sign_up_timestamp
            }
        }

        return json

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
    
    def get(self, course_name):
        return self.courses[course_name]

    def add(self, course: Course):
        self.courses[course.course_name] = course

class UserDirectory(Directory):

    def __init__(self) -> None:
        self._users = {} # UID : User
    
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

    def add_document(self, user_id, document_id, course_id, pdf_url, header, categorization, add_to_db=True):
        pass

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

d = FirebaseManager()
e = FirebaseManager()
f = FirebaseManager()
