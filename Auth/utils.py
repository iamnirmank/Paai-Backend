from django.core.mail import EmailMessage
import random
import string
from Auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import string
import jwt
from rest_framework.response import Response
from rest_framework import status

from paAI import settings

def check_valid_request(room, auth_header):
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    parts = auth_header.split(' ')  
    token = parts[1] if len(parts) == 2 else None
    if not room or not token:
        return False
    decoded_token = jwt_decode_handler(token)
    user = User.objects.get(id=decoded_token['user_id'])
    if not user:
        return False
    if room.user != user:
        return False
    return True

def create_response(success, message, body=None, status_code=status.HTTP_200_OK):
        response_data = {'success': success, 'message': message}
        if body is not None:
            response_data['body'] = body
        return Response(response_data, status=status_code)

def jwt_encode_handler(user):
    """Generates a JWT access token with a set expiration time."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
        }

def jwt_decode_handler(token):
    """Decodes a JWT token and returns the payload."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

def send_verification_email(user, email):
    verification_code = ''.join(random.choices(string.digits, k=6))
    user.verification_code = verification_code
    user.save()
    subject = "User Verification"
    message = f"Your verification code is: {verification_code}"
    email = EmailMessage(subject, message, to=[email])
    email.send()

def send_verification_url(user):
    verification_code = ''.join(random.choices(string.digits, k=6))
    user.verification_code = verification_code
    user.save()
    code = verification_code + str(user.id)
    verification_url = f"{settings.BACKEND_URL}/api/auth/api/user/{code}/verify_url/"
    subject = "User Verification"
    message = f"Click the following link to verify your account: {verification_url}"
    email = EmailMessage(subject, message, to=[user.email])
    email.send()

def send_forgot_url(user, reset_token):
    verification_url = f"{settings.FRONTEND_URL}?reset_token={reset_token}"
    subject = "Reset Password"
    message = f"Click the following link to reset your password: {verification_url}"
    email = EmailMessage(subject, message, to=[user.email])
    email.send()

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def send_reset_email(email, reset_token):
    subject = "Password Reset"
    message = f"Use the following token to reset your password: {reset_token}"
    email = EmailMessage(subject, message, to=[email])
    email.send()

def upload_path(instance, filename):
    # Adjust the upload path to include content_id and filename
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return f'upload/{instance.__class__.__name__.lower()}/{random_string}+{filename}'

def get_user(email):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None