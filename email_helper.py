# Functions to support email

import smtplib
# import ssl

def send_mail(subject, body):
    # Sends an email with the input

    port = 25  # For SSL
    smtp_server = "smtp.envirosys.com"
    sender_email = "dadams@envirosys.com"  # Enter your address
    receiver_email = "dadams@envirosys.com"  # Enter receiver address
    message = 'Subject: {}\n\n{}'.format(subject, body)

    # msg = MIMEText(body)
    # msg['Subject'] = subject
    # msg['From'] = 'admin@example.com'
    # msg['To'] = 'info@example.com'

    # context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        # server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

send_mail('test email subject', 'test email body')
