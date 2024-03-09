import firebase_admin, os
from firebase_admin import db, credentials, storage
import datetime
from pathlib import Path

class Timestamp:
    def __init__(self) -> None:
        datetime_now = datetime.datetime.utcnow()
        self.timestamp = {
            "date":datetime_now.strftime("%Y-%m-%d"),
            "time":datetime_now.strftime("%H:%M:%S")
        }

class FileStorage:
    def __init__(self) -> None:
        self.db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + '/cert.json')
        storage_url = storage_url = {'storageBucket': 'studypal-8a379.appspot.com'}
        self.app = firebase_admin.initialize_app(self.db_cert, storage_url, name = 'pdf_storage')

    def upload_pdf(self, pdf_file_path: str, document_id: int):
        '''
        Save PDF file to firebase storage.
        '''
        
        storage_path = f'PDF/{document_id}.pdf'
        bucket = storage.bucket(app=self.app)
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(pdf_file_path)
        
        return storage_path
    
    def download_pdf(self, document_id: int):
        
        download_path = (f'{Path.home()}/Downloads')

        with open(f'{download_path}/{document_id}.pdf', 'wb') as f:    
            storage.bucket(app=self.app).get_blob(f'PDF/{document_id}.pdf').download_to_file(f)

    # Generates url to filestorage document
    def generate_download_url(self, document_id: int):
        """Generate a download URL for a document."""
        storage_path = f'PDF/{document_id}.pdf'
        bucket = storage.bucket(app=self.app)
        blob = bucket.blob(storage_path)
        download_url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET') # URL expires in 5 minutes
        return download_url

class DatabaseManager:
    def __init__(self) -> None:
        db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + "/cert.json")
        db_url = {"databaseURL":"https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/"}
        self.app = firebase_admin.initialize_app(db_cert, db_url)
        self.file_storage = FileStorage()
        self.users = {}

        self.course_directory = CourseDirectory()

        # Fetch all users from database
        user_ref = db.reference("/Users")
        users = user_ref.get()
        for user_id in users:
            self.add_user(user_id=user_id, username=users[user_id]["username"], add_to_db=False)
        
        # Fetch all documents from database
        document_ref = db.reference("/Documents")
        #loop...

    def add_user(self, user_id, username, add_to_db=True):
        """Create user and add to database."""

        # Create a new user
        user = User(user_id=user_id, username=username)

        # Add user to dict
        self.users[user_id] = user

        # Save user in database
        if add_to_db:
            self._add_to_db(ref="/Users/", json=user.to_json())

    def add_document(self, user_id, document_id, course_id, pdf_url, header, categorization, add_to_db=True):
        pass

    def add_course(self, course_id, university):
        self.course_directory.add()

    def _add_to_db(self, ref, json):
        db.reference(ref).update(json)

class Comment:
    def __init__(self, user_id, text) -> None:
        self.user_id = user_id
        self.text = text
        self.timestamp = Timestamp().timestamp
    
class Document:
    def __init__(self, pdf_url, header, document_id, user_id, categorization) -> None:
        self.header = header
        self.author = user_id
        self.pdf_url = pdf_url
        self.id = document_id
        self.categorization = categorization
        self.validated = False
        self.comments = {}
        self.votes = {}
        self.timestamp = Timestamp().timestamp
    
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
                    "header":self.header,
                    "pdf_url":self.pdf_url,
                    "validated":self.validated
                },

                "categorization":{
                    
                },

                "votes":{

                },

                "timestamp":self.timestamp
                
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

class CourseDirectory:
    def __init__(self) -> None:
        self.courses = {}
    
    def get(self, course_name):
        return self.courses[course_name]

    def add(self, course: Course):
        self.courses[course.course_name] = course

class User:
    def __init__(self, user_id, username) -> None:
        self._user_id = user_id
        self._username = username
        self._sign_up_timestamp = Timestamp().timestamp
    
    def to_json(self) -> str:
        json = {
            self._user_id:{
                "username":self._username,
                "creation_date":self._sign_up_timestamp
            }
        }

        return json

class SearchController:
    def __init__(self) -> None:
        pass

    def search(self):
        pass
