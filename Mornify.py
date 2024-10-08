import time
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from plyer import notification
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty, DictProperty

# Persistent storage file
ROUTINE_FILE = "routine.json"
THEME_FILE = "theme.json"

class RoutineReminderApp(App):
    theme = DictProperty({
        "background_color": [1, 1, 1, 1],  # White background
        "text_color": [0, 0, 0, 1],        # Black text
        "button_color": [0.2, 0.6, 0.86, 1] # Blue buttons
    })

    def build(self):
        self.sound = SoundLoader.load('alarm_sound.mp3')  # Load alarm sound
        self.routine = self.load_routine()  # Load routine from storage
        self.load_theme()  # Load theme from storage

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        with layout.canvas.before:
            Color(*self.theme['background_color'])
            self.rect = Rectangle(size=(layout.size), pos=layout.pos)

        layout.bind(size=self._update_rect, pos=self._update_rect)
        
        self.label = Label(text='Daily Routine Reminder', font_size='20sp', color=self.theme['text_color'])
        layout.add_widget(self.label)
        
        self.button_start = Button(text='Start Routine', background_color=self.theme['button_color'], on_press=self.start_routine)
        layout.add_widget(self.button_start)
        
        self.button_customize = Button(text='Customize Routine', background_color=self.theme['button_color'], on_press=self.open_customization_popup)
        layout.add_widget(self.button_customize)
        
        self.button_theme = Button(text='Change Theme', background_color=self.theme['button_color'], on_press=self.open_theme_popup)
        layout.add_widget(self.button_theme)
        
        return layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def load_routine(self):
        try:
            with open(ROUTINE_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                {"time": "08:00", "activity": "Wake Up", "duration": 30},
                {"time": "08:30", "activity": "Drink a glass of water", "duration": 5},
                {"time": "08:35", "activity": "Prayer and Worship", "duration": 15},
                {"time": "08:50", "activity": "Gentle Movement (Stretching/Yoga/Walk)", "duration": 20},
                {"time": "09:10", "activity": "Healthy Breakfast", "duration": 20},
                {"time": "09:30", "activity": "Focused Planning for the Day", "duration": 10},
                {"time": "09:40", "activity": "Start Productive Work Session", "duration": 60}
            ]

    def save_routine(self):
        with open(ROUTINE_FILE, 'w') as f:
            json.dump(self.routine, f, indent=4)

    def load_theme(self):
        try:
            with open(THEME_FILE, 'r') as f:
                self.theme.update(json.load(f))
        except FileNotFoundError:
            pass

    def save_theme(self):
        with open(THEME_FILE, 'w') as f:
            json.dump(self.theme, f, indent=4)

    def start_routine(self, instance):
        self.label.text = 'Routine Started'
        Clock.unschedule(self.check_time)  # Ensure no duplicate scheduling
        Clock.schedule_interval(self.check_time, 60)

    def check_time(self, dt):
        current_time = time.strftime("%H:%M")
        for i, task in enumerate(self.routine):
            if current_time == task["time"]:
                self.trigger_reminder(task)
                if i + 1 < len(self.routine):
                    next_task = self.routine[i + 1]
                    next_time = self.calculate_next_time(task["time"], task["duration"])
                    Clock.schedule_once(lambda dt: self.trigger_reminder(next_task), self.get_seconds_until(next_time))

    def calculate_next_time(self, start_time, duration):
        hour, minute = map(int, start_time.split(':'))
        minute += duration
        if minute >= 60:
            hour += minute // 60
            minute = minute % 60
        if hour >= 24:
            hour = hour % 24
        return f"{hour:02}:{minute:02}"

    def get_seconds_until(self, next_time):
        next_time_obj = time.strptime(next_time, "%H:%M")
        now_time_obj = time.strptime(time.strftime("%H:%M"), "%H:%M")
        delta = time.mktime(next_time_obj) - time.mktime(now_time_obj)
        return max(delta, 0)

    def trigger_reminder(self, task):
        notification.notify(
            title=f"Reminder: {task['activity']}",
            message=f"It's {task['time']} - Time for {task['activity']}",
            timeout=10
        )
        if self.sound:
            self.sound.play()
        self.label.text = f"Reminder: {task['activity']} at {task['time']}"

    def open_customization_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=3, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        self.inputs = []
        
        for task in self.routine:
            time_input = TextInput(text=task['time'], size_hint_y=None, height=30)
            activity_input = TextInput(text=task['activity'], size_hint_y=None, height=30)
            duration_input = TextInput(text=str(task.get('duration', '0')), size_hint_y=None, height=30)
            grid.add_widget(time_input)
            grid.add_widget(activity_input)
            grid.add_widget(duration_input)
            self.inputs.append((time_input, activity_input, duration_input))
        
        scroll.add_widget(grid)
        content.add_widget(scroll)
        
        save_button = Button(text='Save', size_hint_y=None, height=50, on_press=self.save_custom_routine)
        content.add_widget(save_button)
        
        popup = Popup(title='Customize Routine', content=content, size_hint=(0.8, 0.8))
        popup.open()

    def save_custom_routine(self, instance):
        self.routine = []
        for time_input, activity_input, duration_input in self.inputs:
            task = {
                "time": time_input.text,
                "activity": activity_input.text,
                "duration": int(duration_input.text)  # Ensure duration is an integer
            }
            self.routine.append(task)
        self.save_routine()
        self.label.text = 'Routine Updated'

    def open_theme_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        
        light_theme_button = Button(text='Light Theme', size_hint_y=None, height=50, on_press=self.set_light_theme)
        content.add_widget(light_theme_button)
        
        dark_theme_button = Button(text='Dark Theme', size_hint_y=None, height=50, on_press=self.set_dark_theme)
        content.add_widget(dark_theme_button)
        
        popup = Popup(title='Select Theme', content=content, size_hint=(0.5, 0.5))
        popup.open()

    def set_light_theme(self, instance):
        self.theme.update({
            "background_color": [1, 1, 1, 1],  # White background
            "text_color": [0, 0, 0, 1],        # Black text
            "button_color": [0.2, 0.6, 0.86, 1] # Blue buttons
        })
        self.apply_theme()
        
    def set_dark_theme(self, instance):
        self.theme.update({
            "background_color": [0.1, 0.1, 0.1, 1],  # Dark background
            "text_color": [1, 1, 1, 1],              # White text
            "button_color": [0.7, 0.1, 0.1, 1]       # Red buttons
        })
        self.apply_theme()

    def apply_theme(self):
        self.label.color = self.theme['text_color']
        self.button_start.background_color = self.theme['button_color']
        self.button_customize.background_color = self.theme['button_color']
        self.button_theme.background_color = self.theme['button_color']
        self.save_theme()

if __name__ == "__main__":
    RoutineReminderApp().run()
