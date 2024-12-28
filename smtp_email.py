from collections import defaultdict

import resend

resend.api_key = "re_8ZzRzVuc_FNfi9V9Kk8o6QjiA4FUsHGDw"
def load_html_template(content,email_type):
    file_path = None
    match email_type:
        case 'proposal_execute':
          file_path = "mail_templates/proposal_execute.html"
        case 'email_verification':
            file_path = "mail_templates/email_verification.html"
        case 'welcome':
            file_path = "mail_templates/welcome.html"
        case _ :
            print("unkown email type")
            return ""
    try:
        with open(file_path, "r", encoding="utf-8") as file:  # Corrected line
            template = file.read()
            # Replace placeholders in the HTML template
            for key, value in content.items():
                template = template.replace(f"{{{{ {key} }}}}", str(value))
            return template
    except FileNotFoundError:
        print(f"this Error: File '{file_path}' not found.")
        return ""

def send_email(email_type:str,email_object,user_mail:str):
    html_body = load_html_template(email_object,email_type)
    try:
        subject = None
        match email_type:
            case 'proposal_execute':
                subject = "proposal executed"
            case 'email_verification':
                subject = "Pandao email verification"
            case 'welcome':
                subject = "Welcome to Pandao"
            case _:
                print("unkown email type")
                return ""

        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": user_mail,
            "subject": subject,
            "html": f"{html_body}"
        })
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
