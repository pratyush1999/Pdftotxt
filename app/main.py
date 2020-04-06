from flask import Flask
from flask import request
from txt_extracter import Pdftotxt_extract
from copy import deepcopy
import json
import os

app = Flask(__name__)

@app.route('/pdfupload', methods=['POST'])
def pdfupload():

    PDF_PATH = "./PDFs"

    if not os.path.exists(PDF_PATH):
        os.mkdir(PDF_PATH)

    files = request.files['file']
    files.save(PDF_PATH + '/' + files.filename)
    return "Successfully Uploadded {}".format(files.filename)


@app.route('/pdftotxt', methods=['POST'])
def pdftotxt():
    temp=request.get_json()
    content=json.loads(temp)
    pdfs=content['pdfs']
    txts=[]
    for pdf in pdfs:
            pdftotxt_extract=Pdftotxt_extract(pdf)
            txts.append(pdftotxt_extract.extract_text()) 
    output={}
    output['pdfs']=txts
    return json.dumps(output) 

if __name__ == '__main__':

    port = os.getenv("URL_PORT", "NOPORT")
    if port == "NOPORT":
            port = 80
    app.run('0.0.0.0', debug=True, port=int(port))
