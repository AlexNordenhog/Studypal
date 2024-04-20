import firebase_admin, os
from firebase_admin import db, credentials, storage
from datetime import datetime
from pathlib import Path
import uuid
import difflib
import time
import operator

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

    def push_to_path(self, path, data):
        ref = db.reference(path, self._app)
        ref.update(data)

    def get_from_path(self, path):
        """Returns the json string from the database avalable under specified 'path'"""
        try:
            return db.reference(path, self._app).get()
        except:
            print("Error fetching from FirebaseStorage")

    def _initialize_firebase(self):
        self._firebase_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + "/cert.json")
        self._firebase_url = {"databaseURL":"https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/"}
        self._app = firebase_admin.initialize_app(self._firebase_cert, self._firebase_url, "database")
    
    def add_document(self, document, user_id: str, course_name: str):
        """Add a document to the database."""

        ref = db.reference("/Documents", self._app)
        ref.update(document.to_json())

        document_id = document.get_id()
        document_type = document.get_type()

        ref = db.reference(f"/Courses/{course_name}/Documents/{document_type}", self._app)

        # get and update course document reference list
        course_documents = ref.get()

        try:
            course_documents.append(document_id)
        
        except:
            course_documents = [document_id]

        ref.parent.update({document_type:course_documents})

        # add document reference to user
        ref = db.reference(f"/Users/{user_id}/Documents", self._app)
        user_documents = ref.get()
        
        try:
            user_documents.append(document_id)

        except:
            user_documents = [document_id]
        
        ref.parent.update({"Documents":user_documents})
    
    def update_document_votes(self, document_id, vote_directory_json):
        """Updates a document's vote directory in the database"""
        try:
            ref = db.reference(f"/Documents/{document_id}/vote_directory", self._app)
            ref.update(vote_directory_json)
            
        except:
            ref = db.reference(f"/Documents/{document_id}/", self._app)
            ref.update({"vote_directory":vote_directory_json})

    def update_document_comment_section(self, document_id, document_comment_section_json):
        try:
            ref = db.reference(f"/Documents/{document_id}/comment_section", self._app)
            ref.update(document_comment_section_json)
            
        except:
            ref = db.reference(f"/Documents/{document_id}/", self._app)
            ref.update({"comment_section":document_comment_section_json})

    def update_course_comment_section(self, course_name: str, comment_section: str):
        try:
            ref = db.reference(f"/Courses/{course_name}/comment_section", self._app)
            ref.update(comment_section)
        except:
            ref = db.reference(f"/Courses/{course_name}", self._app)
            ref.update({"comment_section":comment_section})

    def get_users(self):
        """
        Takes the users from the database and creates User objects from the data.

        Returns list containing all users avalable in the database.
        """
        
        users = []
        users_dict = self.get_from_path(path="/Users")
        
        if users_dict:
            for user_id in users_dict:
                try:
                    documents = users_dict[user_id]["Documents"]
                except:
                    documents = []

                user = User(user_id=user_id, 
                            username=users_dict[user_id]["username"],
                            documents=documents,
                            role=users_dict[user_id]["role"], 
                            sign_up_timestamp=users_dict[user_id]["creation_date"])
                
                users.append(user)
        
        return users
    
    def add_course(self, course):
        """Add a course to the database"""
        ref = db.reference("/Courses", self._app)
        ref.update(course.to_json())

    def get_courses(self) -> list:
        """Returns list containing all courses avalable in the database."""
        courses = []
        courses_dict = self.get_from_path("/Courses")
        
        if courses_dict:

            # Do for each course
            for course_name in courses_dict:
                
                current_course = courses_dict[course_name]["Course Content"]
                
                # Comment Section
                comment_section = None

                if "comment_section" in list(current_course.keys()):

                    #comment_section_id = current_course["comment_section"]["comment_section_id"]
                    parent_path = f"Courses/{course_name}/Course Content/comment_section"
                    comment_section = self._load_comment_section(comment_section_json=current_course["comment_section"],
                                                                 parent_path=parent_path)
                
                # Create the course
                course = Course(course_name=course_name,
                                university=current_course["university"],
                                subject=current_course["subject"],
                                validated=current_course["validated"],
                                comment_section=comment_section)
                
                courses.append(course)

        return courses

    def _load_comment_section(self, comment_section_json, parent_path):
        
        # Comment Section
        comment_section = None
        comments = {}
        comment_section_id = comment_section_json

        try:
            # Course Comments
            if comment_section_json["comments"].keys():
                for comment_id in list(comment_section_json["comments"].keys()):
                    comment_json = comment_section_json["comments"][comment_id]
                    
                    # Vote directory for each comment
                    try:
                        vote_directory = VoteDirectory(vote_directory_id=comment_json["vote_directory"]["vote_directory_id"],
                                                        votes=comment_json["vote_directory"]["votes"])
                    except:
                        vote_directory = VoteDirectory(vote_directory_id=comment_json["vote_directory"]["vote_directory_id"])

                    comment = Comment(comment_id=comment_id,
                                        user_id=comment_json["user_id"],
                                        parent_path=comment_json["parent_path"],
                                        timestamp=datetime.strptime(comment_json["timestamp"], "%Y-%m-%d %H:%M:%S.%f"),
                                        vote_dir=vote_directory,
                                        text=comment_json["text"])

                    comments[comment_id] = comment
        except:
            comments = {}

        # Replies
        replies = {}
        try:
            comment_ids = list(comment_section_json["replies"].keys())
            if comment_ids:

                # Replies for each comment
                for comment_id in comment_ids:
                    reply_ids = list(comment_section_json["replies"][comment_id].keys())

                    for reply_id in reply_ids:
                        reply_json = comment_section_json["replies"][comment_id][reply_id]
                        
                        # Vote directory for each reply
                        try:
                            vote_directory = VoteDirectory(vote_directory_id=reply_json["vote_directory"]["vote_directory_id"],
                                                        votes=reply_json["vote_directory"]["votes"])
                        except:
                            vote_directory = VoteDirectory(vote_directory_id=reply_json["vote_directory"]["vote_directory_id"])

                        reply = Comment(comment_id=reply_id,
                                        user_id=reply_json["user_id"],
                                        parent_path=reply_json["parent_path"],
                                        timestamp=datetime.strptime(reply_json["timestamp"], "%Y-%m-%d %H:%M:%S.%f"),
                                        vote_dir=vote_directory,
                                        text=reply_json["text"])
                        
                        if not comment_id in replies.keys():
                            replies[comment_id] = {}
                        
                        replies[comment_id][reply_id] = reply

        except:
            replies = {}

        comment_section = comment_section=CommentSection(parent_path=parent_path,
                                                            comment_section_id=comment_section_id,
                                                            comments=comments,
                                                            replies=replies)
        return comment_section

    def update(self, path, json):
        """
        Updates the Firebase Realtime Database with 'json' under 'path'
        """
        db.reference(path, self._app).update(json)

    def get_documents(self) -> list:
        """Returns list containing all documents avalable in the database."""
        documents = []
        documents_dict = self.get_from_path("/Documents")
        if documents_dict:
            for document_id in documents_dict:
                document_dict = documents_dict[document_id]
                document_path = f"Documents/{document_id}"
                
                # Vote Directory
                try:
                    vote_directory = VoteDirectory(vote_directory_id=document_dict["vote_directory"]["vote_directory_id"],
                                                   votes=document_dict["vote_directory"]["votes"])
                except:
                    vote_directory = VoteDirectory(vote_directory_id=document_dict["vote_directory"]["vote_directory_id"])

                # Comment Section
                comment_section = None

                if "comment_section" in list(document_dict.keys()):

                    #comment_section_id = current_course["comment_section"]["comment_section_id"]
                    parent_path = f"Documents/{document_id}/comment_section"
                    comment_section = self._load_comment_section(comment_section_json=document_dict["comment_section"],
                                                                 parent_path=parent_path)
                
                document = Document(document_id=document_id,
                                    pdf_url=document_dict["content"]["pdf_url"],
                                    user_id=document_dict["content"]["user_id"],
                                    grade=document_dict["content"]["grade"],
                                    
                                    write_date=document_dict["content"]["write_date"],
                                    validated=document_dict["categorization"]["validated"],
                                    university=document_dict["categorization"]["university"],
                                    document_type=document_dict["categorization"]["document_type"],
                                    course_name=document_dict["categorization"]["course_name"],
                                    subject=document_dict["categorization"]["subject"],

                                    vote_directory=vote_directory,
                                    comment_section=comment_section,

                                    timestamp=datetime.strptime(document_dict["timestamp"], "%Y-%m-%d %H:%M:%S.%f"))
                
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
        
    def get_all_courses(self) -> list:
        return self._database.get_courses()

    def get_all_documents(self) -> list:
        return self._database.get_documents()

    def get_all_users(self) -> list:
        return self._database.get_users()

    def add_document(self, document, user_id: str, course_name:str):
        self._database.add_document(document=document, user_id=user_id, course_name=course_name)
    
    def update_document_votes(self, document_id, vote_directory_json):
        self._database.update_document_votes(document_id=document_id, vote_directory_json=vote_directory_json)

    def update_document_comment_sectino_votes(self, document_id, document_comment_section_json):
        self._database.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)

    def update_document_comment_section(self, document_id, document_comment_section_json):
        self._database.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)

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

    def add_course(self, course):
        self._database.add_course(course=course)


class Timestamp:
    def __init__(self) -> None:
        datetime_now = datetime.datetime.utcnow()
        self.timestamp = {
            "date":datetime_now.strftime("%Y-%m-%d"),
            "time":datetime_now.strftime("%H:%M:%S")
        }

class Directory:

    def add(self):
        pass

    def get(self):
        pass

class VoteDirectory(Directory):

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
                print("User vote already stored")
                return self._votes
            
            else:
                self._votes[user_id] = upvote
                print("User vote updated")
                return self._votes
            
        except:
            self._votes[user_id] = upvote
            print("User vote stored")
            return self._votes
        
    def to_json(self):
        return {
            "votes":self._votes,
            "vote_directory_id":self._vote_directory_id
        }

class CommentSection():

    def __init__(self, parent_path, 
                       comment_section_id = uuid.uuid4().hex, 
                       comments = {}, 
                       replies = {}
                       ) -> None:
        
        self._comment_section_id = comment_section_id
        self._comments = comments # { comment_id : Comment }
        self._replies = replies # { reply_to_comment_id : { reply_id : Comment } }
        self._db_path = f"{parent_path}"

    def add_comment(self, user_id: str, text: str):
        comment = Comment(user_id=user_id, text=text, parent_path=f"{self._db_path}/comments")
        FirebaseDatabase().push_to_path(comment._db_path, data=comment.to_json())
        self._comments[comment.get_id()] = comment

    def add_reply(self, user_id: str, text: str, reply_to_comment_id: str):
        reply = Comment(user_id=user_id, text=text, parent_path=f"{self._db_path}/replies/{reply_to_comment_id}")
        FirebaseDatabase().push_to_path(reply._db_path, data=reply.to_json())
        self._replies[reply.get_id()] = reply

    def get_comment(self, page, comment_id):

        if comment_id in list(self._comments[page].keys()):
            return self._comments[page][comment_id]
        else:
            replied_to_comment_ids = list(self._replies.keys())
            for replied_to_comment_id in replied_to_comment_ids:
                print(replied_to_comment_id)
                if comment_id in list(self._replies[replied_to_comment_id]):
                    return self._replies[replied_to_comment_id][comment_id]
        
        print("404: Comment not found error")
    
    def get_comments(self, sorting='popular', order='desc', amount: int = 10, page: int = 1):
        """
        Returns dict of comments on page :page:, if there is :amount: comments per page.

        :sorting: "popular", "new"
        :order: "desc" (descending), "asc" (ascending)
        :amount: int
        :page: int (1 is the first page)
        """

        _comments = self._comments # {}
        _sorted_comments = {}
        #comment_ids = list(self._comments.keys()) #list(self.get_comments_on_page(page))

        #for comment_id in comment_ids:
        #    comment = self._comments[comment_id] #self.get_comment(page, comment_id)
        #    _comments.update({comment_id : comment})

        if sorting == 'popular':

            if order == 'asc':
                for comment in (sorted(_comments.values(), key = operator.attrgetter('rating'))):
                    _sorted_comments.update({comment.get_id() : comment})

            elif order == 'desc':
                for comment in (sorted(_comments.values(), key = operator.attrgetter('rating'), reverse=True)):
                    _sorted_comments.update({comment.get_id() : comment})

        elif sorting == 'new':

            if order == 'asc':
                for comment in (sorted(_comments.values(), key = operator.attrgetter('timestamp'))):
                    _sorted_comments.update({comment.get_id() : comment})

            elif order == 'desc':
                for comment in (sorted(_comments.values(), key = operator.attrgetter('timestamp'), reverse=True)):
                    _sorted_comments.update({comment.get_id() : comment})

        else:
            print(f"Error: Sorting ({sorting}) or order ({order}) option not avalable")

        return _sorted_comments

    def get_replies(self, comment_id: str):
        """
        Structure of return will change to the same way comments are returned.

        Get replies from the comment_id.
        
        Returns a list of comments, or empty list if there are no replies.
        """

        replies = []

        if self._has_replies(comment_id=comment_id):
            replies = self._replies[comment_id]
            
        return replies

    def _has_replies(self, comment_id):
        try:
            self._replies[comment_id]
            return True
        except:
            return False

    def get_id(self):
        return self._comment_section_id
    
    def add_comment_vote(self, comment_id, user_id, upvote):
        try:
            comment = self._comments[comment_id]
            return comment.add_vote(user_id=user_id, upvote=upvote)
        except:
            print(f"CommentSection: Failed to add vote to comment: {comment_id}")

    def add_reply_vote(self, comment_id, reply_id, user_id, upvote):
        try:
            reply = self._replies[comment_id][reply_id]
            return reply.add_vote(user_id=user_id, upvote=upvote)
        except:
            print(f"CommentSection: Failed to add vote to reply: {reply_id}, on comment: {comment_id}")

    def to_json(self):

        comments_json = {}
        replies_json = {}

        comment_ids = list(self._comments.keys())

        for comment_id in comment_ids:
            comments_json[comment_id] = self._comments[comment_id].to_json()

        comment_ids_with_replies = list(self._replies.keys())

        for comment_id in comment_ids_with_replies:
            reply_ids = list(self._replies[comment_id].keys())
            replies_json[comment_id] = {}

            for reply_id in reply_ids:
                replies_json[comment_id][reply_id] = self._replies[comment_id][reply_id].to_json()

        return {
            "comments":comments_json,
            "replies":replies_json,
            "comment_section_id":self._comment_section_id
        }
    
    def get_comments_on_page(self, page):
        '''
        Get the comment dictionary for a certain page.
        Based on _comments having the following structure:
        _comments={
            1:{
                id:comment,
                id:comment,
                id:comment,
                id:comment,
                id:comment,
            },
            
            2:{
                id:comment,
                id:comment,
                id:comment,
                id:comment,
                id:comment,
            }
        }
        '''
        return self._comments[page]

class Comment:

    def __init__(self, user_id, text, parent_path, comment_id = uuid.uuid4().hex, timestamp = datetime.now(), vote_dir = None):
        self._user_id = user_id
        self._comment_id = comment_id
        self._text = text
        self.timestamp = timestamp
        self._db_path = f"{parent_path}/{comment_id}"

        if vote_dir:
            self._vote_dir = vote_dir

        else:
            self._vote_dir = VoteDirectory()

        votes = self._vote_dir.get()
        self.rating = votes['upvotes'] - votes['downvotes']

    def get_json(self) -> str:
        json = {
            "user_id": self._user_id,
            "text":self._text,
            "timestamp":self._timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "votes":self._vote_dir.get()
        }
        return json

    def get_timestamp(self):
        return self._timestamp

    def to_json(self):
        """
        Returns a json string
        """

        json = {
            "comment_id":self._comment_id,
            "user_id": self._user_id,
            "text":self._text,
            "timestamp":self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "vote_directory":self._vote_dir.to_json(),
            "parent_path":self._db_path.replace(f"/{self._comment_id}", "")
        }

        return json

    def add_vote(self, user_id, upvote):
        return self._vote_dir.add(user_id=user_id, upvote=upvote)

    def get_votes(self) -> dict:
        return self._vote_dir.get()

    def get_vote_directory_json(self):
        return self._vote_dir.to_json()

    def get_id(self):
        return self._comment_id

class Document:

    def __init__(self, pdf_url: str, 
                 document_type: str, 
                 user_id: str, 
                 university: str, 
                 course_name: str, 
                 subject: str,
                 write_date: str,
                 grade: str = "ungraded",
                 validated: bool = False, 
                 vote_directory: VoteDirectory = None, 
                 comment_section: CommentSection = None, 
                 document_id: str = uuid.uuid4().hex,
                 timestamp = datetime.now(),
                 reported = False) -> None:
                
        
        # document content
        self._user_id = user_id
        self._header = f"{document_type} {write_date}"
        self._pdf_url = pdf_url
        self._document_type = document_type
        self._grade = grade
        self._write_date = write_date

        # categorization
        self._university = university
        self._course_name = course_name
        self._subject = subject
        self._validated = validated
        self._document_id = document_id
        self._db_path = f"Documents/{self._document_id}"

        self._timestamp = timestamp

        if vote_directory:
            self._vote_directory = vote_directory
        else:
            #path = f"Documents/{self._document_id}/vote_directory"
            self._vote_directory = VoteDirectory()

        if comment_section:
            self._comment_section = comment_section
        else:
            self._comment_section = CommentSection(parent_path="")

        self._reported = reported
    
    def get_id(self):
        return self._document_id

    def get_header(self):
        return self._header

    def get_validation(self):
        return self._validated

    def to_json(self):
        json = {
            self._document_id:{
                "content":{
                    "header":self._header,
                    "pdf_url":self._pdf_url,
                    "user_id":self._user_id,
                    "grade":self._grade,
                    "write_date":self._write_date
                },

                "categorization":{
                    "university":self._university,
                    "course_name":self._course_name,
                    "subject":self._subject,
                    "validated":self._validated,
                    "document_type":self._document_type
                },

                "vote_directory":self._vote_directory.to_json(),

                "comment_section":self._comment_section.to_json(),

                "timestamp":self._timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            }
        }
    
        return json

    def get_author(self) -> str:
        """Returns the author user id as str"""
        return self._user_id

    def get_course_name(self) -> str:
        """Returns the course name as str"""
        return self._course_name

    def get_comment_section_json(self):
        return self._comment_section.to_json()

    def get_report_status(self):
        '''
        Find out if the comment is reported.
        '''
        return self._reported
    
    def validate_document(self):
        '''
        Validate the document.
        '''
        self._validated = True

    # document votes

    def add_document_vote(self, user_id, upvote):
        try:
            data = self._vote_directory.add(user_id=user_id, upvote=upvote)
            path = f"{self._db_path}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Document: Failed to add vote to document: {self._document_id}")

    def get_vote_directory_json(self):
        return self._vote_directory.to_json()
        return self._document_type
       
    # comment section

    def add_comment(self, user_id, text):
        self._comment_section.add_comment(user_id=user_id, text=text)

    def add_comment_vote(self, user_id, comment_id, upvote):
        try:
            data = self._comment_section.add_comment_vote(user_id=user_id, comment_id=comment_id, upvote=upvote)
            path = f"{self._db_path}/comment_section/comments/{comment_id}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Document: Failed to add vote to comment: {self._document_id}")

    def get_comment(self, comment_id):
        return self._comment_section.get_comment(comment_id=comment_id)
    
    def add_comment_reply(self, user_id, text, reply_to_comment_id):
        self._comment_section.add_reply(user_id=user_id, text=text, reply_to_comment_id=reply_to_comment_id)

    def get_comments(self, sorting='popular', order="desc"):
        return self._comment_section.get_comments(sorting=sorting, order=order)


class Course:
    '''
    A course.
    '''
    def __init__(self, course_name, university, subject, validated = False, comment_section = None) -> None:
        self._course_name = course_name # id
        self._university = university
        self._subject = subject
        self._documents = {'Graded Exams' : [], 'Exams' : [], 'Lecture Materials' : [], 'Assignments' : [], 'Other Documents' : []}
        self._validated = validated
        self._db_path = f"/Courses/{self._course_name}/"

        if comment_section:
            self._comment_section = comment_section
        
        else:
            self._comment_section = CommentSection(parent_path=f"{self._db_path}/Course Content/comment_section")


    def get_comments(self, sorting="popular", order="desc", amount: int = 10, page: int = 1):
        """
        Returns list of comments on page :page:, if there is :amount: comments per page.

        :sorting: "popular", "new"
        :order: "desc" (descending), "asc" (ascending)
        :amount: int
        :page: int (1 is the first page)
        """

        return self._comment_section.get_comments(sorting=sorting, order=order, amount=amount, page=page)

    def get_replies(self, comment_id, sorting="popular", order="desc", amount: int = 10, page: int = 1):
        return self._comment_section.get_replies(comment_id=comment_id)

    def approve_course(self):
        '''
        Approves the course by changing _validated to True.
        '''
        self._validated = True

    def get_course_name(self) -> str:
        '''
        Returns the course name.
        '''
        return self._course_name

    def add_document(self, document_type, document_id):
        '''
        Adds a document id to the _documents dict.
        '''
        try:
            self._documents[document_type].append(document_id)
        except:
            print('Could not add document.')

    def add_comment(self, user_id, text):
        '''
        Adds a comment to the course.

        Updates the course object as well as firebase database.
        '''
        
        #try:
        #self._db_path = f"/Courses/{self._course_name}/comment_section/comments"
            #FirebaseDatabase().push_to_path(path=path, data=data)
        self._comment_section.add_comment(user_id=user_id, text=text)
        #except:
        #    print(f"Course: Failed to add comment to {self._course_name}")

    def add_reply(self, user_id, reply_to_comment_id, text):
        '''
        Adds a comment to the course.

        Updates the course object as well as firebase database.
        '''
        
        try:
            self._db_path = f"/Courses/{self._course_name}/comment_section/comments"
            #FirebaseDatabase().push_to_path(path=path, data=data)
            self._comment_section.add_reply(user_id=user_id, text=text, reply_to_comment_id=reply_to_comment_id)
        except:
            print(f"Failed to add reply to {self._course_name}")

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

    def add_comment_vote(self, comment_id, user_id, upvote):
        try:
            data = self._comment_section.add_comment_vote(comment_id=comment_id, user_id=user_id, upvote=upvote)
            path = f"{self._db_path}/Course Content/comment_section/comments/{comment_id}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Course: Failed to add vote to comment: {comment_id}")

    def add_reply_vote(self, comment_id, reply_id, user_id, upvote):
        try:
            data = self._comment_section.add_reply_vote(comment_id=comment_id, reply_id=reply_id, user_id=user_id, upvote=upvote)
            path = f"{self._db_path}/Course Content/comment_section/replies/{comment_id}/{reply_id}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Course: Failed to add vote to reply: {reply_id}, on comment: {comment_id}")


    def to_json(self):
        json = {
            self._course_name:{
                "Documents":{
                    "Graded Exams":(self._documents["Graded Exams"]),
                    "Exams":(self._documents["Exams"]),
                    "Lecture Materials":(self._documents["Lecture Materials"]),
                    "Assignments":(self._documents["Assignments"]),
                    "Other Documents":(self._documents["Other Documents"])
                },

                "Course Content":{
                    "course_name":self._course_name,
                    "university":self._university,
                    "subject":self._subject,
                    "validated":self._validated,
                    "comment_section":self._comment_section.to_json()
                }
            }
        }
        
        return json

class User:
    def __init__(self, user_id, username, role = "student", sign_up_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), documents: list = []) -> None:
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
                "username":self._username,
                "creation_date":self._sign_up_timestamp,
                "documents":self._documents,
                "role":self._role
        }

        return json

    def add_document_link(self, document_id):
        self._documents.append(document_id)

    def get_documents(self):
        '''
        Returns a list of ids for all documents uploaded by the user.
        '''
        return self._documents

class Moderator(User):
    def __init__(self, user_id, username) -> None:
        super().__init__(user_id, username)

class Student(User):
    def __init__(self, user_id, username) -> None:
        super().__init__(user_id, username)

class CourseDirectory(Directory):
    '''
    A directory containing courses.
    '''

    _pending_courses = {}
    _courses = {}


    def add_course(self, course: Course, add_to_firebase = True):
        '''
        Takes a course object and adds it to the course dictionary.
        '''
        if "/" in course.get_course_name():
            print(f"Failed to add course. The course, {course.course_name}, containts invalid characters.")
            return "Failed to add course, course contains invalid characters"

        if not self.course_exists(course_name=course._course_name):
            self._courses.update({course._course_name : course})
            
            if add_to_firebase:
                path = f"/Universities/{course.get_university()}/{course.get_subject()}"
                data = {
                    course.get_course_name():False
                }
                FirebaseManager().add_course(course=course)
                FirebaseDatabase().push_to_path(path=path, data=data)
        else:
            print(f"Failed to add course. The course, {course.get_course_name()}, already exists.")

    def add_comment(self, course_name, user_id, text):
        if course_name in list(self._courses.keys()):
            #try:
                course = self.get_course(course_name=course_name)
                course.add_comment(user_id=user_id, text=text)
            #except:
             #   print(f"CourseDirectory: Failed to add comment to {course_name}")
        elif course_name in list(self._pending_courses.keys()):
            print(f"'{course_name}' is awaiting validation. The course must be validated before adding comments to the course.")
        else:
            print(f"'{course_name}' does not exist.")
    
    def add_reply(self, course_name, user_id, reply_to_comment_id, text):
        if course_name in list(self._courses.keys()):
            try:
                course = self.get_course(course_name=course_name)
                course.add_reply(user_id=user_id, text=text, reply_to_comment_id=reply_to_comment_id)
            except:
                print(f"CourseDirectory: Failed to add reply to {course_name}")
        elif course_name in list(self._pending_courses.keys()):
            print(f"'{course_name}' is awaiting validation. The course must be validated before adding comments to the course.")
        else:
            print(f"'{course_name}' does not exist.")

    def add_comment_vote(self, course_name, comment_id, user_id, upvote):
        try:
            course = self._courses[course_name]
            course.add_comment_vote(comment_id=comment_id, user_id=user_id, upvote=upvote)
        except:
            print(f"CourseDirectory: Failed to add vote to comment: {comment_id}")

    def add_reply_vote(self, course_name, comment_id, reply_id, user_id, upvote):
        try:
            course = self._courses[course_name]
            course.add_reply_vote(comment_id=comment_id, reply_id=reply_id, user_id=user_id, upvote=upvote)
        except:
            print(f"CourseDirectory: Failed to add vote to comment: {comment_id}")


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

    def get_course(self, course_name) -> Course:
        '''
        Returns the course object for a certain course name.
        '''
        
        if self.course_exists(course_name=course_name):
            return self._courses[course_name]

        try:
            return self._courses[course_name]
        except KeyError:
            raise ValueError(f'Could not get course for: {course_name}')
    

    def get_course_comments(self, course_name, sorting="popular", order="desc", amount: int = 10, page: int = 1):
        """
        Returns list of comments on page :page:, if there is :amount: comments per page.

        :sorting: "popular", "new"
        :order: "desc" (descending), "asc" (ascending)
        :amount: int
        :page: int (1 is the first page)
        """

        if course_name in list(self._courses):
            course = self._courses[course_name]
        else:
            print(f"CourseDirectory: Could not find {course_name}.")
            return
        
        comments = course.get_comments(sorting=sorting, order=order, amount=amount, page=page)

        return comments

    def course_exists(self, course_name: str) -> bool:
        """
        Takes a string and returns a bool wether if course_name is in the courses dict.

        Only counts courses in _courses list.
        """
        course_names = self.get_courses()

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

    def get_username(self, user_id):
        try:
            return self._users[user_id].get_username()
        except:
            return "removed user"

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

    def add(self, document:Document, add_to_firebase = True):
        if not self.document_exists(document.get_id()):
            self._documents[document.get_id()] = document

            if add_to_firebase:
                user_id = document.get_author()
                course_name = document.get_course_name()
                FirebaseManager().add_document(document=document, user_id=user_id, course_name=course_name)

        else:
            print("Document already exists.")

    def get(self, document_id) -> Document:
        return self._documents[document_id] if self.document_exists(document_id) else None

    def document_exists(self, document_id: str) -> bool:
        return True if document_id in self._documents.keys() else False
    
    def get_waiting_documents(self):
        '''
        Returns a list of document ids awaiting validation.
        '''
        waiting_documents = []
        for document in self._documents:
            if document.get_validation():
                document_id = document.get_id()
                waiting_documents.append(document_id)

        return waiting_documents
    
    def get_reported_documents(self):
        '''
        Returns a list of all document ids that are reported.
        '''
        reported_documents = []
        for document in self._documents:
            if document.get_report_status():
                document_id = document.get_id()
                reported_documents.append(document_id)

        return reported_documents

class SearchController:

    def __init__(self) -> None:
        self._course_dict = {
            "Universities":FirebaseDatabase().get_from_path(path="Universities")
        }

    def print_course_dict(self):
        print(self._course_dict)

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

class Main:
    _main = None
    _firebase_manager = FirebaseManager()
    _course_dir = CourseDirectory()
    _user_dir = UserDirectory()
    _document_dir = DocumentDirectory()

    def __new__(cls):
        if cls._main == None:
            cls._main = super(Main, cls).__new__(cls)
            cls._set_from_firebase(cls)

        return cls._main

    def add_user(self, user_id, username):
        user = User(user_id=user_id, username=username)
        self._user_dir.add(user=user)

    def add_course_comment(self, course_name, user_id, text):
        try:
            course = self._course_dir.get_course(course_name=course_name)
            course.add_comment(user_id=user_id, text=text)
        except:
            print(f"Failed to add comment to course")

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

    def add_document_comment_vote(self, document_id: str, user_id: str, comment_id: str, upvote: bool):
        try:
            document = self._document_dir.get(document_id=document_id)
            comment = document.get_comment(comment_id=comment_id)
            comment.add_vote(user_id=user_id, upvote=upvote)
            document_comment_section_json = document.get_comment_section_json()

            # update to firebase database
            self._firebase_manager.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)
        except:
            print(f"Failed to add vote to comment: {comment_id}")

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
    
    def get_course(self, course_name: str) -> Course:
        return self._course_dir.get(course_name=course_name)

    def add_document(self, pdf_url, document_type, 
                 user_id, university, course_name, subject,
                 write_date, grade = "ungraded",
                 validated = False, vote_directory = None, 
                 comment_section = None, document_id = uuid.uuid4().hex,
                 timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")):
        
        document = Document(pdf_url=pdf_url, document_type=document_type, 
                 user_id=user_id, university=university, course_name=course_name, 
                 subject=subject, write_date=write_date, grade=grade)
        
        if not self._course_dir.course_exists(course_name=course_name):
            print("Course does not exist, please create the course before (for now?)")
        
        else:
            # add to document dir and firebase
            course = self._course_dir.get(course_name=course_name)
            self._document_dir.add(document=document)

            # add reference in course
            course.add_document(document_id=document_id, document_type=document_type)

            # add reference in user
            user = self._user_dir.get(user_id=user_id)
            user.add_document_link(document_id=document_id)

    def add_course(self, course_name: str, university: str, subject: str) -> bool:
        """
        Adds a course to the Course Directory.
        """

        course = Course(course_name=course_name,
                        university=university,
                        subject=subject
        )

        self._course_dir.add_course(course=course)

    def add_document_comment(self, user_id, document_id, text):
        try:
            document = self._document_dir.get(document_id=document_id)
            document.add_comment(user_id=user_id, text=text)
            document_comment_section_json = document.get_comment_section_json()
            self._firebase_manager.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)
        except:
            print(f"Failed to add comment to document {document_id}")

    def add_document_comment_reply(self, user_id, document_id, reply_to_comment_id, text):
        try:
            document = self._document_dir.get(document_id=document_id)
            document.add_comment_reply(user_id=user_id, text=text, reply_to_comment_id=reply_to_comment_id)
            document_comment_section_json = document.get_comment_section_json()
            self._firebase_manager.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)
        except:
            print(f"Failed to add comment reply to document {document_id}")

    def _set_user_directory_from_firebase(self):
        users = self._firebase_manager.get_all_users()
        
        for user in users:
            self._user_dir.add(user)

    def _set_course_directory_from_firebase(self):
        courses = self._firebase_manager.get_all_courses()
        
        for course in courses:
            self._course_dir.add_course(course, add_to_firebase=False)

    def _set_documents_from_firebase(self):
        documents = self._firebase_manager.get_all_documents()

        for document in documents:
            self._document_dir.add(document=document, add_to_firebase=False)

    def _set_from_firebase(self):
        self._set_documents_from_firebase(self)
        try:
            print("FirebaseRealtimeDatabase sync initiated")
            self._set_user_directory_from_firebase(self)
            self._set_course_directory_from_firebase(self)
            
            print("FirebaseRealtimeDatabase sync completed")
        except:
            print("Error: FirebaseRealtimeDatabase sync failed")
        
        
        
    def to_json(self, type: str, id: str):
        '''
        Takes a type of page and converts it to json.
        '''
        if type == 'document':
            document = self.get_document(id)
            json = document.to_json()
            return json

        elif type == 'course':
            course = self.get_course(id)
            json = course.to_json()
            return json
        
        elif type == 'user':
            user = self.get_user(id)
            json = user.to_json()
            return json
        
        elif type == 'document_comments':
            document = self.get_document(document_id=id)
            json = document.get_comments()
            return json

        else:
            return 'Failed to get course/document json.'
        
    def get_user(self, user_id):
        '''
        Calls on the user directory to return a certain user object.
        '''
        return self._user_dir.get(user_id)
    
    def get_user_documents(self, user_id):
        '''
        Calls on the relevant user object to return a list of the documents
        uploaded by the user.
        '''
        user = self._user_dir.get(user_id)
        document_ids = user.get_documents()

        documents = []

        for document_id in document_ids:
            document = self._document_dir.get(document_id)

            documents.append({
                    document_id:{
                        "header":f"{document.get_course_name()} - {document.get_header()}",
                        "validated":document.get_validation()
                    }
                })

        return documents
    
    def get_waiting_documents(self):
        '''
        Calls on the doc directory to return a list of documents
        that are awaiting validation.
        '''
        return self._document_dir.get_waiting_documents()
    
    def get_reported_documents(self):
        '''
        Calls on the doc direcotory to return a list of documents
        that are reported.
        '''
        return self._document_dir.get_reported_documents()
    
    def validate_document(self, document_id):
        '''
        Validate a document with a certain document id.
        '''
        document = self._document_dir.get(document_id)
        document.validate_document()

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

def test_course_search(search_controller):

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
    search_results = search_controller.search('', 'Blekinge Institute of Technology', 'Mathematics')

    if search_results:
        for result in search_results:
            print(result.get_course_name())
    else:
        print('No search results.')

#test_course_search()

# add document reports



main = Main()
#course = Course(course_name="IY1422 Finansiell ekonomi", university="Blekinge Institute of Technology", subject="Economics")
#main._course_dir.add_course(course)
#main._course_dir.add_comment("IY1422 Finansiell ekonomi", "GrG6hgFUKHbQtNxKpSpGM6Sw84n2", "I don't like this course")
#main._course_dir.add_comment("IY1422 Finansiell ekonomi", "GrG6hgFUKHbQtNxKpSpGM6Sw84n2", "third")
#comments = main._course_dir.get_course("IY1422 Finansiell ekonomi").get_comments(sorting="new", order="desc")
#for comment in comments:
#    print(comments[comment]._text)




#print(main.get_user_documents("GrG6hgFUKHbQtNxKpSpGM6Sw84n2"))
#print(main._course_dir.get_course("IY1422 Finansiell ekonomi").get_comments())
#print(main._course_dir.get_course("IY1422 Finansiell ekonomi").get_comments())
#print(main._course_dir.get_course("IY1422 Finansiell ekonomi").get_replies("7ad10a9b14c04f84817ac0579520f3a1"))
#main._course_dir.add_reply("IY1422 Finansiell ekonomi", "GrG6hgFUKHbQtNxKpSpGM6Sw84n2", "7ad10a9b14c04f84817ac0579520f3a1", "sure")
#main._course_dir.add_reply_vote(course_name="IY1422 Finansiell ekonomi", comment_id="7ad10a9b14c04f84817ac0579520f3a1", reply_id="5a56134e13b749d9a69cda7cda64b05e", user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2", upvote=True)



#main._course_dir.add_comment_vote(course_name="IY1422 Finansiell ekonomi", comment_id="cb83822fea1243539687d70f264038f6", user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2", upvote=True)
#main._course_dir.add_comment_vote(course_name="IY1422 Finansiell ekonomi", comment_id="cb83822fea1243539687d70f264038f6", user_id="6dZ517M5qoSdg740CJ2ThtzlJMx2", upvote=True)
#main._course_dir.add_comment_vote(course_name="IY1422 Finansiell ekonomi", comment_id="cb83822fea1243539687d70f264038f6", user_id="HufctBjyzkSdSOpm94q4Pk71OBX2", upvote=False)
#main._course_dir.add_comment_vote(course_name="IY1422 Finansiell ekonomi", comment_id="cb83822fea1243539687d70f264038f6", user_id="uvkNLsaTVDR9yg8JuTikKUkZv9y1", upvote=False)
#main._course_dir.add_reply_vote(course_name="IY1422 Finansiell ekonomi", comment_id="1afcfdab49b64af191a72647305d0739", user_id="GrG6hgFUKHbQtNxKpSpGM6Sw84n2", upvote=True)

#course = Course(course_name="PA2576 Programvaruintensiv produktutveckling", university="Blekinge Institute of Technology", subject="Software Development")
#main._course_dir.add_course(course)


#main._document_dir.get("37d779249c2f4086986514c2dc4b7330").add_comment_vote("GrG6hgFUKHbQtNxKpSpGM6Sw84n2", True)

# does not load comments rn
#main._document_dir.get("37d779249c2f4086986514c2dc4b7330").add_comment_vote("GrG6hgFUKHbQtNxKpSpGM6Sw84n2", "0a5823bde9a944cb9f0f5ed3ff109f3d", True)

def test_comment_sorting():
    vote_dir1 = VoteDirectory('id', {'upvotes' : 17, 'downvotes' : 3})
    vote_dir2 = VoteDirectory('id', {'upvotes' : 50, 'downvotes' : 10})
    vote_dir3 = VoteDirectory('id', {'upvotes' : 30, 'downvotes' : 20})
    vote_dir4 = VoteDirectory('id', {'upvotes' : 40, 'downvotes' : 10})
    vote_dir5 = VoteDirectory('id', {'upvotes' : 100, 'downvotes' : 0})
    comment1 = Comment(1, 'Första kommentaren', None, comment_id='id1', timestamp = '2024-04-18 15:30:00.000000', vote_dir=vote_dir1)
    comment2 = Comment(1, 'Vad säger du??', None, comment_id='id2', timestamp = '2024-04-18 16:30:00.000000', vote_dir=vote_dir5)
    comment3 = Comment(1, 'Nee va?', None, comment_id='id3', timestamp = '2024-04-18 14:30:00.000000', vote_dir=vote_dir2)
    comment4 = Comment(1, 'Bra dokument tyckte jag iallafall.', None, comment_id='id4', timestamp = '2024-04-18 20:30:00.000000', vote_dir=vote_dir4)
    comment5 = Comment(1, 'Cool hemsida', None, comment_id='id5', timestamp = '2024-04-18 18:30:00.000000', vote_dir=vote_dir3)

    comment_section = CommentSection(None, comment_section_id='id', comments = {

    1:{
        'id1':comment1,
        'id2':comment2,
        'id3':comment3,
        'id4':comment4,
        'id5':comment5,
    }
    }, 
    replies = {})

    comments = comment_section.get_comments('new', 'asc', 10, 1)

    for comment in comments.values():
        print(comment._text)