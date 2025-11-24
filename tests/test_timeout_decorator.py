"""
Test timeout decorator functionality.

Verifies that timeout decorator actually stops execution.
"""

import pytest
import time
import asyncio
import platform
from reroute.decorators import timeout


class TestTimeoutDecorator:
    """Test timeout decorator."""

    def test_async_timeout_triggers(self):
        """Test that async timeout actually stops execution."""
        @timeout(1)
        async def slow_async_function():
            """Function that takes too long."""
            await asyncio.sleep(3)
            return {"completed": True}

        # Run the async function
        result = asyncio.run(slow_async_function())

        # Should return timeout response
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 408
        assert response["error"] == "Request timeout"
        assert "1s" in response["limit"]

    def test_async_timeout_completes(self):
        """Test that async function completes within timeout."""
        @timeout(2)
        async def fast_async_function():
            """Function that completes quickly."""
            await asyncio.sleep(0.1)
            return {"completed": True}

        # Run the async function
        result = asyncio.run(fast_async_function())

        # Should complete successfully
        assert result == {"completed": True}

    @pytest.mark.skipif(
        platform.system() == 'Windows',
        reason="Signal-based timeout not available on Windows"
    )
    def test_sync_timeout_triggers_unix(self):
        """Test that sync timeout stops execution on Unix."""
        execution_completed = []

        @timeout(1)
        def slow_sync_function():
            """Function that takes too long."""
            time.sleep(3)
            execution_completed.append(True)
            return {"completed": True}

        # Call the function
        result = slow_sync_function()

        # Should return timeout response
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 408
        assert response["error"] == "Request timeout"

        # Function should NOT have completed (Unix signal stops it)
        assert len(execution_completed) == 0

    @pytest.mark.skipif(
        platform.system() != 'Windows',
        reason="Thread-based timeout fallback is Windows-specific"
    )
    def test_sync_timeout_triggers_windows(self):
        """Test that sync timeout returns on Windows (but function continues)."""
        @timeout(1)
        def slow_sync_function():
            """Function that takes too long."""
            time.sleep(3)
            return {"completed": True}

        # Call the function
        result = slow_sync_function()

        # Should return timeout response
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 408
        assert response["error"] == "Request timeout"
        # Should have warning about Windows limitation
        assert "warning" in response

    def test_sync_timeout_completes(self):
        """Test that sync function completes within timeout."""
        @timeout(2)
        def fast_sync_function():
            """Function that completes quickly."""
            time.sleep(0.1)
            return {"completed": True}

        # Call the function
        result = fast_sync_function()

        # Should complete successfully
        assert result == {"completed": True}

    def test_timeout_metadata(self):
        """Test that timeout decorator stores metadata."""
        @timeout(5)
        def test_function():
            return {"test": True}

        # Check metadata
        assert hasattr(test_function, '_timeout')
        assert test_function._timeout == 5

    def test_async_timeout_metadata(self):
        """Test that async timeout decorator stores metadata."""
        @timeout(10)
        async def test_async_function():
            return {"test": True}

        # Check metadata
        assert hasattr(test_async_function, '_timeout')
        assert test_async_function._timeout == 10

    def test_timeout_with_exception(self):
        """Test that timeout decorator handles exceptions."""
        @timeout(2)
        def error_function():
            """Function that raises an exception."""
            raise ValueError("Test error")

        # Should raise the exception
        with pytest.raises(ValueError, match="Test error"):
            error_function()

    def test_async_timeout_with_exception(self):
        """Test that async timeout decorator handles exceptions."""
        @timeout(2)
        async def async_error_function():
            """Async function that raises an exception."""
            await asyncio.sleep(0.1)
            raise ValueError("Test async error")

        # Should raise the exception
        with pytest.raises(ValueError, match="Test async error"):
            asyncio.run(async_error_function())

    @pytest.mark.skipif(
        platform.system() == 'Windows',
        reason="Signal-based timeout not available on Windows"
    )
    def test_sync_timeout_actually_stops_unix(self):
        """Test that sync timeout actually prevents function from completing on Unix."""
        side_effect = []

        @timeout(1)
        def slow_function_with_side_effect():
            """Function with side effects."""
            time.sleep(0.5)
            side_effect.append("started")
            time.sleep(2)  # This should be interrupted
            side_effect.append("completed")  # This should never execute
            return {"done": True}

        # Call the function
        result = slow_function_with_side_effect()

        # Should timeout
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 408

        # Side effect should show function started but never completed
        time.sleep(0.5)  # Give it time to potentially complete
        assert "started" in side_effect
        assert "completed" not in side_effect  # Should NOT be present
