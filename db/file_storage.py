import firebase_admin, os
from pathlib import Path
from firebase_admin import credentials, storage

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

#f = FileStorage()
#f.download_pdf(1)
#f.upload_pdf(os.path.dirname(os.path.abspath(__file__))+ '/test.pdf', 3)