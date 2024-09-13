from django.core.mail import EmailMessage
import random
import string
from Auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from rest_framework.response import Response
from rest_framework import status
from paAI import settings

# Helper functions
def generate_code(length=6, characters=string.digits):
    """Generates a random code of specified length."""
    try:
        return ''.join(random.choices(characters, k=length))
    except Exception as e:
        return None  

def send_email(subject, message, recipient):
    """Sends an email with the given subject, message, and recipient."""
    try:
        email = EmailMessage(subject, message, to=[recipient])
        email.send()
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def jwt_encode_handler(user):
    """Generates JWT access and refresh tokens for the user."""
    try:
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    except Exception as e:
        return None  
def jwt_decode_handler(token):
    """Decodes a JWT token and returns its payload."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        return None  

def create_response(success, message, body=None, status_code=status.HTTP_200_OK):
    """Creates a standardized response format."""
    try:
        response_data = {'success': success, 'message': message}
        if body:
            response_data['body'] = body
        return Response(response_data, status=status_code)
    except Exception as e:
        return Response({'success': False, 'message': f"Error creating response: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Email-related functions
def send_verification_email(user, email):
    """Sends a verification code via email."""
    try:
        verification_code = generate_code()
        user.verification_code = verification_code
        user.save()
        subject = "User Verification"
        message = f"Your verification code is: {verification_code}"
        send_email(subject, message, email)
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")

def send_verification_url(user):
    """Sends a verification URL via email."""
    try:
        verification_code = generate_code()
        user.verification_code = verification_code
        user.save()
        code = f"{verification_code}{user.id}"
        verification_url = f"{settings.BACKEND_URL}/api/auth/api/user/{code}/verify_url/"
        subject = "User Verification"
        message = f"Click the following link to verify your account: {verification_url}"
        send_email(subject, message, user.email)
    except Exception as e:
        print(f"Error sending verification URL: {str(e)}")

def send_forgot_url(user, reset_token):
    """Sends a password reset URL via email."""
    try:
        verification_url = f"{settings.FRONTEND_URL}?reset_token={reset_token}"
        subject = "Reset Password"
        message = f"Click the following link to reset your password: {verification_url}"
        send_email(subject, message, user.email)
    except Exception as e:
        print(f"Error sending forgot URL: {str(e)}")

def send_reset_email(email, reset_token):
    """Sends a password reset token via email."""
    try:
        subject = "Password Reset"
        message = f"Use the following token to reset your password: {reset_token}"
        send_email(subject, message, email)
    except Exception as e:
        print(f"Error sending reset email: {str(e)}")

# Utility functions
def check_valid_request(room, auth_header):
    """Validates if the request is valid based on room and JWT token."""
    try:
        if not auth_header or not auth_header.startswith('Bearer '):
            return False

        token = auth_header.split(' ')[1] if len(auth_header.split(' ')) == 2 else None
        if not room or not token:
            return False

        decoded_token = jwt_decode_handler(token)
        if not decoded_token:
            return False

        user = User.objects.get(id=decoded_token['user_id'])
        return room.user == user
    except User.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error validating request: {str(e)}")
        return False

def upload_path(instance, filename):
    """Generates a unique file path for uploaded files."""
    try:
        random_string = generate_code(16, string.ascii_lowercase + string.digits)
        return f'upload/{instance.__class__.__name__.lower()}/{random_string}+{filename}'
    except Exception as e:
        print(f"Error generating upload path: {str(e)}")
        return None

def get_user(email):
    """Fetches a user by email, or returns None if not found."""
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None

def get_user_from_token(request):
    """Extracts and returns the user from the JWT token in the request header."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1] if len(auth_header.split(' ')) == 2 else None
        if not token:
            return None

        decoded_token = jwt_decode_handler(token)
        return User.objects.get(id=decoded_token['user_id'])
    except User.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error extracting user from token: {str(e)}")
        return None

def create_response(success, message, body=None, status_code=status.HTTP_200_OK):
    try:
        response_data = {'success': success, 'message': message}
        if body is not None:
            response_data['body'] = body
        return Response(response_data, status=status_code)
    except Exception as e:
        error_message = f"Error creating response: {str(e)}"
        return Response({'success': False, 'message': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def check_auth(room, auth_header):
    """
    Check if the request is valid and authorized based on the room and the authorization header.
    """
    check = check_valid_request(room, auth_header)
    if not check:
        return create_response(
            success=False, 
            message='Unauthorized request', 
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    return check