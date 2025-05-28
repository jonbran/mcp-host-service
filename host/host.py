import requests
import datetime

class McpHostService:
    def __init__(self, base_url, client_id, api_key):
        self.base_url = base_url
        self.client_id = client_id
        self.api_key = api_key
        self.token = None
        self.token_expiry = None

    def authenticate(self):
        if self.token and self.token_expiry > datetime.datetime.now():
            return self.token

        response = requests.post(
            f"{self.base_url}/api/auth/token",
            json={"clientId": self.client_id, "apiKey": self.api_key},
        )

        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.text}")

        data = response.json()
        self.token = data["token"]
        self.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=data["expiresIn"] - 60)
        return self.token

    def execute_tool(self, tool_id, parameters):
        token = self.authenticate()

        response = requests.post(
            f"{self.base_url}/mcp/execute",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"toolId": tool_id, "toolParameters": parameters},
        )

        if response.status_code != 200:
            raise Exception(f"Tool execution failed: {response.text}")

        return response.json()

    def schedule_conversation(self, conversation_text, scheduled_time, endpoint, method="POST", additional_info=None):
        return self.execute_tool(
            "scheduleConversation",
            {
                "conversationText": conversation_text,
                "scheduledTime": scheduled_time,
                "endpoint": endpoint,
                "method": method,
                "additionalInfo": additional_info,
            },
        )

    def get_conversation_status(self, conversation_id):
        return self.execute_tool("getConversationStatus", {"conversationId": conversation_id})

    def cancel_conversation(self, conversation_id):
        return self.execute_tool("cancelConversation", {"conversationId": conversation_id})