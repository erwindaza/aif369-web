"""
Udemy Instructor API Client

Reads course metadata (price, students, rating) from Udemy.
This is a READ-ONLY client — Udemy API does not support creating courses via API.

Authentication: Uses client_id and client_secret (OAuth2).
Rate Limiting: 15-minute cache to avoid hitting rate limits.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import requests


class UdemyClient:
    """Client for Udemy Instructor API (read-only)."""

    UDEMY_API_BASE = "https://www.udemy.com/api-2.0"

    def __init__(self):
        """Initialize with credentials from environment."""
        self.client_id = os.getenv("UDEMY_CLIENT_ID")
        self.client_secret = os.getenv("UDEMY_CLIENT_SECRET")
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

        # In-memory cache: course_id → course_data
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self.cache_duration_minutes = 15

    def is_configured(self) -> bool:
        """Check if Udemy credentials are available."""
        return bool(self.client_id and self.client_secret)

    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token from Udemy.
        Tokens are valid for ~1 hour; we cache locally.
        """
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        if not self.is_configured():
            print("⚠️  Udemy credentials not configured. Set UDEMY_CLIENT_ID and UDEMY_CLIENT_SECRET.")
            return None

        try:
            response = requests.post(
                f"{self.UDEMY_API_BASE}/oauth2/token/",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            return self.access_token
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get Udemy access token: {e}")
            return None

    def _is_cached(self, course_id: str) -> bool:
        """Check if course data is in cache and still valid."""
        if course_id not in self._cache:
            return False
        expiry = self._cache_ttl.get(course_id)
        if not expiry or datetime.now() > expiry:
            del self._cache[course_id]
            del self._cache_ttl[course_id]
            return False
        return True

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch course data from Udemy API.

        Args:
            course_id: Udemy course ID (numeric)

        Returns:
            Dict with: id, title, headline, price, currency, num_subscribers, rating, url
            Or None if not configured / error
        """
        if not self.is_configured():
            return None

        # Check cache first
        if self._is_cached(course_id):
            return self._cache[course_id]

        token = self._get_access_token()
        if not token:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            # Endpoint: GET /courses/{id}/
            response = requests.get(
                f"{self.UDEMY_API_BASE}/courses/{course_id}/",
                headers=headers,
                timeout=5
            )

            if response.status_code == 404:
                print(f"⚠️  Udemy course {course_id} not found (404)")
                return None

            response.raise_for_status()
            data = response.json()

            # Extract relevant fields
            course_info = {
                "id": data.get("id"),
                "title": data.get("title"),
                "headline": data.get("headline"),
                "price": data.get("price"),
                "currency": data.get("currency", "USD"),
                "num_subscribers": data.get("num_subscribers", 0),
                "rating": data.get("rating", 0.0),
                "url": data.get("url", f"https://www.udemy.com/course/{data.get('url_title', '')}"),
                "status": data.get("status"),  # "draft" or "published"
                "fetched_at": datetime.now().isoformat()
            }

            # Cache for 15 minutes
            self._cache[course_id] = course_info
            self._cache_ttl[course_id] = datetime.now() + timedelta(minutes=self.cache_duration_minutes)

            return course_info

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch Udemy course {course_id}: {e}")
            return None

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Fetch instructor profile info."""
        if not self.is_configured():
            return None

        token = self._get_access_token()
        if not token:
            return None

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.UDEMY_API_BASE}/users/me/",
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch instructor info: {e}")
            return None

    def get_instructor_courses(self) -> Optional[Dict[str, Any]]:
        """Fetch list of all instructor's courses."""
        if not self.is_configured():
            return None

        token = self._get_access_token()
        if not token:
            return None

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.UDEMY_API_BASE}/courses/?filter=instructor_id&search=",
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch instructor courses: {e}")
            return None


# Singleton instance
_udemy_client: Optional[UdemyClient] = None


def get_udemy_client() -> UdemyClient:
    """Get or create the Udemy client singleton."""
    global _udemy_client
    if _udemy_client is None:
        _udemy_client = UdemyClient()
    return _udemy_client
