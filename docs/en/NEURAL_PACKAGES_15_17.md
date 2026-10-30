# JARVIS Neural Core — packages 15–17

## Package 15 — Model lifecycle

IDLE, LOADING, READY, BUSY and EVICTING states, logical Resource Governor reservations, and refusal to evict a busy model.

## Package 16 — Model evaluation

Deterministic input/expected-output test cases, accuracy and exception accounting. Provisional policy: at least 10 cases, 95% accuracy, zero inference errors. This does not establish real-world model quality.

## Package 17 — Safe promotion

Only evaluated candidates can be promoted through the guarded interface; metadata rollback remains available.

Limitations: no actual model weights are loaded, no operating-system process is stopped, and live Ollama inference is unchanged. Physical integration and acceptance tests remain pending.
