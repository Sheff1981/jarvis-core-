# Package 12: Neural Core background scheduler

Implemented a bounded five-level priority queue with deadlines, Resource Governor admission, and diagnostic counters.

This is cooperative scheduling: running jobs cannot be preempted, no worker starts automatically, and the existing voice pipeline is unchanged. Jobs are deferred if logical memory admission fails.

Tests: tests/test_background_scheduler.py. Future work: real background-job integration and operating-system resource limits.
