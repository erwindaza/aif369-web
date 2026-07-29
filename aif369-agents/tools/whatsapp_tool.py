"""WhatsApp Tool - Send messages to customers"""
import asyncio
import time
from typing import Optional, Dict, Any
import httpx
from tools.base import BaseTool
from config import ConfigManager


class WhatsAppTool(BaseTool):
    """
    Send messages to customers via WhatsApp

    Single Responsibility: Send WhatsApp messages only
    Dependency Injection: ConfigManager, httpx.AsyncClient injected

    Integration:
    - Calls WhatsApp Bot API (Node.js bot.js)
    - Non-blocking (async/await)
    - Includes retry logic

    Example:
        tool = WhatsAppTool()
        result = await tool.execute(
            phone="+56912345678",
            message="Tu producto está siendo enriquecido"
        )
    """

    def __init__(self, whatsapp_api_url: Optional[str] = None):
        super().__init__(tool_name="whatsapp")

        self.config = ConfigManager.get_instance()
        self.whatsapp_api_url = whatsapp_api_url or "http://whatsapp-bot:3000/send"

        self.client = httpx.AsyncClient(timeout=10.0)
        self.max_retries = 3
        self.retry_delay_ms = 1000

    async def validate_inputs(self, phone: str, message: str) -> bool:
        """Validate phone and message"""
        if not phone or len(phone) < 10:
            self.logger.warning(f"Invalid phone: {phone}")
            return False

        if not message or len(message) < 1:
            self.logger.warning("Empty message")
            return False

        if len(message) > 1000:
            self.logger.warning(f"Message too long: {len(message)} chars")
            return False

        return True

    async def execute(self, phone: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send WhatsApp message to customer

        Args:
            phone: customer phone number (format: +56912345678)
            message: message text
            **kwargs: additional options (priority, schedule_time, etc)

        Returns:
            {
                "status": "sent" | "failed" | "queued",
                "phone": phone,
                "message_id": str (optional),
                "error": str (optional),
                "attempts": int
            }
        """
        start_time = time.time()

        # Validate
        if not await self.validate_inputs(phone, message):
            return {
                "status": "failed",
                "phone": phone,
                "error": "Invalid inputs",
                "attempts": 0,
            }

        # Retry loop
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.debug(
                    f"Sending WhatsApp to {phone} (attempt {attempt}/{self.max_retries})"
                )

                response = await self.client.post(
                    self.whatsapp_api_url,
                    json={
                        "phone": phone,
                        "message": message,
                        "metadata": kwargs.get("metadata", {}),
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    execution_time = (time.time() - start_time) * 1000

                    self._execution_count += 1
                    self._total_execution_time += execution_time

                    self.logger.info(
                        f"WhatsApp sent to {phone} in {execution_time:.0f}ms"
                    )

                    return {
                        "status": "sent",
                        "phone": phone,
                        "message_id": result.get("message_id"),
                        "attempts": attempt,
                    }

                else:
                    last_error = f"HTTP {response.status_code}"
                    self.logger.warning(
                        f"WhatsApp API error: {response.status_code} - {response.text}"
                    )

            except httpx.ConnectError as e:
                last_error = f"Connection error: {e}"
                self.logger.warning(f"Cannot connect to WhatsApp API: {e}")

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                self.logger.warning(f"WhatsApp API timeout: {e}")

            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Unexpected error: {e}")

            # Retry delay (exponential backoff)
            if attempt < self.max_retries:
                delay_ms = self.retry_delay_ms * (2 ** (attempt - 1))
                self.logger.debug(f"Retrying in {delay_ms}ms...")
                await asyncio.sleep(delay_ms / 1000)

        # All retries failed
        execution_time = (time.time() - start_time) * 1000

        self._execution_count += 1
        self._total_execution_time += execution_time

        self.logger.error(
            f"WhatsApp failed after {self.max_retries} attempts: {last_error}"
        )

        return {
            "status": "failed",
            "phone": phone,
            "error": last_error,
            "attempts": self.max_retries,
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()
