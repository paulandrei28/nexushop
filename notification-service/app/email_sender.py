import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


def send_order_confirmed_email(order_id: str, customer_email: str):
    """Send order confirmation email."""
    subject = f"Order Confirmed - {order_id}"
    html = f"""
    <html>
    <body>
        <h2>Order Confirmed!</h2>
        <p>Your order <strong>{order_id}</strong> has been confirmed.</p>
        <p>We are preparing your items for shipment.</p>
        <p>Thank you for shopping with NexuShop!</p>
    </body>
    </html>
    """
    _send_email(customer_email, subject, html)


def send_order_failed_email(order_id: str, customer_email: str, reason: str):
    """Send order failure notification email."""
    subject = f"Order Failed - {order_id}"
    html = f"""
    <html>
    <body>
        <h2>Order Could Not Be Processed</h2>
        <p>We are sorry, but your order <strong>{order_id}</strong> could not be completed.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p>Please try again or contact support.</p>
    </body>
    </html>
    """
    _send_email(customer_email, subject, html)


def _send_email(to: str, subject: str, html_body: str):
    """Send an email via SMTP (Mailhog in dev)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.sendmail(settings.FROM_EMAIL, [to], msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s: %s", to, subject)
