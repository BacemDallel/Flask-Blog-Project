import smtplib

class EmailSender:
    def __init__(self, email):
        self.sender_email = 'YOUR EMAIL'
        self.receiver_email = email
        self.password = 'YOUR EMAIL PROJECT PASSWORD'

    def send_email(self, token):

        email_text = f"""
        From: Super Blog resetting service
        
        We received a request to reset your Blog password.\n
        Enter the following password reset code: {token}
        """

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_email, email_text)
            server.quit()
            return True  # Email sent successfully
        except Exception as e:
            return False  # Failed to send email
