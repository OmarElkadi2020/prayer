

import unittest
from unittest.mock import Mock
from src.presenter.focus_steps_presenter import FocusStepsPresenter

# Define a dummy STEPS list for consistent testing
DUMMY_STEPS = [
    ("Step 1 Title", "Step 1 Description"),
    ("Step 2 Title", "Step 2 Description"),
    ("Step 3 Title", "Step 3 Description"),
]

class TestFocusStepsPresenter(unittest.TestCase):

    def setUp(self):
        # Pass DUMMY_STEPS directly to the constructor
        self.presenter = FocusStepsPresenter(steps=DUMMY_STEPS)
        self.view = Mock()
        self.presenter.attach_view(self.view)

    def test_initial_state(self):
        self.assertEqual(self.presenter.current_step_index, 0)
        self.assertIsNotNone(self.presenter.all_steps)
        self.assertEqual(len(self.presenter.all_steps), len(DUMMY_STEPS) + 1) # DUMMY_STEPS + "Finished" step

    def test_attach_view(self):
        # No assertions here, as display_step_content is now called by the view's __init__
        pass

    def test_go_to_next_step(self):
        initial_index = self.presenter.current_step_index
        self.presenter.go_to_next_step()
        self.assertEqual(self.presenter.current_step_index, initial_index + 1)
        self.assertEqual(self.view.display_step_content.call_count, 1)
        self.assertEqual(self.view.set_navigation_state.call_count, 1)
        self.assertEqual(self.view.play_completion_sound.call_count, 1)

    def test_go_to_previous_step(self):
        self.presenter.go_to_next_step()
        initial_index = self.presenter.current_step_index
        self.presenter.go_to_previous_step()
        self.assertEqual(self.presenter.current_step_index, initial_index - 1)
        self.assertEqual(self.view.display_step_content.call_count, 2)
        self.assertEqual(self.view.set_navigation_state.call_count, 2)
        self.assertEqual(self.view.play_completion_sound.call_count, 2)

    def test_handle_action_next(self):
        initial_index = self.presenter.current_step_index
        self.presenter.handle_action()
        self.assertEqual(self.presenter.current_step_index, initial_index + 1)

    def test_handle_action_close(self):
        # Go to the last step (which is len(DUMMY_STEPS) for content steps)
        for _ in range(len(DUMMY_STEPS)):
            self.presenter.go_to_next_step()
        
        self.presenter.handle_action()
        self.view.close_view.assert_called_once()

    def test_parse_step_description(self):
        description = "**الهدف:** Goal text.\n1. **الدليل:** Evidence text. *الفائدة الروحية:* Benefit text."
        parsed_content = self.presenter.parse_step_description(description)
        self.assertIsInstance(parsed_content, list)
        self.assertGreater(len(parsed_content), 0)

    def test_get_current_step_data(self):
        # Test initial state
        data = self.presenter._get_current_step_data()
        self.assertIn("title", data)
        self.assertIn("description", data)
        self.assertFalse(data["is_final_step"])
        self.assertEqual(data["current_step"], 0)
        self.assertEqual(data["total_steps"], len(DUMMY_STEPS))
        self.assertFalse(data["prev_enabled"])
        self.assertTrue(data["next_enabled"])
        self.assertEqual(data["step_counter_text"], f"1 / {len(DUMMY_STEPS)}")
        self.assertEqual(data["action_button_text"], "تم")

        # Go to a middle step
        self.presenter.go_to_next_step()
        data = self.presenter._get_current_step_data()
        self.assertFalse(data["is_final_step"])
        self.assertEqual(data["current_step"], 1)
        self.assertTrue(data["prev_enabled"])
        self.assertTrue(data["next_enabled"])
        self.assertEqual(data["step_counter_text"], f"2 / {len(DUMMY_STEPS)}")
        self.assertEqual(data["action_button_text"], "تم")

        # Go to the final content step
        self.presenter.go_to_next_step() # Move from index 1 to 2 (last content step)
        data = self.presenter._get_current_step_data()
        self.assertFalse(data["is_final_step"]) # Should be False for the last content step
        self.assertEqual(data["current_step"], len(DUMMY_STEPS) - 1)
        self.assertTrue(data["prev_enabled"])
        self.assertTrue(data["next_enabled"]) # Should be True to go to "Finished" step
        self.assertEqual(data["step_counter_text"], f"{len(DUMMY_STEPS)} / {len(DUMMY_STEPS)}")
        self.assertEqual(data["action_button_text"], "تم")

        # Go to the "Finished" step
        self.presenter.go_to_next_step()
        data = self.presenter._get_current_step_data()
        self.assertTrue(data["is_final_step"])
        self.assertEqual(data["current_step"], len(DUMMY_STEPS))
        self.assertTrue(data["prev_enabled"])
        self.assertFalse(data["next_enabled"])
        self.assertEqual(data["step_counter_text"], "")
        self.assertEqual(data["action_button_text"], "إغلاق")


if __name__ == '__main__':
    unittest.main()

