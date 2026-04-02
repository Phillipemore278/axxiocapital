from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_html_email(
    subject: str,
    to_email: list[str],
    template_name: str,
    context: dict,
    from_email: str | None = None,
    fail_silently: bool = False,
):
    """
    Send an email with both HTML and plain-text content.

    :param subject: Email subject
    :param to_email: List of recipient emails
    :param template_name: HTML template path (e.g. 'emails/welcome.html')
    :param context: Context dictionary for template rendering
    :param from_email: Optional sender email
    :param fail_silently: Whether to suppress exceptions
    """

    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    # Render HTML content
    html_content = render_to_string(template_name, context)

    # Create plain-text version from HTML
    text_content = strip_tags(html_content)

    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=to_email,
    )

    # Attach HTML version
    email.attach_alternative(html_content, "text/html")

    # Send email
    email.send(fail_silently=fail_silently)


# hopw to call
# send_html_email(
#     subject="Welcome to Our Platform",
#     to_email=["user@example.com"],
#     template_name="emails/welcome.html",
#     context={
#         "user_name": "Alex",
#         "login_url": "https://example.com/login",
#     },
# )