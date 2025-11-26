"""
Custom throttling classes
"""
from rest_framework.throttling import UserRateThrottle as DRFUserRateThrottle
from rest_framework.throttling import AnonRateThrottle


class UserRateThrottle(DRFUserRateThrottle):
    """
    Throttle for authenticated users
    100 requests per minute
    """
    rate = '100/min'


class MerchantRateThrottle(DRFUserRateThrottle):
    """
    Throttle for merchant API requests
    1000 requests per minute
    """
    rate = '1000/min'


class WebhookRateThrottle(AnonRateThrottle):
    """
    Throttle for webhook endpoints
    500 requests per minute
    """
    rate = '500/min'
