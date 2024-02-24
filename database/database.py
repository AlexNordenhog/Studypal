import firebase_admin, os
from firebase_admin import db, credentials

class database():
    def __init__(self) -> None:
        db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + '/cert.json')
        db_url = {'databaseURL':'https://studypal-8a379-default-rtdb.europe-west1.firebasedatabase.app/'}
        firebase_admin.initialize_app(db_cert, db_url)

    def __str__(self):        
        return str(db.reference('/').get())
    
    def add_documet(self, pdf, solution: bool, tags: list):
        '''
        Save a document to the database.
        '''

        id = self._new_id()
        ref = db.reference('/documents/' + str(id))
        ref.update({'id':id, 'pdf':pdf, 'solution':solution, 'tags':tags})

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
            doc['tags']
        except:
            return []

        return doc['tags']
    
    def _new_id(self):
        new_id = max(self._get_id_lst()) + 1
        return new_id
    
    def _get_id_lst(self):
        id_lst_str = list(db.reference('/documents').get(shallow=True).keys())
        id_lst_int = [eval(id) for id in id_lst_str]
        return id_lst_int