import tkinter as tk
from tkinter import ttk
from gui_settings import GUI_Settings
import copy
from tkinter import messagebox
from calculation import Calculation

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

        self.method_dict = {'Linear': 'linear',
                            'Newton-Raphson': 'NR',
                            'Mod. Newton-Raphson': 'modNR'}

        self.method_reverse_dict = {'linear': 'Linear',
                                    'NR': 'Newton-Raphson',
                                    'modNR': 'Mod. Newton-Raphson'}

        self.ele_number = 0
        self.force_number = 0
        self.support_number = 0
        self.add_element_initialise = 0
        self.add_support_initialise = 0
        self.add_load_initialise = 0
        self.add_calc_initialise = 0
        self.input_elements = copy.deepcopy(self.input_elements_init)
        self.input_supports = copy.deepcopy(self.input_supports_init)
        self.input_forces = copy.deepcopy(self.input_forces_init)
        self.input_calc_param = copy.deepcopy(self.input_calc_param_init)

    def init_ui(self):
        # Adjust the size to full screen self.winfo_screenwidth()
        self.geometry(f"{GUI_Settings.screensize[0]}x{GUI_Settings.screensize[1]}")
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
        self.canvas = tk.Canvas(canvas_frame, width=GUI_Settings.screensize[0] * 0.7,
                                height=GUI_Settings.screensize[1] * 0.6,
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

        # Frame for system information and scrollbar
        sys_info_frame = tk.Frame(self)
        sys_info_frame.place(relx=0.01, rely=0.72, relwidth=0.4, relheight=0.17)  # Adjust dimensions as needed

        # Text widget for system information
        current_system_information_label = tk.Label(self, text="System Information:",
                                                    font=GUI_Settings.FRAME_HEADER_FONT)
        current_system_information_label.place(relx=0.01, rely=0.7)
        initial_system_information = f"Information about the system parameters will be displayed here."
        self.current_system_information = tk.Text(sys_info_frame, wrap=tk.WORD,
                                                  font=GUI_Settings.STANDARD_FONT_2, bg='light gray', fg='black')
        self.current_system_information.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.current_system_information.insert(tk.END, initial_system_information)
        self.current_system_information.config(state='disabled')

        # Scrollbar for the Text widget
        scrollbar_systeminfo = tk.Scrollbar(sys_info_frame, orient='vertical',
                                            command=self.current_system_information.yview)
        scrollbar_systeminfo.pack(side=tk.RIGHT, fill=tk.Y)

        # Attach the scrollbar to the Text widget
        self.current_system_information.config(yscrollcommand=scrollbar_systeminfo.set)

        # Frame for calculation information and scrollbar
        calc_info_frame = tk.Frame(self)
        calc_info_frame.place(relx=0.47, rely=0.72, relwidth=0.4, relheight=0.17)  # Adjust dimensions as needed

        # Text widget for calculation information
        calculation_information_label = tk.Label(self, text="Calculation Information:",
                                                 font=GUI_Settings.FRAME_HEADER_FONT)
        calculation_information_label.place(relx=0.47, rely=0.7)
        initial_calculation_information = f"Information about the calculation will be displayed here."
        self.current_calculation_information = tk.Text(calc_info_frame, wrap=tk.WORD,
                                                       font=GUI_Settings.STANDARD_FONT_2, bg='light gray', fg='black')
        self.current_calculation_information.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.current_calculation_information.insert(tk.END, initial_calculation_information)
        self.current_calculation_information.config(state='disabled')

        # Scrollbar for the Text widget
        scrollbar_calcinfo = tk.Scrollbar(calc_info_frame, orient='vertical',
                                          command=self.current_calculation_information.yview)
        scrollbar_calcinfo.pack(side=tk.RIGHT, fill=tk.Y)

        # Attach the scrollbar to the Text widget
        self.current_calculation_information.config(yscrollcommand=scrollbar_calcinfo.set)

    def update_system_information(self):
        info_text = "Current System Information:\n"

        # Adding information about elements
        if self.input_elements and self.add_element_initialise == 1:
            info_text += "\nElements:\n"
            for ele in self.input_elements.values():
                info_text += (
                    f"Element {ele['ele_number']}: Node i = {ele['ele_node_i']}, Node j = {ele['ele_node_j']},"
                    f" A = {ele['ele_A']} cm², E = {ele['ele_E']} MPa, α = {ele['ele_lin_coeff']} [-],"
                    f" β = {ele['ele_quad_coeff']} [-], ε = {ele['ele_eps_f']} [-].\n")

        # Adding information about supports
        if self.input_supports and self.add_support_initialise == 1:
            info_text += "\nSupports:\n"
            for sup in self.input_supports.values():
                info_text += (f"Support {sup['sup_number']}: Node = {sup['sup_node']}, c_x = {sup['c_x']} kN/m, "
                              f"c_y = {sup['c_y']} kN/m.\n")

        # Adding information about loads
        if self.input_forces and self.add_load_initialise == 1:
            info_text += "\nLoads:\n"
            for load in self.input_forces.values():
                info_text += (f"Load {load['force_number']}: Node = {load['force_node']}, F_x = {load['f_x']} kN, "
                              f"F_y = {load['f_y']} kN.\n")
        # Adding information about calculation parameters
        if self.input_calc_param and self.add_calc_initialise == 1:
            info_text += "\nCalculation Parameters:\n"
            info_text += f"Method: {self.method_reverse_dict[self.input_calc_param['calc_method']]}, "
            info_text += f"Iterations: {self.input_calc_param['number_of_iterations']}, "
            info_text += f"Max node imbalance ΔF = {self.input_calc_param['delta_f_max']} kN.\n"

        # Updating the text widget
        self.current_system_information.config(state='normal')
        self.current_system_information.delete(1.0, tk.END)
        self.current_system_information.insert(tk.END, info_text)
        self.current_system_information.config(state='disabled')

    def add_elements_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Define elements")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column width
        frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1)
        frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL2)

        # Create Entry boxes and labels for element input parameters
        ttk.Label(frame, text="Node i (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.node_i_entry = ttk.Entry(frame)
        self.node_i_entry.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Node j (x, y) [m]:").grid(row=1, column=0, sticky='w')
        self.node_j_entry = ttk.Entry(frame)
        self.node_j_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Cross-section area A [cm²]:").grid(row=2, column=0, sticky='w')
        self.area_entry = ttk.Entry(frame)
        self.area_entry.grid(row=2, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Young's modulus E [MPa]:").grid(row=3, column=0, sticky='w')
        self.emod_entry = ttk.Entry(frame)
        self.emod_entry.grid(row=3, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Linear coefficient α [-]:").grid(row=4, column=0, sticky='w')
        self.lin_coeff_entry = ttk.Entry(frame)
        self.lin_coeff_entry.grid(row=4, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Quadratic coefficient β [-]:").grid(row=5, column=0, sticky='w')
        self.quad_coeff_entry = ttk.Entry(frame)
        self.quad_coeff_entry.grid(row=5, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Limit strain ε [-]:").grid(row=6, column=0, sticky='w')
        self.strain_entry = ttk.Entry(frame)
        self.strain_entry.grid(row=6, column=1, sticky='ew', padx=5)

        # Create Button to add the element
        ttk.Button(frame, text="Add Element", command=self.add_element).grid(row=7, columnspan=2, pady=10)
        # Create Button to edit an element
        ttk.Button(frame, text="Edit/Delete Element", command=self.edit_element).grid(row=8, columnspan=2, pady=0)

    def add_supports_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Define Supports")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column width
        frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1)
        frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL2)

        # Create Entry boxes and labels for element input parameters
        ttk.Label(frame, text="Support Node (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.support_node_entry = ttk.Entry(frame)
        self.support_node_entry.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Stiffness c_x [kN/m]:").grid(row=1, column=0, sticky='w')
        self.stiffness_cx_entry = ttk.Entry(frame)
        self.stiffness_cx_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Stiffness c_y [kN/m]:").grid(row=2, column=0, sticky='w')
        self.stiffness_cy_entry = ttk.Entry(frame)
        self.stiffness_cy_entry.grid(row=2, column=1, sticky='ew', padx=5)

        # Create Button to add the support
        ttk.Button(frame, text="Add Support", command=self.add_support).grid(row=3, columnspan=2, pady=10)
        # Create Button to edit a support
        ttk.Button(frame, text="Edit/Delete Support", command=self.edit_support).grid(row=4, columnspan=2, pady=0)

    def add_loads_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Define Loads")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column width
        frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1)
        frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL2)

        # Create Entry boxes and labels for element input parameters
        ttk.Label(frame, text="Force Node (x, y) [m]:").grid(row=0, column=0, sticky='w')
        self.force_node_entry = ttk.Entry(frame)
        self.force_node_entry.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Force F_x [kN]:").grid(row=1, column=0, sticky='w')
        self.force_x_entry = ttk.Entry(frame)
        self.force_x_entry.grid(row=1, column=1, sticky='ew', padx=5)
        # self.force_x_entry.place(relx=0.9, rely=0.5)

        ttk.Label(frame, text="Force F_y [kN]:").grid(row=2, column=0, sticky='w')
        self.force_y_entry = ttk.Entry(frame)
        self.force_y_entry.grid(row=2, column=1, sticky='ew', padx=5)

        # Create Button to add the load
        ttk.Button(frame, text="Add Load", command=self.add_load).grid(row=3, columnspan=2, pady=10)
        # Create Button to edit a load
        ttk.Button(frame, text="Edit/Delete Load", command=self.edit_load).grid(row=4, columnspan=2, pady=0)

    def calculation_settings_form(self, parent_frame):
        # Create Frame
        frame = ttk.LabelFrame(parent_frame, text="Calculation Settings")
        frame.pack(padx=10, pady=10, fill='x', anchor='nw')

        # Configure the column width
        frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1)
        frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL2)

        # Dropdown menu options
        methods = ["Linear", "Newton-Raphson", "Mod. Newton-Raphson"]

        # Label for dropdown menu
        ttk.Label(frame, text="Select method:").grid(row=0, column=0, sticky='w')

        # Dropdown menu
        self.method_combobox = ttk.Combobox(frame, values=methods, state="readonly")
        self.method_combobox.grid(row=0, column=1, sticky='ew', padx=5)
        self.method_combobox.current(0)  # Set default selection

        # Create Entry boxes and labels for element calculation parameters
        ttk.Label(frame, text="Max. number of iterations [-]:").grid(row=1, column=0, sticky='w')
        self.num_iterations_entry = ttk.Entry(frame)
        self.num_iterations_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Max. deviation F [kN]:").grid(row=2, column=0, sticky='w')
        self.delta_f_entry = ttk.Entry(frame)
        self.delta_f_entry.grid(row=2, column=1, sticky='ew', padx=5)

        ttk.Button(frame, text="Save Settings", command=self.calc_settings).grid(row=3, columnspan=2, pady=10)

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
            strain_entry = float(self.strain_entry.get())

            # Check for duplicate element
            if self.add_element_initialise == 1:
                for key, element in self.input_elements.items():
                    if element['ele_node_i'] == node_i and element['ele_node_j'] == node_j:
                        messagebox.showerror("Duplicate Element", "An element with these nodes already exists!"
                                                                  f"Consider editing element {key} instead!")
                        return

            # Add the new element to the input_elements dictionary
            self.input_elements[str(self.ele_number)] = {'ele_number': self.ele_number,
                                                         'ele_node_i': node_i,
                                                         'ele_node_j': node_j,
                                                         'ele_A': area,
                                                         'ele_E': emod,
                                                         'ele_lin_coeff': lin_coeff,
                                                         'ele_quad_coeff': quad_coeff,
                                                         'ele_eps_f': strain_entry}
            # Increase unique element number
            self.ele_number += 1

            # Clearing the entry boxes after adding the element
            self.node_i_entry.delete(0, tk.END)
            self.node_j_entry.delete(0, tk.END)
            self.area_entry.delete(0, tk.END)
            self.emod_entry.delete(0, tk.END)
            self.lin_coeff_entry.delete(0, tk.END)
            self.quad_coeff_entry.delete(0, tk.END)
            self.strain_entry.delete(0, tk.END)
            # Set element initializer to 1, required to overwrite initial elements properly
            self.add_element_initialise = 1
            # Update information window
            self.update_system_information()
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the element: {e}")
            print(f"An error occurred while adding the element: {e}")
            return

    def edit_element(self):
        self.edit_window = tk.Toplevel(self)
        self.edit_window.title("Edit Element")

        # Frame for entry boxes and labels
        edit_frame = ttk.Frame(self.edit_window)
        edit_frame.pack(padx=10, pady=10)

        # Label for dropdown menu
        ttk.Label(edit_frame, text="Select element:").grid(row=0, column=0, sticky='w')

        # Dropdown for selecting the element to edit
        self.element_dropdown = ttk.Combobox(edit_frame, state="readonly")
        self.element_dropdown.grid(row=0, column=1, sticky='ew', padx=5, pady=10)
        self.element_dropdown.bind("<<ComboboxSelected>>", self.populate_element_fields)

        # Creating labeled entry boxes
        ttk.Label(edit_frame, text="Node i (x, y) [m]:").grid(row=1, column=0, sticky='w')
        self.edit_node_i_entry = ttk.Entry(edit_frame)
        self.edit_node_i_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Node j (x, y) [m]:").grid(row=2, column=0, sticky='w')
        self.edit_node_j_entry = ttk.Entry(edit_frame)
        self.edit_node_j_entry.grid(row=2, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Cross-section area A [cm²]:").grid(row=3, column=0, sticky='w')
        self.edit_area_entry = ttk.Entry(edit_frame)
        self.edit_area_entry.grid(row=3, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Young's modulus E [MPa]:").grid(row=4, column=0, sticky='w')
        self.edit_emod_entry = ttk.Entry(edit_frame)
        self.edit_emod_entry.grid(row=4, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Linear coefficient α [-]:").grid(row=5, column=0, sticky='w')
        self.edit_lin_coeff_entry = ttk.Entry(edit_frame)
        self.edit_lin_coeff_entry.grid(row=5, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Quadratic coefficient β [-]:").grid(row=6, column=0, sticky='w')
        self.edit_quad_coeff_entry = ttk.Entry(edit_frame)
        self.edit_quad_coeff_entry.grid(row=6, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Limit strain ε [-]:").grid(row=7, column=0, sticky='w')
        self.edit_strain_entry = ttk.Entry(edit_frame)
        self.edit_strain_entry.grid(row=7, column=1, sticky='ew', padx=5)

        # Button for saving changes
        ttk.Button(edit_frame, text="Save Changes", command=self.save_element_changes).grid(row=8, column=1, padx=5,
                                                                                            pady=10)
        # Button for deleting the selected element
        ttk.Button(edit_frame, text="Delete Element", command=self.delete_element).grid(row=8, column=0, padx=5)

        # Initially populate the entry boxes with the current values of the first element
        self.populate_element_fields()

        # Call update_element_dropdown to initialize the combobox values
        self.update_element_dropdown()

    def populate_element_fields(self, event=None):
        selected_index = self.element_dropdown.current()
        element_id = list(self.input_elements.keys())[selected_index]
        element = self.input_elements[element_id]

        self.edit_node_i_entry.delete(0, tk.END)
        self.edit_node_i_entry.insert(0, f"{element['ele_node_i'][0]}, {element['ele_node_i'][1]}")

        self.edit_node_j_entry.delete(0, tk.END)
        self.edit_node_j_entry.insert(0, f"{element['ele_node_j'][0]}, {element['ele_node_j'][1]}")

        self.edit_area_entry.delete(0, tk.END)
        self.edit_area_entry.insert(0, f"{element['ele_A']}")

        self.edit_emod_entry.delete(0, tk.END)
        self.edit_emod_entry.insert(0, f"{element['ele_E']}")

        self.edit_lin_coeff_entry.delete(0, tk.END)
        self.edit_lin_coeff_entry.insert(0, f"{element['ele_lin_coeff']}")

        self.edit_quad_coeff_entry.delete(0, tk.END)
        self.edit_quad_coeff_entry.insert(0, f"{element['ele_quad_coeff']}")

        self.edit_strain_entry.delete(0, tk.END)
        self.edit_strain_entry.insert(0, f"{element['ele_eps_f']}")

    def save_element_changes(self):
        selected_index = self.element_dropdown.current()
        element_id = list(self.input_elements.keys())[selected_index]
        # Parse values from entry boxes
        node_i = self.parse_coordinates(self.edit_node_i_entry.get())
        node_j = self.parse_coordinates(self.edit_node_j_entry.get())
        area = float(self.edit_area_entry.get())
        emod = float(self.edit_emod_entry.get())
        lin_coeff = float(self.edit_lin_coeff_entry.get())
        quad_coeff = float(self.edit_quad_coeff_entry.get())
        strain_entry = float(self.edit_strain_entry.get())

        # Update the element in the input_elements dictionary
        self.input_elements[element_id] = {
            'ele_number': int(element_id),
            'ele_node_i': node_i,
            'ele_node_j': node_j,
            'ele_A': area,
            'ele_E': emod,
            'ele_lin_coeff': lin_coeff,
            'ele_quad_coeff': quad_coeff,
            'ele_eps_f': strain_entry}
        # Update information window
        self.update_system_information()
        # Close window
        self.edit_window.destroy()

    def update_element_dropdown(self):
        element_ids = list(self.input_elements.keys())
        element_display_values = [f"Element {number}" for number in element_ids]

        self.element_dropdown['values'] = element_display_values
        if element_ids:
            self.element_dropdown.current(0)
        else:
            self.element_dropdown.set('')

        self.populate_element_fields()

    def delete_element(self):
        selected_index = self.element_dropdown.current()
        if selected_index == -1:  # No selection
            return

        element_id = list(self.input_elements.keys())[selected_index]
        del self.input_elements[element_id]
        # Renumbering the remaining elements
        new_input_elements = {}
        for i, key in enumerate(sorted(self.input_elements.keys())):
            new_input_elements[str(i)] = self.input_elements[key]

        self.input_elements = new_input_elements
        # Update information window
        self.update_system_information()
        # Update the combobox options and entry fields
        self.update_element_dropdown()

    def add_load(self):
        try:
            # Parse the coordinates from the entry fields
            force_node = self.parse_coordinates(self.force_node_entry.get())

            # Do not proceed further if the coordinates are invalid
            if force_node is None:
                return

            force_x = float(self.force_x_entry.get())
            force_y = float(self.force_y_entry.get())
            # Check for duplicate load
            if self.add_load_initialise == 1:
                for key, force in self.input_forces.items():
                    if force['force_node'] == force_node:
                        messagebox.showerror("Duplicate load", "A load at this node already exists!"
                                                               f"Consider editing load {key} instead.")
                        return
            # Add the new load to the input_forces dictionary
            self.input_forces[str(self.force_number)] = {'force_number': self.force_number,
                                                         'force_node': force_node,
                                                         'f_x': force_x,
                                                         'f_y': force_y}
            # Increase unique element number
            self.force_number += 1

            # Clearing the entry boxes after adding the load
            self.force_node_entry.delete(0, tk.END)
            self.force_x_entry.delete(0, tk.END)
            self.force_y_entry.delete(0, tk.END)
            # Set load initializer to 1, required to overwrite initial loads properly
            self.add_load_initialise = 1
            # Update information window
            self.update_system_information()
        except Exception as e:
            print(f"An error occurred while adding the load: {e}")

    def edit_load(self):
        self.edit_window_load = tk.Toplevel(self)
        self.edit_window_load.title("Edit Load")

        # Frame for entry boxes and labels
        edit_frame = ttk.Frame(self.edit_window_load)
        edit_frame.pack(padx=10, pady=10)

        # Label for dropdown menu
        ttk.Label(edit_frame, text="Select load:").grid(row=0, column=0, sticky='w')

        # Dropdown for selecting the load to edit
        self.load_dropdown = ttk.Combobox(edit_frame, state="readonly")
        self.load_dropdown.grid(row=0, column=1, sticky='ew', padx=5, pady=10)
        self.load_dropdown.bind("<<ComboboxSelected>>", self.populate_load_fields)

        # Creating labeled entry boxes
        ttk.Label(edit_frame, text="Force Node (x, y) [m]:").grid(row=1, column=0, sticky='w')
        self.edit_force_node_entry = ttk.Entry(edit_frame)
        self.edit_force_node_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Force F_x [kN]:").grid(row=2, column=0, sticky='w')
        self.edit_force_x_entry = ttk.Entry(edit_frame)
        self.edit_force_x_entry.grid(row=2, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Force F_y [kN]:").grid(row=3, column=0, sticky='w')
        self.edit_force_y_entry = ttk.Entry(edit_frame)
        self.edit_force_y_entry.grid(row=3, column=1, sticky='ew', padx=5)

        # Button for saving changes
        ttk.Button(edit_frame, text="Save Changes", command=self.save_load_changes).grid(row=4, column=1, padx=5,
                                                                                         pady=10)
        # Button for deleting the selected load
        ttk.Button(edit_frame, text="Delete Load", command=self.delete_load).grid(row=4, column=0, padx=5)

        # Initially populate the entry boxes with the current values of the first load
        self.populate_load_fields()

        # Call update_load_dropdown to initialize the combobox values
        self.update_load_dropdown()

    def populate_load_fields(self, event=None):
        selected_index = self.load_dropdown.current()
        force_id = list(self.input_forces.keys())[selected_index]
        force = self.input_forces[force_id]

        self.edit_force_node_entry.delete(0, tk.END)
        self.edit_force_node_entry.insert(0, f"{force['force_node'][0]}, {force['force_node'][1]}")

        self.edit_force_x_entry.delete(0, tk.END)
        self.edit_force_x_entry.insert(0, f"{force['f_x']}")

        self.edit_force_y_entry.delete(0, tk.END)
        self.edit_force_y_entry.insert(0, f"{force['f_y']}")

    def save_load_changes(self):
        selected_index = self.load_dropdown.current()
        force_id = list(self.input_forces.keys())[selected_index]
        # Parse values from entry boxes
        force_node = self.parse_coordinates(self.edit_force_node_entry.get())
        f_x = float(self.edit_force_x_entry.get())
        f_y = float(self.edit_force_y_entry.get())

        # Update the load in the input_elements dictionary
        self.input_forces[force_id] = {
            'force_number': int(force_id),
            'force_node': force_node,
            'f_x': f_x,
            'f_y': f_y}
        # Update information window
        self.update_system_information()
        # Close window
        self.edit_window_load.destroy()

    def update_load_dropdown(self):
        load_ids = list(self.input_forces.keys())
        load_display_values = [f"Load {number}" for number in load_ids]

        self.load_dropdown['values'] = load_display_values
        if load_ids:
            self.load_dropdown.current(0)
        else:
            self.load_dropdown.set('')

        self.populate_load_fields()

    def delete_load(self):
        selected_index = self.load_dropdown.current()
        if selected_index == -1:  # No selection
            return

        load_id = list(self.input_forces.keys())[selected_index]
        del self.input_forces[load_id]
        # Renumbering the remaining loads
        new_input_loads = {}
        for i, key in enumerate(sorted(self.input_forces.keys())):
            new_input_loads[str(i)] = self.input_forces[key]

        self.input_forces = new_input_loads
        # Update information window
        self.update_system_information()
        # Update the combobox options and entry fields
        self.update_load_dropdown()

    def add_support(self):
        try:
            # Parse the coordinates from the entry fields
            support_node = self.parse_coordinates(self.support_node_entry.get())

            # Do not proceed further if the coordinates are invalid
            if support_node is None:
                return

            c_x = float(self.stiffness_cx_entry.get())
            c_y = float(self.stiffness_cy_entry.get())

            # Check for duplicate support
            if self.add_load_initialise == 1:
                for key, support in self.input_supports.items():
                    if support['sup_node'] == support_node:
                        messagebox.showerror("Duplicate Support", "A support with this node already exists!"
                                                                  f"Consider editing support {key} instead!")
                        return

            # Add the new support to the input_supports dictionary
            self.input_supports[str(self.support_number)] = {'sup_number': self.support_number,
                                                             'sup_node': support_node,
                                                             'c_x': c_x,
                                                             'c_y': c_y}
            # Increase unique element number
            self.support_number += 1

            # Clearing the entry boxes after adding the support
            self.support_node_entry.delete(0, tk.END)
            self.stiffness_cx_entry.delete(0, tk.END)
            self.stiffness_cy_entry.delete(0, tk.END)
            # Set support initializer to 1, required to overwrite initial supports properly
            self.add_support_initialise = 1
            # Update information window
            self.update_system_information()

        except Exception as e:
            print(f"An error occurred while adding the support: {e}")

    def edit_support(self):
        self.edit_window_support = tk.Toplevel(self)
        self.edit_window_support.title("Edit Support")

        # Frame for entry boxes and labels
        edit_frame = ttk.Frame(self.edit_window_support)
        edit_frame.pack(padx=10, pady=10)

        # Label for dropdown menu
        ttk.Label(edit_frame, text="Select support:").grid(row=0, column=0, sticky='w')

        # Dropdown for selecting the support to edit
        self.support_dropdown = ttk.Combobox(edit_frame, state="readonly")
        self.support_dropdown.grid(row=0, column=1, sticky='ew', padx=5, pady=10)
        self.support_dropdown.bind("<<ComboboxSelected>>", self.populate_support_fields)

        # Creating labeled entry boxes
        ttk.Label(edit_frame, text="Support Node (x, y) [m]:").grid(row=1, column=0, sticky='w')
        self.edit_support_node_entry = ttk.Entry(edit_frame)
        self.edit_support_node_entry.grid(row=1, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Stiffness c_x [kN/m]:").grid(row=2, column=0, sticky='w')
        self.edit_stiffness_cx_entry = ttk.Entry(edit_frame)
        self.edit_stiffness_cx_entry.grid(row=2, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Stiffness c_y [kN/m]:").grid(row=3, column=0, sticky='w')
        self.edit_stiffness_cy_entry = ttk.Entry(edit_frame)
        self.edit_stiffness_cy_entry.grid(row=3, column=1, sticky='ew', padx=5)

        # Button for saving changes
        ttk.Button(edit_frame, text="Save Changes", command=self.save_support_changes).grid(row=4, column=1, padx=5,
                                                                                            pady=10)
        # Button for deleting the selected support
        ttk.Button(edit_frame, text="Delete Support", command=self.delete_support).grid(row=4, column=0, padx=5)

        # Initially populate the entry boxes with the current values of the first support
        self.populate_support_fields()

        # Call update_support_dropdown to initialize the combobox values
        self.update_support_dropdown()

    def populate_support_fields(self, event=None):
        selected_index = self.support_dropdown.current()
        support_id = list(self.input_supports.keys())[selected_index]
        support = self.input_supports[support_id]

        self.edit_support_node_entry.delete(0, tk.END)
        self.edit_support_node_entry.insert(0, f"{support['sup_node'][0]}, {support['sup_node'][1]}")

        self.edit_stiffness_cx_entry.delete(0, tk.END)
        self.edit_stiffness_cx_entry.insert(0, f"{support['c_x']}")

        self.edit_stiffness_cy_entry.delete(0, tk.END)
        self.edit_stiffness_cy_entry.insert(0, f"{support['c_y']}")

    def save_support_changes(self):
        selected_index = self.support_dropdown.current()
        support_id = list(self.input_supports.keys())[selected_index]
        # Parse values from entry boxes
        support_node = self.parse_coordinates(self.edit_support_node_entry.get())
        c_x = float(self.edit_stiffness_cx_entry.get())
        c_y = float(self.edit_stiffness_cy_entry.get())

        # Update the load in the input_elements dictionary
        self.input_supports[support_id] = {
            'sup_number': int(support_id),
            'sup_node': support_node,
            'c_x': c_x,
            'c_y': c_y}
        # Update information window
        self.update_system_information()
        # Close window
        self.edit_window_support.destroy()

    def update_support_dropdown(self):
        support_ids = list(self.input_supports.keys())
        support_display_values = [f"Support {number}" for number in support_ids]

        self.support_dropdown['values'] = support_display_values
        if support_ids:
            self.support_dropdown.current(0)
        else:
            self.support_dropdown.set('')

        self.populate_support_fields()

    def delete_support(self):
        selected_index = self.support_dropdown.current()
        if selected_index == -1:  # No selection
            return

        support_id = list(self.input_supports.keys())[selected_index]
        del self.input_supports[support_id]
        # Renumbering the remaining supports
        new_input_supports = {}
        for i, key in enumerate(sorted(self.input_supports.keys())):
            new_input_supports[str(i)] = self.input_supports[key]

        self.input_supports = new_input_supports
        # Update information window
        self.update_system_information()
        # Update the combobox options and entry fields
        self.update_support_dropdown()

    def calc_settings(self):
        # Get settings from calc setting form
        method = str(self.method_dict[self.method_combobox.get()])
        try:
            number_of_iterations = int(self.num_iterations_entry.get())
        except ValueError as e:
            # Show a warning message box
            messagebox.showwarning("Warning", "Number of iterations must be an integer!")
            return
        delta_f = float(self.delta_f_entry.get())
        # Add the new load to the input_forces dictionary
        self.input_calc_param = {'calc_method': method,
                                 'number_of_iterations': number_of_iterations,
                                 'delta_f_max': delta_f}
        # Set calculation parameter initializer to 1, required to overwrite initial parameters properly
        self.add_calc_initialise = 1
        # Update information window
        self.update_system_information()

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
        input_parameters_calculation = [self.input_elements,
                                        self.input_supports,
                                        self.input_forces,
                                        self.input_calc_param
                                        ]
        # calculation = Calculation(*input_parameters_calculation)
        calculation = Calculation(self.input_elements, self.input_supports, self.input_forces, self.input_calc_param)
        self.solution = calculation.return_solution()
        print('The axial forces of the linear elastic calculation are:')
        print(self.solution['axial_forces_linear'])
        print('The axial forces of the nonlinear elastic / ideal plastic calculation are:')
        print(self.solution['axial_forces_nonlinear'])

    def clear_all(self):
        pass
        # Clear all
        # ...


# Run the application
if __name__ == "__main__":
    app = TrussAnalysisApp()
    app.mainloop()
