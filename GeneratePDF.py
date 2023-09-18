import os
import jinja2
import pdfkit
import random
import string
import cloudinary
from datetime import datetime
from cloudinary.uploader import upload
from EmailTestReport import EmailTeethTestReport

global patientGetDetails


def GeneratePDF(patientDetails, uploadedTestedImages, cloudinaryUploadFolder):
    global patientGetDetails
    print(cloudinaryUploadFolder)
    patientGetDetails = patientDetails
    PatientTestID = str(patientGetDetails["PT_ID"])
    PatientID = str(patientGetDetails["PT_PatientID"])
    Firstname = str(patientGetDetails["tblPatient"]["P_FirstName"])
    Lastname = str(patientGetDetails["tblPatient"]["P_LastName"])
    PhoneNumber = str(patientGetDetails["tblPatient"]["P_PhoneNumber"])
    EmailAddress = str(patientGetDetails["tblPatient"]["P_Email"])
    Gender = str(patientGetDetails["tblPatient"]["P_Gender"])
    Address = str(patientGetDetails["PatientAddress"]["Area"]) + ', ' + str(
        patientGetDetails["PatientAddress"]["City"]) + ', ' + str(patientGetDetails["PatientAddress"]["State"])
    Age = "22"
    DentistName = "Muhammad Shahzad"
    DentistPhoneNumber = "03312398777"
    Date = datetime.today().strftime("%d %b, %Y")
    Time = datetime.today().strftime("%I:%M:%S %p")
    patientImage = "https://dmswebappofficial.azurewebsites.net" + str(patientGetDetails["tblPatient"]["P_ProfileImage"]). \
        replace("~", "")
    DentistService = "Smelly Breath and Toothache"
    image_paths = uploadedTestedImages
    image_tags = ''
    for path in image_paths:
        image_tags += f'<img class="image-item" src="{path}" />'

    context = {'PatientTestID': PatientTestID, 'PatientID': PatientID, 'Firstname': Firstname, 'Lastname': Lastname,
               'PhoneNumber': PhoneNumber, 'EmailAddress': EmailAddress, 'Gender': Gender, 'Address': Address,
               'Age': Age, 'DentistName': DentistName,
               'DentistPhoneNumber': DentistPhoneNumber, 'Date': Date, 'patientImage': patientImage,
               'DentistService': DentistService, 'Time': Time, 'image_tags': image_tags}

    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)

    html_template = 'index.html'
    template = template_env.get_template(html_template)
    output_text = template.render(context)

    options = {
        'margin-top': '0',
        'margin-right': '0',
        'margin-bottom': '0',
        'margin-left': '0'
    }

    config = pdfkit.configuration(wkhtmltopdf='.\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    randomPDFName = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    output_pdf = os.getcwd() + "\\Teeth Test Report PDF\\" + 'Patient' + str(patientGetDetails["PT_PatientID"]) + '_' + \
                 randomPDFName + '.pdf'
    pdfkit.from_string(output_text, output_pdf, configuration=config, css='style.css', options=options)
    print("PDF Generated Successfully!")
    # Config Cloudinary
    cloudinary.config(
        cloud_name="dg5esqkeb",
        api_key="654286619656251",
        api_secret="7-JkBR5t_EU8lN3ArIdvsZ1txCw",
        secure=True
    )

    # Upload Detected Images PDF File in Cloudinary
    folderName = str(cloudinaryUploadFolder).replace("PatientUploaded", "PatientResults")
    randomImageName = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6)) + 'Patient' \
                      + PatientID
    result = upload(file=output_pdf, use_filename=True, unique_filename=False, tags="PatientOutputPDF", folder=folderName)
    EmailTeethTestReport(patientGetDetails, output_pdf, result['secure_url'])
