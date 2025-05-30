import os
from dotenv import load_dotenv
import stripe

load_dotenv()  # Loads variables from .env if present

STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")

stripe.api_key = STRIPE_SECRET_KEY
