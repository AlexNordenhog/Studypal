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
                                    'timestamp':{
                                        'date':upload_datetime.strftime('%Y-%m-%d'),
                                        'time':upload_datetime.strftime('%H:%M:%S')
                                    }  
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

        document_path = self._get_document_ref(document_id).path
        
        ref = db.reference(f'{document_path}/votes')
        votes = dict(ref.get())
        
        if upvote:
            votes['upvotes'] += 1
        else:
            votes['downvotes'] += 1

        ref.update(votes)

        return True if votes == ref.get() else False


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
    
    def _get_timestamp(self) -> dict:
        
        datetime_now = datetime.datetime.utcnow()
        
        timestamp = {
            'date':datetime_now.strftime('%Y-%m-%d'),
            'time':datetime_now.strftime('%H:%M:%S')
        }

        return timestamp

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

d = Database()

#print(d.add_document_vote(1, True, ''))
#print(d.add_document_vote(1, True, ''))
#print(d.add_document_vote(1, False, ''))




#print(d.add_document_comment(1, 'student_1', 'so helpful'))
#print(d.add_document_comment(1, 'toxic_student', 'y did u post this nonsense'))

#d.add_documet(os.path.dirname(os.path.abspath(__file__)) + '/test.pdf', 'IY0000', 'Royal Institute of Simon Flisberg', 'This is my exma', 'Economics', 'some_user', 'Some exam i found in the trashcan', 'Exams', ['this is a tag', 'this is another tag'])
#d.add_course('Royal Institute of Simon Flisberg', 'Economics', 'IY0000', 'En introduktionskurs', 'Företagsekonomi - Introduktionskurs')
#d.add_course('Royal Institute of Simon Flisberg', 'Programming', 'PA2576', 'This is a programming course', 'Programvaruintensiv produktutveckling')

#d.add_documet('pdf', 'PA2576', 'Royal Institute of Simon Flisberg', 'lecture notes from 28 feb', 'Programming', 'hampus', 'My Lecture Notes', 'Lecture Notes', ['programming', 'good'])
#print(d.get_document(1))