import os
import json
import random
from datetime import datetime
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
import httpx

from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from app.tools import tool_check_availability, tool_book_slot, tool_list_events

load_dotenv()

# Load keys and parse into list
OPENROUTER_API_KEYS = os.getenv("OPENROUTER_API_KEY", "")
print("ENV RAW:", os.getenv("OPENROUTER_API_KEY"))

API_KEYS_LIST = [key.strip() for key in OPENROUTER_API_KEYS.split(",") if key.strip()]
print("API List",API_KEYS_LIST)

OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324:free"

class TailorTalkState(TypedDict):
    messages: Annotated[List[dict], "Conversation messages"]
    user_id: str
    pending_clarification: bool
    tool_calls_made: List[str]
    session_context: dict

def call_openrouter(messages, model=OPENROUTER_MODEL, temperature=0.3):
    # Randomly select an API key
    if not API_KEYS_LIST:
        return "No API keys available. Please check configuration."

    selected_key = random.choice(API_KEYS_LIST)
    print(selected_key)
    headers = {
        "Authorization": f"Bearer {selected_key}",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "TailorTalk"
    }

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    timeout = httpx.Timeout(30.0, connect=10.0, read=30.0, write=10.0, pool=5.0)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except httpx.RequestError as e:
        return "Sorry, there was a delay processing your request. Please try again."


@tool
def check_availability(start_date: str, end_date: str) -> str:
    """Check available slots between start_date and end_date."""
    return tool_check_availability(start_date, end_date)

@tool
def book_slot(start_time: str, duration: str = "1h", title: str = "TailorTalk", description: str = "") -> str:
    """Book a calendar meeting with specified details."""
    return tool_book_slot(start_time, duration, title, description)

@tool
def list_events(start_date: str = None, end_date: str = None) -> list:
    """List upcoming events, optionally filtered by date range."""
    return tool_list_events(start_date, end_date)

tools = [check_availability, book_slot, list_events]

def build_system_prompt() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""
You are TailorTalk, a friendly, precise AI assistant managing a shared Google Calendar. You DO have full access to the user's calendar and can perform real-time operations using tool calls.

🕒 Always remember: Current date and time: {now}.
Use this to resolve terms like "today", "tomorrow", "next week", etc.

---

🎯 Your Role:
1️⃣ Reply naturally ONLY when no tool call is needed.
2️⃣ Otherwise, return ONLY structured JSON (no explanations, no markdown, no extra commentary) to call tools:
- check_availability
- book_slot
- list_events
✅ If the user does not specify a duration for book_slot or any other important data for a tool call always ask for clarification.
If you recieve ⚠️ Overlap detected then alert user immediately.

Example: 
User: book event for 1 july 4 pm.
Reply: Please specify a duration is the event for 1 hour, 2 hours or some other duration.
---

🛠 TOOL CALL FORMAT:

{{
  "tool_call": "check_availability",
  "arguments": {{
    "start_date": "2025-06-25",
    "end_date": "2025-06-25"
  }}
}}

{{
  "tool_call": "book_slot",
  "arguments": {{
    "start_time": "2025-06-26 15:00",
    "duration": "1h",
    "title": "Project Discussion",  //optional
    "description": "Quick review of UI changes" //optional
  }}
}}

{{
  "tool_call": "list_events",
  "arguments": {{
    "start_date": "2025-06-25",
    "end_date": "2025-06-30"
  }}
}}

---

🧠 Time Parsing & Resolution:
✅ Always convert:
- "today" → current date
- "tomorrow" → +1 day
- "yesterday" → -1 day
- "in 3 days" → explicit date
- "next Monday" → explicit date
- "next week" → Monday to Sunday next week

✅ Use "YYYY-MM-DDTHH:MM:SS" format for all tool call arguments that require date-times.
✅ Examples:
- "2025-06-29T09:00:00"
- "2025-06-29T17:00:00"


---

⚡ Important Rules:
✅ If user input is vague:
- Proactively ask follow-up questions to clarify date, time, duration before calling tools.
- For book_slot, DO NOT call unless time and duration are explicitly known.

✅ If you receive a list of events, summarize them clearly:
- Title
- Date
- Start time – End time
- Description (if any)
- A clickable URL (if provided)

✅ If you receive a link or URL, present it as:
🔗 View/Edit Event

---

🖼️ Examples:
User: "Am I free next Tuesday at 3 PM?"
→ Check availability using check_availability for that date.

User: "Book a call tomorrow afternoon."
→ Ask: “Would 2 PM or 3 PM work for you? How long should the call be?”

User: "List my events next week."
→ Use list_events with next week's dates, then return a structured, clear summary.

User: "Schedule a meeting with John."
→ Ask: “What date and time would you like to schedule the meeting with John? How long should it last?”

---

❌ Strict Output Rules:
- Never output explanations, markdown, or commentary with JSON tool calls.
- Only use the three allowed tools.
- Only call book_slot when details are fully clear.
- Always provide explicit, clean summaries if tool results contain event data.

⚡ Begin now.
"""

def user_input_node(state: TailorTalkState) -> TailorTalkState:
    # print("[DEBUG] user_input_node:", state)
    return state

def llm_node(state: TailorTalkState) -> TailorTalkState:
    messages = [{"role": "system", "content": build_system_prompt()}] + state["messages"]
    response_content = call_openrouter(messages)
    state["messages"].append({"role": "assistant", "content": response_content})
    state["pending_clarification"] = False
    # print("[DEBUG] llm_node:", state)
    return state

def router_node(state: TailorTalkState) -> dict:
    last_content = state["messages"][-1]["content"]
    # print("[DEBUG] router_node:", last_content)

    try:
        parsed = json.loads(last_content)
        if isinstance(parsed, dict) and "tool_call" in parsed and "arguments" in parsed:
            return {"next": "tool_execution"}
    except json.JSONDecodeError:
        pass

    if any(keyword in last_content.lower() for keyword in ["specify", "unclear", "missing", "duration"]):
        return {"next": "clarification"}
    return {"next": "output"}

def clarification_node(state: TailorTalkState) -> TailorTalkState:
    # print("[DEBUG] clarification_node:", state)
    state["pending_clarification"] = True
    return state

def tool_execution_node(state: TailorTalkState) -> TailorTalkState:
    last_content = state["messages"][-1]["content"]
    tools_used, results = [], []

    try:
        parsed = json.loads(last_content)
        tool_call = parsed.get("tool_call")
        arguments = parsed.get("arguments", {})

        if tool_call == "check_availability":
            result = check_availability.invoke(arguments)
            tools_used.append("check_availability")
            results.append(result)

        elif tool_call == "book_slot":
            result = book_slot.invoke(arguments)
            tools_used.append("book_slot")
            results.append(result)

        elif tool_call == "list_events":
            raw_result = list_events.invoke(arguments)
            tools_used.append("list_events")

            if raw_result and isinstance(raw_result, list):
                lines = ["📋 **Upcoming Events:**"]
                for event in raw_result:
                    summary = event.get("summary", "No Title")
                    date_str = event.get("date", "")
                    time_str = event.get("time", "")
                    description = event.get("description", "")
                    link = event.get("link", "")

                    desc_text = f"\n  📝 {description}" if description else ""
                    link_text = f"\n  🔗 [Open in Calendar]({link})" if link else ""

                    lines.append(f"• **{summary}** - {date_str} {time_str}{desc_text}{link_text}")

                response_text = "\n".join(lines)
                results.append(response_text)
            else:
                results.append("📭 No upcoming events found in your calendar.")

        else:
            results.append(f"⚠️ Unknown tool call: `{tool_call}`")

    except Exception as e:
        results.append(f"❌ Tool execution error: {str(e)}")

    # Append user-visible summary to messages
    state["messages"].append({
        "role": "user",
        "content": "\n".join(results)
    })

    # Continue conversation with LLM
    follow_up = call_openrouter(
        [{"role": "system", "content": build_system_prompt()}] + state["messages"]
    )
    state["messages"].append({"role": "assistant", "content": follow_up})
    state["tool_calls_made"] += tools_used

    # Debug:
    # print("[DEBUG] tool_execution_node updated state:", state)

    return state



def output_node(state: TailorTalkState) -> TailorTalkState:
    print("[DEBUG] output_node:", state)
    return state

def create_tailortalk_graph():
    graph = StateGraph(TailorTalkState)
    graph.add_node("user_input", user_input_node)
    graph.add_node("llm", llm_node)
    graph.add_node("router", router_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("tool_execution", tool_execution_node)
    graph.add_node("output", output_node)

    graph.add_edge("user_input", "llm")
    graph.add_edge("llm", "router")
    graph.add_conditional_edges(
        "router",
        lambda state: router_node(state)["next"],
        {
            "tool_execution": "tool_execution",
            "clarification": "clarification",
            "output": "output"
        }
    )
    graph.add_edge("tool_execution", "output")
    graph.add_edge("clarification", "output")
    graph.add_edge("output", END)
    graph.set_entry_point("user_input")
    return graph.compile()

conversation_sessions = {}

def get_agent_response(message: str, user_id: str = "default") -> str:
    try:
        if user_id not in conversation_sessions:
            conversation_sessions[user_id] = {
                "messages": [],
                "user_id": user_id,
                "pending_clarification": False,
                "tool_calls_made": [],
                "session_context": {}
            }

        state = conversation_sessions[user_id]
        state["messages"].append({"role": "user", "content": message})

        graph = create_tailortalk_graph()
        result = graph.invoke(state)
        conversation_sessions[user_id] = result

        last_msg = result["messages"][-1]
        return last_msg["content"] if last_msg["role"] == "assistant" else "Sorry, could not process the request."
    except Exception as e:
        return f"Sorry, internal error: {e}"
