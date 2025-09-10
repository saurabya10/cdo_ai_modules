from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    user_input: str
    intent: Optional[dict]
    final_response: Optional[str]

class AgentGraph:
    def __init__(self, intent_agent, rag_agent):
        self.intent_agent = intent_agent
        self.rag_agent = rag_agent
        self.graph = self._build_graph()

    async def _analyze_intent(self, state: AgentState):
        """Node to analyze user intent."""
        user_input = state['user_input']
        intent_result = await self.intent_agent.analyze_intent(user_input)
        return {"intent": intent_result}

    def _get_troubleshooting_plan(self, state: AgentState):
        """Node to get troubleshooting plan using RAG agent."""
        user_input = state['user_input']
        rag_response = self.rag_agent.invoke(user_input)
        return {"final_response": rag_response}

    def _general_chat(self, state: AgentState):
        """Node for general chat."""
        return {"final_response": "I can only help with troubleshooting. Please ask me a troubleshooting question."}

    def _router(self, state: AgentState):
        """Router to decide the next step based on intent."""
        intent_action = state['intent'].get('action')
        if intent_action == 'sal_troubleshoot':
            return 'get_troubleshooting_plan'
        else:
            return 'general_chat'

    def _build_graph(self):
        """Builds the LangGraph."""
        workflow = StateGraph(AgentState)

        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("get_troubleshooting_plan", self._get_troubleshooting_plan)
        workflow.add_node("general_chat", self._general_chat)

        workflow.set_entry_point("analyze_intent")

        workflow.add_conditional_edges(
            "analyze_intent",
            self._router,
            {
                "get_troubleshooting_plan": "get_troubleshooting_plan",
                "general_chat": "general_chat",
            },
        )
        
        workflow.add_edge("get_troubleshooting_plan", END)
        workflow.add_edge("general_chat", END)

        return workflow.compile()

    async def invoke(self, user_input: str):
        """Invokes the graph with user input."""
        return await self.graph.ainvoke({"user_input": user_input})
