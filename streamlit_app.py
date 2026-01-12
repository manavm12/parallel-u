"""Streamlit frontend for Parallel U - Your digital clone that explores the web."""

import streamlit as st
import httpx
import json
import asyncio
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Page configuration
st.set_page_config(
    page_title="Parallel U",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for black and white minimalist theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --bg-primary: #FFFFFF;
        --bg-secondary: #F8F9FA;
        --text-primary: #000000;
        --text-secondary: #6C757D;
        --border-color: #E9ECEF;
        --accent: #212529;
    }
    
    /* Dark mode */
    [data-theme="dark"] {
        --bg-primary: #000000;
        --bg-secondary: #1A1A1A;
        --text-primary: #FFFFFF;
        --text-secondary: #A0A0A0;
        --border-color: #2A2A2A;
        --accent: #FFFFFF;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--bg-primary);
    }
    
    /* Header */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: var(--text-primary);
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    /* Input sections */
    .stTextInput > div > div > input {
        border: 2px solid var(--border-color);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 1rem;
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--accent);
        color: var(--bg-primary);
        border: none;
        border-radius: 8px;
        padding: 12px 32px;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    
    /* Cards */
    .card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    
    .card-text {
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    /* Stream container */
    .stream-container {
        background-color: #000000;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.9rem;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .stream-event {
        color: #00FF00;
        margin: 4px 0;
        padding: 4px 0;
        border-bottom: 1px solid #1A1A1A;
    }
    
    .stream-event-type {
        color: #FFFFFF;
        font-weight: 600;
    }
    
    .stream-event-started {
        color: #00BFFF;
    }
    
    .stream-event-progress {
        color: #FFD700;
    }
    
    .stream-event-complete {
        color: #00FF00;
    }
    
    .stream-event-error {
        color: #FF4444;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'exploration_running' not in st.session_state:
        st.session_state.exploration_running = False
    if 'stream_events' not in st.session_state:
        st.session_state.stream_events = []
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None


async def stream_mino_automation(url: str, goal: str, api_key: str, base_url: str = "https://mino.ai"):
    """Stream Mino browser automation events."""
    endpoint = f"{base_url.rstrip('/')}/v1/automation/run-sse"
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    
    payload = {
        "url": url,
        "goal": goal,
        "browser_profile": "lite",
    }
    
    events = []
    result = {
        "website": url,
        "content": "",
        "status": "pending",
        "browser_url": None,
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}: {await response.aread()}"
                    error_event = {"type": "ERROR", "message": error_msg}
                    result["status"] = "error"
                    result["error"] = error_msg
                    yield error_event, result
                    return
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type", "")
                        
                        events.append(event)
                        
                        if event_type == "STARTED":
                            result["run_id"] = event.get("runId")
                            result["status"] = "running"
                            # Extract Tetra browser URL from the event
                            browser_url = event.get("browserUrl") or event.get("url") or event.get("viewUrl") or event.get("streamingUrl")
                            if browser_url:
                                result["browser_url"] = browser_url
                        elif event_type == "STREAMING_URL":
                            # Capture the streaming URL from STREAMING_URL event
                            streaming_url = event.get("streamingUrl")
                            if streaming_url:
                                result["browser_url"] = streaming_url
                        elif event_type == "PROGRESS":
                            # Check for browser URL in progress events too
                            browser_url = event.get("browserUrl") or event.get("url") or event.get("viewUrl") or event.get("streamingUrl")
                            if browser_url and not result["browser_url"]:
                                result["browser_url"] = browser_url
                        elif event_type == "COMPLETE":
                            status = event.get("status", "")
                            result["status"] = status.lower()
                            if status == "COMPLETED":
                                result_json = event.get("resultJson", {})
                                result["content"] = json.dumps(result_json, indent=2) if isinstance(result_json, dict) else str(result_json)
                            else:
                                result["error"] = f"Automation {status}"
                        
                        yield event, result
                        
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        error_event = {"type": "ERROR", "message": str(e)}
        events.append(error_event)
        result["status"] = "error"
        result["error"] = str(e)
        yield error_event, result


async def run_exploration(topics: list[str], depth: str, time_budget: int, user_id: str, backend_url: str):
    """Run the full exploration via the backend API."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{backend_url}/v1/run",
            json={
                "user_id": user_id,
                "topics": topics,
                "depth": depth,
                "time_budget_min": time_budget,
            }
        )
        response.raise_for_status()
        return response.json()


def render_stream_event(event: dict):
    """Render a single stream event."""
    event_type = event.get("type", "UNKNOWN")
    timestamp = event.get("timestamp", "")
    
    color_map = {
        "STARTED": "stream-event-started",
        "STREAMING_URL": "stream-event-started",
        "PROGRESS": "stream-event-progress",
        "COMPLETE": "stream-event-complete",
        "ERROR": "stream-event-error",
    }
    
    color_class = color_map.get(event_type, "stream-event")
    
    if event_type == "STARTED":
        run_id = event.get("runId", "")
        return f'<div class="stream-event {color_class}"><span class="stream-event-type">[STARTED]</span> Run ID: {run_id}</div>'
    elif event_type == "STREAMING_URL":
        streaming_url = event.get("streamingUrl", "")
        return f'<div class="stream-event {color_class}"><span class="stream-event-type">[STREAMING_URL]</span> 🔗 {streaming_url}</div>'
    elif event_type == "PROGRESS":
        # PROGRESS events may have different fields - show what's available
        message = event.get("message") or event.get("status") or event.get("action") or event.get("step")
        if message:
            return f'<div class="stream-event {color_class}"><span class="stream-event-type">[PROGRESS]</span> {message}</div>'
        else:
            # Show the full event data if no standard message field
            event_data = {k: v for k, v in event.items() if k not in ["type", "timestamp"]}
            if event_data:
                return f'<div class="stream-event {color_class}"><span class="stream-event-type">[PROGRESS]</span> {json.dumps(event_data)}</div>'
            else:
                return f'<div class="stream-event {color_class}"><span class="stream-event-type">[PROGRESS]</span> ...</div>'
    elif event_type == "COMPLETE":
        status = event.get("status", "")
        return f'<div class="stream-event {color_class}"><span class="stream-event-type">[COMPLETE]</span> Status: {status}</div>'
    elif event_type == "ERROR":
        message = event.get("message", "")
        return f'<div class="stream-event {color_class}"><span class="stream-event-type">[ERROR]</span> {message}</div>'
    elif event_type == "HEARTBEAT":
        return f'<div class="stream-event"><span class="stream-event-type">[HEARTBEAT]</span></div>'
    else:
        return f'<div class="stream-event"><span class="stream-event-type">[{event_type}]</span> {json.dumps(event)}</div>'


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">Parallel U</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your digital clone that explores the web while you\'re busy</p>', unsafe_allow_html=True)
    
    # Main content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Input section
        st.markdown("### 🎯 What should I explore?")
        
        topics_input = st.text_input(
            "Topics (comma-separated)",
            placeholder="e.g., AI agents, web automation, browser APIs",
            help="Enter topics you want your digital clone to explore"
        )
        
        col_a, col_b = st.columns(2)
        with col_a:
            depth = st.selectbox(
                "Exploration Depth",
                ["shallow", "medium", "deep"],
                index=1,
                help="How deep should the exploration go?"
            )
        
        with col_b:
            time_budget = st.number_input(
                "Time Budget (minutes)",
                min_value=1,
                max_value=60,
                value=5,
                help="How much time to spend exploring"
            )
        
        user_id = st.text_input(
            "User ID",
            value="demo_user",
            help="Your unique identifier"
        )
        
        # Start button
        if st.button("🚀 Start Exploration", type="primary"):
            if not topics_input:
                st.error("Please enter at least one topic")
                return
            
            topics = [t.strip() for t in topics_input.split(",")]
            
            # Get API keys
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            
            # Step 1: Get the plan from backend
            st.markdown("---")
            st.markdown("### 🧠 Planning Exploration...")
            
            with st.spinner("Creating browsing plan"):
                try:
                    # Call backend to get plan
                    async def get_plan():
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            response = await client.post(
                                f"{backend_url}/v1/plan",
                                json={
                                    "user_id": user_id,
                                    "topics": topics,
                                    "depth": depth,
                                    "time_budget_min": time_budget,
                                }
                            )
                            response.raise_for_status()
                            return response.json()
                    
                    plan_data = asyncio.run(get_plan())
                    goal = plan_data.get("goal", "")
                    tasks = plan_data.get("tasks", [])
                    
                    st.success(f"✅ Plan created: {goal}")
                    st.markdown(f"**{len(tasks)} browsing tasks planned**")
                    
                except Exception as e:
                    # If backend doesn't have /v1/plan endpoint, use /v1/run directly
                    st.info("Using full exploration endpoint...")
                    
                    with st.spinner("🔄 Running exploration..."):
                        try:
                            results = asyncio.run(run_exploration(
                                topics=topics,
                                depth=depth,
                                time_budget=time_budget,
                                user_id=user_id,
                                backend_url=backend_url
                            ))
                            
                            st.session_state.results = results
                            st.session_state.session_id = results.get("session_id")
                            
                            # Display results
                            st.markdown("---")
                            st.markdown("### 📊 Exploration Results")
                            
                            st.markdown(f"**Goal:** {results.get('goal', 'N/A')}")
                            
                            brief = results.get("brief", {})
                            
                            # Top 3 findings
                            st.markdown("#### 🔍 Top 3 Findings")
                            for i, finding in enumerate(brief.get("top_3_things", []), 1):
                                with st.expander(f"**{i}. {finding.get('title', 'N/A')}**", expanded=True):
                                    st.markdown(f"**Summary:** {finding.get('summary', 'N/A')}")
                                    st.markdown(f"**Why it matters:** {finding.get('why_it_matters', 'N/A')}")
                                    st.markdown(f"**Source:** [{finding.get('source_link', 'N/A')}]({finding.get('source_link', '#')})")
                            
                            # Deeper insight
                            st.markdown("#### 💡 Deeper Insight")
                            st.info(brief.get("one_deeper_insight", "N/A"))
                            
                            # Opportunity
                            st.markdown("#### 🎯 Opportunity")
                            st.success(brief.get("one_opportunity", "N/A"))
                            
                            # Sources
                            with st.expander("📚 Sources Used"):
                                for source in brief.get("sources_used", []):
                                    st.markdown(f"- [{source}]({source})")
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    return
            
            # Step 2: Stream each browsing task
            st.markdown("---")
            st.markdown("### 🌐 Live Browser Automation")
            
            mino_api_key = os.getenv("MINO_API_KEY")
            if not mino_api_key:
                st.error("MINO_API_KEY not found in environment variables")
                return
            
            all_results = []
            
            for i, task in enumerate(tasks, 1):
                st.markdown(f"#### Task {i}/{len(tasks)}: {task.get('website', 'N/A')}")
                st.markdown(f"*{task.get('instructions', 'N/A')}*")
                
                # Browser URL placeholder
                browser_url_placeholder = st.empty()
                
                # Stream placeholder
                stream_placeholder = st.empty()
                
                async def run_task():
                    stream_html = '<div class="stream-container">'
                    browser_url_shown = False
                    
                    async for event, result in stream_mino_automation(
                        url=task.get("website"),
                        goal=task.get("instructions"),
                        api_key=mino_api_key,
                        base_url=os.getenv("MINO_BASE_URL", "https://mino.ai")
                    ):
                        # Display browser URL if available
                        if result.get("browser_url") and not browser_url_shown:
                            browser_url_placeholder.markdown(
                                f'### 🔗 [Open Live Browser View]({result["browser_url"]}) ↗️',
                                unsafe_allow_html=True
                            )
                            browser_url_shown = True
                        
                        stream_html += render_stream_event(event)
                        stream_placeholder.markdown(stream_html + '</div>', unsafe_allow_html=True)
                    
                    stream_html += '</div>'
                    stream_placeholder.markdown(stream_html, unsafe_allow_html=True)
                    
                    return result
                
                result = asyncio.run(run_task())
                all_results.append(result)
                
                # Show task completion status
                if result.get("status") == "completed":
                    st.success(f"✅ Task {i} completed")
                else:
                    st.error(f"❌ Task {i} failed: {result.get('error', 'Unknown error')}")
                
                st.markdown("---")
            
            # Step 3: Synthesize results
            st.markdown("### 🧪 Synthesizing Findings...")
            
            with st.spinner("Creating your personalized brief..."):
                try:
                    async def synthesize():
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            response = await client.post(
                                f"{backend_url}/v1/synthesize",
                                json={
                                    "goal": goal,
                                    "topics": topics,
                                    "browsing_results": all_results,
                                    "user_id": user_id,
                                }
                            )
                            response.raise_for_status()
                            return response.json()
                    
                    results = asyncio.run(synthesize())
                    st.session_state.results = results
                    st.session_state.session_id = results.get("session_id")
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("### 📊 Your Personalized Brief")
                    
                    st.markdown(f"**Goal:** {goal}")
                    
                    brief = results.get("brief", {})
                    
                    # Top 3 findings
                    st.markdown("#### 🔍 Top 3 Findings")
                    for i, finding in enumerate(brief.get("top_3_things", []), 1):
                        with st.expander(f"**{i}. {finding.get('title', 'N/A')}**", expanded=True):
                            st.markdown(f"**Summary:** {finding.get('summary', 'N/A')}")
                            st.markdown(f"**Why it matters:** {finding.get('why_it_matters', 'N/A')}")
                            st.markdown(f"**Source:** [{finding.get('source_link', 'N/A')}]({finding.get('source_link', '#')})")
                    
                    # Deeper insight
                    st.markdown("#### 💡 Deeper Insight")
                    st.info(brief.get("one_deeper_insight", "N/A"))
                    
                    # Opportunity
                    st.markdown("#### 🎯 Opportunity")
                    st.success(brief.get("one_opportunity", "N/A"))
                    
                    # Sources
                    with st.expander("📚 Sources Used"):
                        for source in brief.get("sources_used", []):
                            st.markdown(f"- [{source}]({source})")
                    
                except Exception as e:
                    st.error(f"❌ Synthesis error: {str(e)}")
        
        # Chat section (if session exists)
        if st.session_state.session_id:
            st.markdown("---")
            st.markdown("### 💬 Chat with Your Clone")
            
            chat_message = st.text_input("Ask a question about the findings...")
            
            if st.button("Send") and chat_message:
                backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                
                try:
                    async def send_chat():
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                f"{backend_url}/v1/chat",
                                json={
                                    "session_id": st.session_state.session_id,
                                    "message": chat_message,
                                }
                            )
                            response.raise_for_status()
                            return response.json()
                    
                    chat_response = asyncio.run(send_chat())
                    st.markdown(f"**Response:** {chat_response.get('response', 'N/A')}")
                    
                except Exception as e:
                    st.error(f"Chat error: {str(e)}")


if __name__ == "__main__":
    main()
