import firebase_admin, os
from firebase_admin import db, credentials, storage
import datetime
from pathlib import Path

class Database:
    def __init__(self) -> None:
        db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + '/cert.json')
        db_url = {'databaseURL':'https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/'}
        firebase_admin.initialize_app(db_cert, db_url)
        self.file_storage = FileStorage()

    def add_user(self, uid: str, username: str):
        ref = db.reference('/Users')

        # Create the user
        user = {
            uid:{
                'username': username,
                'creation_date': self._get_timestamp()['date'],
                'documents':[]
            }
        }

        print(user)

        ref.update(user)
            
    def add_documet(self, pdf_file_path, course: str, school: str, upload_comment: str, subject: str, username: str, header: str, type_of_document: str, tags: list) -> bool:
        '''
        Save a document to the database.
        
        Returns bool to confirm if document was successfully uploaded or not.
        '''
        
        # Compile document
        id = self._get_new_id()
        storage_path = self.file_storage.upload_pdf(pdf_file_path, id)

        doc_content = {
                'upload':{
                        'pdf_url': storage_path,
                        'author':username,
                        'header':header
                },

                'timestamp':self._get_timestamp(),

                'categorization':{
                        'school':school,
                        'course':course,
                        'subject':subject,
                        'tags':tags
                },

                'votes':{
                        'upvotes':0,
                        'downvotes':0
                },

                'comments':{
                        'upload_comment':upload_comment,
                        'document_comments':{
                                1:{
                                    'username':'simon',
                                    'comment':'omg what',
                                    'timestamp':self._get_timestamp()
                                }
                        }
                }
        }

        # Create db reference, then add to db
        ref = db.reference(f'/Universities/{school}/{subject}/{course}/Documents/{type_of_document}/{str(id)}')
        ref.update(doc_content)
        
        # Check if the document is stored in db
        doc = self.get_document(id)

        return True if doc == doc_content else False

    def add_course(self, university, subject, course_abbr, course_desc, course_name):
        
        ref = db.reference(f'Universities/{university}/{subject}/{course_abbr}/')
        course_info = {'Course Info':{

                'Description':course_desc,
                'Name':course_name
            }
        }

        ref.update(course_info)
        
        return

    def add_document_comment(self, document_id, username, comment):
        '''
        Add a comment to a document
        '''

        document_path = self._get_document_ref(document_id).path
        comments_path = f'{document_path}/comments/document_comments/'
        
        # generate new comment id
        comment_id_lst = list(eval(str_id) for str_id in (self._get_keys(comments_path)))
        if len(comment_id_lst) == 0:
            comment_id = 1
        else:
            comment_id = max(comment_id_lst) + 1

        # Compile comment 
        comment_content = {
            'comment':comment,
            'username':username,
            'timestamp':self._get_timestamp()
        }

        ref = db.reference(f'{comments_path}/{comment_id}')
        ref.update(comment_content)

        # Check if comment was added to db
        json_comment = ref.get()
        
        return True if json_comment == comment_content else False

    def add_document_vote(self, document_id: int, upvote: bool, username: str) -> bool:
        '''
        Add an up or downvote to a document. 
        '''

        votes = self.get_document_votes(document_id)
        
        if upvote:
            votes['upvotes'] += 1
        else:
            votes['downvotes'] += 1

        ref = db.reference(f'{self._get_document_ref(document_id).path}/votes')
        ref.update(votes)

        return True if votes == ref.get() else False

    def get_user(self, uid):
        
        ref = db.reference(f'/Users/{uid}')
        user = ref.get()
        
        return user

    def get_document_votes(self, document_id: int) -> dict:
        '''
        Returns dict with document upvotes & downvotes.
        '''
        document_path = self._get_document_ref(document_id).path
        ref = db.reference(f'{document_path}/votes')
        votes = dict(ref.get())

        return votes
    
    def get_document_comments(self, document_id: int):
        '''
        Returns dict with all post-upload document comments.
        '''
        
        document_path = self._get_document_ref(document_id).path
        ref = db.reference(f'{document_path}/comments/document_comments')
        
        comment_ids = [eval(key) for key in list(self._get_keys(document_path + '/comments/document_comments'))]

        comments = {}
        
        for key in comment_ids:
            comments[key] = ref.get()[key]

        return comments
    
    def get_document_upload_comment(self, document_id: int):
        '''
        Returns dict with the upload comment only.
        '''

        document_path = self._get_document_ref(document_id).path
        ref = db.reference(f'{document_path}/comments/upload_comment')

        return ref.get()

    def get_document(self, id: int):
        '''
        Returns document json string. If no document with :id: in database, returns None.
        '''
        ref = self._get_document_ref(id)
        
        try:
            ref.get()
        except:
            return None
        
        return ref.get()
    
    def get_categorization(self, id: int):
        '''
        Returns a json string with a document categorization. If no document with :id: in database, returns None.
        '''

        doc = self.get_document(id)

        try:
            doc['categorization']
        except:
            return None

        return doc['categorization']
    
    def get_full(self):
        '''Returns full database dict'''
        return db.reference('').get()

    def get_all_universities(self):
        '''
        Returns a list of all universities in the database.
        '''

        universities = self._get_keys('Universities')
        
        return universities

    def get_all_unique_subjects(self):
        '''
        Returns a list of all subjects in the database (no duplicates).
        '''

        unique_subjects = []
        universities = self.get_all_universities()

        for u in universities:
            subjects = self._get_keys(f'Universities/{u}')

            for s in subjects:
                if s not in unique_subjects:
                    unique_subjects.append(s)

        return unique_subjects
    
    def get_all_subjects_from_university(self, university):
        university_subjects = self._get_keys(f'Universities/{university}')

        return university_subjects

    def get_all_courses(self):
        '''
        Returns a list of all courses in the database.
        '''

        all_courses = []
        universities = self.get_all_universities()

        for u in universities:
            subjects = self.get_all_subjects_from_university(u)

            for s in subjects:
                subject_courses = self.get_courses_from_subject_at_university(u, s)
                all_courses.extend(subject_courses)

        return all_courses

    def get_courses_from_subject_at_university(self, university, subject):
        '''
        Returns a list of all courses from a specific subject at a specific university.
        '''

        subject_courses = self._get_keys(f'Universities/{university}/{subject}')

        return subject_courses

    def get_courses_from_university(self, university):
        '''
        Returns a list of all courses from a specific university.
        '''

        university_courses = []
        university_subjects = self.get_all_subjects_from_university(university)

        for s in university_subjects:
            subject_courses = self.get_courses_from_subject_at_university(university, s)
            university_courses.extend(subject_courses)

        return university_courses
            
    def get_courses_from_subject(self, subject):
        '''
        Returns a list of all courses for a specific subject from all universities.
        '''

        all_subject_courses = []
        universities = self.get_all_universities()

        for u in universities:
            university_subjects = self.get_all_subjects_from_university(u)

            for s in university_subjects:
                if subject == s:
                    subject_courses = self.get_courses_from_subject_at_university(u, s)
                    all_subject_courses.extend(subject_courses)

        return all_subject_courses
    
    def get_all_universities(self):
        '''
        Returns a list of all universities in the database.
        '''
        universities = self._get_keys('Universities')
        return universities

    def get_all_unique_subjects(self):
        '''
        Returns a list of all subjects in the database (no duplicates).
        '''
        unique_subjects = []
        universities = self.get_all_universities()
        for u in universities:
            subjects = self._get_keys(str('Universities/' + u))
            for s in subjects:
                if s not in unique_subjects:
                    unique_subjects.append(s)
        return unique_subjects
    
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
    
    def get_all_subjects_from_university(self, university):
        university_subjects = self._get_keys(str('Universities/' + university))
        return university_subjects

    def get_all_courses(self):
        '''
        Returns a list of all courses in the database.
        '''
        all_courses = []
        universities = self.get_all_universities()
        for u in universities:
            subjects = self.get_all_subjects_from_university(u)
            for s in subjects:
                subject_courses = self.get_courses_from_subject_at_university(u, s)
                all_courses.extend(subject_courses)
        return all_courses

    def get_courses_from_subject_at_university(self, university, subject):
        '''
        Returns a list of all courses from a specific subject at a specific university.
        '''
        subject_courses = self._get_keys(str('Universities/') + '/' + university + '/' + subject)
        return subject_courses

    def get_courses_from_university(self, university):
        '''
        Returns a list of all courses from a specific university.
        '''
        university_courses = []
        university_subjects = self.get_all_subjects_from_university(university)
        for s in university_subjects:
            subject_courses = self.get_courses_from_subject_at_university(university, s)
            university_courses.extend(subject_courses)
        return university_courses
            
    def get_courses_from_subject(self, subject):
        '''
        Returns a list of all courses for a specific subject from all universities.
        '''
        all_subject_courses = []
        universities = self.get_all_universities()
        for u in universities:
            university_subjects = self.get_all_subjects_from_university(u)
            for s in university_subjects:
                if subject == s:
                    subject_courses = self.get_courses_from_subject_at_university(u, s)
                    all_subject_courses.extend(subject_courses)
        return all_subject_courses

    def _get_new_id(self) -> int:
        '''
        Generates the next document id.
        '''
        id_lst = self._get_id_lst()
        new_id = max(id_lst) + 1
        return new_id
    
    def _get_id_lst(self) -> list:
        '''
        Returns a list containing all document id's.
        '''
        
        id_lst_str = []

        schools = self._get_keys(f'/Universities/')
        # Get all document id's and add them to list
        for school in schools:
            subjects = self._get_keys(f'/Universities/{school}')
            
            for subject in subjects:
                courses = self._get_keys(f'/Universities/{school}/{subject}')
                    
                for course in courses:
                    if 'Documents' in self._get_keys(f'/Universities/{school}/{subject}/{course}'):
                        document_types = self._get_keys(f'/Universities/{school}/{subject}/{course}/Documents')

                        for document_type in document_types:
                            document_ids = self._get_keys(f'/Universities/{school}/{subject}/{course}/Documents/{document_type}')
                        
                            for id in document_ids:
                                id_lst_str.append(id)

        # Parse id's to int
        id_lst_int = [eval(id) for id in id_lst_str]
        
        #print(id_lst_int)
        return id_lst_int
    
    def _get_keys(self, ref_path) -> list:
        '''
        Get all keys from reference path in the database.
        '''
        
        try:
            keys = list(db.reference(ref_path).get(shallow=True).keys())
        except:
            return []

        return keys
    
    def _get_document_ref(self, id: int):
        '''
        Returns document firebase reference.
        '''

        ref = None
        schools = self._get_keys(f'/Universities/')

        for school in schools:
            subjects = self._get_keys(f'/Universities/{school}')
            
            for subject in subjects:
                courses = self._get_keys(f'/Universities/{school}/{subject}')
                    
                for course in courses:
                    document_types = self._get_keys(f'/Universities/{school}/{subject}/{course}/Documents')
                    
                    for document_type in document_types:
                        document_ids = self._get_keys(f'/Universities/{school}/{subject}/{course}/Documents/{document_type}')

                    for _id in document_ids:
                        if int(_id) == int(id):
                            ref = db.reference(f'/Universities/{school}/{subject}/{course}/Documents/{document_type}/{id}')
                            break

        return ref
    
    def _get_course_ref(self, course_name):
        '''
        Returns course firebase reference.
        '''
        found = False
        course_ref = None
        universities = self._get_keys(f'/Universities/')
        for university in universities:
            subjects = self._get_keys(f'/Universities/{university}')
            for subject in subjects:
                courses = self._get_keys(f'/Universities/{university}/{subject}')
                if course_name in courses:
                    found = True
                    course_ref = f'Universities/{university}/{subject}/{course_name}/Course Info'
                    break
            if found:
                break
        return course_ref
    
    def _get_document_id_by_name(self, document_name):
        """
        Returns the document ID for a given document name, searching within 'assignments' and 'exams' categories.
        """
        document_id = None
        universities = self._get_keys('/Universities/')
        for university in universities:
            subjects = self._get_keys(f'/Universities/{university}')
            for subject in subjects:
                courses = self._get_keys(f'/Universities/{university}/{subject}')
                for course in courses:
                    # Directly check in 'assignments' and 'exams' categories. We have to add paths if needed
                    for doc_type in ['Assignments', 'Exams']:
                        document_ids = self._get_keys(f'/Universities/{university}/{subject}/{course}/Documents/{doc_type}')
                        for doc_id in document_ids:
                            doc_ref = f'/Universities/{university}/{subject}/{course}/Documents/{doc_type}/{doc_id}'
                            doc = db.reference(doc_ref).get()
                            # Check if the document name matches the one we're looking for
                            if doc and 'upload' in doc and doc['upload'].get('header') == document_name:
                                return doc_id  # Found the document ID
        return document_id  # Return None if not found

    def _get_timestamp(self) -> dict:
        
        datetime_now = datetime.datetime.utcnow()
        
        timestamp = {
            'date':datetime_now.strftime('%Y-%m-%d'),
            'time':datetime_now.strftime('%H:%M:%S')
        }

        return timestamp

    def _get_document_ids_for_course(self, course_university, course_subject, course_name):
        '''
        Takes a university, subject and a course name (str) as parameters and
        returns a dictionary including the document types and the document ids.
        The dictionary will be of the form:
        {Graded exams : [1, 2, 3, ...], 
        Non-Graded Exams : [4, 5, 6, ...],
        Assignments : [7, 8, 9, ...],
        Lecture Notes : [10, 11, 12, ...],
        Other Documents : [13, 14, 15, ...]}
        '''
        course_documents_id_dict = {}
        document_types = self._get_keys(f'/Universities/{course_university}/{course_subject}/{course_name}/Documents')
        for document_type in document_types:
            document_ids = self._get_keys(f'/Universities/{course_university}/{course_subject}/{course_name}/Documents/{document_type}')
            course_documents_id_dict.update({document_type : document_ids})
        return course_documents_id_dict

    def _get_university_and_subject_for_course_name(self, course_name):
        '''
        Takes a string for a course name and returns the university and
        the subject for that course in a list [university, subject]
        '''
        all_courses = self.get_all_courses()
        for c in all_courses:
            if c == course_name:
                course_ref = self._get_course_ref(course_name)
                university_name = db.reference(course_ref).get()['University']
                subject_name = db.reference(course_ref).get()['Subject']
                break
        return [university_name, subject_name]

    def _get_document_names_for_course(self, course_university, course_subject, course_name, course_documents_id_dict):
        '''
        Takes a university, subject, a course name (str) and a course documents id dict 
        as parameters and returns a dictionary including the document types and the document names.
        The dictionary will be of the form:
        {Graded exams : [A, B, C, ...], 
        Non-Graded Exams : [D, E, F, ...],
        Assignments : [G, H, I, ...],
        Lecture Notes : [J, K, L, ...],
        Other Documents : [M, N, O, ...]}
        '''
        course_documents_name_dict = {}
        course_document_types = course_documents_id_dict.keys()
        for document_type in course_document_types:
            document_names_for_document_type = []
            for id in course_documents_id_dict.get(document_type):
                document_name = db.reference(f'/Universities/{course_university}/{course_subject}/{course_name}/Documents/{document_type}/{id}/upload').get()['header']
                document_names_for_document_type.append(document_name)
            course_documents_name_dict.update({document_type : document_names_for_document_type})
        return course_documents_name_dict

    def get_course_data(self, course_name):
        course_university_and_subject = self._get_university_and_subject_for_course_name(course_name)
        course_university = course_university_and_subject[0]
        course_subject = course_university_and_subject[1]
        course_documents_id_dict = self._get_document_ids_for_course(course_university, course_subject, course_name)
        course_documents_name_dict = self._get_document_names_for_course(course_university, course_subject, course_name, course_documents_id_dict)
        course_data_dict = {
            "course_name": course_name,
            "course_university": course_university,
            "course_subject": course_subject,
            "course_documents_id_dict": course_documents_id_dict,
            "course_documents_name_dict": course_documents_name_dict,
        }
        return course_data_dict

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

d = Database()


def upload_comments_example():

    doc_1_upload_comment = d.get_document_upload_comment(1)

    print(f'\nThis is the upload comment: {doc_1_upload_comment}\n')
    doc_1_post_upload_comments = d.get_document_comments(1)

    for key in doc_1_post_upload_comments.keys():
        print(f'This is comment id: {key}, and the comment data is: {doc_1_post_upload_comments[key]}')

#upload_comments_example()

#print(d.add_document_vote(1, True, ''))
#print(d.add_document_vote(1, True, ''))
#print(d.add_document_vote(1, False, ''))



#print(d.add_document_comment(1, 'student_1', 'so helpful'))
#print(d.add_document_comment(1, 'toxic_student', 'y did u post this nonsense'))

# d.add_documet(os.path.dirname(os.path.abspath(__file__)) + '/test.pdf', 'MA1444', 'Blekinge Institute of Technology', 'This is my exma', 'Mathematics', 'some_user', 'Some exam i found in the trashcan', 'Exams', ['this is a tag', 'this is another tag'])
#d.add_course('Royal Institute of Simon Flisberg', 'Economics', 'IY0000', 'En introduktionskurs', 'Företagsekonomi - Introduktionskurs')
#d.add_course('Royal Institute of Simon Flisberg', 'Programming', 'PA2576', 'This is a programming course', 'Programvaruintensiv produktutveckling')

#d.add_documet('pdf', 'PA2576', 'Royal Institute of Simon Flisberg', 'lecture notes from 28 feb', 'Programming', 'hampus', 'My Lecture Notes', 'Lecture Notes', ['programming', 'good'])
#print(d.get_document(1))


#os.path.dirname(os.path.abspath(__file__)).



