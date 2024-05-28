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
        """
        Sets up connection to firebase storage.
        """
        pass

class FirebaseStorage(Firebase):
    """
    Connection to Firebase Realtime Database.
    """
    _firebase_cert = None
    _app = None
    _storage_url = None

    def __new__(cls):
        return super().__new__(cls)
    
    def _initialize_firebase(self):
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
    
    def generate_download_url(self, document_id: int):
        """Generate a download URL for a document."""
        storage_path = f"PDF/{document_id}.pdf"
        bucket = storage.bucket(app=self.app)
        blob = bucket.blob(storage_path)
        download_url = blob.generate_signed_url(datetime.timedelta(seconds=300), method="GET") # URL expires in 5 minutes
        return download_url

class FirebaseDatabase(Firebase):
    """
    Connection to Firebase Realtime Database.
    """
    _app = None
    _firebase_cert = None
    _firebase_url = None

    def __new__(cls):
        return super().__new__(cls)

    def push_to_path(self, path, data):
        """
        Push json data to a path in Firebase Realtime Database.
        """
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
        """
        Updates the comment section of a document in Firebase.
        """
        try:
            ref = db.reference(f"/Documents/{document_id}/comment_section", self._app)
            ref.update(document_comment_section_json)
            
        except:
            ref = db.reference(f"/Documents/{document_id}/", self._app)
            ref.update({"comment_section":document_comment_section_json})

    def update_course_comment_section(self, course_name: str, comment_section: str):
        """
        Updates the comment section of a course in Firebase.
        """
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
                    #documents.remove(None)
                except:
                    documents = []

                user = User(user_id=user_id, 
                            username=users_dict[user_id]["username"],
                            documents=documents,
                            role=users_dict[user_id]["role"], 
                            sign_up_timestamp=datetime.strptime(users_dict[user_id]["creation_date"], "%Y-%m-%d %H:%M:%S.%f"),
                            score=users_dict[user_id]["score"])
                
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
                
                if "Documents" in list(courses_dict[course_name].keys()):
                    for document_type in courses_dict[course_name]["Documents"].keys():
                        document_ids = courses_dict[course_name]["Documents"][document_type].keys()
                        for document_id in document_ids:
                            document_name = courses_dict[course_name]["Documents"][document_type][document_id]
                            course.add_document(document_id=document_id, document_type=document_type, document_name=document_name, add_to_firebase = False)

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
                dict_keys = list(document_dict.keys())
                
                # Vote Directory
                try:
                    vote_directory = VoteDirectory(vote_directory_id=document_dict["vote_directory"]["vote_directory_id"],
                                                   votes=document_dict["vote_directory"]["votes"])
                except:
                    vote_directory = VoteDirectory(vote_directory_id=document_dict["vote_directory"]["vote_directory_id"])

                # Comment Section
                comment_section = None

                if "comment_section" in dict_keys:

                    #comment_section_id = current_course["comment_section"]["comment_section_id"]
                    parent_path = f"Documents/{document_id}/comment_section"
                    comment_section = self._load_comment_section(comment_section_json=document_dict["comment_section"],
                                                                 parent_path=parent_path)
                
                if "reports" in document_dict["categorization"]:
                    reports = {}
                    reports_ids = list(document_dict["categorization"]["reports"].keys())
                    for report_id in reports_ids:
                        report = Report(document_id=document_id,
                                        user_id=document_dict["categorization"]["reports"][report_id]["user_id"],
                                        reason=document_dict["categorization"]["reports"][report_id]["reason"],
                                        text=document_dict["categorization"]["reports"][report_id]["text"],
                                        report_id=report_id)
                        reports[report_id] = report
                else:
                    reports = {}

                try:
                    grade_system = document_dict["categorization"]["grade_system"]
                except:
                    grade_system = None

                document = Document(document_id=document_id,
                                    pdf_url=document_dict["content"]["pdf_url"],
                                    user_id=document_dict["content"]["user_id"],
                                    write_date=document_dict["content"]["write_date"],
                                    upload_comment=document_dict["content"]["upload_comment"],

                                    grade=document_dict["categorization"]["grade"],
                                    grade_system=grade_system,
                                    validated=document_dict["categorization"]["validated"],
                                    university=document_dict["categorization"]["university"],
                                    document_type=document_dict["categorization"]["document_type"],
                                    course_name=document_dict["categorization"]["course_name"],
                                    subject=document_dict["categorization"]["subject"],
                                    submitted_anonymously=document_dict["categorization"]["submitted_anonymously"],

                                    vote_directory=vote_directory,
                                    comment_section=comment_section,

                                    reports=reports,
                                    reported=document_dict["categorization"]["reported"],

                                    timestamp=datetime.strptime(document_dict["timestamp"], "%Y-%m-%d %H:%M:%S.%f"))
                
                documents.append(document)

        return documents

class FirebaseManager:
    """
    Manages connections to Firebase Storage and Realtime Database. 
    """
    _firebase_manager = None
    _storage = FirebaseStorage()
    _database = FirebaseDatabase()

    def __new__(cls):
        # Make sure there is only one instance of FirebseManager
        if cls._firebase_manager == None:
            # Sync with firebase
            cls._firebase_manager = super(FirebaseManager, cls).__new__(cls)
        
        return cls._firebase_manager

    def push_to_path(self, path, data):
        """
        Push json data to a path in Firebase Realtime Database.
        """
        self._database.push_to_path(path=path, data=data)

    def get_from_database_path(self, path):
        """
        Get json data from a path in Firebase Realtime Database.

        Returns None if no data exists in the path.
        """
        data = self._database.get_from_path(path)

        return data if data else None

    def _set_from_firebase(self):
        """
        Sync current instance of data with Firebase Realtime Database.
        """
        users = {}
        db_users = self._database.get_users()

        for user in db_users:
            self._user_dir.add(users[user])
        
    def get_all_courses(self) -> list:
        """
        Returns a list of all courses from the Firebase database.
        """
        return self._database.get_courses()

    def get_all_documents(self) -> list:
        """
        Returns a list of all documents from the Firebase Database.
        """
        return self._database.get_documents()

    def get_all_users(self) -> list:
        """
        Returns a list of all users from the Firebase Database.
        """
        return self._database.get_users()

    def add_document(self, document, user_id: str, course_name:str):
        """
        Adds a document to the Firebase database.
        """
        self._database.add_document(document=document, user_id=user_id, course_name=course_name)
    
    def update_document_votes(self, document_id, vote_directory_json):
        """
        Updates a document's vote directory in the database.
        """
        self._database.update_document_votes(document_id=document_id, vote_directory_json=vote_directory_json)

    def update_document_comment_sectino_votes(self, document_id, document_comment_section_json):
        """
        Updates the comment section of a document in Firebase.
        """
        self._database.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)

    def update_document_comment_section(self, document_id, document_comment_section_json):
        """
        Updates the comment section of a document in Firebase.
        """
        self._database.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)

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
        """
        Adds a course to the database.
        """
        self._database.add_course(course=course)


class Report:
    """
    A Report contains the information about a document report.
    """
    def __init__(self, document_id, user_id, reason, text, report_id = None) -> None:
        self._document_id = document_id
        self._user_id = user_id
        self._reason = reason
        self._text = text
        if report_id == None:
            self._report_id = uuid.uuid4().hex
        else:
            self._report_id = report_id
    
    def get_report(self):
        """
        Returns a dict with keys Reason and Text to display the report.
        """

        report = {}
        report["reason"] = self._reason
        
        if len(self._text.replace(" ", "")) < 1:
            report["text"] = f"{self._reason}: User {Main()._user_dir.get_username(self._user_id)} wrote 'No Additional Comment'"
        else:
            report["text"] = f"{self._reason}: User {Main()._user_dir.get_username(self._user_id)} wrote '{self._text}'"

        return report

    def get_id(self):
        return self._report_id

    def to_json(self):
        json = {
            "document_id":self._document_id,
            "user_id":self._user_id,
            "reason":self._reason,
            "text":self._text
        }

        return json

class Directory:

    def add(self):
        """
        Add an object to the Directory.
        """
        pass

    def get(self):
        """
        Return object from the directory.
        """
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
        
    def current_vote(self, user_id):
        """
        Returns a string with the current user vote status.
        
        Can be:
        'novote'
        'upvote'
        'downvote'
        """

        status = "novote"
        
        if user_id in list(self._votes.keys()):
            current_vote = self._votes[user_id]
            if current_vote:
                status = "upvote"
            else:
                status = "downvote"
        
        return status
    
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
        """
        Adds a comment to the CommentSection, and syncs it with the Firebase database.
        """
        comment = Comment(user_id=user_id, text=text, parent_path=f"{self._db_path}/comments")
        FirebaseDatabase().push_to_path(comment._db_path, data=comment.to_json())
        self._comments[comment.get_id()] = comment

    def add_reply(self, user_id: str, text: str, reply_to_comment_id: str):
        """
        Adds a reply to the CommentSection, and syncs it with the Firebase database.
        """
        reply = Comment(user_id=user_id, text=text, parent_path=f"{self._db_path}/replies/{reply_to_comment_id}")
        FirebaseDatabase().push_to_path(reply._db_path, data=reply.to_json())
        self._replies[reply.get_id()] = reply

    def get_comment(self, page, comment_id):
        """
        Returns a comment from the CommentSection.
        """
        if comment_id in list(self._comments[page].keys()):
            return self._comments[page][comment_id]
        else:
            replied_to_comment_ids = list(self._replies.keys())
            for replied_to_comment_id in replied_to_comment_ids:
                print(replied_to_comment_id)
                if comment_id in list(self._replies[replied_to_comment_id]):
                    return self._replies[replied_to_comment_id][comment_id]
        
        print("404: Comment not found error")
    
    def delete_comment(self, comment_id):
        """
        Removes a comment from the CommentSection.
        """
        if comment_id in list(self._comments.keys()):
            self._comments.pop(comment_id)
        else:
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

    def add_comment_report(self, comment_id, user_id, reason, text):
        """
        Adds a comment report to the comment in the CommentSection.
        """
        try:
            comment = self._comments[comment_id]
            comment.add_report(user_id, reason, text)
        except IndexError:
            print("404: Comment not found")

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
        """
        Returns if a comment has replies.
        """
        try:
            self._replies[comment_id]
            return True
        except:
            return False

    def get_id(self):
        return self._comment_section_id
    
    def add_comment_vote(self, comment_id, user_id, upvote):
        """
        Adds a vote to a comment.
        """
        try:
            comment = self._comments[comment_id]
            return comment.add_vote(user_id=user_id, upvote=upvote)
        except:
            print(f"CommentSection: Failed to add vote to comment: {comment_id}")

    def add_reply_vote(self, comment_id, reply_id, user_id, upvote):
        """
        Adds a vote to a reply.
        """
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

class Comment:
    def __init__(self, user_id, text, parent_path, comment_id = None, timestamp = datetime.now(), vote_dir = None):
        self._user_id = user_id
        
        if comment_id == None:
            self._comment_id = uuid.uuid4().hex
        else:
            self._comment_id = comment_id
        
        self._text = text
        self._timestamp = timestamp
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

    def to_display_json(self) -> str:
        json = {
            "username": Main().get_user(user_id=self._user_id).get_username(),
            "text":self._text,
            "timestamp":{
                "time":self._timestamp.strftime("%H:%M"),
                "date":self._timestamp.strftime("%Y-%m-%d")
            },
            "votes":self._vote_dir.get()
        }
        return json

    def get_timestamp(self):
        """
        Returns the timestamp of the Comment.
        """
        return self._timestamp

    def to_json(self):
        """
        Returns a json string
        """

        json = {
            "comment_id":self._comment_id,
            "user_id": self._user_id,
            "text":self._text,
            "timestamp":self._timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "vote_directory":self._vote_dir.to_json(),
            "parent_path":self._db_path.replace(f"/{self._comment_id}", "")
        }

        return json

    def add_vote(self, user_id, upvote):
        """
        Adds a vote to the comment.
        """
        return self._vote_dir.add(user_id=user_id, upvote=upvote)

    def get_votes(self) -> dict:
        """
        Returns a dict with the current votes of the comment.
        """
        return self._vote_dir.get()

    def get_vote_directory_json(self):
        """
        Returns the VoteDirectory as a json.
        """
        return self._vote_dir.to_json()
    
    def get_id(self):
        return self._comment_id

class Document:
    """
    A document contains the data of a document upload.
    """

    def __init__(self, pdf_url: str, 
                 document_type: str, 
                 user_id: str, 
                 university: str, 
                 course_name: str, 
                 subject: str,
                 write_date: str,
                 upload_comment: str,
                 grade_system = None,
                 grade = None,
                 validated: bool = False,
                 vote_directory: VoteDirectory = None, 
                 comment_section: CommentSection = None, 
                 document_id: str = uuid.uuid4().hex,
                 timestamp = datetime.now(),
                 reported = False,
                 reports = {},
                 submitted_anonymously = False
                 ) -> None:
                
        
        # document content
        self._user_id = user_id
        self._header = f"{document_type} {write_date}"
        self._pdf_url = pdf_url
        self._document_type = document_type
        self._grade = grade
        self._grade_system = grade_system
        self._write_date = write_date

        if len(upload_comment.replace(" ", "")) < 1:
            self._upload_comment = "No Upload Comment"
        else:
            self._upload_comment = upload_comment

        # categorization
        self._submitted_anonymously = submitted_anonymously
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
        self._reports = reports
    
    def get_user_vote_status(self, user_id):
        """
        Returns a string with the current user vote status.
        
        Can be:
        'novote'
        'upvote'
        'downvote'
        """

        return self._vote_directory.current_vote(user_id=user_id)

    def to_display_json(self):
        if self._submitted_anonymously:
            username = "Submitted Anonymously"
        else:
            username = Main().get_user(self._user_id).get_username()

        return {
            "content":{
                "header":self._header,
                "pdf_url":self._pdf_url,
                "username":username,
                "grade":self._grade,
                "write_date":self._write_date,
                "upload_comment":self._upload_comment
            },

            "categorization":{
                "university":self._university,
                "course_name":self._course_name,
                "subject":self._subject,
                "validated":self._validated,
                "document_type":self._document_type,
                "reported":self._reported,
                "grade":self._grade,
                "grade_system":self._grade_system
            },

            "votes":self._vote_directory.get(),

            "timestamp":{
                "time":self._timestamp.strftime("%H:%M"),
                "date":self._timestamp.strftime("%Y-%m-%d")
            }
        }

    def get_type(self):
        """
        Returns the document type.
        """
        return self._document_type

    def get_id(self):
        return self._document_id

    def get_header(self):
        """
        Returns the header of the document.
        """
        return self._header

    def get_validation(self):
        """
        Returns if the document is validated.
        """
        return self._validated

    def to_json(self):
        json = {
            self._document_id:{
                "content":{
                    "header":self._header,
                    "pdf_url":self._pdf_url,
                    "user_id":self._user_id,
                    "write_date":self._write_date,
                    "upload_comment":self._upload_comment
                },

                "categorization":{
                    "university":self._university,
                    "course_name":self._course_name,
                    "subject":self._subject,
                    "validated":self._validated,
                    "document_type":self._document_type,
                    "reports":self._reports,
                    "reported":self._reported,
                    "grade":self._grade,
                    "grade_system":self._grade_system,
                    "submitted_anonymously":self._submitted_anonymously
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
        """
        Returns the CommentSection as a json.
        """
        return self._comment_section.to_json()

    def add_report(self, user_id, reason, text):
        """
        Adds a report to the document and syncs it with firebase.
        """
        report = Report(document_id=self._document_id, user_id=user_id, reason=reason, text=text)
        
        if not self._reported:
            self._reported = True
            FirebaseDatabase().push_to_path(path = f"Documents/{self._document_id}/categorization", data = {"reported":True})
        
        self._reports[report.get_id()] = report
        data = {report.get_id():report.to_json()}
        path = f"Documents/{self._document_id}/categorization/reports"
        FirebaseDatabase().push_to_path(data=data, path=path)

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
        path = f"Documents/{self.get_id()}/categorization"
        data = {"validated":True}
        FirebaseDatabase().push_to_path(path=path, data=data)

    # document votes

    def add_document_vote(self, user_id, upvote):
        """
        Adds a vote to the document.
        """
        try:
            data = self._vote_directory.add(user_id=user_id, upvote=upvote)
            path = f"{self._db_path}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Document: Failed to add vote to document: {self._document_id}")

    def get_vote_directory_json(self):
        """
        Returns the VoteDirectory as a json.
        """

        return self._vote_directory.to_json()
       
    # comment section

    def add_comment(self, user_id, text):
        """
        Adds a comment to the document's CommentSection.
        """
        self._comment_section.add_comment(user_id=user_id, text=text)

    def add_comment_vote(self, user_id, comment_id, upvote):
        """
        Adds a vote to a comment in the document's CommentSection.
        """
        try:
            data = self._comment_section.add_comment_vote(user_id=user_id, comment_id=comment_id, upvote=upvote)
            path = f"{self._db_path}/comment_section/comments/{comment_id}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Document: Failed to add vote to comment: {self._document_id}")

    def get_comment(self, comment_id):
        """
        Returns a comment from the document's CommentSection.
        """
        return self._comment_section.get_comment(comment_id=comment_id)
    
    def add_comment_reply(self, user_id, text, reply_to_comment_id):
        """
        Adds a reply to a document comment.
        """
        self._comment_section.add_reply(user_id=user_id, text=text, reply_to_comment_id=reply_to_comment_id)

    def get_comments(self, sorting='popular', order="desc"):
        """
        Returns the comments of the document.
        """
        return self._comment_section.get_comments(sorting=sorting, order=order)    
    
    def is_anonymous(self):
        '''
        Returns if the document is anonymous.
        '''
        return self._submitted_anonymously

    def get_descriptive_reports(self):
        """
        Returns a string with all reports.
        """
        reports = {}
        if self._reported:
            for report in self._reports:
                reports[report] = self._reports[report].get_report()
        
        return reports
    
    def remove_all_reports(self):
        """
        Removes all reports from the document.
        """
        self._reported = False
        self._reports = {}

    def delete_comment(self, comment_id):
        """
        Deletes a comment from the document's CommentSection.
        """
        self._comment_section.delete_comment(comment_id)

class Course:
    '''
    A course.
    '''
    def __init__(self, course_name, university, subject, validated = False, comment_section = None) -> None:
        self._course_name = course_name # id
        self._university = university
        self._subject = subject
        self._documents = {'Graded Exams' : {}, 'Exams' : {}, 'Lecture Materials' : {}, 'Assignments' : {}, 'Other Documents' : {}}
        self._validated = validated
        self._db_path = f"/Courses/{self._course_name}/"

        if comment_section:
            self._comment_section = comment_section
        
        else:
            self._comment_section = CommentSection(parent_path=f"{self._db_path}/Course Content/comment_section")

    def delete_comment(self, comment_id):
        """
        Detletes a comment from a course page.
        """
        self._comment_section.delete_comment(comment_id)

    def get_documents(self):
        """
        Returns the course's documents.
        """
        return self._documents

    def validate(self):
        """Validates the course, and syncs the validation status with firebase"""
        path = f"Courses/{self._course_name}/Course Content"
        data = {
            "validated":True
        }
        self._validated = True
        FirebaseDatabase().push_to_path(path=path, data=data)
        path = f"Universities/{self._university}/{self._subject}"
        data = {
            self._course_name:True
        }
        FirebaseDatabase().push_to_path(path=path, data=data)

    def get_comments(self, sorting="popular", order="desc"):
        """
        Returns list of comments on page :page:, if there is :amount: comments per page.

        :sorting: "popular", "new"
        :order: "desc" (descending), "asc" (ascending)
        :amount: int
        :page: int (1 is the first page)
        """
        return self._comment_section.get_comments(sorting=sorting, order=order)

    def get_replies(self, comment_id, sorting="popular", order="desc", amount: int = 10, page: int = 1):
        """
        Returns the replies of a comment.
        """
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
    
    def remove_document(self, document_id, document_type):
        """
        Removes a document from the course.
        """
        del self._documents[document_type][document_id]

    def add_document(self, document_type, document_id, document_name, add_to_firebase=True):
        '''
        Adds a document id to the _documents dict.
        '''
        try:
            self._documents[document_type][document_id] = document_name
        except:
            self._documents[document_type] = {}
            self._documents[document_type][document_id] = document_name

        if add_to_firebase:
            path = f"Courses/{self._course_name}/Documents/{document_type}s"
            data = {document_id:document_name}
            FirebaseDatabase().push_to_path(path=path, data=data)


    def add_comment(self, user_id, text):
        '''
        Adds a comment to the course.

        Updates the course object as well as firebase database.
        '''
        
        self._comment_section.add_comment(user_id=user_id, text=text)
        
    def add_reply(self, user_id, reply_to_comment_id, text):
        '''
        Adds a comment to the course.

        Updates the course object as well as firebase database.
        '''
        
        try:
            self._db_path = f"/Courses/{self._course_name}/comment_section/comments"
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

    def add_comment_vote(self, comment_id, user_id, upvote):
        """
        Adds a vote to a comment in the course, and syncs it with firebase.
        """
        try:
            data = self._comment_section.add_comment_vote(comment_id=comment_id, user_id=user_id, upvote=upvote)
            path = f"{self._db_path}/Course Content/comment_section/comments/{comment_id}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Course: Failed to add vote to comment: {comment_id}")

    def add_reply_vote(self, comment_id, reply_id, user_id, upvote):
        """
        Adds a vote to a reply in the course, and syncs it with firebase.
        """
        try:
            data = self._comment_section.add_reply_vote(comment_id=comment_id, reply_id=reply_id, user_id=user_id, upvote=upvote)
            path = f"{self._db_path}/Course Content/comment_section/replies/{comment_id}/{reply_id}/vote_directory/votes"
            FirebaseDatabase().push_to_path(path=path, data=data)
        except:
            print(f"Course: Failed to add vote to reply: {reply_id}, on comment: {comment_id}")

    def to_json(self):
        json = {
            self._course_name:{
                "Documents":self.get_documents(),

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

    def to_display_json(self):
        json = {
            "Documents":self.get_documents(),

            "Content":{
                "course_name":self._course_name,
                "university":self._university,
                "subject":self._subject,
                "validated":self._validated,
                "top_contributors":self.get_top_contributors()
            }
        }

        return json
    
    def is_validated(self):
        '''
        Returns the validation status of the course.
        '''
        return self._validated
    
    def get_top_contributors(self):
        '''
        Returns a list of the usernames of the users that have made
        the most contributions to a course, descending order.
        '''
        contributors = {}
        for document_id in self._get_doc_ids():
            document = Main().get_document(document_id)
            if isinstance(document, Document) and document.is_anonymous() == False:
                author_id = document.get_author()
                user = Main().get_user(author_id)
                username = user.get_username()
                if username not in contributors.keys():
                    contributors.update({username : 10})
                else:
                    contributors[username] += 10
        sorted_contributors = dict(sorted(contributors.items(), key=lambda item: item[1], reverse=True))
        return sorted_contributors
    
    def _get_doc_ids(self):
        '''
        Returns a list of all the document ids in the course.
        '''
        all_ids = []
        for category in self._documents.values():
                if isinstance(category, dict):
                    all_ids.extend(category.keys())
        return all_ids


class User:
    '''
    A user of the system, abstract class for both students and moderators.
    '''
    def __init__(self, user_id, username, role = "student", sign_up_timestamp=datetime.now(), documents: list = [], score = 0) -> None:
        self._id = user_id
        self._username = username
        self._sign_up_timestamp = sign_up_timestamp
        self._documents = documents
        self._role = role
        self._score = score

    def get_score(self):
        '''
        Returns the score for the user.
        '''
        return self._score

    def get_username(self):
        '''
        Returns the username for the user.
        '''
        return self._username
    
    def get_id(self):
        '''
        Returns the user's uid.
        '''
        return self._id
    
    def get_role(self) -> str:
        '''
        Returns the role of the user.
        '''
        return self._role

    def to_json(self) -> str:
        '''
        Returns a json string with information about the user.
        '''
        json = {
                "username":self._username,
                "creation_date":self._sign_up_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "documents":self._documents,
                "role":self._role,
                "score":self._score
        }

        return json

    def to_display_json(self) -> str:
        '''
        Returns a json string with the information that is to be displayed about the user.
        '''
        json = {
                "username":self._username,
                "creation_date":self._sign_up_timestamp.strftime("%Y-%m-%d"),
                "documents":self._documents,
                "role":self._role,
                "score":self._score
        }

        return json
    
    def remove_document(self, document_id):
        '''
        Removes a document from the user.
        '''
        self._documents.remove(document_id)

    def add_document_link(self, document_id):
        '''
        Adds a document to the user.
        '''
        if document_id not in self._documents:
            self._documents.append(document_id)

    def get_documents(self):
        '''
        Returns a list of ids for all documents uploaded by the user.
        '''
        return self._documents
    
    def change_user_score(self, change):
        '''
        Changes the user score by the specified number.
        '''
        if isinstance(change, int):
            self._score += change
            current_score = self._score
            FirebaseDatabase().push_to_path(path=f"Users/{self._id}", 
                                            data={"score":current_score})
        else:
            return 'Change must be an integer.'

class Moderator(User):
    '''
    A moderator user.
    '''
    def __init__(self, user_id, username) -> None:
        super().__init__(user_id, username)

class Student(User):
    '''
    A student user.
    '''
    def __init__(self, user_id, username) -> None:
        super().__init__(user_id, username)

class CourseDirectory(Directory):
    '''
    A directory containing courses.
    '''

    _pending_courses = {}
    _courses = {}

    def validate_course(self, course_name, approve):
        """Change the validation status of a course. If 'validate' is set to False, the course is deleted."""

        if approve:
            course = self.get_course(course_name=course_name)
            course.validate()
        else:
            self.delete_course(course_name)

    def delete_course(self, course_name):
        """
        Deletes a course from the CourseDirectory and removes it from firebase.
        """

        if course_name in self._courses:
            self._courses.pop(course_name)
            # firebase
            path = f"/Courses"
            FirebaseManager().push_to_path(path=path, data={course_name:None})
        else:
            return "Failed to delete course: 404 Course not found."

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
        '''
        Adds a comment to a course.
        '''
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
        '''
        Adds a reply to a comment.
        '''
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
        '''
        Adds a vote to a comment.
        '''
        try:
            course = self._courses[course_name]
            course.add_comment_vote(comment_id=comment_id, user_id=user_id, upvote=upvote)
        except:
            print(f"CourseDirectory: Failed to add vote to comment: {comment_id}")

    def add_reply_vote(self, course_name, comment_id, reply_id, user_id, upvote):
        '''
        Adds a vote to a reply comment.
        '''
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
    
    def get_waiting_courses(self):
        '''
        Returns a list of course names awaiting validation.
        '''
        waiting_courses = []
        for course_name in self._courses:
            course = Main().get_course(course_name)
            if course.is_validated() == False:
                waiting_courses.append(course_name)
        return waiting_courses

class UserDirectory(Directory):
    '''
    A user directory.
    '''
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
        '''
        Returns the username for a user id.
        '''
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
    '''
    A document directory.
    '''
    
    _documents = {}

    def add(self, document:Document, add_to_firebase = True):
        '''
        Adds a document to the document directory and firebase.
        '''
        if not self.document_exists(document.get_id()):
            self._documents[document.get_id()] = document

            if add_to_firebase:
                user_id = document.get_author()
                course_name = document.get_course_name()
                FirebaseManager().add_document(document=document, user_id=user_id, course_name=course_name)

        else:
            print("Document already exists.")

    def get(self, document_id) -> Document:
        '''
        Returns the document object for a document id.
        '''
        return self._documents[document_id] if self.document_exists(document_id) else None

    def remove(self, document_id):
        '''
        Removes a document from the document directory.
        '''
        self._documents.pop(document_id)

    def document_exists(self, document_id: str) -> bool:
        '''
        Checks if a document exists in the document directory.
        '''
        return True if document_id in self._documents.keys() else False
    
    def get_waiting_documents(self):
        '''
        Returns a list of document ids awaiting validation.
        '''
        waiting_documents = []
        for document_id in self._documents:
            if not self._documents[document_id].get_validation():
                waiting_documents.append(document_id)

        return waiting_documents
    
    def get_reported_documents(self):
        '''
        Returns a list of all document ids that are reported.
        '''
        reported_documents = {}
        for document_id in self._documents:
            document = self._documents[document_id]

            if self._documents[document_id].get_report_status():
                report_str = document.get_descriptive_reports()
                reported_documents[document_id] = report_str

        return reported_documents

class SearchController:
    '''
    Uses the course directory to search its courses.
    '''

    def __init__(self) -> None:
        self._course_dict = {
            "Universities":FirebaseDatabase().get_from_path(path="Universities")
        }

    def search(self, query, course_directory: CourseDirectory, university=None, subject=None, course=None):
        '''
        Search function to search for courses.
        
        Parameters:
        - query: Search keyword provided by the user. Can be empty, meaning no keyword search.
        - university: Selected university.
        - subject: Selected subject.
        - course: Selected course.

        Returns a list of matching courses based on the search criteria.
        '''
        filtered_courses = []
        all_courses = course_directory.get_courses().values()

        if university and subject and course:
            for c in all_courses:
                course_university = c.get_university()
                course_subject = c.get_subject()
                course_name = c.get_course_name()
                if course_university == university and course_subject == subject and course_name == course:
                    if c.is_validated():
                        filtered_courses.append(c)
                        break

        elif university and subject and not course:
            for c in all_courses:
                course_university = c.get_university()
                course_subject = c.get_subject()
                if course_university == university and course_subject == subject:
                    if c.is_validated():
                        filtered_courses.append(c)

        elif university and not subject and not course:
            for c in all_courses:
                course_university = c.get_university()
                if course_university == university:
                    if c.is_validated():
                        filtered_courses.append(c)

        elif not university and subject and not course:
            for c in all_courses:
                course_subject = c.get_subject()
                if course_subject == subject:
                    if c.is_validated():
                        filtered_courses.append(c)

        elif not university and not subject and not course:
            for c in all_courses:
                if c.is_validated():
                    filtered_courses.append(c)

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
                    matching_courses.append(course_name)
        else:
            matching_courses = [course.get_course_name() for course in filtered_courses]

        return matching_courses

    def get_courses_from_subject_at_university(self, university, subject):
        '''
        Returns a list of all courses from a specific subject at a specific university.
        '''

        subject_courses = list(self._course_dict['Universities'][university][subject])
        #print(subject_courses)

        return subject_courses
    
    def get_all_subjects_from_university(self, university):
        '''
        Returns a list of all subjects for a certain university.
        '''
        try:
            university_subjects = list(self._course_dict['Universities'][university])
        except KeyError:
            university_subjects = []
        return university_subjects
    
    def get_subject_universities(self, subject):
        '''
        Returns a list of all universities for a certain subject.
        '''
        subject_universities = []
        universities = list(self._course_dict['Universities'])
        #print(universities)
        for u in universities:
            university_subjects = self.get_all_subjects_from_university(u)
            for s in university_subjects:
                if s == subject:
                    subject_universities.append(u)
        #print(subject_universities)
        return subject_universities

class Main:
    '''
    The Main class is a controller for all parts of the system.
    '''
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

    def get_user_like_status_on_document(self, user_id, document_id):
        '''
        Returns whether or not the user has already voted on a document.
        '''
        document = self._document_dir.get(document_id=document_id)
        vote_status = document.get_user_vote_status(user_id=user_id)

        return vote_status

    def validate_course(self, course_name, approve):
        '''
        Changes a course's status to validated by calling on the course directory.
        '''
        self._course_dir.validate_course(course_name=course_name, approve=approve)

    def add_user(self, user_id, username):
        '''
        Adds a user to the user directory and Firebase storage.
        '''
        user = User(user_id=user_id, username=username)
        self._user_dir.add(user=user)
        user_id = user.get_id()
        data = {user_id: user.to_json()}
        path = "Users"
        FirebaseDatabase().push_to_path(path=path, data=data)

    def add_course_comment(self, course_name, user_id, text):
        '''
        Adds a course comment.
        '''
        try:
            course = self._course_dir.get_course(course_name=course_name)
            course.add_comment(user_id=user_id, text=text)
        except:
            print(f"Failed to add comment to course")

    def add_document_vote(self, document_id: str, user_id: str, upvote: bool):
        '''
        Adds a vote to a document.
        '''
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
        '''
        Adds a vote to a document comment.
        '''
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
        '''
        Calls on the search controller to search using specific parameters.
        '''
        return self._search_controller.search(query=query, course_directory=self._course_dir, university=university, subject=subject, course=course)
    
    def get_universities(self):
        '''
        Returns all universities.
        '''
        return self._firebase_manager.get_from_database_path("/categorization/universities")

    def get_document_types(self):
        '''
        Returns all document types.
        '''
        return self._firebase_manager.get_from_database_path("/categorization/document_types")
    
    def get_subjects(self):
        '''
        Returns all subjects.
        '''
        return self._firebase_manager.get_from_database_path("/categorization/subjects")

    def get_document(self, document_id: str) -> Document:
        '''
        Returns the document object for a document with a certain document id.
        '''
        return self._document_dir.get(document_id=document_id)
    
    def get_course(self, course_name: str) -> Course:
        '''
        Returns the course object with a certain course name.
        '''
        return self._course_dir.get_course(course_name=course_name)

    def add_document(self, 
                     pdf_url, 
                     document_type, 
                     user_id, 
                     university, 
                     course_name, 
                     subject,
                     write_date, 
                     upload_comment, 
                     grade = "ungraded",
                     validated = False, 
                     vote_directory = None, 
                     comment_section = None,
                     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), 
                     submitted_anonymously = False):
        '''
        Creates a document object and adds it to document directory and user.
        '''
        document_id = uuid.uuid4().hex

        document = Document(pdf_url=pdf_url, document_type=document_type, 
                 user_id=user_id, university=university, course_name=course_name, 
                 subject=subject, write_date=write_date, grade=grade, 
                 upload_comment=upload_comment, document_id=document_id, submitted_anonymously=submitted_anonymously)
        
        if not self._course_dir.course_exists(course_name=course_name):
            return 'Course does not exist.'
        
        else:
            # add to document dir and firebase
            #course = self._course_dir.get_course(course_name=course_name)
            self._document_dir.add(document=document)

            # add reference in course
            #course.add_document(document_id=document_id, document_type=document_type, document_name=document.get_header())

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
        '''
        Adds a reply to a document comment.
        '''
        try:
            document = self._document_dir.get(document_id=document_id)
            document.add_comment_reply(user_id=user_id, text=text, reply_to_comment_id=reply_to_comment_id)
            document_comment_section_json = document.get_comment_section_json()
            self._firebase_manager.update_document_comment_section(document_id=document_id, document_comment_section_json=document_comment_section_json)
        except:
            print(f"Failed to add comment reply to document {document_id}")

    def _set_user_directory_from_firebase(self):
        '''
        Creates users based on Firebase Storage.
        '''
        users = self._firebase_manager.get_all_users()
        
        for user in users:
            self._user_dir.add(user)

    def _set_course_directory_from_firebase(self):
        '''
        Creates courses based on Firebase Storage.
        '''
        courses = self._firebase_manager.get_all_courses()
        
        for course in courses:
            self._course_dir.add_course(course, add_to_firebase=False)

    def _set_documents_from_firebase(self):
        '''
        Creates documents based on Firebase Storage.
        '''
        documents = self._firebase_manager.get_all_documents()

        for document in documents:
            self._document_dir.add(document=document, add_to_firebase=False)

    def _set_from_firebase(self):
        '''
        Creates a user directory and course directory based on Firebase Storage.
        '''
        try:
            print("FirebaseRealtimeDatabase sync initiated")
            self._set_documents_from_firebase(self)
            self._set_user_directory_from_firebase(self)
            self._set_course_directory_from_firebase(self)
            
            print("FirebaseRealtimeDatabase sync completed")
        except:
            print("Error: FirebaseRealtimeDatabase sync failed")
        
        
        
    def to_json(self, type: str, id: str, main=None):
        '''
        Takes a type of page and converts it to json.
        '''
        if type == 'document':
            print(id)
            document = self.get_document(id)
            json = document.to_display_json()
            return json

        elif type == 'course':
            course = self.get_course(id)
            json = course.to_json()
            return json
        
        elif type == 'course_page':
            course = self.get_course(id)
            course_name = course.get_course_name()
            return course.to_display_json()
            #json = course.get_course_data(course_name, main)
        
        elif type == 'user':
            user = self.get_user(id)
            json = user.to_display_json()
            return json
        
        elif type == 'document_comments':
            document = self.get_document(document_id=id)
            comments = document.get_comments()

            json = {}

            for comment_id in comments:
                json[comment_id] = comments[comment_id].to_display_json()

            return json
        
        elif type == 'course_comments':
            course = self.get_course(course_name=id)
            comments = course.get_comments()

            json = {}

            for comment_id in comments:
                json[comment_id] = comments[comment_id].to_display_json()

            return json

        else:
            return 'Failed to get course/document json.'
    
    def get_username(self, user_id):
        """Returns the username of a specific user."""
        return self._user_dir.get_username(user_id)

    def get_user(self, user_id):
        '''
        Calls on the user directory to return a certain user object.
        '''
        return self._user_dir.get(user_id)
    
    def get_user_documents(self, user_id, validated=False):
        '''
        Calls on the relevant user object to return a list of the documents
        uploaded by the user.
        '''
        user = self._user_dir.get(user_id)
        document_ids = user.get_documents()

        documents = []
        for document_id in document_ids:
            document = self._document_dir.get(document_id)
            if document != None:
                # if validated is true, then only include documents that are validated
                if (validated and document.get_validation()) or (not validated):
                    documents.append({
                            document_id:{
                                "header":f"{document.get_course_name()} - {document.get_header()}",
                                "validated":document.get_validation()
                            }
                        })

        return documents
    
    def get_user_score(self, user_id):
        '''
        Returns the score of a specific user.
        '''
        user = self._user_dir.get(user_id)
        return user.get_score()
    
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
    
    def validate_document(self, document_id, approve):
        '''
        Validate a document with a certain document id.
        '''
        if approve == True:
            document = self._document_dir.get(document_id)
            course_name = document.get_course_name()
            document_type = document.get_type()
            document.validate_document()
            course = self._course_dir.get_course(course_name=course_name)
            course.add_document(document_id=document_id, document_type=document_type, document_name=document.get_header())
            print("Document has been validated")
        else:
            # remove the document
            document = self._document_dir.get(document_id)
            course_name = document.get_course_name()
            document_type = document.get_type()
            document.validate_document()
            course = self._course_dir.get_course(course_name=course_name)
            course.add_document(document_id=document_id, document_type=document_type, document_name=document.get_header())
            self.delete_document(document_id=document_id)
            print("Document has been deleted")

    def delete_document(self, document_id):
        """
        Deletes a document from the database.
        """
        document = self._document_dir.get(document_id)
        course_name = document.get_course_name()
        document_type = document.get_type() + 's'
        user_id = document.get_author()
        
        course = self._course_dir.get_course(course_name=course_name)
        course.remove_document(document_id=document_id, document_type=document_type)
        user = self._user_dir.get(user_id=user_id)
        user.remove_document(document_id)
        self._document_dir.remove(document_id=document_id)

        data = {document_id:{}}
        path = f"/Documents"
        FirebaseDatabase().push_to_path(path=path, data=data)
        path = f"/Users/{user_id}/Documents"
        FirebaseDatabase().push_to_path(path=path, data=data)

        print(f"Removed document: {document_id}")
        return f"Successfully removed document: {document_id}"
        
    def add_document_report(self, document_id, user_id, reason, text):
        """Add a report to a document"""
        document = self._document_dir.get(document_id=document_id)
        document.add_report(user_id, reason, text)
    
    def add_user_upload(self, pdf_id, pdf_url):
        '''
        Add user upload.
        '''
        path = f"/Files/Uploads/PDF"
        data = {
            pdf_id: pdf_url
        }

        self._firebase_manager.push_to_path(path=path, data=data)

    def get_user_upload_pdf(self, pdf_id):
        '''
        Get user upload pdf.
        '''
        path = f"Files/Uploads/PDF/{pdf_id}"
        try:
            url = self._firebase_manager.get_from_database_path(path=path)
        except:
            print("404: No file found")
            url = None
        return url
    
    def change_user_score(self, uid, change):
        '''
        Changes the user score.
        '''
        try:
            user = self._user_dir.get(uid)
            user.change_user_score(change)
        except:
            return 'Failed to change user score.'
        
    def get_waiting_courses(self):
        '''
        Calls on the course directory to return a list of waiting course names.
        '''
        return self._course_dir.get_waiting_courses()
    
    def get_document_reports(self, document_id):
        document = self._document_dir.get(document_id)
        return document.get_descriptive_reports()
    
    def delete_document_comment(self, document_id, comment_id):
        """
        Delete a comment on a document page.
        """
        document = self._document_dir.get(document_id)
        course_name = document.get_course_name()
        
        document.delete_comment(comment_id)
        # firebase
        path = f"Documents/{document_id}/comment_section/comments"
        self._firebase_manager.push_to_path(path=path, data={comment_id:{}})


    def delete_course_comment(self, course_name, comment_id):
        """
        Delete a comment on a course page.
        """
        
        course = self._course_dir.get_course(course_name)
        
        course.delete_comment(comment_id)
        # firebase
        path = f"Courses/{course_name}/Course Content/comment_section/comments"
        self._firebase_manager.push_to_path(path=path, data={comment_id:{}})

    def remove_document_reports(self, document_id):
        """
        Removes all reports for a document.
        """

        document = self._document_dir.get(document_id)
        document.remove_all_reports()

        # firebase
        path = f"Documents/{document_id}/categorization"
        data = {
            "reported":False,
            "reports":None
        }
        self._firebase_manager.push_to_path(path=path, data=data)


main = Main()