
from flask import Flask, request, render_template, jsonify,send_from_directory, abort
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)

# Adjust this to your actual folder containing the PDFs

PDF_FOLDER = "" # Update with your network drive path

es = Elasticsearch(

    "https://localhost:9200",

    basic_auth=("elastic", "your password here"),

    verify_certs=False

)

 

@app.route('/')

def index():

    return render_template('index.html')

 

@app.route("/docs/<path:filename>")

def serve_pdf(filename):

    try:

        return send_from_directory(PDF_FOLDER, filename)

    except FileNotFoundError:

        abort(404)

 

@app.route('/search')

def search():

    q = request.args.get('q')

    filename = request.args.get('filename')

    year = request.args.get('year')

    language = request.args.get('language')

    doc_type = request.args.get('doc_type')

 

    must_clauses = []

    filter_clauses = []

 

    if q:

        must_clauses.append({"match": {"text": q}})

 

    if filename:

        filter_clauses.append({"term": {"filename.keyword": filename}})

 

    if year:

        try:

            year_int = int(year)

            filter_clauses.append({"term": {"year": year_int}})

        except ValueError:

            pass

 

    if language:

        filter_clauses.append({"term": {"language": language}})

 

    if doc_type:

        filter_clauses.append({"term": {"doc_type": doc_type}})

 

    query_body = {

        "bool": {}

    }

 

    if must_clauses:

        query_body["bool"]["must"] = must_clauses

    else:

        query_body["bool"]["must"] = [{"match_all": {}}]

 

    if filter_clauses:

        query_body["bool"]["filter"] = filter_clauses

 

    result = es.search(

        index='doc_index',

        query=query_body,

        highlight={

            "fields": {

                "text": {

                    "pre_tags": ["<span class='highlight'>"],

                    "post_tags": ["</span>"],

                    "fragment_size": 300,

                    "number_of_fragments": 1

                }

            }

        }

    )

 

    print(f"Found {len(result['hits']['hits'])} hits")

 

    return jsonify([

        {

            'filename': hit['_source']['filename'],

            'page_number': hit['_source'].get('page_number', 1),

            'filepath': os.path.basename(hit['_source']['filepath']),

            'text_snippet': hit.get('highlight', {}).get('text', [hit['_source']['text'][:300]])[0]

        }

        for hit in result['hits']['hits']

    ])




@app.route('/viewer')

def viewer():

    return render_template('viewer.html')  # pdf.js file viewer

 

 

if __name__ == '__main__':

    app.run(debug=True)