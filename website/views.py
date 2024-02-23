from flask import Blueprint, request, render_template
from .search import search

views = Blueprint("views", __name__)


@views.route("/")
def home():
    return render_template("home.html")

#Temporär lista för att prova sökfunktionen, ta bort senare.
dummy_list = ['Analys 1', 'Analys 2', 'Matematisk Problemlösning', 'Mikroekonomi', 'Flervariabelanalys', 'Datorstöd för Ingenjörer', 'Programvaruintensiv Produktutveckling', 'Objektorienterad Design', 'Grunderna i Industriell Ekonomi']

@views.route("/search")
def search_results():
    query = request.args.get('query', '')
    results = search(dummy_list, query)  
    return render_template('search_results.html', query=query, results=results)


@views.route("/upload")
def upload():
    return render_template("upload.html")


@views.route("/profile")
def profile():
    return render_template("profile.html")