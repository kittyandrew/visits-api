from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
import os

MAIL_FROM = os.environ["MAIL_FROM"]
MAIL_PASS = os.environ["MAIL_PASS"]
MAIL_HOST = os.environ["MAIL_HOST"]
MAIL_PORT = int(os.environ["MAIL_PORT"])
# html hacks
TAB = "&nbsp;&nbsp;&nbsp;&nbsp;"
NEWLINE = "<br>"
wrap = lambda s: TAB + s + NEWLINE

async def send_email(email, ctx):
    message = MIMEMultipart()
    message["From"] = MAIL_FROM
    message["To"] = email
    message["Subject"] = f"Report for domain {ctx['domain']}"

    # Generating report body
    text = f"<b>{ctx['domain']}:</b>" + NEWLINE
    text += wrap(f"Total visits this month: <code>{ctx['total_visits']}</code>")
    text += wrap(f"Total unique visitors: <code>{ctx['unique_visitors']}</code>")
    if ctx["count"]:
        text += "<div style=\"text-align: center; margin-left: 20px;\">"
        text += "<table border=\"1\" cellspacing=\"2\" cellpadding=\"2\" class=\"dataframe\">"
        text += "<tr><th>#</th><th>Page</th><th>Visits</th></tr>"
        text += "<tbody>"
        for i, (path, visits) in enumerate(ctx["count"]):
            text += f"<tr><th>{i + 1}</th>"
            text += f"<td>{path}</td><td>{visits}</td>"
            text += f"</tr>"
        text += "</tbody></table></div>"

    # Add note about how many emails left
    text += NEWLINE + "<p style=\"font-size: 8px;\">"
    text += "<b>Note:</b> every user has certain amount of emails available to them every 30 minutes. "
    text += f"You have {ctx['emails_left']}, consider waiting some time before sending next request or "
    text += "<b>upgrade to premium</b>"
    text += "</p>"
        
    message.attach(MIMEText(f"<html><head></head><body>{text}</body></html>", "html", "utf-8"))
    await aiosmtplib.send(
        message,
        hostname=MAIL_HOST,
        port=MAIL_PORT,
        use_tls=True,
        username=MAIL_FROM,
        password=MAIL_PASS,
    )
