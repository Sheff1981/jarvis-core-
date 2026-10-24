# Resource Governor

Package 11 introduces a logical 384 MB budget for future optional Neural Core jobs. Reservations are denied if the budget is exhausted. Releases require valid tokens. This is not physical RAM or CPU enforcement. Existing voice processing is unchanged.

Tests: tests/test_resource_governor.py.
