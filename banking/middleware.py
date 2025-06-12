from django.http import JsonResponse
from django.conf import settings
import jwt
from datetime import datetime

class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude authentication endpoints from token validation
        if request.path.startswith('/accounts/login/') or request.path.startswith('/accounts/register/'):
            return self.get_response(request)

        token = request.GET.get('token') or request.COOKIES.get('django_api_token')
        
        if not token:
            return JsonResponse({
                'error': 'No token provided',
                'message': 'Please log in again'
            }, status=401)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if datetime.fromtimestamp(payload['exp']) < datetime.now():
                return JsonResponse({
                    'error': 'Token expired',
                    'message': 'Please log in again'
                }, status=401)
            request.user_token = payload
        except jwt.InvalidTokenError:
            return JsonResponse({
                'error': 'Invalid token',
                'message': 'Please log in again'
            }, status=401)

        response = self.get_response(request)
        return response
