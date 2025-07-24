import smtplib
import logging
from src.settings import Settings

class SMTP:
    @classmethod
    def send_to(cls, to, subject, content):
        server_host = Settings.get("smtp_server")
        from_email = Settings.get("smtp_from_email")

        if not server_host or not from_email:
            logging.warning("SMTP Server is not configured.")
            return 

        with smtplib.SMTP(server_host) as server:
            lines = [f"From: {from_email}", f"To: {', '.join(to)}", f"Subject: {subject}"] + content.split("\n")
            msg = "\r\n".join(lines)
            server.sendmail(from_email, to, msg)