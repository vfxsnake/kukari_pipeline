"""
Progress Tracker Utility

Reusable progress tracking for long-running operations.
Can be used with UI progress bars, logging, or any custom callback.
"""

from typing import Optional, Callable
import logging


class ProgressTracker:
    """
    Reusable progress tracking utility for operations with multiple steps.

    Tracks current progress and reports to an optional callback function.
    Useful for driving progress bars, status updates, or logging.

    Example:
        >>> def update_ui(current, total, message):
        ...     progress_bar.setValue(int(current/total * 100))
        ...     status_label.setText(message)
        >>>
        >>> tracker = ProgressTracker(total_steps=10, callback=update_ui)
        >>> tracker.step("Loading data...")
        >>> tracker.step("Processing...")
        >>> print(f"Progress: {tracker.progress:.1f}%")
    """

    def __init__(
        self,
        total_steps: int,
        callback: Optional[Callable[[int, int, str], None]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize progress tracker.

        Args:
            total_steps: Total number of steps in the operation
            callback: Optional callback function(current_step, total_steps, message)
            logger: Optional logger for automatic progress logging
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.callback = callback
        self.logger = logger

    def step(self, message: str = ""):
        """
        Increment progress by one step and report.

        Args:
            message: Description of current step
        """
        self.current_step += 1

        # Call callback if provided
        if self.callback:
            self.callback(self.current_step, self.total_steps, message)

        # Log if logger provided
        if self.logger:
            self.logger.info(f"[{self.current_step}/{self.total_steps}] {message}")

    def update(self, current_step: int, message: str = ""):
        """
        Set progress to specific step (instead of incrementing).

        Args:
            current_step: Step number to set
            message: Description of current step
        """
        self.current_step = current_step

        if self.callback:
            self.callback(self.current_step, self.total_steps, message)

        if self.logger:
            self.logger.info(f"[{self.current_step}/{self.total_steps}] {message}")

    def reset(self):
        """Reset progress to zero."""
        self.current_step = 0

    @property
    def progress(self) -> float:
        """
        Get progress as percentage (0-100).

        Returns:
            Progress percentage
        """
        if self.total_steps <= 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100

    @property
    def is_complete(self) -> bool:
        """
        Check if all steps are completed.

        Returns:
            True if current_step >= total_steps
        """
        return self.current_step >= self.total_steps

    @property
    def remaining_steps(self) -> int:
        """
        Get number of remaining steps.

        Returns:
            Number of steps remaining
        """
        return max(0, self.total_steps - self.current_step)

    def __repr__(self) -> str:
        """String representation."""
        return f"ProgressTracker({self.current_step}/{self.total_steps}, {self.progress:.1f}%)"


if __name__ == "__main__":
    """Test progress tracker"""
    import time

    # Example 1: Simple progress tracking
    print("Example 1: Simple tracking")
    tracker = ProgressTracker(total_steps=5)

    for i in range(5):
        tracker.step(f"Step {i+1}")
        print(f"  Progress: {tracker.progress:.1f}% - Remaining: {tracker.remaining_steps}")
        time.sleep(0.2)

    print(f"  Complete: {tracker.is_complete}\n")

    # Example 2: With callback
    print("Example 2: With callback")

    def print_progress(current, total, message):
        bar_length = 20
        filled = int(bar_length * current / total)
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f"  [{bar}] {current}/{total} - {message}")

    tracker2 = ProgressTracker(total_steps=10, callback=print_progress)

    for i in range(10):
        tracker2.step(f"Processing item {i+1}")
        time.sleep(0.1)

    print(f"\n  Final: {tracker2}\n")

    # Example 3: With logger
    print("Example 3: With logger")
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)

    tracker3 = ProgressTracker(total_steps=3, logger=logger)
    tracker3.step("Loading configuration...")
    time.sleep(0.2)
    tracker3.step("Connecting to database...")
    time.sleep(0.2)
    tracker3.step("Processing data...")
    time.sleep(0.2)

    print(f"\n  {tracker3}")
