"""
Request logging middleware
Logs all API requests for security and auditing
"""
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

logger = logging.getLogger('api_requests')


class LogRequestMiddleware(MiddlewareMixin):
    """Log all API requests"""

    def process_request(self, request):
        """Log request details"""
        if request.path.startswith('/api/'):
            log_data = {
                'timestamp': timezone.now().isoformat(),
                'method': request.method,
                'path': request.path,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            }

            logger.info(json.dumps(log_data))

    def process_response(self, request, response):
        """Log response details"""
        if request.path.startswith('/api/'):
            log_data = {
                'timestamp': timezone.now().isoformat(),
                'path': request.path,
                'status_code': response.status_code,
            }

            if response.status_code >= 400:
                logger.warning(json.dumps(log_data))
            else:
                logger.info(json.dumps(log_data))

        return response

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
