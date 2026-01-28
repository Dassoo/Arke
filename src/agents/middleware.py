from langchain.agents.middleware import (
    AgentMiddleware, AgentState, ContextEditingMiddleware, ClearToolUsesEdit, hook_config
)
from langgraph.runtime import Runtime
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from typing import Any


class SafetyGuardrail(AgentMiddleware):
    """
    A middleware class that implements safety guardrails for agent interactions.

    This middleware checks incoming human messages for unsafe content using a safety model.
    If unsafe content is detected, it prevents further processing and returns a safe response.
    """
    def __init__(self):
          super().__init__()
          self.model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation")
          self.tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation")

    @hook_config(can_jump_to=["end"])
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        if not state["messages"]:
            return None
        last_message = state["messages"][-1]
        if last_message.type != "human":
           return None

        content = last_message.content
        inputs = self.tokenizer(content, return_tensors="pt")
        outputs = self.model(**inputs)

        logits = outputs.logits
        probabilities = logits.softmax(dim=-1).squeeze()

        id2label = self.model.config.id2label
        labels = [id2label[idx] for idx in range(len(probabilities))]

        label_prob_pairs = list(zip(labels, probabilities))
        label_prob_pairs.sort(key=lambda item: item[1], reverse=True)  

        safety = False

        for label, probability in label_prob_pairs:
            if label == "OK" and probability > 0.75:
                safety = True
        
        if not safety:
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I cannot process requests containing inappropriate content."
                    }],
                    "jump_to": "end"
                }

        return None


custom_middleware = [
    SafetyGuardrail(),
    ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(
                trigger=100000,
                keep=3,
            ),
        ],
    ),
]
