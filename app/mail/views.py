from django.shortcuts import render, redirect
from .models import EmailTracked, Destinatario
from django.utils import timezone
from django.http import HttpResponse
from django import forms
from .funcs import send_tracked_email, send_custom_tracked_email
from os import listdir, path 
from django.conf import settings
import base64
import traceback
import csv
# Create your views here.

BASE_DIR = settings.BASE_DIR

def track_email_view(request, email_id):
    """
    obs. Só funciona em contas com alto grau de confiança em em provedores sérios como Gmail, Outlook.
    ## Rastreia a abertura de um e-mail por meio da inserção de um pixel transparente na mensagem de e-mail.
    Quando o e-mail é aberto, o pixel é carregado, acionando este endpoint que marca o e-mail como 'aberto'.

    Parameters:
    - request (HttpRequest): Objeto de solicitação HTTP do Django.
    - email_id (int): ID único do e-mail rastreado.

    Returns:
    HttpResponse: Uma imagem GIF transparente de 1x1 pixel.
    """
    try:
        email = EmailTracked.objects.get(pk=email_id)
        if not email.opened:
            email.opened_at = timezone.now()
            email.opened = True
            email.save()
            
    except EmailTracked.DoesNotExist:
        pass
    pixel_data = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    
    return HttpResponse(pixel_data, content_type='image/gif')


class EmailSubjectForm(forms.Form):
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        "placeholder": "Subject",
        "name": "subject"
    }))

def send_emails_view(request):
    """
    ## Envia um e-mail rastreado para um destinatário específico usando a API Mailjet.

    Parameters:
    - destinatario (Destinatario): O objeto Destinatario para quem o e-mail será enviado.
    - subject (str): O assunto do e-mail.
    - email_template_path (str): O caminho para o arquivo de template do e-mail.

    ## Returns:
    tuple: Um tuple contendo o código de status e o JSON de resposta da API.
    """
    selected_ids = request.session.get("selected_dest_ids")

    if not selected_ids:
        return redirect("admin:mail_Destinatario_changelist")
    
    if request.method == "POST":
        form = EmailSubjectForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            email = request.POST.get("email")
            if email != None:
                queryset = Destinatario.objects.filter(id__in=selected_ids)
                for dest in queryset:
                    send_tracked_email(dest, subject, f"{BASE_DIR}/mail/emails/{email}")

    emails_templates = [f for f in listdir(f"{BASE_DIR}/mail/emails") if f.endswith(".html")]
    form = EmailSubjectForm()
    context = {
        "templates": emails_templates,
        "form": form
    }
    return render(request, "mail/send_email_form.html", context)

class CustomEmailForm(forms.Form):
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        "placeholder": "Subject",
        "name": "subject"
    }))
    header = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        "placeholder": "Header",
        "name": "subject"
    }))
    image = forms.ImageField(widget=forms.FileInput)
    texto = forms.CharField(max_length=1000 ,widget=forms.Textarea(attrs={
        "placeholder": "Texto",
        "name": "texto"
    }))

def send_custom_emails_view(request):
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
    selected_ids = request.session.get("selected_dest_ids")

    if not selected_ids:
        return redirect("admin:mail_Destinatario-changelist")

    if request.method == "POST":
        form = CustomEmailForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                email = request.POST.get("email")
                subject = form.cleaned_data['subject']
                header = form.cleaned_data['header'] 
                texto = form.cleaned_data['texto']        
                image = form.cleaned_data.get('image')
                image_path = path.join(f'{BASE_DIR}/mail/static/images/', image.name)
                with open(image_path, "wb+") as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                with open(f'{BASE_DIR}/mail/static/images/{image.name}', "rb") as image_file:
                    img_base64 = base64.b64encode(image_file.read()).decode("utf-8")

                if email != None:
                    queryset = Destinatario.objects.filter(pk__in=selected_ids)
                    for dest in queryset:
                        send_custom_tracked_email(dest, subject,header, texto, img_base64, f"{BASE_DIR}/mail/emails/custom/{email}")
            except Exception as e:
                traceback.print_exc()
                print(f'Erro email custom: {e}')

                        
                
    emails_templates = [f for f in listdir(f"{BASE_DIR}/mail/emails/custom") if f.endswith(".html")]
    form = CustomEmailForm()
    context = {
        "templates": emails_templates,
        "form": form
    }
    return render(request, "mail/send_email_form.html", context)


def create_csv_file(request):
    '''
    # Função: `create_csv_file`

    ## Descrição
    A função `create_csv_file` é uma view do Django que gera um arquivo CSV contendo detalhes dos emails rastreados.
    O arquivo CSV é então enviado ao cliente como anexo.

    ## Parâmetros
    - **request**: O objeto de solicitação HTTP do cliente. Esta função espera uma variável de sessão `'selected_emails_ids'`
      a ser definido. Esta variável de sessão deve conter uma lista de chaves primárias (`ids`) dos emails que serão incluídos no arquivo CSV.

    ## Saída
    - Um objeto de resposta HTTP que contém o arquivo CSV como anexo. O arquivo CSV inclui as seguintes colunas:
        - Identificação do email
        - E-mail do destinatário
        - Destino Nome
        - Tentativa de envio
        - Enviado
        -Aberto
        - Dados de abertura

    ## Exemplo de uso
    ```python
    # Suponha que definimos request.session['selected_emails_ids'] = [1, 2, 3]
    resposta = create_csv_file(solicitação)
    ```

    ## Observação
    - Certifique-se de que a variável de sessão `'selected_emails_ids'` esteja definida antes de chamar esta função.
    '''

    ids = request.session.get('selected_emails_ids')
    emails = EmailTracked.objects.filter(pk__in=ids)
    
    resposta = HttpResponse(content_type='texto/csv')
    resposta['Content-Disposition'] = "anexo; nome do arquivo='emails.csv'"
    
    escritor = csv.writer(resposta)
    escritor.writerow(['Email ID', 'Destinatário Email', 'Destinatário Nome', 'Tentativa de envio', 'Enviado', 'Aberto', 'Dados de abertura'])
    ids = request.session.get('selected_emails_ids')
    emails = EmailTracked.objects.filter(pk__in=ids)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = "attachment; filename='emails.csv'"
    writer = csv.writer(response)
    writer.writerow(['Email ID', 'Destinatario Email', 'Destinatario Nome',  'Tentativa de envio', 'Enviado', 'Aberto', 'Data de abertura']) 

    for email in emails:
        writer.writerow([email.id, email.dest.email, email.dest.nome, email.sent_try, email.sent, email.opened, email.opened_at])
    return response
    