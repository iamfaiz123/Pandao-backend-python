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
        case _ :
            print("unkown email type")
            return ""
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

def send_email(email_type:str,email_object,user_mail:str):
    if email_type != 'proposal_execute':
        print('invalid email_type, expected [proposal_execute]')
        return
    html_body = load_html_template(email_object,email_type)
    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": user_mail,
            "subject": "Proposal executed",
            "html": f"{html_body}"
        })

        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
