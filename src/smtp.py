import smtplib

class SMTP:
    FROM = "domotic@iot.bzh"
    SERVER_HOST = "mail.ovh.iot"

    @classmethod
    def init(cls):
        # cls.server = smtplib.SMTP(cls.SERVER_HOST)
        pass

    @classmethod
    def send_to(cls, to, subject, content):
        with smtplib.SMTP(cls.SERVER_HOST) as server:
            lines = [f"From: {cls.FROM}", f"To: {', '.join(to)}", f"Subject: {subject}"] + content.split("\n")
            msg = "\r\n".join(lines)
            server.sendmail(cls.FROM, to, msg)