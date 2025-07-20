

import re
import random
import os
import sys
from importlib import resources

def load_steps_from_file(file_path):
    """
    Loads step content from a text file.
    Steps are separated by '---STEP_START---'.
    Each step has a title (first line) and a description.
    """
    if not file_path:
        return [("Error", "Step content file not found.")]

    steps = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        raw_steps = content.split('---STEP_START---')
        for raw_step in raw_steps:
            if not raw_step.strip():
                continue
            
            step_content = raw_step.split('---STEP_END---')[0].strip()
            
            title_end_idx = step_content.find('\n')
            if title_end_idx != -1:
                title = step_content[:title_end_idx].strip()
                description = step_content[title_end_idx:].strip()
            else:
                title = step_content
                description = ""
            
            steps.append((title, description))
    except FileNotFoundError:
        print(f"Error: Could not find the steps content file at '{file_path}'.")
        return [("Error", f"Content file not found:\n{file_path}")]
    
    return steps

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    STEPS_FILE_PATH = os.path.join(sys._MEIPASS, 'config', 'steps_content.txt')
else:
    # Running in a normal Python environment
    STEPS_FILE_PATH = str(resources.files('src.config').joinpath('steps_content.txt'))
STEPS = load_steps_from_file(STEPS_FILE_PATH)

class FocusStepsPresenter:
    def __init__(self, initial_step_index: int = 0, steps: list = None):
        self.current_step_index = initial_step_index
        self.content_steps = steps if steps is not None else STEPS # Store content steps separately
        self.all_steps = self.content_steps + [("Finished", "May your prayers be accepted.")]
        self.view = None

    def attach_view(self, view):
        self.view = view

    def _get_current_step_data(self):
        is_final_step = self.current_step_index == len(self.content_steps)
        title, description = self.all_steps[self.current_step_index]
        
        total_content_steps = len(self.content_steps)
        prev_enabled = self.current_step_index > 0
        next_enabled = self.current_step_index < len(self.content_steps)
        step_counter_text = f"{self.current_step_index + 1} / {total_content_steps}" if not is_final_step else ""
        action_button_text = "إغلاق" if is_final_step else "تم"

        return {
            "title": title,
            "description": description,
            "is_final_step": is_final_step,
            "current_step": self.current_step_index,
            "total_steps": total_content_steps, # Use total_content_steps here
            "prev_enabled": prev_enabled,
            "next_enabled": next_enabled,
            "step_counter_text": step_counter_text,
            "action_button_text": action_button_text,
        }

    def _notify_view_update(self):
        if self.view:
            step_data = self._get_current_step_data()
            
            parsed_description = self.parse_step_description(step_data["description"])
            self.view.display_step_content(step_data["title"], parsed_description)
            self.view.set_navigation_state(
                step_data["prev_enabled"],
                step_data["next_enabled"],
                step_data["step_counter_text"],
                step_data["action_button_text"]
            )
            
            # Decide whether to play sound based on step progression or other logic
            # For now, we'll assume sound plays on every step update.
            self.view.play_completion_sound()

    def go_to_next_step(self):
        if self.current_step_index < len(self.content_steps): # Use content_steps for navigation limit
            self.current_step_index += 1
            self._notify_view_update()

    def go_to_previous_step(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self._notify_view_update()

    def handle_action(self):
        if self.current_step_index == len(self.content_steps): # Use content_steps for final step check
            if self.view:
                self.view.close_view()
        else:
            self.go_to_next_step()

    def parse_step_description(self, description):
        goal_pattern = re.compile(r'\*\*الهدف:\*\*\s*(.*?)(?=\n\d+\.\s\*\*الدليل:|\Z)', re.DOTALL)
        evidence_pattern = re.compile(r'\d+\.\s\*\*الدليل:\*\*\s*(.*?)\s*\*الفائدة الروحية:\*\s*(.*?)(?=\n\d+\.\s\*\*الدليل:|\Z)', re.DOTALL)
        
        goals = goal_pattern.findall(description)
        evidences = evidence_pattern.findall(description)

        display_items = []
        if goals:
            display_items.append(('goal', random.choice(goals).strip()))
        if evidences:
            evidence_text, benefit_text = random.choice(evidences)
            display_items.append(('evidence', (evidence_text.strip(), benefit_text.strip())))
        
        random.shuffle(display_items)

        if not display_items:
            return [('content', description)]

        parsed_content = []
        for item_type, content in display_items:
            if item_type == 'goal':
                parsed_content.append(('title', '<b>الهدف:</b>'))
                parsed_content.append(('content', content))
            elif item_type == 'evidence':
                evidence_text, benefit_text = content
                parsed_content.append(('title', '<b>الدليل:</b>'))
                parsed_content.append(('content', evidence_text))
                parsed_content.append(('title', '<em>الفائدة الروحية:</em>'))
                parsed_content.append(('content', benefit_text))
        
        return parsed_content

