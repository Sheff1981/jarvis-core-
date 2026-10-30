# Neural Core — unified contour

Date: 2026-10-16. Status: UNFROZEN, INTEGRATION IN PROGRESS.

Implemented: logical resource governor, bounded job scheduler, metadata registry and persistence, lifecycle, evaluation, guarded promotion/rollback, local Ollama adapter, latency/RSS measurement, shadow evaluation. NeuralRuntime provides an optional inference facade and coordinates registry, lifecycle and attached backends. Controller activation, rollback and unload are serialized.

Not confirmed: physical Ollama runtime on laptop, real model weight loading in lifecycle, subprocess RAM enforcement, measured performance targets, training native model weights or production voice integration. Do not claim completion.

Contour acceptance requires Windows/Ubuntu CI, physical Ollama/error testing, laptop memory and load testing, documented rollback and opt-in integration with existing JARVIS. Until then: NOT ACCEPTED. Laptop updates only after owner command 'Выгружаем'. Main remains untouched.
