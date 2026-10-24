# Package 14 — persistent model registry

Added atomic JSON snapshot writes and validated restoration after restart. Model cards, active versions and previous versions are preserved. Unsupported schemas and unknown version references are rejected.

Store the registry under local application data, not in GitHub. This module does not download model files or switch live inference backends.

Tests: tests/test_model_registry_storage.py.
