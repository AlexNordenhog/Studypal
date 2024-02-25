from flask import Blueprint, request, render_template
from .search import search
import json

views = Blueprint("views", __name__)

#Temporärt för att prova sökfunktionen, ta bort senare.
course_list = ['Analys 1', 'Analys 2', 'Matematisk Problemlösning', 'Mikroekonomi', 'Flervariabelanalys', 'Datorstöd för Ingenjörer', 'Programvaruintensiv Produktutveckling', 'Objektorienterad Design', 'Grunderna i Industriell Ekonomi']
universities = ['Blekinge Institute of Technology', 'Chalmers Institute of Technology']
university_data = {
    'Blekinge Institute of Technology': {
      'Mathematics': ['Analys 1', 'Analys 2', 'Matematisk Problemlösning', 'Flervariabelanalys'],
      'Economics': ['Mikroekonomi', 'Grunderna i Industriell Ekonomi'],
      'CAD': ['Datorstöd för Ingenjörer'],
      'IT': ['Programvaruintensiv Produktutveckling', 'Objektorienterad Design']
    },
    'Chalmers Institute of Technology': {
      'Mathematics': ['Inledande Matematisk Analys']
    }
  }

@views.route("/")
def home():
    return render_template("home.html",
                           universities=universities,
                           university_data=json.dumps(university_data))
                           

@views.route("/search")
def search_results():
    university = request.args.get('university')
    subject = request.args.get('subject')
    course = request.args.get('course')
    query = request.args.get('query', '')
    
    results = search(university_data, query, university, subject, course)  
    return render_template('search_results.html', query=query, results=results)


@views.route("/upload")
def upload():
    return render_template("upload.html")


@views.route("/profile")
def profile():
    return render_template("profile.html")