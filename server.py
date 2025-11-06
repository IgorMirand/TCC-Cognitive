from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import sendgrid
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

app = FastAPI(title="Cognitive Mail API", version="1.0")

# Modelo de dados recebido do app
class EmailRequest(BaseModel):
    email: EmailStr
    codigo: str
    psicologo: str

@app.get("/")
def home():
    return {"status": "ok", "message": "API Cognitive funcionando 🚀"}

@app.post("/send-invite")
def send_invite(request: EmailRequest):
    """Envia e-mail via SendGrid"""
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        remetente = os.getenv("EMAIL_SENDER")

        if not sg_api_key or not remetente:
            raise Exception("Configuração ausente: SENDGRID_API_KEY ou EMAIL_SENDER.")

        sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background:#f7f9fc; padding:20px;">
            <div style="max-width:600px;margin:auto;background:white;border-radius:8px;padding:20px;">
                <h2 style="color:#2563EB;text-align:center;">Convite Cognitive</h2>
                <p>Olá!</p>
                <p>O psicólogo <b>{request.psicologo}</b> convidou você para se juntar à plataforma <b>Cognitive</b>.</p>
                <p>Use este código de acesso ao criar sua conta:</p>
                <div style="font-size:28px;font-weight:bold;color:#2563EB;text-align:center;margin:16px 0;">
                    {request.codigo}
                </div>
                <a href="https://cognitive.app/register"
                   style="display:inline-block;background:#2563EB;color:white;
                          padding:10px 20px;border-radius:6px;text-decoration:none;">
                   Criar conta agora
                </a>
                <p style="margin-top:20px;">Obrigado por usar o Cognitive 💙</p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=remetente,
            to_emails=request.email,
            subject="Convite para a plataforma Cognitive",
            html_content=html
        )

        response = sg.client.mail.send.post(request_body=message.get())

        if response.status_code not in [200, 202]:
            raise Exception(f"SendGrid retornou {response.status_code}")

        return {"status": "success", "message": f"E-mail enviado para {request.email}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
