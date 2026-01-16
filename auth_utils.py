import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def verify_password(plain_password, hashed_password):
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

# JWT Token
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this") # Ensure this is in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Email Verification
def send_verification_email(email_to: str, token: str):
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    sender_email = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    
    if not sender_email or not password:
        print("Email credentials not set. Skipping email sending.")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your account - JKKNIU Helpdesk"
    message["From"] = sender_email
    message["To"] = email_to

    # Verify link (assuming frontend runs on localhost:5173 by default or configured URL)
    # The user clicks this, frontend calls backend verify endpoint
    # Or simplified: backend verification link directly.
    # Let's verify via frontend to keep flow clean: Frontend verifies then tells user "Verified"
    # Actually, simpler to click link -> Backend verifies -> Redirects or shows "Verified"
    # But for SPA, usually Link -> Frontend Page -> API Call
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    verify_url = f"{frontend_url}/verify-email?token={token}"

    text = f"""\
    Hi,
    Thank you for registering at JKKNIU Helpdesk.
    Please click the link below to verify your account:
    {verify_url}
    """
    html = f"""\
    <html>
      <body>
        <p>Hi,<br>
           Thank you for registering at JKKNIU Helpdesk.<br>
           Please click the link below to verify your account:<br>
           <a href="{verify_url}">Verify Email</a>
        </p>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, email_to, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
