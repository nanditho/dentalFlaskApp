import os
import time
import urllib
import requests
import threading
from flask import Flask, jsonify
from flask_restx import Api, Resource
from TeethDetection import TeethDetection
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='V1', title='Patient Test API',
          description='A simple Patient Test API',
          url_scheme=app.url_map,
          prefix='')

ns = api.namespace('api', description='Patient Test Operations')
patient = api.model('Patient', {})

testImagesDir = ""
resultImagesDir = ""
cloudinaryUploadFolder = ""
patientDetails = {}


def InitiateDirectories(patient_id):
    global testImagesDir, resultImagesDir
    patientDir = time.strftime("%M%S", time.localtime()) + "Patient" + str(patient_id)
    testImagesDir = "\\PatientTeethDetection\\" + patientDir + "\\PatientUploaded"
    os.makedirs(os.getcwd() + testImagesDir)
    resultImagesDir = "\\PatientTeethDetection\\" + patientDir + "\\PatientResults"
    os.makedirs(os.getcwd() + resultImagesDir)
    print('Directories created!')


def download(result):
    for i in range(len(result)):
        urllib.request.urlretrieve(result[i], os.getcwd() + testImagesDir + f'\\image-{i}.jpg')
    print('Image download completed.')
    threading.Thread(target=TeethDetection, args=(testImagesDir, resultImagesDir, cloudinaryUploadFolder,
                                                  patientDetails)).start()


def get_patient(patient_id):
    global cloudinaryUploadFolder, patientDetails
    if patient_id > 0 and patient_id is not None:
        api_url = 'https://dmswebapi.azurewebsites.net/api/Get/PatientWantTest?patientTestID=' + str(patient_id)
        response = requests.get(api_url)
        if response.status_code == 200:
            patient_data = response.json()
            if patient_data["Datalist"] is not None:
                result = patient_data["Datalist"]["Images"]
                if result is not None:
                    cloudinaryUploadFolder = patient_data["Datalist"]["PT_Images"]
                    patientDetails = patient_data["Datalist"]
                    InitiateDirectories(patient_id)
                    threading.Thread(target=download, args=(result,)).start()
                    return jsonify(
                        {'Status': 'Success', 'StatusCode': '200',
                         'Message': 'Record exists. Image download initiated.'})
                else:
                    return jsonify(
                        {'Status': 'No-Content', 'StatusCode': '204', 'Message': 'Record exists. No images found.'})
            else:
                return jsonify(
                    {'Status': 'Error Not Found', 'StatusCode': '404', 'Message': 'Record does not exist.'})
        else:
            return jsonify(
                {'Status': 'Internal Server Error', 'StatusCode': '500', 'Message': 'Error in retrieving data.'})
    else:
        return jsonify(
            {'Status': 'Internal Server Error', 'Status Code': '504', 'Message': 'Please provide patient id.'})


@ns.route('/patientTeethTest/<int:patient_id>')
@ns.response(200, 'Patient found')
@ns.response(204, 'Patient found but no images found')
@ns.response(404, 'Patient not found')
@ns.response(500, 'Internal Server Error')
@ns.param('patient_id', 'The Patient identifier')
class Patient(Resource):
    @ns.doc('get_patient')
    def get(self, patient_id):
        return get_patient(patient_id)


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))