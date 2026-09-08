# Authorization context

User said "The pod was terminated- well restart it." (chat, 2026-09-08T03:41:00Z). The prior Pod
(fzytn6eyb3exi3) was NOT stopped by me manually; its local watchdog fired at the
pre-agreed 1-hour deadline (2026-09-08T03:36:47Z), confirmed clean termination, and
retained the persistent model volume (v53gj9flzs). This is a genuinely new "Start
Veronica" request for a fresh Pod. Duration: 1 hour (default, user unavailable to
answer live). GPU/ceiling/supervision per saved profile (A100 80GB, $1.75/hour,
supervised shutdown from this awake/connected computer). This session also patched
src/veronica_core/provider.py health() to use a more tolerant timeout (5s -> 10s)
with one retry, to reduce false "offline" flapping from brief WAN/tunnel latency;
all tests pass (188 passed, 1 skipped via .venv).
