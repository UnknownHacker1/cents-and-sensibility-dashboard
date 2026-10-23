"""App settings, read from environment variables (or a .env file). Never hard-code these."""

import os
import secrets
from dataclasses import dataclass, field


@dataclass
class Settings:
    secret_key: str | None = None      # signs the session cookie
    app_password: str | None = None    # owner login; demo login works without it
    plaid_client_id: str | None = None
    plaid_secret: str | None = None
    cookie_secure: bool = False        # set COOKIE_SECURE=1 when served over HTTPS
    session_key: str = field(init=False, default="")

    def __post_init__(self):
        # No SECRET_KEY: make a throwaway one. Works, but sessions reset on restart (Security Center flags it).
        self.session_key = self.secret_key or secrets.token_urlsafe(32)

    @property
    def plaid_available(self) -> bool:
        return bool(self.plaid_client_id and self.plaid_secret)

    @classmethod
    def from_env(cls) -> "Settings":
        from dotenv import load_dotenv

        load_dotenv()
        return cls(
            secret_key=os.environ.get("SECRET_KEY") or None,
            app_password=os.environ.get("APP_PASSWORD") or None,
            plaid_client_id=os.environ.get("PLAID_CLIENT_ID") or None,
            plaid_secret=os.environ.get("PLAID_SECRET") or None,
            cookie_secure=os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes"),
        )
