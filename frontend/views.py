from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect

from notification.email_utils import send_html_email
from .forms import ContactForm

def home_view(request):
    return render(request, 'frontend/index.html')

def about_view(request):
    return render(request, 'frontend/about.html')

# def contact_view(request):
#     return render(request, 'frontend/contact.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Collect all form data
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone = form.cleaned_data.get('phone', '')  # optional
            subject = form.cleaned_data.get('subject', '')  # optional
            topic = form.cleaned_data['topic']
            message = form.cleaned_data['message']

            try:
                # Send email to admin using your HTML template
                send_html_email(
                    subject=f"[Contact Form] {subject or topic}",
                    to_email=[settings.ADMIN_EMAIL],
                    template_name="notification/emails/contact_email.html",
                    context={
                        "username": username,
                        "email": email,
                        "phone": phone,
                        "subject": subject,
                        "topic": topic,
                        "message": message,
                        "site_name": settings.SITE_NAME,
                    },
                )
                messages.success(request, "Your message has been sent successfully!, support team will get back to you as soon as possible.")
                return redirect('frontend:contact')
            except Exception as e:
                messages.error(request, f"An error occurred while sending the message: {str(e)}")
    else:
        form = ContactForm()

    return render(request, 'frontend/contact.html', {'form': form})