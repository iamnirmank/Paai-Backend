from django.shortcuts import redirect
from paAI import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import Feedback, User
from .serializers import UserSerializer, FeedbackSerializer
from .utils import get_user, jwt_decode_handler, jwt_encode_handler, generate_code, create_response, send_forgot_url, send_reset_email, send_verification_email, send_verification_url
from rest_framework.permissions import IsAuthenticated

class UserViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer
    
    @action(detail=False, methods=['POST'])
    def register(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            password = request.data.get('password')
            serializer.validated_data['password'] = make_password(password)
            user = serializer.save()
            send_verification_url(user)

            # Serialize the user instance before returning the response
            serialized_user = UserSerializer(user).data

            return create_response(
                True,
                'User registered successfully. Please check your email for verification instructions.',
                serialized_user,
                status.HTTP_201_CREATED
            )

        return create_response(False, serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=False, methods=['POST'])
    def login(self, request):
        email, password = request.data.get('email'), request.data.get('password')
        user = get_user(email)

        if not user:
            return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

        if user.check_password(password):
            if not user.is_verified:
                return create_response(False, 'Email not verified. Please check your email for verification instructions.', status_code=status.HTTP_403_FORBIDDEN)

            token = jwt_encode_handler(user)
            response = {
                'user': UserSerializer(user).data,  
                'token': token  
            }
            return create_response(True, 'User logged in successfully.', response)

        return create_response(False, 'Invalid email or password.', status_code=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['POST'])
    def verify_email(self, request):
        email, verification_code = request.data.get('email'), request.data.get('verification_code')
        user = get_user(email)

        if not user:
            return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

        if user.verification_code == verification_code:
            user.is_verified = True
            user.save()
            return create_response(True, 'Email verified successfully.')

        return create_response(False, 'Invalid verification code.', status_code=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['GET'])
    def verify_url(self, request, pk=None):
        id = pk[6:]
        verification_code = pk[:6]
        user = User.objects.get(id=id)

        if not user:
            return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

        if user.verification_code == verification_code:
            user.is_verified = True
            user.save()
            return redirect(settings.FRONTEND_URL)

        return create_response(False, 'Invalid verification code.', status_code=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def forget_password(self, request):
        email = request.data.get('email')
        user = User.objects.get(email=email)

        if not user:
            return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

        reset_token = generate_code()
        user.password_reset_token = reset_token
        user.password_reset_token_created_at = timezone.now()
        user.save()

        send_forgot_url(user, reset_token)

        return create_response(True, 'Password reset email sent. Please check your email for instructions.')

    @action(detail=False, methods=['POST'])
    def reset_password(self, request):
        email, reset_token, new_password = request.data.get('email'), request.data.get('reset_token'), request.data.get('new_password')

        user = get_user(email)

        if not user:
            return create_response(False, 'User not found.', status_code=status.HTTP_404_NOT_FOUND)

        if user.password_reset_token != reset_token:
            return create_response(False, 'Invalid reset token.', status_code=status.HTTP_400_BAD_REQUEST)

        reset_token_created_at = user.password_reset_token_created_at
        if reset_token_created_at and (timezone.now() - reset_token_created_at).days > 1:
            return create_response(False, 'Reset token has expired. Please request a new one.', status_code=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_created_at = None
        user.save()

        return create_response(True, 'Password reset successfully.')
    
class FeedbackViewSet(viewsets.ModelViewSet):
    serializer = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['POST'])
    def create_feedback(self, request):
        try:
            auth_header = request.headers.get('Authorization')  
            if not auth_header or not auth_header.startswith('Bearer '):
                return False
            parts = auth_header.split(' ')
            token = parts[1] if len(parts) == 2 else None
            decoded_token = jwt_decode_handler(token)
            user = User.objects.get(id=decoded_token['user_id'])
            feedback = Feedback(user=user, feedback=request.data.get('feedback'), agreeToPay=request.data.get('useInFuture'))
            feedback.save()
            serialized_feedback = FeedbackSerializer(feedback).data

            return create_response(True, 'Feedback created successfully.', serialized_feedback)
        
        except:
            return create_response(False, 'Error creating feedback.', status_code=status.HTTP_400_BAD_REQUEST)
        

    @action(detail=False, methods=['GET'])
    def get_feedbacks(self, request):

        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return False
            parts = auth_header.split(' ')  
            token = parts[1] if len(parts) == 2 else None
            decoded_token = jwt_decode_handler(token)
            user = User.objects.get(id=decoded_token['user_id'])
            if user:
                get_all_feedbacks = Feedback.objects.filter(user=user)
                serialized_feedbacks = FeedbackSerializer(get_all_feedbacks, many=True).data

            return create_response(True, 'Feedbacks retrieved successfully.', serialized_feedbacks)
        
        except:
            return create_response(False, 'Error retrieving feedbacks.', status_code=status.HTTP_400_BAD_REQUEST)
        