import ssl
import smtplib
import requests
from email import encoders
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def EmailTeethTestReport(patientDetails, PDFPath, PDFUrl):
    subject = "Dental Teeth Test Report"
    body = f'''<html><body>
    <p><b>Dear {str(patientDetails["tblPatient"]["P_FirstName"])},</b></p>
    <p>I hope this email finds you well. I am writing to provide you with a brief summary of the dental teeth test report
    conducted on {datetime.today().strftime("%d %b, %Y")}. The results of the examination is attached on the Email!</p>

    <p>If you have any questions or require further information, please do not hesitate to contact me. <br>
    Thank you for your attention to this matter.</p>

    <p><b>Best regards,</b><br>
    Denticon Support</p>
    </body></html>
    '''
    sender_email = "saafali804@gmail.com"
    receiver_email = str(patientDetails["tblPatient"]["P_Email"])
    password = "diiouqkyebkiblku"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "html"))

    filename = PDFPath  # In same directory as script

    # Open PDF file in binary mode
    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    pdfFileName = "Patient" + str(patientDetails["tblPatient"]["P_ID"]) + ".pdf"
    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {pdfFileName}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
    print("Email send successfully!")
    PatientTestID = str(patientDetails["PT_ID"])
    PatientID = str(patientDetails["PT_PatientID"])
    UpdatePdfFileURL(PatientTestID, PDFUrl, PatientID)


def UpdatePdfFileURL(PatientTestID, PdfURL, PatientID):
    url = "https://dmswebapi.azurewebsites.net/api/Update/PatientTest"

    payload = 'PT_Pdf=' + PdfURL + '&PT_ID=' + PatientTestID + '&PT_PatientID=' + PatientID + '&PT_Images=Abc&ImagesCount=5'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    print("Database Updated Successfully!")
