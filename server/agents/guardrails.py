import re
from users.utils import log_audit_event

class AIGuardrail:
    # High-risk Prompt Injection & Jailbreak Regular Expressions
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
        r"(?i)you\s+are\s+now\s+a",
        r"(?i)system\s+prompt",
        r"(?i)</?system_prompt>",
        r"(?i)jailbreak",
        r"(?i)override\s+(system|safety|rules)",
        r"(?i)print\s+(your\s+)?(exact\s+)?system",
        r"(?i)drop\s+table",
        r"(?i)<script.*?>",
        r"(?i)eval\(",
        r"(?i)exec\(",
        r"(?i)base64",
    ]

    @classmethod
    def inspect(cls, prompt_text, user=None, request=None):
        if not prompt_text:
            return True, None

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, prompt_text):
                # Log security violation in AuditLog for Student 1 & 2 evidence
                if user:
                    log_audit_event(
                        user=user,
                        action='AI_GUARDRAIL_VIOLATION',
                        details=f"Blocked prompt injection pattern: '{pattern}' in input: '{prompt_text[:100]}'",
                        request=request
                    )
                return False, f"Query blocked by AI Guardrail Safety Filter. Jailbreak / Prompt Injection pattern detected: ({pattern})"

        return True, None
