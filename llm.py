import json
from typing import Dict, Optional, List
from openai import OpenAI
from ..config import settings


LLM_SYSTEM_PROMPT = (
    "You are an expert meeting summarizer. "
    "Given a raw meeting transcript, produce concise, actionable outputs. "
    "Return JSON with fields: summary (string), decisions (string[]), action_items (string[])."
)


class LLMService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        key = api_key or settings.openai_api_key
        self.client = OpenAI(api_key=key) if key else OpenAI()
        self.model = model or settings.llm_model

    def summarize(self, transcript: str) -> Dict[str, object]:
        # Heuristic mode (no external API)
        if (settings.llm_provider or "openai").lower() == "heuristic":
            return self._heuristic_summary(transcript)

        user_prompt = (
            "Summarize this meeting transcript into key decisions and action items.\n"
            "Be concise but capture important details.\n"
            "Transcript:\n" + transcript
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content.strip()
        except Exception as e:
            if "insufficient_quota" in str(e) or "You exceeded your current quota" in str(e):
                return self._heuristic_summary(transcript)
            raise

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: wrap plain text as summary
            data = {
                "summary": content,
                "decisions": [],
                "action_items": [],
            }
        if not isinstance(data.get("decisions", []), list):
            data["decisions"] = []
        if not isinstance(data.get("action_items", []), list):
            data["action_items"] = []
        return data

    def _heuristic_summary(self, transcript: str) -> Dict[str, object]:
        # Very lightweight heuristic: take first ~5-7 long sentences as summary,
        # extract lines starting with verbs or explicit markers as decisions/actions.
        import re

        sentences = re.split(r"(?<=[.!?])\s+", transcript.strip())
        long_sentences: List[str] = [s for s in sentences if len(s.split()) >= 6]
        summary_sentences = long_sentences[:6] if long_sentences else sentences[:6]

        # Extract potential decisions and action items using simple patterns
        decision_patterns = [r"\bdecided to\b", r"\bconclude(d)?\b", r"\bagreed to\b", r"\bdecision\b"]
        action_patterns = [r"\bwill\b", r"\btodo\b", r"\baction item\b", r"\bassign(ed)? to\b", r"\bby (monday|tuesday|wednesday|thursday|friday|\d{1,2}\/[\d]{1,2})\b"]

        def find_matches(pats: List[str]) -> List[str]:
            out: List[str] = []
            for s in sentences:
                if any(re.search(p, s, flags=re.IGNORECASE) for p in pats):
                    out.append(s.strip(" -"))
            return out[:10]

        decisions = find_matches(decision_patterns)
        action_items = find_matches(action_patterns)

        return {
            "summary": " ".join(summary_sentences).strip(),
            "decisions": decisions,
            "action_items": action_items,
        }
