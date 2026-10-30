# Package 18 — coordinated model management

NeuralModelController integrates Model Registry, Model Lifecycle, Resource Governor, and evaluation gates. Activation requires READY state and a passing evaluation. Rollback requires the previous version to be READY; active versions cannot be unloaded.

ProcessMemory reports the Python process RSS using Windows APIs or Linux /proc/self/status. It is diagnostic only, not an enforced RAM limit and not the combined memory of Ollama subprocesses.

No actual model weights are loaded or live inference engines switched. Tests: tests/test_neural_model_controller.py.
