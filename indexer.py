import os

import fitz  # PyMuPDF for PDFs

import docx  # python-docx for Word

import langdetect

from elasticsearch import Elasticsearch

from datetime import datetime

 

DOC_FOLDER = 'pdfs'  # Update with your drive path

INDEX_NAME = 'index file' # Update with your index file

 

es = Elasticsearch(

    "https://localhost:9200",

    basic_auth=("elastic", "your password here"),

    verify_certs=False

)

 

# Create index with mapping if not exists

def create_index():

    if not es.indices.exists(index=INDEX_NAME):

        es.indices.create(index=INDEX_NAME, body={

            "mappings": {

                "properties": {

                    "filename": {"type": "keyword"},

                    "page_number": {"type": "integer"},

                    "text": {"type": "text"},

                    "filepath": {"type": "keyword"},

                    "year": {"type": "integer"},

                    "language": {"type": "keyword"},

                    "doc_type": {"type": "keyword"}

                }

            }

        })

        print("Index created")

    else:

        print("Index already exists")

 

def extract_text_pdf(path):

    doc = fitz.open(path)

    for i in range(len(doc)):

        yield i + 1, doc[i].get_text()

 

def extract_text_docx(path):

    doc = docx.Document(path)

    text = "\n".join(p.text for p in doc.paragraphs)

    yield 1, text

 

def extract_text_txt(path):

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:

        yield 1, f.read()

 

def detect_language(text):

    try:

        return langdetect.detect(text)

    except:

        return "unknown"

 

def extract_year(path):

    try:

        timestamp = os.path.getmtime(path)

        return datetime.fromtimestamp(timestamp).year

    except:

        return None

 

def index_documents():

    create_index()

 

    indexed_paths = set()

    existing = es.search(index=INDEX_NAME, size=10000, source=["filepath"])

    for hit in existing['hits']['hits']:

        indexed_paths.add(hit['_source']['filepath'])

 

    total_files = sum(len(files) for _, _, files in os.walk(DOC_FOLDER))

    indexed_count = 0

 

    for root, _, files in os.walk(DOC_FOLDER):

        for file in files:

            ext = file.lower().split('.')[-1]

            full_path = os.path.join(root, file)

            if full_path in indexed_paths:

                print(f"[SKIP] Already indexed: {file}")

                continue

 

            try:

                if ext == 'pdf':

                    for page, text in extract_text_pdf(full_path):

                        es.index(index=INDEX_NAME, document={

                            'filename': file,

                            'page_number': page,

                            'text': text,

                            'filepath': full_path,

                            'year': extract_year(full_path),

                            'language': detect_language(text),

                            'doc_type': 'pdf'

                        })

                elif ext == 'docx':

                    for page, text in extract_text_docx(full_path):

                        es.index(index=INDEX_NAME, document={

                            'filename': file,

                            'page_number': page,

                            'text': text,

                            'filepath': full_path,

                            'year': extract_year(full_path),

                            'language': detect_language(text),

                            'doc_type': 'docx'

                        })

                elif ext == 'txt':

                    for page, text in extract_text_txt(full_path):

                        es.index(index=INDEX_NAME, document={

                            'filename': file,

                            'page_number': page,

                            'text': text,

                            'filepath': full_path,

                            'year': extract_year(full_path),

                            'language': detect_language(text),

                            'doc_type': 'txt'

                        })

                indexed_count += 1

                print(f"[Indexed {indexed_count}/{total_files}] {file}")

            except Exception as e:

                print(f"[ERROR] Failed to index {file}: {e}")

 

if __name__ == '__main__':

    index_documents()