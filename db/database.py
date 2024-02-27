import firebase_admin, os
from firebase_admin import db, credentials
import datetime



class Database:
    def __init__(self) -> None:
        db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + '/cert.json')
        db_url = {'databaseURL':'https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/'}
        firebase_admin.initialize_app(db_cert, db_url)
    
    def add_documet(self, pdf, course: str, school: str, upload_comment: str, subject: str, username: str, header: str, tags: list) -> bool:
        '''
        Save a document to the database.
        
        Returns bool to confirm if document was successfully uploaded or not.
        '''
        
        # Compile document
        id = self._new_id()
        upload_datetime = datetime.datetime.utcnow()
        doc_content = { 
                'upload':{
                        'pdf': pdf,
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
                        'upload_comment':upload_comment
                }
        }

        # Create db reference, then add to db
        ref = db.reference(f'/documents/{school}/{subject}/{course}/{str(id)}')
        ref.update(doc_content)
        
        # Check if the document is stored in db
        doc = self.get_document(id)

        return True if doc == doc_content else False

    def get_document(self, id: int):
        '''
        Returns document json string. If no document with :id: in database, returns None.
        '''

        ref = None
        schools = self._get_keys(f'/documents/')
        for school in schools:
            subjects = self._get_keys(f'/documents/{school}')
            
            for subject in subjects:
                courses = self._get_keys(f'/documents/{school}/{subject}')
                    
                for course in courses:
                    document_ids = self._get_keys(f'/documents/{school}/{subject}/{course}')
                    
                    for _id in document_ids:
                        if int(_id) == id:
                            ref = db.reference(f'/documents/{school}/{subject}/{course}/{id}')
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

        schools = self._get_keys(f'/documents/')

        # Get all document id's and add them to list
        for school in schools:
            subjects = self._get_keys(f'/documents/{school}')
            
            for subject in subjects:
                courses = self._get_keys(f'/documents/{school}/{subject}')
                    
                for course in courses:
                    document_ids = self._get_keys(f'/documents/{school}/{subject}/{course}')
                    
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

d = Database()