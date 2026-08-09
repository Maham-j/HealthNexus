from langchain_groq import ChatGroq          # Groq LLM wrapper for LangChain
from langchain.agents import create_tool_calling_agent, AgentExecutor  # Create and run the LangChain agent
from langchain_core.prompts import ChatPromptTemplate   # Build structured prompts
from app.core.langchain_tools import tools   # Import all LangChain tools (Neo4j + FAISS)
from langchain_core.messages import HumanMessage, AIMessage
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()


from functools import lru_cache

@lru_cache(maxsize=4)
def get_agent_executor(model_name: str):
    extra_kwargs = {}
    if model_name == "openai/gpt-oss-120b":
        extra_kwargs["model_kwargs"] = {"reasoning_effort": "medium"}

    llm = ChatGroq(
        model=model_name,
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        **extra_kwargs,
    )
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=6,
    )
    return agent_executor, llm


# XML system prompt that defines the agent's behavior and rules
SYSTEM_PROMPT = """
<agent>

    <role>
        You are a biomedical assistant connected to a Neo4j medical knowledge graph.
    </role>

    <behavior>

        <priority>
            Always use the available tools before relying on your internal knowledge.
        </priority>

        <reasoning>
            Use concise reasoning.
            Limit reasoning to at most 3 reasoning steps.
        </reasoning>

        <clarification>
            If required information is missing, ask one focused clarifying question.
        </clarification>

    </behavior>

    <tools>

        <neo4j>
            Treat the Neo4j knowledge graph as the primary biomedical source.
        </neo4j>

        <faiss>
            Use only for retrieving similar Cypher query examples.
            Never use FAISS as medical evidence.
        </faiss>

        <selection>
            Decide automatically which tool or tools to call.
        </selection>

    </tools>

    <answering>

        <medical>
            Use Neo4j results whenever available.
            Do not invent biomedical facts.
            Never state a mechanism, cause, or attribute (e.g. inheritance pattern, dosage, prevalence) unless it is explicitly 
            present in the tool output.
            If asked to categorize or filter results, only state what the data supports — do not assume a disease is hereditary 
            just because its name contains a word like "syndrome" or "susceptibility."
            When falling back to general knowledge, never invent disease or syndrome names that do not exist in standard medical 
            terminology (e.g. do not create phrases like "hereditary sarcoma of the aorta" by combining a graph entry with a hereditary label).
            If uncertain whether a specific disease has a well-established hereditary form, say so explicitly rather than asserting one.
        </medical>

        <missing_information>
            If the knowledge graph does not contain the answer, clearly say so,
            then still answer using general knowledge, explicitly labeled as such.
            Never stop at "the graph does not contain this" without providing an answer.
        </missing_information>

    </answering>

    <citations>

        <neo4j>
            Mention that the answer is based on the Neo4j medical knowledge graph.
        </neo4j>

        <internal>
            If answering from general knowledge, clearly state that it is based on the model's general knowledge.
        </internal>
        <mixed_sources>
        If part of the answer comes from Neo4j and part comes from general knowledge,
        label each part separately. Never present fabricated or general-knowledge details as if they came from Neo4j.
       </mixed_sources>

    </citations>

</agent>
"""

# Create the prompt template sent to the LLM
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


def format_tool_call(action) -> str:
    tool_name = action.tool
    tool_input = action.tool_input

    if tool_name == "run_neo4j_query":
        cypher = tool_input.get("cypher_query", "")
        return f"**🔍 `{tool_name}`**\n```cypher\n{cypher}\n```"

    if tool_name == "fetch_similar_queries":
        query = tool_input.get("query", "")
        return f"**🔍 `{tool_name}`**\n> {query}"

    return f"**🛠️ `{tool_name}`**\n```\n{tool_input}\n```"


# Function to send a question to the agent

def describe_step(action, observation):
    formatted_call = format_tool_call(action)

    if isinstance(observation, dict) and "results" in observation:
        count = len(observation["results"])
    elif isinstance(observation, list):
        count = len(observation)
    else:
        count = None

    if count == 0:
        result_phrase = "→ returned nothing."
    elif count == 1:
        result_phrase = "→ returned 1 result."
    elif count is not None:
        result_phrase = f"→ returned {count} results."
    else:
        result_phrase = "→ got a response back."

    return f"{formatted_call}\n{result_phrase}"


def ask_agent(question: str, model_name: str, chat_history: list | None = None):
    agent_executor, llm = get_agent_executor(model_name)
    print("ACTUALLY USING MODEL:", llm.model_name)
    response = agent_executor.invoke(
        {
            "input": question,
            "chat_history": chat_history or [],
        }
    )

    steps = response.get("intermediate_steps", [])
    final_answer = response["output"]

    if not steps:
        return "<think>\n⌛ Answered directly from general knowledge — no knowledge graph lookup needed\n✅ Done\n</think>\n\n" + final_answer

    tools_called = [action.tool for action, _ in steps]
    summary = " Tools Used: " + ", ".join(dict.fromkeys(tools_called))

    thinking_lines = [summary, ""]
    for action, observation in steps:
        thinking_lines.append(describe_step(action, observation))
        
    answer_lower = final_answer.lower()
    used_general_knowledge = (
        "general knowledge" in answer_lower
        or "general biomedical knowledge" in answer_lower
    )

    thinking_lines.append("")
    if used_general_knowledge:
        thinking_lines.append("⌛  Graph data was insufficient — filled gaps using general medical knowledge")
    thinking_lines.append("⌛  Building the summary")
    thinking_lines.append("✔ Done")


    thinking_block = "<think>\n" + "\n".join(thinking_lines) + "\n</think>\n\n"
    return thinking_block + final_answer



# provide summary of chain of thoughts instead of hardcoded
# def ask_agent_llm_summary(question: str, chat_history: list | None = None):
#     response = agent_executor.invoke(
#         {
#             "input": question,
#             "chat_history": chat_history or [],
#         }
#     )
#     steps = response.get("intermediate_steps", [])
#     final_answer = response["output"]

#     if not steps:
#         return final_answer

#     steps_text = "\n".join(
#         f"Tool: {action.tool}, Input: {action.tool_input}, Result: {str(observation)[:200]}"
#         for action, observation in steps
#     )

#     summary_prompt = (
#         f"Summarize the following reasoning steps in 2-3 short sentences, "
#         f"as if explaining your own thought process:\n\n{steps_text}"
#     )
#     summary_response = llm.invoke(summary_prompt)

#     thinking_block = f"<think>\n{summary_response.content}\n</think>\n\n"
#     return thinking_block + final_answer


    