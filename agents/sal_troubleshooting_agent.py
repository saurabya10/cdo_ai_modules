import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import sys
from pathlib import Path

from langchain.agents import create_tool_calling_agent, AgentExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cdo_ai_modules.config import load_config
from cdo_ai_modules.core.auth import get_api_key
from cdo_ai_modules.services.embedding_service import EmbeddingService
from cdo_ai_modules.tools.sal_tools import get_resource_status, get_event_status, get_device_status

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class SalTroubleshootAgent:
    def __init__(self, config):
        self.config = config
        self.llm = self._get_llm()
        self.agent_executor = self._create_agent_executor()

    def _get_llm(self):
        api_key = get_api_key(self.config)
        llm = AzureChatOpenAI(
            model=self.config.llm.model,
            api_key=api_key,
            api_version=self.config.llm.api_version,
            azure_endpoint=self.config.llm.endpoint,
            temperature=0.7,
            model_kwargs=dict(user='{"appkey": "' + self.config.llm.app_key + '", "user": "user1"}'),
        )
        return llm

    def _create_agent_executor(self):
        tools = [get_resource_status, get_event_status, get_device_status]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a troubleshooting agent. Your task is to execute a given troubleshooting plan, analyze the results, and identify the root cause of the issue. "
                       "Follow these steps:\n"
                       "1. The user will provide a troubleshooting plan.\n"
                       "2. Execute the steps in the plan using the available tools.\n"
                       "3. Analyze the output from the tools to diagnose the problem.\n"
                       "4. Provide a concise summary of your findings and state where the issue lies."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        return agent_executor

    def invoke(self, user_query: str):
        return self.agent_executor.invoke({"input": user_query})

if __name__ == "__main__":
    config = load_config()

    # The troubleshooting plan would be provided by a retriever agent in a real scenario.
    # For testing, we can simulate a plan.
    troubleshooting_plan = ("1. Check resource status for stream_id '12345'.\n"
                            "2. Check event status for stream_id '12345'.\n"
                            "3. Check device status for sse_id 'abcde'.")

    agent = SalTroubleshootAgent(config)

    print(f"Troubleshooting Plan:\n{troubleshooting_plan}")

    response = agent.invoke(troubleshooting_plan)
    print(f"\nAssistant: {response}")
