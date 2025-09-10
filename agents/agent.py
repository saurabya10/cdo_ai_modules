import os
import base64
import certifi
import requests
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cdo_ai_modules.config import load_config
from cdo_ai_modules.core.auth import get_api_key
from cdo_ai_modules.services.embedding_service import EmbeddingService

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class RAGAgent:
    def __init__(self, config, retriever):
        self.config = config
        self.retriever = retriever
        self.llm = self._get_llm()
        self.rag_chain = self._create_rag_chain()

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

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def _create_rag_chain(self):
        system_prompt = """You are an expert technical support assistant. Your only function is to provide troubleshooting steps from the knowledge base.

Follow these rules strictly:
1.  Analyze the user's question to understand the issue.
2.  Review the following context, which contains troubleshooting steps from the knowledge base.
3.  If the context contains relevant steps, present them clearly in a numbered list.
4.  If the context does not contain relevant steps for the user's issue, you MUST respond with ONLY this exact sentence: "I'm sorry, I could not find troubleshooting steps for that issue in the knowledge base."
5.  Do not add any extra information, apologies, or introductory sentences. Stick to the facts from the context.

CONTEXT:
{context}
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        rag_chain = (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return rag_chain

    def invoke(self, user_query: str):
        return self.rag_chain.invoke(user_query)

if __name__ == "__main__":
    # This is for testing purposes only
    config = load_config()
    
    # Initialize the embedding service and get the retriever
    embedding_service = EmbeddingService(config)
    embedding_service.create_and_store_embeddings()
    retriever = embedding_service.get_retriever()
    
    rag_agent = RAGAgent(config, retriever)
    
    while True:
        user_query = input("\nYou: ")
        if user_query.lower() in ["exit", "quit"]:
            break
        response = rag_agent.invoke(user_query)
        print(f"\nAssistant: {response}")
    
