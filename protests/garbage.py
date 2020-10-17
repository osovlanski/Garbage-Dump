#excel
import pandas as pd
import os
import io
import pdfkit
from shutil import copyfile
#from datetime import date

#email
import email, smtplib, ssl

from email.header import Header
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import listdir


dirname = os.path.dirname(__file__)
excel_path = os.path.join(dirname, 'input.xlsx')  # path to file + excel name
html_path = os.path.join(dirname, 'template.html')  # path to file + html name
pdfkit_config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
output_dir = os.path.join(dirname, 'output')

users = {}
def copy_resources_output():
   copyfile(os.path.join(dirname, 'logo.jpg'), os.path.join(output_dir, 'logo.jpg'))

subject = "An email with attachment from Python"
body = ""
sender_email = "itayosov@gmail.com"
receiver_email = "itayosov@gmail.com"
password = input("Type your password and press enter:")

def sendEmail(sender_email,f):
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))
    path = os.path.join(output_dir,f)
    with open(path, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream",)
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header('Content-Disposition', 'attachment',
                                  filename=(Header(f, 'utf-8').encode()))
    
    name = f.replace(".pdf","")
    message["Subject"] = f"דרוש מהפך - מכתב מאת {name}"

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)


def gen_report(data,template):
    print('generate pdf for {firstName} {lastName}'.format(firstName=data['שם פרטי'],lastName=data['שם משפחה']))
    #end if file exist
    fullName = data['שם פרטי'] + " " + data['שם משפחה']
    if os.path.isfile(os.path.join(output_dir,f'{fullName}')+'.pdf'):
        return

    userId = str(data['מספר תעודת זהות '])
    template = template.replace('{ID}', userId)
    template = template.replace('{USERNAME}',data['שם פרטי'] + " " + data['שם משפחה'])
    template = template.replace('{ADDRESS}', data['כתובת מגורים '])
    template = template.replace('{DATE}', str(data.name.strftime('%d/%m/%Y')))

    fileName = userId
    path = os.path.join(output_dir,f'{fileName}')

    with open(path+'.html', 'w', encoding='utf-8') as f:
        f.write(template) 

    options = {'enable-local-file-access': None}
    pdfkit.from_file(path+'.html',path+'.pdf', configuration=pdfkit_config, options=options)
    os.remove(path+'.html')
    #small fix due of language issue with pdfkit file name
    #maybe add ID to name as well
    os.rename(path+'.pdf',os.path.join(output_dir,f'{fullName}')+'.pdf')

def main():
    if not os.path.exists('output'):
        os.makedirs('output')

    copy_resources_output()

    print('read excel file')
    df = pd.read_excel(io=excel_path,index_col=0)
    
    with open(html_path,encoding="utf-8") as f:
        template = f.read()
        for _, row in df.head(3).iterrows():           
            gen_report(row,template)
   
    print('Done creating PDFs')
    print('sending emails')
    for f in listdir(output_dir):
        
        if not ''.join(f).endswith(".pdf"):
            continue    
        
        sendEmail(sender_email,f)
    print('Done sending emails')

if __name__ == "__main__":
    main()