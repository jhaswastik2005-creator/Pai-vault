import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", '"PAI Platform" <no-reply@paivoult.com>')

def send_otp_email(to_email: str, otp: str) -> bool:
    """
    Transmit an HTML email verification OTP code to the user.
    Falls back to console printing if SMTP configurations are missing.
    """
    normalized_to = to_email.lower().strip()
    
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto; padding: 30px; border: 1px solid #1e293b; background-color: #020617; color: #f8fafc; border-radius: 16px;">
      <h2 style="font-weight: 900; margin-bottom: 6px; font-size: 24px; color: #fbbf24; text-align: center; letter-spacing: -0.025em;">PAI<span style="color: #2dd4bf;">.</span></h2>
      <p style="text-align: center; font-size: 11px; font-weight: bold; color: #a78bfa; text-transform: uppercase; margin-bottom: 24px;">Post-AI Startup Network</p>
      
      <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1;">Hello,</p>
      <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1;">Use the following security authorization code to access your PAI dashboard. This code remains active for the next 10 minutes.</p>
      
      <div style="margin: 30px 0; text-align: center;">
        <span style="font-family: monospace; font-size: 32px; font-weight: 900; color: #ffffff; background-color: #0f172a; padding: 12px 24px; border-radius: 12px; border: 1px solid #334155; letter-spacing: 0.15em;">{otp}</span>
      </div>
      
      <p style="font-size: 12px; color: #64748b; line-height: 1.5; margin-top: 30px; border-top: 1px solid #1e293b; padding-top: 15px;">
        This email was transmitted dynamically for verification of login intent. If you did not trigger this request, you may securely disregard this message.
      </p>
    </div>
    """

    if SMTP_HOST and SMTP_USER and SMTP_PASS:
        try:
            # Set up message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"PAI Security Code: {otp}"
            msg["From"] = SMTP_FROM
            msg["To"] = normalized_to
            
            # Attach parts
            text_part = MIMEText(f"Your PAI security verification code is: {otp}", "plain")
            html_part = MIMEText(html_content, "html")
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Dispatch via SMTP server
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.ehlo()
            if SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, normalized_to, msg.as_string())
            server.quit()
            
            print(f"[SMTP] Successfully dispatched OTP email to {normalized_to}")
            return True
        except Exception as e:
            print(f"[SMTP ERROR] Failed to send verification email: {e}")
            
    # Fallback to local terminal print
    print("\n========================================")
    print(f"[PAI AUTH SIMULATION] OTP for {normalized_to}: {otp}")
    print("========================================\n")
    return False
