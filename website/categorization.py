from db.database import d

class CategorizationController:
    def categorize(self, pdf_url, uid, document_type, date, university, subject, course, comment, grading_system=None, grade=None):
        header = str(course + ' ' + document_type + ' ' + date)
        tags = []
        d.add_document(pdf_url, course, university, comment, subject, uid, header, document_type, tags)

c = CategorizationController()