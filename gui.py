import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
from gui_settings import GUI_Settings

#################################################
# Other
AUTHOR = 'Marius Mellmann, Elias Perras'
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
#################################################


# Main application class
class TrussAnalysisApp(tk.Tk):
    """
    Class for the GUI. Calls for the Calculation and Output Classes
    """
    def __init__(self):
        """
        Constructor, inherits from tkinter
        """
        super().__init__()
        # Set title of main window
        self.title("Truss FEM - Nonlinear Truss Structure Analysis")
        # Initialise main window
        self.init_ui()

    def init_ui(self):
        # Adjust the size to full screen
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.resizable(False, False)

        # Main frame for forms
        main_frame = ttk.Frame(self)
        main_frame.pack(side="left", fill="y")

        # Canvas frame for plotting
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side="right", fill="both", expand=True)

        # Initialize forms and canvas
        self.add_elements_form(main_frame)
        self.add_supports_form(main_frame)
        self.add_loads_form(main_frame)
        self.calculation_settings_form(main_frame)

        # Canvas for displaying results
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(side="right", fill="both", expand=True)

        # Calculation button
        ttk.Button(main_frame, text="Run Calculation", command=self.run_calculation).pack(pady=10)

        # Add Icon
        # icon_image = ImageTk.PhotoImage(data=GUI_Settings.return_icon_bytestring())
        # root.tk.call('wm', 'iconphoto', root._w, icon_image)

    def add_elements_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Add Elements")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Create Entry boxes and labels for element input parameters
        ttk.Label(frame, text="Node i (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.node_i_entry = ttk.Entry(frame)
        self.node_i_entry.grid(row=0, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Node j (x, y) [m]:").grid(row=1, column=0, sticky='w')
        self.node_j_entry = ttk.Entry(frame)
        self.node_j_entry.grid(row=1, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Cross-section area A [cm²]:").grid(row=2, column=0, sticky='w')
        self.area_entry = ttk.Entry(frame)
        self.area_entry.grid(row=2, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Young's modulus E [MPa]/[N/mm²]:").grid(row=3, column=0, sticky='w')
        self.emod_entry = ttk.Entry(frame)
        self.emod_entry.grid(row=3, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Linear coefficient α [-]:").grid(row=4, column=0, sticky='w')
        self.lin_coeff_entry = ttk.Entry(frame)
        self.lin_coeff_entry.grid(row=4, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Quadratic coefficient β [-]:").grid(row=5, column=0, sticky='w')
        self.quad_coeff_entry = ttk.Entry(frame)
        self.quad_coeff_entry.grid(row=5, column=1, sticky='e', padx=5)

        # Create Button to add the element
        ttk.Button(frame, text="Add Element", command=self.add_element).grid(row=6, columnspan=2)

    def add_supports_form(self, parent_frame):
        frame = ttk.LabelFrame(parent_frame, text="Define Supports")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        ttk.Label(frame, text="Support Node (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.force_node_entry = ttk.Entry(frame)
        self.force_node_entry.grid(row=0, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Stiffness c_x [kN/m]:").grid(row=1, column=0, sticky='w')
        self.stiffness_cx_entry = ttk.Entry(frame)
        self.stiffness_cx_entry.grid(row=1, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Stiffness c_y [kN/m]:").grid(row=2, column=0, sticky='w')
        self.stiffness_cy_entry = ttk.Entry(frame)
        self.stiffness_cy_entry.grid(row=2, column=1, sticky='e', padx=5)

        ttk.Button(frame, text="Add Support", command=self.add_load).grid(row=3, columnspan=2)

    def add_loads_form(self, parent_frame):
        frame = ttk.LabelFrame(parent_frame, text="Define Loads")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        ttk.Label(frame, text="Force Node (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.force_node_entry = ttk.Entry(frame)
        self.force_node_entry.grid(row=0, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Force X [kN]:").grid(row=1, column=0, sticky='w')
        self.force_x_entry = ttk.Entry(frame)
        self.force_x_entry.grid(row=1, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Force Y [kN]:").grid(row=2, column=0, sticky='w')
        self.force_y_entry = ttk.Entry(frame)
        self.force_y_entry.grid(row=2, column=1, sticky='e', padx=5)

        ttk.Button(frame, text="Add Load", command=self.add_load).grid(row=3, columnspan=2)

    def calculation_settings_form(self, parent_frame):
        frame = ttk.LabelFrame(parent_frame, text="Calculation Settíngs")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        ttk.Label(frame, text="Max. number of iterations [-]:").grid(row=1, column=0, sticky='w')
        self.num_iterations_entry = ttk.Entry(frame)
        self.num_iterations_entry.grid(row=1, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Max. deviation F [kN]:").grid(row=2, column=0, sticky='w')
        self.delta_f_entry = ttk.Entry(frame)
        self.delta_f_entry.grid(row=2, column=1, sticky='e', padx=5)

        ttk.Button(frame, text="Save Settings", command=self.add_load).grid(row=3, columnspan=2)

    def add_element(self):
        node_i = self.parse_coordinates(self.node_i_entry.get())
        node_j = self.parse_coordinates(self.node_j_entry.get())
        # Parse other fields and add the element to a data structure
        # ...

    def add_load(self):
        force_node = self.parse_coordinates(self.force_node_entry.get())
        force_x = float(self.force_x_entry.get())
        force_y = float(self.force_y_entry.get())
        # Add the load to a data structure
        # ...

    def parse_coordinates(self, coord_str):
        # Function to parse coordinate strings into tuples
        x, y = map(float, coord_str.split(','))
        return (x, y)

    def run_calculation(self):
        pass
        # Gather data from the forms and run the calculations
        # ...


# Run the application
if __name__ == "__main__":
    app = TrussAnalysisApp()
    app.mainloop()