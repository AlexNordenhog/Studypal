from firebase_admin import credentials, initialize_app, storage
import os





# Init firebase with your credentials
db_cert = credentials.Certificate(os.path.dirname(os.path.abspath(__file__)) + '/cert.json')
storage_url = {'storageBucket': 'studypal-8a379.appspot.com'}

initialize_app(db_cert, storage_url)

# Put your local file path 
fileName = os.path.dirname(os.path.abspath(__file__)) + '/test.pdf'
bucket = storage.bucket()
blob = bucket.blob(fileName)
blob.upload_from_filename(fileName)

# Opt : if you want to make public access from the URL
#blob.make_public()

print("your file url", blob.public_url)