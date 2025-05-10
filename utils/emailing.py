import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(subject, body, sender, sender_password, recipient, sender_name=None, html=False):
    if html:
        msg = MIMEText(body, 'html')
    else:
        msg = MIMEText(body)
    msg['Subject'] = subject
    if sender_name:
        msg['From'] = f"{sender_name} <{sender}>"
    else:
        msg['From'] = sender
    msg['To'] = recipient
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, sender_password)
       smtp_server.sendmail(sender, recipient, msg.as_string())

def send_access_code(access_code, user_email):
    """
    Send an access code email to the user.
    
    Args:
        access_code (str): The 6-digit access code to send
        user_email (str): The recipient's email address
    """
    sender = 'build.ai.tutors@gmail.com'
    sender_password = os.environ['EMAIL_PASSWORD']
    subject = 'Playlab Courses: Your Access Code'
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Welcome to Playlab Courses! 👋</h2>
        
        <p style="color: #34495e; font-size: 16px; line-height: 1.5;">
            Your access code is: <strong style="font-size: 24px; color: #2c3e50;">{access_code}</strong>
        </p>
        
        <p style="color: #34495e; font-size: 16px; line-height: 1.5;">
            Please return to your previous tab to verify your access code.
        </p>
        
        <div style="margin-top: 30px; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="margin: 0;">Best regards,</p>
            <p style="margin: 5px 0;">Playlab Courses Team 🎓</p>
        </div>
    </div>
    """
    
    send_email(subject, body, sender, sender_password, user_email, sender_name='Playlab Courses', html=True)

def send_email_support(user_email, message):
    sender = 'build.ai.tutors@gmail.com'
    recipient = 'build.ai.tutors@gmail.com'
    sender_password = os.environ['EMAIL_PASSWORD']

    subject = 'Playlab Courses: User Support'
    #message = message.replace('\n', '<br>')
    body = 'User: ' + user_email + '\n\n' + message
    send_email(subject, body, sender, sender_password, recipient)