# Neural Core — architecture freeze

Date: 2026-10-16. Packages 11–21 form an isolated architectural foundation; final CI must pass before declaring this checkpoint verified.

11 Resource Governor; 12 Background Scheduler; 13 Model Registry; 14 JSON persistence; 15 Model Lifecycle; 16 Evaluation; 17 Safe Promotion; 18 NeuralModelController and ProcessMemory; 19 local Ollama adapter and callable backend contract; 20 latency/RSS telemetry; 21 isolated shadow evaluation.

These modules do NOT constitute trained JARVIS neural weights or an integrated production inference engine. ONNX execution, live Ollama switching, OS memory enforcement, voice integration, and physical laptop acceptance are outstanding. Shadow evaluation never routes answers to the user.

After CI success, freeze Neural Core feature expansion and return to N0 physical voice acceptance in docs/ru/VOICE_N0_ACCEPTANCE.md. Laptop updates require the owner's explicit 'Выгружаем' command. Do not modify main.
