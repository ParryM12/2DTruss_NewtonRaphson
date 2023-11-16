import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
from PIL import ImageTk
from gui_settings import GUI_Settings
import copy
from tkinter import messagebox

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
        self.solution = None
        # Set title of main window
        self.title("Truss FEM - Nonlinear Truss Structure Analysis")
        # Initialise main window
        self.init_ui()
        self.input_elements_init = {'0': {'ele_number': 0,
                                          'ele_node_i': (0., 0.),
                                          'ele_node_j': (0., 0.),
                                          'ele_A': 0.,
                                          'ele_E': 0.,
                                          'ele_lin_coeff': 0.,
                                          'ele_quad_coeff': 0.,
                                          'ele_eps_f': 0.}}

        self.input_supports_init = {'0': {'sup_number': 0,
                                          'sup_node': (0., 0.),
                                          'c_x': 0.,
                                          'c_y': 0.}}

        self.input_forces_init = {'0': {'force_number': 0,
                                        'force_node': (0., 0.),
                                        'f_x': 0.,
                                        'f_y': 0.}}

        self.input_calc_param_init = {'calc_method': 'linear',
                                      'number_of_iterations': 0,
                                      'delta_f_max': 0.}
        self.ele_number = 0
        self.input_elements = copy.deepcopy(self.input_elements_init)
        self.input_supports = copy.deepcopy(self.input_supports_init)
        self.input_forces = copy.deepcopy(self.input_forces_init)
        self.input_calc_param = copy.deepcopy(self.input_calc_param_init)

    def init_ui(self):
        # Adjust the size to full screen
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.resizable(False, False)

        # Main frame for forms
        main_frame = ttk.Frame(self)
        main_frame.pack(side="left", fill='y', padx=20, pady=20)

        # Canvas frame for plotting
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side="right", fill="both", expand=True)

        # Initialize forms and canvas
        input_param_text = tk.Label(main_frame, text="Input parameters", font=GUI_Settings.FRAME_HEADER_FONT)
        input_param_text.pack(anchor='nw')
        self.add_elements_form(main_frame)
        self.add_supports_form(main_frame)
        self.add_loads_form(main_frame)
        self.calculation_settings_form(main_frame)

        # Canvas for displaying results
        canvas_text = tk.Label(canvas_frame, text="System and results", font=GUI_Settings.FRAME_HEADER_FONT)
        canvas_text.place(relx=0.02, rely=0.014)
        self.canvas = tk.Canvas(canvas_frame, width=self.winfo_screenwidth() * 0.7,
                                height=self.winfo_screenheight() * 0.6,
                                bg=GUI_Settings.CANVAS_BG, highlightbackground="black", highlightthickness=1)
        self.canvas.place(relx=0.02, rely=0.04)
        # self.canvas.pack(side="right", fill="both", expand=True, padx=50, pady=50)

        # Calculation button
        ttk.Button(main_frame, text="Run Calculation", command=self.run_calculation).pack(pady=10)

        # Clear button
        ttk.Button(main_frame, text="Clear all", command=self.clear_all).pack(pady=10)

        # Add Icon
        # icon_image = ImageTk.PhotoImage(data=GUI_Settings.return_icon_bytestring())
        # root.tk.call('wm', 'iconphoto', root._w, icon_image)

        # Current system information in bottom (dynamic)
        current_system_information_label = tk.Label(self, text="System Information:",
                                                    font=GUI_Settings.FRAME_HEADER_FONT)
        current_system_information_label.place(relx=0.01, rely=0.7)
        initial_system_information = f"Information about the system parameters will be displayed here."
        current_system_information = tk.Text(self, width=round(self.winfo_screenwidth() * 0.07),
                                             height=round(self.winfo_screenheight() * 0.013), wrap=tk.WORD,
                                             font=GUI_Settings.STANDARD_FONT_2, bg='light gray', fg='black')
        current_system_information.place(relx=0.01, rely=0.72)
        current_system_information.insert(tk.END, initial_system_information)
        current_system_information.config(state='disabled')

        # Calculation information in bottom (dynamic)
        calculation_information_label = tk.Label(self, text="Calculation Information:",
                                                 font=GUI_Settings.FRAME_HEADER_FONT)
        calculation_information_label.place(relx=0.4, rely=0.7)
        initial_calculation_information = f"Information about the calculation will be displayed here."
        current_calculation_information = tk.Text(self, width=round(self.winfo_screenwidth() * 0.07),
                                                  height=round(self.winfo_screenheight() * 0.013), wrap=tk.WORD,
                                                  font=GUI_Settings.STANDARD_FONT_2, bg='light gray', fg='black')
        current_calculation_information.place(relx=0.4, rely=0.72)
        current_calculation_information.insert(tk.END, initial_calculation_information)
        current_calculation_information.config(state='disabled')

    def add_elements_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Define elements")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column weights (0th column takes minimal required space, 1st column expands)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=3)

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

        ttk.Label(frame, text="Young's modulus E [MPa]:").grid(row=3, column=0, sticky='w')
        self.emod_entry = ttk.Entry(frame)
        self.emod_entry.grid(row=3, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Linear coefficient α [-]:").grid(row=4, column=0, sticky='w')
        self.lin_coeff_entry = ttk.Entry(frame)
        self.lin_coeff_entry.grid(row=4, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Quadratic coefficient β [-]:").grid(row=5, column=0, sticky='w')
        self.quad_coeff_entry = ttk.Entry(frame)
        self.quad_coeff_entry.grid(row=5, column=1, sticky='e', padx=5)

        # Create Button to add the element
        ttk.Button(frame, text="Add Element", command=self.add_element).grid(row=6, columnspan=2, pady=10)
        # Create Button to edit an element
        ttk.Button(frame, text="Edit Element", command=self.add_element).grid(row=7, columnspan=2, pady=0)

    def add_supports_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Define Supports")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column weights (0th column takes minimal required space, 1st column expands)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=3)

        # Create Entry boxes and labels for element input parameters
        ttk.Label(frame, text="Support Node (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.support_node_entry = ttk.Entry(frame)
        self.support_node_entry.grid(row=0, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Stiffness c_x [kN/m]:").grid(row=1, column=0, sticky='w')
        self.stiffness_cx_entry = ttk.Entry(frame)
        self.stiffness_cx_entry.grid(row=1, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Stiffness c_y [kN/m]:").grid(row=2, column=0, sticky='w')
        self.stiffness_cy_entry = ttk.Entry(frame)
        self.stiffness_cy_entry.grid(row=2, column=1, sticky='e', padx=5)

        # Create Button to add the support
        ttk.Button(frame, text="Add Support", command=self.add_support).grid(row=3, columnspan=2, pady=10)
        # Create Button to edit a support
        ttk.Button(frame, text="Edit Support", command=self.edit_support).grid(row=4, columnspan=2, pady=0)

    def add_loads_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Define Loads")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column weights (0th column takes minimal required space, 1st column expands)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=3)

        # Create Entry boxes and labels for element input parameters
        ttk.Label(frame, text="Force Node (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.force_node_entry = ttk.Entry(frame)
        self.force_node_entry.grid(row=0, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Force F_x [kN]:").grid(row=1, column=0, sticky='w')
        self.force_x_entry = ttk.Entry(frame)
        self.force_x_entry.grid(row=1, column=1, sticky='e', padx=5)
        # self.force_x_entry.place(relx=0.9, rely=0.5)

        ttk.Label(frame, text="Force F_y [kN]:").grid(row=2, column=0, sticky='w')
        self.force_y_entry = ttk.Entry(frame)
        self.force_y_entry.grid(row=2, column=1, sticky='e', padx=5)

        # Create Button to add the load
        ttk.Button(frame, text="Add Load", command=self.add_load).grid(row=3, columnspan=2, pady=10)
        # Create Button to edit a load
        ttk.Button(frame, text="Edit Load", command=self.add_element).grid(row=4, columnspan=2, pady=0)

    def calculation_settings_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Calculation Settings")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column weights (0th column takes minimal required space, 1st column expands)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=3)

        # Create Entry boxes and labels for element calculation parameters
        ttk.Label(frame, text="Max. number of iterations [-]:").grid(row=1, column=0, sticky='w')
        self.num_iterations_entry = ttk.Entry(frame)
        self.num_iterations_entry.grid(row=1, column=1, sticky='e', padx=5)

        ttk.Label(frame, text="Max. deviation F [kN]:").grid(row=2, column=0, sticky='w')
        self.delta_f_entry = ttk.Entry(frame)
        self.delta_f_entry.grid(row=2, column=1, sticky='e', padx=5)

        ttk.Button(frame, text="Save Settings", command=self.add_load).grid(row=3, columnspan=2, pady=10)

    def add_element(self):
        try:
            # Parse the coordinates from the entry fields
            node_i = self.parse_coordinates(self.node_i_entry.get())
            node_j = self.parse_coordinates(self.node_j_entry.get())

            # Do not proceed further if the coordinates are invalid
            if node_i is None or node_j is None:
                return

            # Parse other fields like area, Young's modulus, coefficients, etc.
            area = float(self.area_entry.get())
            emod = float(self.emod_entry.get())
            lin_coeff = float(self.lin_coeff_entry.get())
            quad_coeff = float(self.quad_coeff_entry.get())
            # Add the new element to the input_elements dictionary
            self.input_elements[str(self.ele_number)] = {'ele_number': self.ele_number,
                                                         'ele_node_i': node_i,
                                                         'ele_node_j': node_j,
                                                         'ele_A': area,
                                                         'ele_E': emod,
                                                         'ele_lin_coeff': lin_coeff,
                                                         'ele_quad_coeff': quad_coeff
                                                         }
            # Increase unique element number
            self.ele_number += 1
        except Exception as e:
            print(f"An error occured: {e}")

        print(self.input_elements)

    def edit_element(self):
        pass

    def add_load(self):
        # Parse the coordinates from the entry fields
        force_node = self.parse_coordinates(self.force_node_entry.get())

        # Do not proceed further if the coordinates are invalid
        if force_node is None:
            return

        force_x = float(self.force_x_entry.get())
        force_y = float(self.force_y_entry.get())
        # Add the load to data structure
        # ...

    def edit_load(self):
        pass

    def add_support(self):
        # Parse the coordinates from the entry fields
        support_node = self.parse_coordinates(self.support_node_entry.get())

        # Do not proceed further if the coordinates are invalid
        if support_node is None:
            return

        force_x = float(self.force_x_entry.get())
        force_y = float(self.force_y_entry.get())
        # Add the support to data structure
        # ...

    def edit_support(self):
        pass

    def parse_coordinates(self, coord_str: str) -> tuple[float, float]:
        # Removing common bracket types and spaces
        coord_str = coord_str.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace(' ', '')
        # Splitting the string by comma and converting to float
        try:
            x, y = map(float, coord_str.split(','))
            return (x, y)
        except ValueError as e:
            # Show a warning message box
            messagebox.showwarning("Warning", "Invalid coordinate format. Please enter as x,y or [x, y] or (x, y)!")
            return None

    def run_calculation(self):
        pass
        # Gather data from the forms and run the calculations
        # ...

    def clear_all(self):
        pass
        # Clear all
        # ...


# Run the application
if __name__ == "__main__":
    app = TrussAnalysisApp()
    app.mainloop()
