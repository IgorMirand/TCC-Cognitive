from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import psycopg2
import os

# 🔹 Carrega variáveis do .env localmente
load_dotenv()

app = FastAPI(
    title="Cognitive Backend",
    description="API de envio de convites via SendGrid + PostgreSQL (Neon)",
    version="1.0.0"
)

# 🔹 Modelo de dados recebido no POST
class EmailRequest(BaseModel):
    email: EmailStr
    codigo: str
    psicologo: str

# 🔹 Rota de teste
@app.get("/")
def root():
    return {"message": "API Cognitive Online 🚀"}

# 🔹 Rota para envio de convite
@app.post("/send-invite")
def send_invite(data: EmailRequest):
    try:
        sender = os.getenv("EMAIL_SENDER")
        api_key = os.getenv("SENDGRID_API_KEY")

        if not sender or not api_key:
            raise HTTPException(status_code=500, detail="Variáveis de ambiente ausentes (EMAIL_SENDER, SENDGRID_API_KEY).")

        # HTML moderno
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background:#f7f9fc; padding:20px;">
            <div style="max-width:600px;margin:auto;background:white;border-radius:8px;padding:20px;">
                <h2 style="color:#2563EB;text-align:center;">Convite Cognitive</h2>
                <p>Olá!</p>
                <p>O psicólogo <b>{data.psicologo}</b> convidou você para participar da plataforma <b>Cognitive</b>.</p>
                <p>Use o código abaixo para criar sua conta:</p>
                <div style="font-size:28px;font-weight:bold;color:#2563EB;text-align:center;margin:16px 0;">
                    {data.codigo}
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
            from_email=sender,
            to_emails=data.email,
            subject="Convite para a plataforma Cognitive",
            html_content=html_content
        )

        sg = SendGridAPIClient(api_key)
        sg.send(message)

        return {"status": "OK", "message": f"Convite enviado para {data.email}"}

    except Exception as e:
        print(f"[ERRO NO ENVIO DE EMAIL] {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🔹 (Opcional) Conexão com Postgres (Neon)
@app.get("/test-db")
def test_db():
    try:
        conn = psycopg2.connect(os.getenv("NEON_DB_URL"))
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        data = cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "OK", "db_time": str(data[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao banco: {e}")
