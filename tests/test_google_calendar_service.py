import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
from src.calendar_api.google_calendar import GoogleCalendarService

class TestGoogleCalendarService(unittest.TestCase):

    def setUp(self):
        self.mock_creds = Mock()
        self.mock_service = Mock()
        self.mock_events_list = Mock()
        self.mock_events_insert = Mock()
        self.mock_events_delete = Mock()

        self.mock_service.events.return_value.list.return_value = self.mock_events_list
        self.mock_service.events.return_value.insert.return_value = self.mock_events_insert
        self.mock_service.events.return_value.delete.return_value = self.mock_events_delete

        # Patch the build function to return our mock service
        patcher = patch('src.calendar_api.google_calendar.build', return_value=self.mock_service)
        self.mock_build = patcher.start()
        self.addCleanup(patcher.stop)

        self.service = GoogleCalendarService(self.mock_creds)

    def test_find_first_available_slot_no_events(self):
        # Mock no events returned
        self.mock_events_list.execute.return_value = {'items': []}

        start_time = datetime(2025, 7, 22, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        duration = 30
        expected_slot = start_time

        found_slot = self.service.find_first_available_slot(start_time, duration)
        self.assertEqual(found_slot, expected_slot)

    def test_find_first_available_slot_with_overlapping_event(self):
        # Mock an event that overlaps with the desired slot
        self.mock_events_list.execute.return_value = {
            'items': [
                {
                    'start': {'dateTime': '2025-07-22T09:15:00+00:00'},
                    'end': {'dateTime': '2025-07-22T09:45:00+00:00'}
                }
            ]
        }

        start_time = datetime(2025, 7, 22, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        duration = 30
        # Expected slot should be after the overlapping event ends
        expected_slot = datetime(2025, 7, 22, 9, 45, 0, tzinfo=ZoneInfo("UTC"))

        found_slot = self.service.find_first_available_slot(start_time, duration)
        self.assertEqual(found_slot, expected_slot)

    def test_find_first_available_slot_with_multiple_overlapping_events(self):
        # Mock multiple events that overlap
        self.mock_events_list.execute.return_value = {
            'items': [
                {
                    'start': {'dateTime': '2025-07-22T09:00:00+00:00'},
                    'end': {'dateTime': '2025-07-22T09:30:00+00:00'}
                },
                {
                    'start': {'dateTime': '2025-07-22T09:30:00+00:00'},
                    'end': {'dateTime': '2025-07-22T10:00:00+00:00'}
                }
            ]
        }

        start_time = datetime(2025, 7, 22, 8, 0, 0, tzinfo=ZoneInfo("UTC")) # Start before any events
        duration = 30
        # Expected slot should be after all overlapping events end
        expected_slot = start_time

        found_slot = self.service.find_first_available_slot(start_time, duration)
        self.assertEqual(found_slot, expected_slot)

    def test_find_first_available_slot_event_after_desired_slot(self):
        # Mock an event that starts after the desired slot
        self.mock_events_list.execute.return_value = {
            'items': [
                {
                    'start': {'dateTime': '2025-07-22T10:00:00+00:00'},
                    'end': {'dateTime': '2025-07-22T10:30:00+00:00'}
                }
            ]
        }

        start_time = datetime(2025, 7, 22, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
        duration = 30
        expected_slot = datetime(2025, 7, 22, 9, 0, 0, tzinfo=ZoneInfo("UTC")) # Should find the slot as it's before the event

        found_slot = self.service.find_first_available_slot(start_time, duration)
        self.assertEqual(found_slot, expected_slot)

    def test_add_event_success(self):
        self.mock_events_list.execute.return_value = {'items': []} # No existing events
        self.mock_events_insert.execute.return_value = {'id': 'new_event_id'}

        start_time = datetime(2025, 7, 22, 11, 0, 0, tzinfo=ZoneInfo("UTC"))
        summary = "Test Event"
        duration = 60

        result = self.service.add_event(start_time, summary, duration)
        self.assertTrue(result)
        self.mock_service.events().insert.assert_called_once()

    def test_add_event_duplicate(self):
        # Mock an existing event with the same summary
        self.mock_events_list.execute.return_value = {
            'items': [
                {
                    'summary': 'Existing Event',
                    'start': {'dateTime': '2025-07-22T11:00:00+00:00'},
                    'end': {'dateTime': '2025-07-22T12:00:00+00:00'}
                }
            ]
        }

        start_time = datetime(2025, 7, 22, 11, 0, 0, tzinfo=ZoneInfo("UTC"))
        summary = "Existing Event" # Same summary as existing
        duration = 60

        result = self.service.add_event(start_time, summary, duration)
        self.assertFalse(result)
        self.mock_service.events().insert.assert_not_called() # Should not try to insert

    def test_add_event_finds_new_slot_due_to_conflict(self):
        # Mock an existing event that conflicts with the initial start_time
        self.mock_events_list.execute.return_value = {
            'items': [
                {
                    'start': {'dateTime': '2025-07-22T11:00:00+00:00'},
                    'end': {'dateTime': '2025-07-22T11:30:00+00:00'}
                }
            ]
        }

        initial_start_time = datetime(2025, 7, 22, 10, 45, 0, tzinfo=ZoneInfo("UTC"))
        summary = "Conflicting Event"
        duration = 30

        # Expected new start time should be after the conflicting event
        expected_new_start_time = datetime(2025, 7, 22, 11, 30, 0, tzinfo=ZoneInfo("UTC"))

        result = self.service.add_event(initial_start_time, summary, duration)
        self.assertTrue(result)

        # Assert that create_event was called with the new, non-conflicting start time
        call_args, kwargs = self.mock_service.events().insert.call_args
        inserted_event_body = kwargs['body']

        self.assertEqual(datetime.fromisoformat(inserted_event_body['start']['dateTime']), expected_new_start_time)
        self.assertEqual(inserted_event_body['summary'], summary)

if __name__ == '__main__':
    unittest.main()