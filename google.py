import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import googleapiclient.discovery
from google.oauth2 import service_account

# Load your Google Cloud credentials
credentials = service_account.Credentials.from_service_account_file(
    'path/to/your/credentials.json'
)

# Define your Gmail API service
service = googleapiclient.discovery.build('gmail', 'v1', credentials=credentials)

def send_email(sender_email, recipient_email, subject, body):
    """Sends an email using the Gmail API."""

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    # Create the message body
    message.attach(MIMEText(body, 'plain'))

    # Encode the message in base64
    raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
    raw_message = raw_message.decode('ascii')

    # Send the email
    try:
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        print('Email sent successfully!')
    except Exception as e:
        print(f'Error sending email: {e}')

# Example usage
sender_email = 'iamfaizalkhn@gmail.com'
recipient_email = 'faizalkhn98641@gmail.com'
subject = 'Test Email from Python'
body = 'This is a test email sent using the Gmail API.'

send_email(sender_email, recipient_email, subject, body)
