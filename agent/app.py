import asyncio
import json
import os

from mcp import Resource
from mcp.types import Prompt

from agent.dial_client import DialClient
from agent.mcp_client import MCPClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT

API_KEY = os.getenv("DIAL_API_KEY", "your_api_key")
ENDPOINT = "https://ai-proxy.lab.epam.com"


# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts


async def main():
    # TODO:
    # 1. Create MCP client and open connection to the MCP server (use `async with {YOUR_MCP_CLIENT} as mcp_client`),
    #    mcp_server_url="http://localhost:8005/mcp"
    async with MCPClient(mcp_server_url="http://localhost:8005/mcp") as mcp_client:
        # 2. Get Available MCP Resources and print them
        resources: list[Resource] = await mcp_client.get_resources()
        print("Available MCP Resources:")
        for resource in resources:
            print(f"  - URI: {resource.uri}, MIME Type: {resource.mimeType}\n")
        # 3. Get Available MCP Tools, assign to `tools` variable, print tool as well
        tools = await mcp_client.get_tools()
        print("Available MCP Tools:")
        for tool in tools:
            print(json.dumps(tool, indent=2))
        # 4. Create DialClient
        dial_client = DialClient(
            mcp_client=mcp_client, tools=tools, api_key=API_KEY, endpoint=ENDPOINT
        )
        # 5. Create list with messages and add there SYSTEM_PROMPT with instructions to LLM
        messages: list[Message] = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]
        # 6. Add to messages Prompts from MCP server as User messages
        prompts: list[Prompt] = await mcp_client.get_prompts()
        for prompt in prompts:
            prompt_content = await mcp_client.get_prompt(prompt.name)
            messages.append(Message(role=Role.USER, content=prompt_content))
        # 7. Create console chat (infinite loop + ability to exit from chat + preserve message history after the call to dial client)

        print("Welcome to the MCP-powered console chat! Type 'exit' to quit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Exiting chat. Goodbye!")
                break

            messages.append(Message(role=Role.USER, content=user_input))

            ai_message: Message = await dial_client.get_completion(messages)
            print(f"AI: {ai_message.content}\n")

            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())
