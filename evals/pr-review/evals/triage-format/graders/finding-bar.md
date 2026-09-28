---
type: llm
---

The PR changes `send_webhook` so that it retries every response with status 400 or higher, including permanent client errors
such as 401, 404, and 410, while the comment says it only retries when the receiver is temporarily unavailable. The caller
disables a subscription on those permanent errors, so retrying them delays that and wastes the delivery budget. The function
also has the short docstring "Send a webhook."

PASS if the review flags the retrying of permanent 4xx errors (or the misleading comment about it) as a finding, and does not
raise a finding asking to remove or expand the short docstring "Send a webhook."

FAIL if it misses the 4xx retry problem, or if it flags the short docstring as a finding.
