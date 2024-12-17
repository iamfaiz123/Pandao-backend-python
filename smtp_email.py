import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
def load_html_template(content):
    file_path = "mail_templates/email_verification.html"
    try:
        with open(file_path, "r", encoding="utf-8") as file:  # Corrected line
            template = file.read()
            # Replace placeholders in the HTML template
            for key, value in content.items():
                template = template.replace(f"{{{{ {key} }}}}", value)
            return template
    except FileNotFoundError:
        print(f"this Error: File '{file_path}' not found.")
        return ""

def send_email():
    # SMTP credentials and server configuration
    SMTP_SERVER = "smtp-relay.brevo.com"  # Replace with your SMTP server
    SMTP_PORT = 587  # Usually 587 for TLS, 465 for SSL
    SMTP_USERNAME = "81dd53001@smtp-brevo.com"  # Replace with your username
    SMTP_PASSWORD = "FrnB7yLpxGmRkADU"  # Replace with your password

    # Email details
    sender_email = "iamfaizalkhn@gmail.com"  # Replace with sender's email
    recipient_email = "faizalkhn98641@gmail.com"  # Replace with recipient's email
    subject = "Test Email"
    html_body = load_html_template({"name":"faizal khan"})
    # mail_templates/email_verification.html
    try:
        # Create the email message
        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(html_body, "html"))
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Start TLS encryption
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


send_email()