"""Tests for TravelCalculator edge cases."""

from unittest.mock import patch

from custom_components.cover_time_based.travel_calculator import (
    TravelCalculator,
    TravelStatus,
)


class TestTravelCalculatorEdgeCases:
    """Test edge cases not covered by integration tests."""

    def test_stop_when_position_none(self):
        """stop() on a fresh calculator with no known position does nothing."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        assert calc.current_position() is None
        calc.stop()
        assert calc.current_position() is None
        assert calc.travel_direction == TravelStatus.STOPPED

    def test_start_travel_when_position_none(self):
        """start_travel() with unknown position snaps to target immediately."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        assert calc._last_known_position is None
        calc.start_travel(50)
        assert calc.current_position() == 50
        assert calc.travel_direction == TravelStatus.STOPPED

    def test_is_opening(self):
        """is_opening() returns True when traveling upward."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        calc.set_position(0)
        calc.start_travel(100)
        assert calc.is_opening() is True
        assert calc.is_closing() is False

    def test_is_closing(self):
        """is_closing() returns True when traveling downward."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        calc.set_position(100)
        calc.start_travel(0)
        assert calc.is_closing() is True
        assert calc.is_opening() is False

    def test_is_not_opening_when_stopped(self):
        """is_opening() returns False when not traveling."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        calc.set_position(50)
        assert calc.is_opening() is False

    def test_is_open(self):
        """is_open() returns True when at fully open position."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        calc.set_position(100)
        assert calc.is_open() is True

    def test_is_not_open(self):
        """is_open() returns False when not at fully open position."""
        calc = TravelCalculator(travel_time_down=30, travel_time_up=30)
        calc.set_position(0)
        assert calc.is_open() is False

    def test_position_returns_target_when_time_exceeded(self):
        """current_position() returns target when travel time has elapsed."""
        calc = TravelCalculator(travel_time_down=10, travel_time_up=10)
        calc.set_position(0)

        # Start travel, then advance time past the full travel duration
        with patch(
            "custom_components.cover_time_based.travel_calculator.time"
        ) as mock_time:
            mock_time.time.return_value = 1000.0
            calc.start_travel(100)
            # Now advance time past the travel duration (10s for full range)
            mock_time.time.return_value = 1020.0
            pos = calc.current_position()
            assert pos == 100

    def test_bottom_retract_time_included_only_when_opening_from_closed(self):
        """Opening from closed includes bottom retract time; mid-travel does not."""
        calc = TravelCalculator(
            travel_time_down=14,
            travel_time_up=15,
            bottom_retract_time_up=3,
        )

        assert calc.calculate_travel_time(0, 25) == 6.75
        assert calc.calculate_travel_time(50, 75) == 3.75

    def test_bottom_deploy_time_included_only_when_closing_to_closed(self):
        """Closing to closed includes bottom deploy time; mid-travel does not."""
        calc = TravelCalculator(
            travel_time_down=14,
            travel_time_up=15,
            bottom_deploy_time_down=3,
        )

        assert calc.calculate_travel_time(25, 0) == 6.5
        assert calc.calculate_travel_time(75, 50) == 3.5

    def test_position_stays_closed_during_bottom_retract(self):
        """Position remains 0 until bottom retract time has elapsed."""
        calc = TravelCalculator(
            travel_time_down=14,
            travel_time_up=15,
            bottom_retract_time_up=3,
        )
        calc.set_position(0)

        with patch(
            "custom_components.cover_time_based.travel_calculator.time"
        ) as mock_time:
            mock_time.time.return_value = 1000.0
            calc.start_travel(25)
            mock_time.time.return_value = 1002.0
            assert calc.current_position() == 0
            assert calc.is_opening() is True

            mock_time.time.return_value = 1004.875
            assert calc.current_position() == 12

    def test_position_stays_closed_during_bottom_deploy_while_closing(self):
        """Position is 0 during deploy tail but calculator still reports closing."""
        calc = TravelCalculator(
            travel_time_down=14,
            travel_time_up=15,
            bottom_deploy_time_down=3,
        )
        calc.set_position(25)

        with patch(
            "custom_components.cover_time_based.travel_calculator.time"
        ) as mock_time:
            mock_time.time.return_value = 1000.0
            calc.start_travel(0)
            mock_time.time.return_value = 1003.6
            assert calc.current_position() == 0
            assert calc.is_closing() is True
            assert calc.position_reached() is False

            mock_time.time.return_value = 1006.6
            assert calc.current_position() == 0
            assert calc.position_reached() is True
