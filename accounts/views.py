# accounts/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.conf import settings
from .models import User, OTP
from .serializers import (
    UserRegistrationSerializer, 
    OTPVerificationSerializer, 
    LoginSerializer,
    SendOTPSerializer
)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Step 1: Register user and send OTP"""
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Generate and send OTP
        otp_obj = OTP.objects.create(user=user, purpose='registration')
        otp_code = otp_obj.generate_otp()
        otp_obj.save()

        # Send OTP via email
        subject = 'Klayons - Email Verification OTP'
        message = f'''
        Welcome to Klayons!

        Your email verification OTP is: {otp_code}

        This OTP is valid for 10 minutes.

        Thank you,
        Klayons Team
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                'message': 'Registration successful. OTP sent to your email.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            user.delete()  # Clean up if email fails
            return Response({
                'error': 'Failed to send OTP email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Step 2: Verify OTP and complete registration/login"""
    serializer = OTPVerificationSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data['purpose']

        try:
            user = User.objects.get(email=email)
            otp_obj = OTP.objects.filter(
                user=user, 
                otp_code=otp_code, 
                purpose=purpose,
                is_verified=False
            ).first()

            if not otp_obj:
                return Response({
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)

            if otp_obj.is_expired():
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as verified
            otp_obj.is_verified = True
            otp_obj.save()

            if purpose == 'registration':
                user.is_email_verified = True
                user.save()

                # Create auth token
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'message': 'Email verified successfully! Registration complete.',
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'phone_number': user.phone_number,
                        'society_name': user.society_name,
                        'flat_no': user.flat_no,
                    }
                }, status=status.HTTP_200_OK)

            elif purpose == 'login':
                # Create auth token
                token, created = Token.objects.get_or_create(user=user)

                return Response({
                    'message': 'Login successful!',
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'phone_number': user.phone_number,
                        'society_name': user.society_name,
                        'flat_no': user.flat_no,
                    }
                }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Step 1: Validate credentials and send OTP for login"""
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data['user']

        # Generate and send OTP for login verification
        otp_obj = OTP.objects.create(user=user, purpose='login')
        otp_code = otp_obj.generate_otp()
        otp_obj.save()

        # Send OTP via email
        subject = 'Klayons - Login Verification OTP'
        message = f'''
        Hello {user.username},

        Your login verification OTP is: {otp_code}

        This OTP is valid for 10 minutes.

        If you didn't request this, please ignore this email.

        Thank you,
        Klayons Team
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                'message': 'Credentials verified. OTP sent to your email.',
                'email': user.email
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to send OTP email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Resend OTP for registration or login"""
    serializer = SendOTPSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']

        try:
            user = User.objects.get(email=email)

            # Invalidate previous OTPs
            OTP.objects.filter(user=user, purpose=purpose, is_verified=False).delete()

            # Generate new OTP
            otp_obj = OTP.objects.create(user=user, purpose=purpose)
            otp_code = otp_obj.generate_otp()
            otp_obj.save()

            # Send OTP via email
            subject = f'Klayons - {purpose.title()} OTP (Resent)'
            message = f'''
            Hello {user.username},

            Your new {purpose} OTP is: {otp_code}

            This OTP is valid for 10 minutes.

            Thank you,
            Klayons Team
            '''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                'message': 'New OTP sent to your email.'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to send OTP email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_user(request):
    """Logout user by deleting token"""
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({
            'error': 'Token not found'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def user_profile(request):
    """Get user profile"""
    user = request.user
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'society_name': user.society_name,
            'flat_no': user.flat_no,
            'is_email_verified': user.is_email_verified,
        }
    }, status=status.HTTP_200_OK)

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

def api_documentation(request):
    """Home page with API documentation"""
    base_url = request.build_absolute_uri('/').rstrip('/')

    context = {
        'base_url': base_url,
        'title': 'Klayons Authentication API Documentation'
    }
    return render(request, 'home/index.html', context)
