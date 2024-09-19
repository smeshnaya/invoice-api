import http
from typing import List

from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient

from app.config.config import settings


class ColorHex:
    red = "#FF0000"
    green = "#00CC00"


class SlackClient:
    token = settings.slack_api_token
    timeout = settings.slack_timeout

    def __init__(self):
        async_client = AsyncWebClient(token=self.token, timeout=self.timeout)
        client = WebClient(token=self.token, timeout=self.timeout)

        self.async_client = async_client
        self.client = client

    def generate_attachments(self, message: str, is_error: bool) -> List[dict]:
        color = ColorHex.red if is_error else ColorHex.green
        return [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "plain_text", "text": f"{message}"},
                    }
                ],
            }
        ]

    def format_header(self, to_mention: bool) -> str:
        res = (
            f"Service={settings.service_name}; "
            f"Environment={settings.environment.value}; "
            f"Version={settings.version}.\r\n"
        )
        if to_mention:
            res = f"<!channel>\n{res}"

        return res

    async def send_async(
        self,
        message: str,
        channel: str,
        to_mention: bool,
        is_error: bool,
    ) -> bool:
        header = self.format_header(to_mention=to_mention)
        attachments = self.generate_attachments(message=message, is_error=is_error)

        response = await self.async_client.chat_postMessage(
            channel=channel,
            text=header,
            attachments=attachments,
        )
        return response.status_code == http.HTTPStatus.OK

    def send(
        self,
        message: str,
        channel: str,
        to_mention: bool,
        is_error: bool,
    ) -> bool:
        header = self.format_header(to_mention=to_mention)
        attachments = self.generate_attachments(message=message, is_error=is_error)

        response = self.client.chat_postMessage(
            channel=channel,
            text=header,
            attachments=attachments,
        )
        return response.status_code == http.HTTPStatus.OK
