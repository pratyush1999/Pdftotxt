import json
import os
from flask import Flask
from flask import request
from txt_extracter import PdfTxtExtract


LOG_ENABLE = os.environ["DEPLOYED"] if "DEPLOYED" in os.environ else ''

if LOG_ENABLE == "1":
    from logger import Logger
    LOG = Logger(os.getenv('LOGGER_ADDR'))


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
    temp = request.get_json()
    content = json.loads(temp)
    pdfs = content['pdfs']
    txts = []
    for pdf in pdfs:
        pdftotxt_extract = PdfTxtExtract(pdf)
        txts.append(pdftotxt_extract.extract_text())
    output = {}
    output['pdfs'] = txts

    if LOG_ENABLE == "1":
        LOG.info('pdf_to_txt', 'POST', 'NULL', 'NULL',
                 'Text generated from PDF successfully')
    return json.dumps(output)


if __name__ == '__main__':

    port = os.getenv("URL_PORT", "NOPORT")
    if port == "NOPORT":
        port = 80
    app.run('0.0.0.0', debug=True, port=int(port))
