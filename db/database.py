import firebase_admin, os
from firebase_admin import db, credentials
import datetime



class Database:
    def __init__(self) -> None:
        db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + '/cert.json')
        db_url = {'databaseURL':'https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/'}
        firebase_admin.initialize_app(db_cert, db_url)

    def __str__(self):        
        return str(db.reference('/').get())
    
    def add_documet(self, pdf, course: str, school: str, upload_comment: str, tags: list) -> bool:
        '''
        Save a document to the database.
        
        Returns True if document was successfully saved to database.
        '''

        # Compile document
        id = self._new_id()
        upload_datetime = datetime.datetime.utcnow()
        doc_content = { 
                'upload':{
                        'pdf': pdf,
                        'comment':upload_comment
                },

                'timestamp':{
                        'date':upload_datetime.strftime('%Y-%m-%d'),
                        'time':upload_datetime.strftime('%H:%M:%S')
                },

                'categorization':{
                        'course':course,
                        'school':school,
                        'tags':tags
                },

                'votes':{
                        'upvotes':0,
                        'downvotes':0
                },

                'comments':{
                        
                }
        }

        # Create db reference, then add to db
        ref = db.reference('/documents/' + str(id))
        ref.update(doc_content)
        
        # Check if the document is stored in db
        doc = self.get_document(id)

        return True if doc == doc_content else False

    def get_document(self, id: int):
        '''
        Returns document json string. If no document with :id: in database, returns None.
        '''

        ref = db.reference('/documents/' + str(id))

        return ref.get()
        
    def get_documents(self, tag: str):
        '''
        Returns document id list for documents with attached :tag:
        '''
        docs = []
        id_lst = self._get_id_lst()

        for id in id_lst:
            if tag in self.get_tags(id):
                docs.append(id)

        return docs

    def get_tags(self, id: int):
        '''
        Returns a list with tags. If no document with :id: in database, returns empty list.
        '''

        doc = self.get_document(id)

        try:
            doc['categorization']['tags']
        except:
            return []

        return doc['categorization']['tags']
    
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
        
        try:
            id_lst_str = list(db.reference('/documents').get(shallow=True).keys())
        except:
            return [0]
        
        id_lst_int = [eval(id) for id in id_lst_str]

        return id_lst_int

### Ta bort innan commit
    def _get_keys(self, ref_path): 
            '''
            Get all keys from reference path in the database.
            '''

            keys = list(db.reference(ref_path).get(shallow=True).keys())

            return keys

d = Database()

print(d._get_keys('documents'))


# d.add_documet(pdf='This is a pdf file', 
#               course='PA2576',
#               school='BTH',
#               upload_comment='This is the upload comment',
#               tags=['programming', 'assignment', 'draft'])
