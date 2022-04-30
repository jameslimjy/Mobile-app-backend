import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

port = 465  # For SSL
password = 'iTown2@SG'
smtp_server = 'smtp.gmail.com'
sender_email = "itown2sg@gmail.com"

def send_email_otp(receiver_email, otp):
    ''' 
    Takes in an email address and OTP and sends an email to the email address containing the OTP
    '''
    message = MIMEMultipart("alternative")
    message["Subject"] = "iTown2@SG OTP Verification"
    message["From"] = sender_email
    message["To"] = receiver_email

    html = f"""
    <html>
    <body>
        <p>Hi there,<br>
        <br> 
            Here is your OTP: <br>
            {otp} <br>
            The OTP will expire after 2 minutes.
            <br>
        <br>
        Cheers, <br>
        The team at iTown2@SG
        </p>
    </body>
    </html>
    """

    # Convert to plain/html MIMEText objects
    part = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part)

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

