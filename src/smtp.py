import smtplib

class SMTP:
    FROM = "domotic@iot.bzh"
    SERVER_HOST = "mail.ovh.iot"

    @classmethod
    def init(cls):
        cls.server = smtplib.SMTP(cls.SERVER_HOST)

    @classmethod
    def send_to(cls, to, subject, content):
        lines = [f"From: {cls.FROM}", f"To: {', '.join(to)}", f"Subject: {subject}"] + content.split("\n")
        msg = "\r\n".join(lines)
        cls.server.sendmail(cls.FROM, to, msg)