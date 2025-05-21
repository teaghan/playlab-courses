import os
import smtplib
from email.mime.text import MIMEText
from utils.core.config import open_config

def send_email(subject, body, sender, sender_password, recipient, sender_name=None, html=False, headers=None):
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
    
    # Add any additional headers
    if headers:
        for key, value in headers.items():
            msg[key] = value
            
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, sender_password)
       smtp_server.sendmail(sender, recipient, msg.as_string())

def send_access_code(access_code, user_email):
    """
    Send an access code email to the user, with both plain-text and HTML formats.
    """
    config = open_config()['email']
    sender = config['email']
    sender_password = os.environ['EMAIL_PASSWORD']
    subject = 'OpenCource: Your Access Code'

    # Plain-text fallback
    body = f"Welcome to OpenCource! \n\n\tYour access code is: {access_code}\n\n" \
                 "Please return to your previous tab to verify your access code.\n\n" \
                 "Best regards,\nOpenCource Team"

    send_email(subject, body, sender, sender_password, user_email, html=False, sender_name='OpenCource')

def send_error_email(traceback, session_state):
    """
    Send an error notification email with traceback and session state information.
    
    Args:
        traceback (str): The error traceback information
        session_state (dict): The current session state information
    """
    sender = open_config()['email']['email']
    recipient = open_config()['email']['email']
    sender_password = os.environ['EMAIL_PASSWORD']
    
    subject = 'OpenCource: Error Notification 🚨'
    
    # Format session state for better readability
    session_state_str = '\n'.join([f"{k}: {v}" for k, v in session_state.items()])
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #e74c3c;">Error Notification 🚨</h2>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
            <h3 style="color: #2c3e50; margin-top: 0;">Traceback:</h3>
            <pre style="background-color: #fff; padding: 10px; border-radius: 3px; overflow-x: auto;">
{traceback}
            </pre>
        </div>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #2c3e50; margin-top: 0;">Session State:</h3>
            <pre style="background-color: #fff; padding: 10px; border-radius: 3px; overflow-x: auto;">
{session_state_str}
            </pre>
        </div>
        
        <div style="margin-top: 30px; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="margin: 0;">This is an automated error notification.</p>
            <p style="margin: 5px 0;">OpenCource System 🎓</p>
        </div>
    </div>
    """
    
    send_email(subject, body, sender, sender_password, recipient, sender_name='OpenCource System', html=True)

def send_email_support(user_email, message):
    sender = open_config()['email']['email']
    recipient = open_config()['email']['email']
    sender_password = os.environ['EMAIL_PASSWORD']

    subject = 'OpenCource: User Support'
    #message = message.replace('\n', '<br>')
    body = 'User: ' + user_email + '\n\n' + message
    send_email(subject, body, sender, sender_password, recipient)