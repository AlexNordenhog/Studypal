import firebase_admin, os
from firebase_admin import db, credentials, storage
import datetime
from db.file_storage import FileStorage

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
        id = self._new_id()
        storage_path = self.file_storage.upload_pdf(pdf_file_path, id)
        upload_datetime = datetime.datetime.utcnow()
        doc_content = {
                'upload':{
                        'pdf_url': storage_path,
                        'author':username,
                        'header':header
                },

                'timestamp':{
                        'date':upload_datetime.strftime('%Y-%m-%d'),
                        'time':upload_datetime.strftime('%H:%M:%S')
                },

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

    def get_document(self, id: int):
        '''
        Returns document json string. If no document with :id: in database, returns None.
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
        return db.reference('').get()

    def add_course(self, university, subject, course_abbr, course_desc, course_name):
        
        ref = db.reference(f'Universities/{university}/{subject}/{course_abbr}/')
        course_info = {'Course Info':{

                'Description':course_desc,
                'Name':course_name
            }
        }

        ref.update(course_info)
        
        return
    
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
    
    def _new_id(self):
        '''
        Generates the next document id.
        '''

        new_id = max(self._get_id_lst()) + 1
        return new_id
    
    def _get_id_lst(self):
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
                    document_types = self._get_keys(f'/Universities/{school}/{subject}/{course}/Documents')

                    for document_type in document_types:
                        document_ids = self._get_keys(f'/Universities/{school}/{subject}/{course}/Documents/{document_type}')
                    
                        for id in document_ids:
                            id_lst_str.append(id)

        # Parse id's to int
        id_lst_int = [eval(id) for id in id_lst_str]
        
        return id_lst_int
    
    def _get_keys(self, ref_path):
        '''
        Get all keys from reference path in the database.
        '''
        keys = list(db.reference(ref_path).get(shallow=True).keys())
        return keys
    
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



d = Database()

#d.add_documet(os.path.dirname(os.path.abspath(__file__)) + '/test.pdf', 'PA2576', 'Royal Institute of Simon Flisberg', 'lecture notes from 28 feb', 'Programming', 'hampus', 'My Lecture Notes', 'Lecture Notes', ['programming', 'good'])
#d.add_documet('pdf', 'PA2576', 'Royal Institute of Simon Flisberg', 'lecture notes from 28 feb', 'Programming', 'hampus', 'My Lecture Notes', 'Lecture Notes', ['programming', 'good'])
#print(d.get_document(1))