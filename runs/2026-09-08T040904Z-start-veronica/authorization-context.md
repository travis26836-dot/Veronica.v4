# Authorization context

User said "We're also going to need to start a new pod... configure this one to run for
at least 2 hours this time" (chat). Duration: 120 minutes (2 hours), explicitly requested.
Declined the separate "no automatic shutdown / run until stopped" request because it
violates the standing project rule requiring a bounded deadline for any paid GPU resource;
offered a longer bounded duration plus a future explicit-extend capability instead.

This run also includes a resilience patch to scripts/runpod_core.py: verify() now uses
fetch_with_retries() (3 attempts, 3s backoff) for the /models check and each chat-completion
call, so a single transient "Connection reset by peer"/RemoteDisconnected (like the one that
terminated the prior Pod x3m5b5zznxoski during its final verification step) does not throw
away an entire Pod. Real HTTP error statuses (401/403/etc, HTTPError) are still NOT retried
since they are not network blips. All existing tests plus 3 new retry-behavior tests pass
(full suite: 217 passed, 1 skipped via .venv).

GPU/ceiling/supervision per saved profile (A100 80GB, $1.75/hour, supervised shutdown from
this awake/connected computer).
