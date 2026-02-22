import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class NutritionCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TACO Nutrition Calculator")
        self.root.geometry("1100x700")

        # --- Data Loading ---
        self.csv_filename = "taco_final.csv"
        self.data = self.load_data(self.csv_filename)
        self.meal_list = [] # Stores dicts of selected foods
        
        # --- UI Layout ---
        self.create_widgets()

    def load_data(self, filepath):
        """Loads and cleans the TACO CSV data."""
        try:
            df = pd.read_csv(filepath)
            
            # Numeric columns to process (excluding ID and Name)
            # We identify them by checking the remaining columns
            numeric_cols = df.columns[2:] 

            # Clean data: Replace 'Tr' (Trace) with 0, 'NA' with 0, and fix commas
            for col in numeric_cols:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = df[col].replace({'Tr': '0', 'NA': '0', '*': '0', '': '0', 'nan': '0'})
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df
        except FileNotFoundError:
            messagebox.showerror("Error", f"File '{filepath}' not found.\nPlease run the extractor script first.")
            return pd.DataFrame()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read CSV:\n{e}")
            return pd.DataFrame()

    def create_widgets(self):
        # Main Layout: Split into Left (Search) and Right (Meal/Totals)
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === LEFT PANEL: Search ===
        left_frame = ttk.Frame(paned_window, width=400)
        paned_window.add(left_frame, weight=1)

        # Search Bar
        lbl_search = ttk.Label(left_frame, text="Search Food:")
        lbl_search.pack(anchor="w", pady=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_food_list)
        entry_search = ttk.Entry(left_frame, textvariable=self.search_var)
        entry_search.pack(fill=tk.X, pady=(0, 10))

        # Food List (Treeview)
        self.tree_foods = ttk.Treeview(left_frame, columns=("ID", "Name"), show="headings", selectmode="browse")
        self.tree_foods.heading("ID", text="ID")
        self.tree_foods.heading("Name", text="Description")
        self.tree_foods.column("ID", width=50, stretch=False)
        self.tree_foods.column("Name", width=300)
        self.tree_foods.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar for list
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree_foods.yview)
        scrollbar.place(relx=1, rely=0.08, relheight=0.9, anchor="ne")
        self.tree_foods.configure(yscrollcommand=scrollbar.set)

        # Add Controls
        frame_controls = ttk.Frame(left_frame)
        frame_controls.pack(fill=tk.X)
        
        ttk.Label(frame_controls, text="Amount (g):").pack(side=tk.LEFT)
        self.entry_amount = ttk.Entry(frame_controls, width=10)
        self.entry_amount.insert(0, "100")
        self.entry_amount.pack(side=tk.LEFT, padx=5)
        
        btn_add = ttk.Button(frame_controls, text="Add to Meal ->", command=self.add_to_meal)
        btn_add.pack(side=tk.LEFT)

        # Populate initial list
        self.update_food_tree(self.data)

        # === RIGHT PANEL: Meal & Totals ===
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)

        # Meal List
        ttk.Label(right_frame, text="Your Meal:").pack(anchor="w")
        
        columns_meal = ("Name", "Amount", "Kcal", "Protein", "Carbs", "Fat")
        self.tree_meal = ttk.Treeview(right_frame, columns=columns_meal, show="headings", height=10)
        
        for col in columns_meal:
            self.tree_meal.heading(col, text=col)
            self.tree_meal.column(col, width=80)
        self.tree_meal.column("Name", width=200)
        
        self.tree_meal.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        btn_remove = ttk.Button(right_frame, text="Remove Selected", command=self.remove_from_meal)
        btn_remove.pack(anchor="e", pady=(0, 10))

        # Totals Display
        lbl_totals = ttk.Label(right_frame, text="Total Daily Intake", font=("Arial", 12, "bold"))
        lbl_totals.pack(anchor="w", pady=(10, 5))
        
        self.text_totals = tk.Text(right_frame, height=10, bg="#000000", state="disabled")
        self.text_totals.pack(fill=tk.BOTH, expand=True)

    def filter_food_list(self, *args):
        """Filters the food treeview based on search input."""
        query = self.search_var.get().lower()
        if not query:
            self.update_food_tree(self.data)
            return

        # Simple string matching
        filtered_df = self.data[self.data['Alimento'].str.lower().str.contains(query, na=False)]
        self.update_food_tree(filtered_df)

    def update_food_tree(self, df):
        """Updates the left-side list."""
        # Clear existing
        for item in self.tree_foods.get_children():
            self.tree_foods.delete(item)
        
        # Insert new (limit to first 100 to prevent lag if empty search)
        for _, row in df.head(100).iterrows():
            self.tree_foods.insert("", "end", values=(row['ID'], row['Alimento']))

    def add_to_meal(self):
        """Calculates nutrients for selected food and adds to meal list."""
        selected_item = self.tree_foods.selection()
        if not selected_item:
            messagebox.showwarning("Selection", "Please select a food from the list.")
            return
            
        try:
            amount_g = float(self.entry_amount.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid numeric amount.")
            return

        # Get food data
        item_values = self.tree_foods.item(selected_item)['values']
        food_id = str(item_values[0])
        
        # Retrieve full row from DataFrame
        food_row = self.data[self.data['ID'].astype(str) == food_id].iloc[0]
        
        # Calculate Ratio (TACO is per 100g)
        ratio = amount_g / 100.0
        
        # Create a record for the meal
        meal_item = {
            "Name": food_row['Alimento'],
            "Amount": amount_g,
            # We store all numeric columns multiplied by ratio
            "Nutrients": food_row[2:].multiply(ratio) 
        }
        
        self.meal_list.append(meal_item)
        
        # Update UI
        self.update_meal_tree()
        self.calculate_totals()

    def remove_from_meal(self):
        """Removes the selected item from the meal list."""
        selected_item = self.tree_meal.selection()
        if not selected_item:
            return
            
        # Treeview index corresponds to list index
        index = self.tree_meal.index(selected_item)
        del self.meal_list[index]
        
        self.update_meal_tree()
        self.calculate_totals()

    def update_meal_tree(self):
        """Refreshes the right-side meal table."""
        for item in self.tree_meal.get_children():
            self.tree_meal.delete(item)
            
        for item in self.meal_list:
            n = item['Nutrients']
            # Get main macros for the simple table (adjust column names if your CSV differs)
            # Standard TACO headers from previous code:
            kcal = f"{n.get('Energia(kcal)', 0):.1f}"
            prot = f"{n.get('Proteína(g)', 0):.1f}"
            carb = f"{n.get('Carboidrato(g)', 0):.1f}"
            fat =  f"{n.get('Lipídeos(g)', 0):.1f}"
            
            self.tree_meal.insert("", "end", values=(item['Name'], item['Amount'], kcal, prot, carb, fat))

    def calculate_totals(self):
        """Sums up all nutrients and displays them."""
        if not self.meal_list:
            self.update_totals_display({})
            return

        # Sum all nutrient series
        total_nutrients = pd.DataFrame([item['Nutrients'] for item in self.meal_list]).sum()
        self.update_totals_display(total_nutrients)

    def update_totals_display(self, totals):
        """Formats the text box with complete nutritional info."""
        self.text_totals.config(state="normal")
        self.text_totals.delete("1.0", tk.END)
        
        if len(totals) == 0:
            self.text_totals.insert(tk.END, "No foods added.")
            self.text_totals.config(state="disabled")
            return

        # Formatting output
        output = "MACRONUTRIENTS:\n"
        output += f"  Energy: {totals.get('Energia(kcal)', 0):.1f} kcal\n"
        output += f"  Protein: {totals.get('Proteína(g)', 0):.1f} g\n"
        output += f"  Carbohydrates: {totals.get('Carboidrato(g)', 0):.1f} g\n"
        output += f"  Lipids (Fat): {totals.get('Lipídeos(g)', 0):.1f} g\n"
        output += f"  Fiber: {totals.get('Fibra(g)', 0):.1f} g\n\n"
        
        output += "MICRONUTRIENTS:\n"
        # Iterate over other interesting keys dynamically
        skip_keys = ['Energia(kcal)', 'Energia(kJ)', 'Proteína(g)', 'Carboidrato(g)', 'Lipídeos(g)', 'Fibra(g)']
        
        for key, value in totals.items():
            if key not in skip_keys and value > 0:
                output += f"  {key}: {value:.2f}\n"

        self.text_totals.insert(tk.END, output)
        self.text_totals.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    # Ensure High DPI support on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = NutritionCalculatorApp(root)
    root.mainloop()