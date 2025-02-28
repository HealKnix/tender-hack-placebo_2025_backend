import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from platform import python_version

server = "smtp.mail.ru"
user = "test@mail.ru"
password = "XXX"

recipients = "www.test@gmail.com"
sender = user
subject = "Тема сообщения"
text = "Текст сообщения"
html = "<html><head></head><body><p>" + text + "</p></body></html>"

msg = MIMEMultipart("alternative")
msg["Subject"] = subject
msg["From"] = "Python script <" + sender + ">"
msg["To"] = recipients
msg["Reply-To"] = sender
msg["Return-Path"] = sender
msg["X-Mailer"] = "Python/" + (python_version())

part_text = MIMEText(text, "plain")

msg.attach(part_text)

mail = smtplib.SMTP_SSL(server)
mail.login(user, password)
mail.sendmail(sender, recipients, msg.as_string())
mail.quit()
