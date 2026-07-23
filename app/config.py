"""
config.py

Centralized application configuration.

Why this file exists:
Instead of scattering `os.getenv(...)` calls throughout the codebase, we load
all environment variables ONCE, in ONE place, and validate that required
values are actually present. Every other module imports `settings` from here
rather than touching environment variables directly.

This is a common pattern called the "Settings object" pattern.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file into the process environment.
# This must run before we read any os.getenv() calls below.
load_dotenv()


class Settings:
    """
    Holds all configuration values needed to run the API.

    Using a class (instead of loose module-level variables) lets us:
    - Group related config together
    - Add validation logic in one place (see __init__ below)
    - Type-hint the values clearly
    """

    def __init__(self) -> None:
        self.urja_base_url: str = os.getenv("URJA_BASE_URL", "").rstrip("/")
        self.urja_email: str = os.getenv("URJA_EMAIL", "")
        self.urja_password: str = os.getenv("URJA_PASSWORD", "")

        # Fail fast: if any required setting is missing, raise a clear error
        # immediately at startup, rather than a confusing failure later when
        # someone tries to log in.
        missing = [
            name
            for name, value in [
                ("URJA_BASE_URL", self.urja_base_url),
                ("URJA_EMAIL", self.urja_email),
                ("URJA_PASSWORD", self.urja_password),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variable(s): {', '.join(missing)}. "
                "Check your .env file."
            )


# A single shared instance, imported by other modules like:
#   from app.config import settings
settings = Settings()