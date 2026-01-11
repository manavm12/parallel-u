"""OpenAI client for planning and synthesis."""

import json
from openai import OpenAI

from parallel_u.schemas import PlannerOutput, BriefOutput


class OpenAIClient:
    """Client for OpenAI API calls (planner + synthesizer)."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def plan(self, topics: list[str], depth: str, time_budget_min: int) -> PlannerOutput:
        """
        Generate an exploration plan based on user interests.

        Returns a structured plan with goal and browsing tasks.
        """
        system_prompt = """You are an intelligent exploration planner for "Parallel U" - a digital clone that browses the web on behalf of users.

Your job is to create a focused browsing plan based on the user's interests. You must output valid JSON matching the schema exactly.

Guidelines:
- Choose 1-2 relevant websites to browse (for MVP, prefer Hacker News or Reddit as they have rich content)
- Write clear, specific browsing instructions that a web automation tool can follow
- The goal should be specific and actionable for today's exploration
- Match the depth to the user's preference (shallow = headlines only, medium = read top discussions, deep = explore comments and linked articles)

Output JSON schema:
{
  "goal": "string - specific exploration goal for today",
  "tasks": [
    {
      "website": "string - full URL to start browsing",
      "instructions": "string - detailed instructions for what to look for and extract"
    }
  ]
}"""

        user_prompt = f"""Create a browsing plan for a user interested in: {', '.join(topics)}

Depth preference: {depth}
Time budget: {time_budget_min} minutes

Generate a focused plan with 1-2 browsing tasks that will find the most relevant, high-signal content for this user."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        result = json.loads(response.choices[0].message.content)
        return PlannerOutput(**result)

    def synthesize(
        self,
        goal: str,
        topics: list[str],
        browsing_results: list[dict]
    ) -> BriefOutput:
        """
        Synthesize browsing results into a condensed intelligence brief.

        Returns a structured brief with top findings, insights, and opportunities.
        """
        system_prompt = """You are the synthesis engine for "Parallel U" - a digital clone that delivers condensed intelligence to users.

Your job is to take raw browsing results and create a highly personalized, actionable brief. Output valid JSON matching the schema exactly.

CRITICAL RULES:
- You can ONLY report on information that is ACTUALLY present in the browsing results provided
- If the browsing results are empty, contain errors, or have no useful content, you MUST say so honestly
- NEVER make up or hallucinate information that wasn't in the actual browsing data
- If there's no real content, return empty top_3_things array and explain in one_deeper_insight

Guidelines (when you have real data):
- Focus on what matters most to THIS specific user based on their topics
- Be concrete and specific, not generic
- The "why_it_matters" should connect directly to the user's interests
- The deeper insight should reveal a non-obvious pattern
- The opportunity should be immediately actionable with a specific link if possible

Output JSON schema:
{
  "top_3_things": [
    {
      "title": "string - concise title",
      "summary": "string - 2-4 sentences explaining what this is",
      "why_it_matters": "string - why this matters to THIS user specifically",
      "source_link": "string - URL to the source"
    }
  ],
  "one_deeper_insight": "string - non-obvious pattern or implication across findings",
  "one_opportunity": "string - specific action with link if available",
  "sources_used": ["string - list of URLs consulted"]
}"""

        # Format browsing results for the prompt
        results_text = ""
        for i, result in enumerate(browsing_results, 1):
            results_text += f"\n--- Result {i} ---\n"
            results_text += f"Website: {result.get('website', 'Unknown')}\n"
            results_text += f"Status: {result.get('status', 'unknown')}\n"
            if result.get('error'):
                results_text += f"Error: {result.get('error')}\n"
            results_text += f"Content: {result.get('content', 'No content')}\n"

        user_prompt = f"""The user is interested in: {', '.join(topics)}

Exploration goal was: {goal}

Here are the raw browsing results:
{results_text}

Create a condensed intelligence brief with exactly 3 top findings (or fewer if the results don't support 3 meaningful findings - in that case, include what's available)."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )

        result = json.loads(response.choices[0].message.content)
        return BriefOutput(**result)

    def chat(
        self,
        question: str,
        goal: str,
        topics: list[str],
        brief: BriefOutput,
        browsing_results: list[dict],
        chat_history: list[dict],
    ) -> str:
        """
        Answer follow-up questions about the exploration results.

        Returns a natural language response.
        """
        system_prompt = f"""You are the conversational interface for "Parallel U" - a digital clone that has just explored the web for the user.

You have context about:
- The user's interests: {', '.join(topics)}
- The exploration goal: {goal}
- The findings from your exploration

Answer questions helpfully and specifically. Reference the actual content you found. If the user asks about something not covered in your exploration, acknowledge that and suggest it for future exploration.

Be conversational but concise. You can share additional details from the raw browsing results that weren't included in the main brief."""

        # Build context from brief and results
        brief_context = f"""
Your exploration summary:
- Top findings: {[f.title for f in brief.top_3_things]}
- Deeper insight: {brief.one_deeper_insight}
- Opportunity: {brief.one_opportunity}
- Sources: {brief.sources_used}
"""

        results_context = "\nRaw browsing data:\n"
        for result in browsing_results:
            results_context += f"- {result.get('website', 'Unknown')}: {result.get('content', '')[:2000]}...\n"

        messages = [
            {"role": "system", "content": system_prompt + brief_context + results_context},
        ]

        # Add chat history
        for msg in chat_history:
            messages.append(msg)

        # Add current question
        messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )

        return response.choices[0].message.content
