from .models import Destinatario, EmailTracked
from os import environ, getenv, remove
from django.template import Template, Context
from mailjet_rest import Client
import traceback
from django.conf import settings

def send_tracked_email(destinatario:Destinatario, subject:str, email_template_path:str):
    """
    Envia um e-mail rastreado para um destinatário específico usando a API Mailjet.

    Parameters:
    - destinatario (Destinatario): O objeto Destinatario para quem o e-mail será enviado.
    - subject (str): O assunto do e-mail.
    - email_template_path (str): O caminho para o arquivo de template do e-mail.

    Returns:
    tuple: Um tuple contendo o código de status e o JSON de resposta da API.
    """
    email = EmailTracked.objects.create(dest=destinatario)
    secret = getenv("MAIL_PRIVATE")
    public = getenv("MAIL_PUBLIC")
    mailjet = Client(auth=(public, secret), version='v3.1')
    context = {
        'tracking_url': str(environ.get("NGROK_URL")) + f'/mail/track-email/{email.id}',
        'dest_name': destinatario.nome
    }
    try:
        with open (email_template_path, 'r') as file:
            template_content = file.read()
            template = Template(template_content)
            email_body = template.render(Context(context))
    except Exception as e:
        print(f"Exception as {e}")
    
    data = {
        'Messages': [
            {
                "From": {
                    "Email": getenv("EMAIL_HOST_USER"),
                    'Name': "Plataforma"
                },
                "To":[
                    {
                    'Email': destinatario.email,
                    'Name': destinatario.nome,
                    },
                ],
                'Subject': subject,
                'HTMLPart': email_body
            }
        ]
    }
    try:
        result = mailjet.send.create(data=data)
        result_json, status_code = result.json(), result.status_code
        status = result_json["Messages"][0]["Status"]
        if status == "success":
            email.sent = True
            email.save()
        return result.status_code, result.json()
    except Exception as e:
        traceback.print_exc()
        return print(f"Exception sending: {e}")


def send_custom_tracked_email(destinatario:Destinatario, subject:str, header:str, texto:str, img_base64:str, email_template_path:str):
    """
    Envia um e-mail customizado e rastreado para um destinatário específico usando a API Mailjet.

    Parameters:
    - destinatario (Destinatario): O objeto Destinatario para quem o e-mail será enviado.
    - subject (str): O assunto do e-mail.
    - header (str): O cabeçalho para o corpo do e-mail.
    - texto (str): O texto principal do e-mail.
    - img_base64 (str): A imagem a ser anexada no e-mail, codificada em base64.
    - email_template_path (str): O caminho para o arquivo de template do e-mail.

    Returns:
    tuple: Um tuple contendo o código de status e o JSON de resposta da API.
    """
    email = EmailTracked.objects.create(dest=destinatario)
    secret = getenv("MAIL_PRIVATE")
    public = getenv("MAIL_PUBLIC")
    mailjet = Client(auth=(public, secret), version='v3.1')
    context = {
        'tracking_url': str(environ.get("NGROK_URL")) + f'/mail/track-email/{email.id}',
        'header': header,
        'texto': texto,
    }
    try:
        with open (email_template_path, 'r') as file:
            template_content = file.read()
            template = Template(template_content)
            email_body = template.render(Context(context))
    except Exception as e:
        print(f"Exception as {e}")
    
    data = {
        'Messages': [
            {
                "From": {
                    "Email": getenv("EMAIL_HOST_USER"),
                    'Name': "Plataforma"
                },
                "To":[
                    {
                    'Email': destinatario.email,
                    'Name': destinatario.nome,
                    },
                ],
                'Subject': f"{destinatario.nome}, {subject}",
                'HTMLPart': email_body,
                "Attachments": [
                    {
                        "ContentType": "image/png",
                        "Filename": 'image',
                        "Base64Content": img_base64
                    }
                ]
            }
        ]
    }
    try:
        result = mailjet.send.create(data=data)
        result_json, status_code = result.json(), result.status_code
        status = result_json["Messages"][0]["Status"]
        if status == "success":
            email.sent = True
            email.save()
        return result.status_code, result.json()
    except Exception as e:
        traceback.print_exc()
        return print(f"Exception sending: {e}")
    

