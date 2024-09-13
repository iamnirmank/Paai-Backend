import os
from django.shortcuts import redirect
from Chatmate.Utility.groq_response import generate_response_with_llama
from paAI import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import Feedback, User
from .serializers import UserSerializer, FeedbackSerializer
from .utils import (
    get_user, get_user_from_token, jwt_encode_handler, generate_code, 
    create_response, send_forgot_url, send_verification_url
)
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    @action(detail=False, methods=['POST'])
    def register(self, request):
        """Registers a new user and sends a verification URL."""
        try:
            serializer = UserSerializer(data=request.data)

            if serializer.is_valid():
                serializer.validated_data['password'] = make_password(request.data.get('password'))
                user = serializer.save()
                send_verification_url(user)
                return create_response(
                    True, 
                    'User registered successfully. Please check your email for verification instructions.',
                    UserSerializer(user).data,
                    status.HTTP_201_CREATED
                )

            return create_response(False, serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_response(False, f'Error registering user: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def login(self, request):
        """Authenticates a user and returns JWT tokens."""
        try:
            email, password = request.data.get('email'), request.data.get('password')
            user = get_user(email)

            if not user:
                return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

            if not user.check_password(password):
                return create_response(False, 'Invalid email or password.', status_code=status.HTTP_401_UNAUTHORIZED)

            if not user.is_verified:
                return create_response(
                    False, 'Email not verified. Please check your email for verification instructions.',
                    status_code=status.HTTP_403_FORBIDDEN
                )

            token = jwt_encode_handler(user)
            return create_response(
                True, 'User logged in successfully.',
                {'user': UserSerializer(user).data, 'token': token}
            )
        except Exception as e:
            return create_response(False, f'Error logging in: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def verify_email(self, request):
        """Verifies a user's email using a verification code."""
        try:
            email, verification_code = request.data.get('email'), request.data.get('verification_code')
            user = get_user(email)

            if not user:
                return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

            if user.verification_code == verification_code:
                user.is_verified = True
                user.save()
                return create_response(True, 'Email verified successfully.')

            return create_response(False, 'Invalid verification code.', status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return create_response(False, f'Error verifying email: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def verify_url(self, request, pk=None):
        """Verifies a user's email using a verification URL."""
        try:
            user_id = pk[6:]
            verification_code = pk[:6]

            user = User.objects.get(id=user_id)

            if user.verification_code == verification_code:
                user.is_verified = True
                user.save()
                return redirect(settings.FRONTEND_URL)

            return create_response(False, 'Invalid verification code.', status_code=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return create_response(False, f'Error verifying email via URL: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def forget_password(self, request):
        """Sends a password reset email to the user."""
        try:
            email = request.data.get('email')
            user = get_user(email)

            if not user:
                return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

            reset_token = generate_code()
            user.password_reset_token = reset_token
            user.password_reset_token_created_at = timezone.now()
            user.save()

            send_forgot_url(user, reset_token)
            return create_response(True, 'Password reset email sent. Please check your email for instructions.')
        except Exception as e:
            return create_response(False, f'Error processing password reset request: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def reset_password(self, request):
        """Resets the user's password using a reset token."""
        try:
            email, reset_token, new_password = request.data.get('email'), request.data.get('reset_token'), request.data.get('new_password')
            user = get_user(email)

            if not user:
                return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

            if user.password_reset_token != reset_token:
                return create_response(False, 'Invalid reset token.', status_code=status.HTTP_400_BAD_REQUEST)

            if (timezone.now() - user.password_reset_token_created_at).days > 1:
                return create_response(False, 'Reset token has expired. Please request a new one.', status_code=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_created_at = None
            user.save()

            return create_response(True, 'Password reset successfully.')
        except Exception as e:
            return create_response(False, f'Error resetting password: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedbackViewSet(viewsets.GenericViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['POST'])
    def create_feedback(self, request):
        """Creates new feedback from the authenticated user."""
        try:
            user = get_user_from_token(request)
            if not user:
                return create_response(False, 'Invalid token.', status_code=status.HTTP_401_UNAUTHORIZED)

            feedback = Feedback.objects.create(
                user=user, 
                feedback=request.data.get('feedback'), 
                agree_to_pay=request.data.get('agreeToPay')
            )
            return create_response(True, 'Feedback created successfully.', FeedbackSerializer(feedback).data)
        except Exception as e:
            return create_response(False, f'Error creating feedback: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_feedbacks(self, request):
        """Retrieves all feedback for the authenticated user."""
        try:
            user = get_user_from_token(request)
            if not user:
                return create_response(False, 'Invalid token.', status_code=status.HTTP_401_UNAUTHORIZED)

            feedbacks = Feedback.objects.filter(user=user)
            return create_response(True, 'Feedbacks retrieved successfully.', FeedbackSerializer(feedbacks, many=True).data)
        except Exception as e:
            return create_response(False, f'Error retrieving feedbacks: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @action(detail=False, methods=['GET'])
    # def delete_all_users(self, request):
    #     """Deletes all users."""
    #     try:
    #         User.objects.all().delete()
    #         return create_response(True, 'All users deleted successfully.')
    #     except Exception as e:
    #         return create_response(False, f'Error deleting all users: {str(e)}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)