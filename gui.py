"""
Cambridge Restaurant Planner - GUI Interface

This script provides a graphical user interface for the Cambridge restaurant planning application.
It collects user inputs and runs the main functionality.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
import io
from contextlib import redirect_stdout

# Import the main function from main.py
from main import main as run_planner

class RedirectText:
    """Redirects stdout to a tkinter Text widget."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")
        
    def flush(self):
        pass

class RestaurantPlannerGUI:
    """GUI for the Cambridge Restaurant Planner application."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cambridge Restaurant Planner")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Set up styles
        self.setup_styles()
        
        # Create the main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the form area
        self.create_form_area()
        
        # Create the output area
        self.create_output_area()
        
        # Create the button area
        self.create_button_area()
        
        # Keep track of the planner task
        self.planner_task = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def setup_styles(self):
        """Set up ttk styles for the application."""
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 11))
        style.configure("TButton", font=("Arial", 11))
        style.configure("TCheckbutton", font=("Arial", 11))
        style.configure("TFrame", background="#f0f0f0")
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))
        
    def create_form_area(self):
        """Create the input form area."""
        form_frame = ttk.Frame(self.main_frame, padding="10")
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(form_frame, text="Cambridge Restaurant Planner", style="Header.TLabel")
        title_label.pack(pady=(0, 20))
        
        # Food preferences
        pref_frame = ttk.Frame(form_frame)
        pref_frame.pack(fill=tk.X, pady=5)
        
        pref_label = ttk.Label(pref_frame, text="Food Preferences:")
        pref_label.pack(anchor=tk.W)
        
        self.pref_var = tk.StringVar(value="casual dining with a mix of traditional British food and international cuisine")
        pref_entry = ttk.Entry(pref_frame, textvariable=self.pref_var, width=70)
        pref_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Constraints
        const_frame = ttk.Frame(form_frame)
        const_frame.pack(fill=tk.X, pady=5)
        
        const_label = ttk.Label(const_frame, text="Dietary Restrictions or Other Constraints:")
        const_label.pack(anchor=tk.W)
        
        self.const_var = tk.StringVar(value="no specific constraints")
        const_entry = ttk.Entry(const_frame, textvariable=self.const_var, width=70)
        const_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Meal selection
        meal_frame = ttk.Frame(form_frame)
        meal_frame.pack(fill=tk.X, pady=5)
        
        meal_label = ttk.Label(meal_frame, text="Select Meals:")
        meal_label.pack(anchor=tk.W)
        
        meals_container = ttk.Frame(meal_frame)
        meals_container.pack(fill=tk.X, pady=(5, 0))
        
        # Checkbuttons for meal selection
        self.breakfast_var = tk.BooleanVar(value=True)
        self.lunch_var = tk.BooleanVar(value=True)
        self.dinner_var = tk.BooleanVar(value=True)
        
        breakfast_cb = ttk.Checkbutton(meals_container, text="Breakfast", variable=self.breakfast_var)
        breakfast_cb.grid(row=0, column=0, padx=(0, 10))
        
        lunch_cb = ttk.Checkbutton(meals_container, text="Lunch", variable=self.lunch_var)
        lunch_cb.grid(row=0, column=1, padx=10)
        
        dinner_cb = ttk.Checkbutton(meals_container, text="Dinner", variable=self.dinner_var)
        dinner_cb.grid(row=0, column=2, padx=10)
    
    def create_output_area(self):
        """Create the output area for displaying results."""
        output_frame = ttk.LabelFrame(self.main_frame, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a scrolled text widget for output
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Create a redirect for stdout
        self.stdout_redirect = RedirectText(self.output_text)
    
    def create_button_area(self):
        """Create the button area."""
        button_frame = ttk.Frame(self.main_frame, padding="10")
        button_frame.pack(fill=tk.X)
        
        # Plan button
        self.plan_button = ttk.Button(button_frame, text="Plan My Restaurant Trip", command=self.start_planning)
        self.plan_button.pack(side=tk.RIGHT, padx=5)
        
        # Clear button
        clear_button = ttk.Button(button_frame, text="Clear Output", command=self.clear_output)
        clear_button.pack(side=tk.RIGHT, padx=5)

    def clear_output(self):
        """Clear the output text area."""
        self.output_text.configure(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state="disabled")
    
    def get_selected_meals(self):
        """Get a list of the selected meals."""
        meals = []
        if self.breakfast_var.get():
            meals.append("breakfast")
        if self.lunch_var.get():
            meals.append("lunch")
        if self.dinner_var.get():
            meals.append("dinner")
        return meals
    
    def start_planning(self):
        """Start the restaurant planning process."""
        # Check if at least one meal is selected
        selected_meals = self.get_selected_meals()
        if not selected_meals:
            self.output_text.configure(state="normal")
            self.output_text.insert(tk.END, "Please select at least one meal.\n")
            self.output_text.configure(state="disabled")
            return
        
        # Disable the plan button
        self.plan_button.configure(state="disabled")
        
        # Clear the output
        self.clear_output()
        
        # Start the planning in a separate thread
        self.executor.submit(self.run_planner_thread)
    
    def run_planner_thread(self):
        """Run the restaurant planner in a separate thread."""
        # Override standard input to provide the user's selections
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        
        # Prepare user inputs
        food_prefs = self.pref_var.get()
        constraints = self.const_var.get()
        selected_meals = self.get_selected_meals()
        
        try:
            # Redirect stdout to our text widget
            sys.stdout = self.stdout_redirect
            
            # Create a class to simulate stdin responses
            class SimulatedStdin:
                def __init__(self, responses):
                    self.responses = responses
                    self.index = 0
                
                def readline(self):
                    if self.index < len(self.responses):
                        response = self.responses[self.index]
                        self.index += 1
                        return response + '\n'
                    return '\n'
            
            # Create meal selection response
            if set(selected_meals) == {"breakfast", "lunch", "dinner"}:
                meal_selection = "4"  # All meals
            else:
                meal_indices = []
                if "breakfast" in selected_meals:
                    meal_indices.append("1")
                if "lunch" in selected_meals:
                    meal_indices.append("2")
                if "dinner" in selected_meals:
                    meal_indices.append("3")
                meal_selection = ",".join(meal_indices)
            
            # Simulate user input for the console interface
            sim_responses = [
                food_prefs,     # Food preferences
                constraints,    # Constraints
                meal_selection  # Meal selection
            ]
            
            sys.stdin = SimulatedStdin(sim_responses)
            
            # Run the planner
            asyncio.run(run_planner())
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            # Restore stdin and stdout
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            
            # Re-enable the plan button
            self.root.after(0, lambda: self.plan_button.configure(state="normal"))

def main():
    """Run the GUI application."""
    root = tk.Tk()
    app = RestaurantPlannerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 