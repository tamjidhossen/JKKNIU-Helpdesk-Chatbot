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
    Welcome to JKKNIU Helpdesk!
    Please verify your email address to continue:
    {verify_url}
    
    If you did not request this, please ignore this email.
    """
    
    # Use university logo execution for sender profile pic (via Gravatar or internal styling if supported by client, 
    # but here we embed it in the HTML header or just make it look good).
    # Since we can't easily set the "sender profile pic" in protocol without Gravatar/BIMI, we'll make the email body look like a branded card.
    
    html = f"""\
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background_color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border: 1px solid #e0e0e0;
            }}
            .header {{
                background-color: #1f2937; /* Dark slate */
                padding: 30px;
                text-align: center;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                background-color: white;
                border-radius: 50%;
                padding: 10px;
                object-fit: contain;
            }}
            .content {{
                padding: 40px 30px;
                color: #333333;
                text-align: center;
            }}
            .title {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #111827;
            }}
            .text {{
                font-size: 16px;
                line-height: 1.6;
                color: #4b5563;
                margin-bottom: 30px;
            }}
            .button {{
                display: inline-block;
                background-color: #2563eb; /* Blue 600 */
                color: white;
                padding: 14px 28px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                transition: background-color 0.2s;
            }}
            .button:hover {{
                background-color: #1d4ed8;
            }}
            .footer {{
                background-color: #f9fafb;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #9ca3af;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <!-- Using a placeholder or public URL for logo if available, otherwise just text/icon -->
                 <img src="https://jkkniu.edu.bd/assets/img/main-logo-white.png" alt="JKKNIU Logo" class="logo"> 
            </div>
            <div class="content">
                <h1 class="title">Verify Your Email</h1>
                <p class="text">
                    Hi there,<br><br>
                    Welcome to the <strong>JKKNIU Helpdesk</strong>! We're excited to have you on board.<br>
                    Please verify your email address to unlock full access to the AI assistant.
                </p>
                <a href="{verify_url}" class="button">Verify My Account</a>
                <p class="text" style="font-size: 14px; margin-top: 30px; color: #6b7280;">
                    Or copy this link to your browser:<br>
                    <a href="{verify_url}" style="color: #2563eb;">{verify_url}</a>
                </p>
            </div>
            <div class="footer">
                &copy; {datetime.now().year} Jatiya Kabi Kazi Nazrul Islam University. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, email_to, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

def send_password_reset_email(email: str, token: str):
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    sender_email = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    
    if not sender_email or not password:
        print("Email credentials not set. Skipping email sending.")
        # For dev/testing, print the link
        print(f"RESET LINK: http://localhost:5173/reset-password?token={token}")
        return True # Return true to simulate success in dev

    msg = MIMEMultipart("alternative")
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Reset Your Password - JKKNIU Helpdesk"

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={token}"

    text = f"Reset your password here: {reset_url}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background-color: #2c3e50; padding: 20px; text-align: center; }}
            .logo {{ max-height: 60px; }}
            .content {{ padding: 30px; color: #333333; line-height: 1.6; text-align: center; }}
            .title {{ color: #2c3e50; margin-top: 0; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #3498db; color: #ffffff; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 20px; }}
            .footer {{ background-color: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                 <img src="https://jkkniu.edu.bd/assets/img/main-logo-white.png" alt="JKKNIU Logo" class="logo"> 
            </div>
            <div class="content">
                <h1 class="title">Reset Your Password</h1>
                <p>Hi there,<br><br>We received a request to reset your password for your JKKNIU Helpdesk account. If you didn't make this request, you can safely ignore this email.</p>
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button" style="color: #ffffff;">Reset Password</a>
                </div>
                <p style="margin-top: 20px; font-size: 12px; color: #777;">This link will expire soon.</p>
            </div>
            <div class="footer">
                &copy; {datetime.now().year} JKKNIU Helpdesk. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        print(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False
