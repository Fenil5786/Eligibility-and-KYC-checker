"""Microsoft Agentic Framework runtime adapter for enterprise orchestration.

Uses Semantic Kernel when installed, and falls back to local deterministic execution.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class RuntimeExecutionMeta:
    framework: str
    enterprise_mode: bool
    correlation_id: str
    started_at: str


class MicrosoftAgenticRuntime:
    """Enterprise runtime abstraction aligned to Microsoft agentic patterns."""

    def __init__(self, enterprise_mode: bool = True):
        self.enterprise_mode = enterprise_mode
        self.framework = "semantic-kernel" if self._semantic_kernel_available() else "local-fallback"

    def _semantic_kernel_available(self) -> bool:
        try:
            import semantic_kernel  # noqa: F401
            return True
        except Exception:
            return False

    def execution_meta(self, correlation_id: str) -> RuntimeExecutionMeta:
        return RuntimeExecutionMeta(
            framework=self.framework,
            enterprise_mode=self.enterprise_mode,
            correlation_id=correlation_id,
            started_at=datetime.utcnow().isoformat() + "Z",
        )

    def invoke_agent(self, agent: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke an agent through the runtime. Current version uses direct invocation.

        This method intentionally keeps a stable interface so the app can switch to
        full Semantic Kernel planners/plugins without changing orchestrator code.
        """
        return agent.run(context)
