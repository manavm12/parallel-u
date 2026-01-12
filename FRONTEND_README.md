# Parallel U - Streamlit Frontend

A clean, modern, minimalistic frontend for Parallel U built with Streamlit featuring a black and white color scheme.

## Features

- **AI-Powered Planning**: OpenAI automatically plans browsing tasks based on your topics (no hardcoded URLs!)
- **Live Browser Streaming**: Watch Mino browser automation in real-time with SSE (Server-Sent Events)
- **Tetra Browser URL Display**: See and access the live browser view URL extracted from streaming events
- **Personalized Synthesis**: AI synthesizes findings into actionable insights
- **Clean UI**: Minimalist black and white design with smooth animations
- **Chat Interface**: Ask questions about exploration findings

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables in `.env.local`:
```bash
MINO_API_KEY=your_mino_api_key
MINO_BASE_URL=https://mino.ai
BACKEND_URL=http://localhost:8000  # Optional, for full mode
OPENAI_API_KEY=your_openai_api_key  # Optional, for full mode
```

3. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

Or with uv:
```bash
uv run streamlit run streamlit_app.py
```

## Usage

### Prerequisites

1. Start the FastAPI backend:
```bash
uvicorn parallel_u.api.main:app --reload
```

2. Make sure you have API keys in `.env.local`:
   - `OPENAI_API_KEY` - for planning and synthesis
   - `MINO_API_KEY` - for browser automation

### Running an Exploration

1. Enter topics you want to explore (comma-separated)
   - Example: "AI agents, web automation, browser APIs"
2. Select exploration depth (shallow/medium/deep)
3. Set time budget in minutes
4. Click "Start Exploration"

**What happens:**
1. **Planning**: OpenAI creates a browsing plan with specific websites and tasks
2. **Browsing**: For each task, you'll see:
   - The website and instructions
   - A clickable link to the **live Tetra browser view** (extracted from Mino events)
   - Real-time streaming events in a terminal-style viewer
3. **Synthesis**: AI creates a personalized brief with:
   - Top 3 findings
   - Deeper insights
   - Actionable opportunities
4. **Chat**: Ask follow-up questions about the findings

## Design

The frontend features:

- **Minimalist black and white color scheme**
- **Terminal-style stream viewer** with color-coded events:
  - 🔵 Blue: STARTED events
  - 🟡 Yellow: PROGRESS events
  - 🟢 Green: COMPLETE events
  - 🔴 Red: ERROR events
- **Card-based layout** for findings and results
- **Responsive design** that works on all screen sizes
- **Clean typography** with proper hierarchy

## Architecture

```
streamlit_app.py
├── Stream Mino browser automation via SSE
├── Display events in real-time
├── Parse and format results
└── Optional: Integrate with FastAPI backend for full exploration
```

## API Integration

The frontend can work in two modes:

1. **Demo Mode**: Direct integration with Mino API for browser streaming
2. **Full Mode**: Integration with Parallel U FastAPI backend for complete exploration cycles

## Troubleshooting

- **"MINO_API_KEY not found"**: Make sure `.env.local` exists with your Mino API key
- **Connection errors**: Check that the backend is running if using Full Mode
- **Stream not updating**: Refresh the page and try again

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Save exploration history
- [ ] Export results to PDF/Markdown
- [ ] Real-time browser screenshot display
- [ ] Multi-session management
