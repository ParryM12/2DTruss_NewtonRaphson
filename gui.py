"""
#######################################################################
LICENSE INFORMATION
This file is part of Truss FEM.

Truss FEM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Truss FEM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Truss FEM. If not, see <https://www.gnu.org/licenses/>.
#######################################################################

#######################################################################
Description:
Main file for starting GUI
#######################################################################
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from gui_settings import GUI_Settings
import copy
from calculation import Calculation
import json
import pyautogui
from PIL import ImageTk, Image
import base64
from io import BytesIO
import webbrowser

#################################################
# Other
AUTHOR = 'Marius Mellmann, Elias Perras'
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
RELEASE_DATE = '06.01.2024'
CONTACT = 'info@pum-consulting.de'


#################################################


# Function to set icon to windows
def set_icon(root):
    """
    Creates Icon from raw byte data to not need external files for creating .exe
    :return:
    """
    icon_image = ImageTk.PhotoImage(data=GUI_Settings.return_icon_bytestring())
    root.tk.call('wm', 'iconphoto', root._w, icon_image)


def center_window(window, width, height):
    # Get the screen dimension
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the x and y coordinates
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    window.geometry(f'{width}x{height}+{x}+{y}')


# Splash screen duration and progress bar update interval in milliseconds
SPLASH_TIME = 3000

# Create splash window
splash_root = tk.Tk()
set_icon(splash_root)
splash_root.title("Truss FEM - Nonlinear Truss Structure Analysis")
splash_root.geometry("512x512")  # Set your desired size
center_window(splash_root, 512, 512)
# Convert base64 string to PIL Image
image_data = base64.b64decode(GUI_Settings.return_splashimage_base64())
logo_image = Image.open(BytesIO(image_data))
logo_photo = ImageTk.PhotoImage(logo_image)

# Create and pack a label with the logo image
logo_label = tk.Label(splash_root, image=logo_photo)
logo_label.pack()


# Function to close the splash screen and open the main window
def end_splash():
    splash_root.destroy()


# Timer to close the splash screen
splash_root.after(SPLASH_TIME, end_splash)

# Run the splash screen
splash_root.mainloop()


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
        set_icon(self)
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
        self.methods = ('linear', 'NR', 'modNR')

        self.ele_number = 0
        self.force_number = 0
        self.support_number = 0
        self.add_element_initialise = 0
        self.add_support_initialise = 0
        self.add_load_initialise = 0
        self.add_calc_initialise = 0
        self.max_force = 1
        self.max_reaction_force = 1
        self.edit_cx = 0
        self.edit_cy = 0
        self.linear_displacement = None
        self.nonlinear_displacement = None
        self.nodes = []
        self.header_text = []
        self.input_elements = copy.deepcopy(self.input_elements_init)
        self.input_supports = copy.deepcopy(self.input_supports_init)
        self.input_forces = copy.deepcopy(self.input_forces_init)
        self.input_calc_param = copy.deepcopy(self.input_calc_param_init)

    def init_ui(self):
        # Adjust the size
        self.geometry(f"{GUI_Settings.screensize[0]}x{GUI_Settings.screensize[1]}")
        self.resizable(False, False)
        center_window(self, GUI_Settings.screensize[0], GUI_Settings.screensize[1])

        # Main frame for forms
        main_frame = ttk.Frame(self)
        main_frame.pack(side="left", fill='y', padx=20, pady=20)

        # Canvas frame for plotting
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(side="left", fill="both", expand=True)

        # New frame for plot options
        plot_options_frame = ttk.Frame(self)
        plot_options_frame.pack(side="left", fill='y', padx=60, pady=20, anchor='nw')

        # Adding a horizontal separator on top
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10, pady=5)
        ##############
        # Initialize buttons for saving/loading input files
        # Create Frame
        save_frame = tk.Frame(main_frame)
        save_frame.pack(padx=10, pady=10, fill='x', anchor='nw')
        # Configure the column width
        save_frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1 * 0.33)
        save_frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL2 * 0.33)
        save_frame.columnconfigure(2, minsize=GUI_Settings.FRAME_WIDTH_COL2 * 0.33)
        # Create Button
        ttk.Button(save_frame, text="Save Data", command=self.save_to_file).grid(row=0, column=0, padx=15, pady=0,
                                                                                 sticky='w')
        ttk.Button(save_frame, text="Load Data", command=self.load_from_file).grid(row=0, column=1, padx=15, pady=0,
                                                                                   sticky='w')
        ttk.Button(save_frame, text="Clear all", command=self.clear_all).grid(row=0, column=2, padx=15, pady=0,
                                                                              sticky='w')
        #############

        # Adding a horizontal separator
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10, pady=5)

        # Initialize forms for input parameters
        input_param_text = tk.Label(main_frame, text="Input parameters", font=GUI_Settings.FRAME_HEADER_FONT)
        input_param_text.pack(anchor='nw')
        self.add_elements_form(main_frame)
        self.add_supports_form(main_frame)
        self.add_loads_form(main_frame)
        self.calculation_settings_form(main_frame)

        # Adding a horizontal separator
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10, pady=5)
        ##############
        # Calculation button
        ttk.Button(main_frame, text="Run Calculation", command=self.run_calculation).pack(pady=10)
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10, pady=5)

        # Canvas for displaying results
        canvas_text = tk.Label(canvas_frame, text="System and results", font=GUI_Settings.FRAME_HEADER_FONT)
        canvas_text.place(relx=0.02, rely=0.014)
        self.canvas = tk.Canvas(canvas_frame, width=round(GUI_Settings.screensize[0] * 0.62),
                                height=round(GUI_Settings.screensize[1] * 0.7),
                                bg=GUI_Settings.CANVAS_BG, highlightbackground="black", highlightthickness=1)
        self.canvas.place(relx=0.02, rely=0.04)

        # Frame for system information and scrollbar
        sys_info_frame = tk.Frame(self)
        sys_info_frame.place(relx=0.215, rely=0.79, relwidth=0.41, relheight=0.17)  # Adjust dimensions as needed

        # Text widget for system information
        current_system_information_label = tk.Label(self, text="System Information:",
                                                    font=GUI_Settings.FRAME_HEADER_FONT)
        current_system_information_label.place(relx=0.215, rely=0.76)
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
        calc_info_frame.place(relx=0.64, rely=0.79, relwidth=0.33, relheight=0.17)  # Adjust dimensions as needed

        # Text widget for calculation information
        calculation_information_label = tk.Label(self, text="Calculation Information:",
                                                 font=GUI_Settings.FRAME_HEADER_FONT)
        calculation_information_label.place(relx=0.64, rely=0.76)
        initial_calculation_information = f"Information about the calculation will be displayed here."
        self.current_calculation_information = tk.Text(calc_info_frame, wrap=tk.WORD,
                                                       font=GUI_Settings.STANDARD_FONT_2, bg='light gray', fg='black')
        self.current_calculation_information.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.current_calculation_information.insert(tk.END, initial_calculation_information)
        self.current_calculation_information.config(state='disabled')
        # Defining tags for different text colors in current_calculation_information Text widget
        self.current_calculation_information.tag_config("green_text", foreground="green")
        self.current_calculation_information.tag_config("red_text", foreground="red")

        # Scrollbar for the Text widget
        scrollbar_calcinfo = tk.Scrollbar(calc_info_frame, orient='vertical',
                                          command=self.current_calculation_information.yview)
        scrollbar_calcinfo.pack(side=tk.RIGHT, fill=tk.Y)

        # Attach the scrollbar to the Text widget
        self.current_calculation_information.config(yscrollcommand=scrollbar_calcinfo.set)

        # Plot options #
        # Adding a horizontal separator on top
        separator11 = ttk.Separator(plot_options_frame, orient='horizontal')
        separator11.pack(fill='x', padx=10, pady=5)
        ##############
        # Initialize buttons for showing info / tutorial
        # Create Frame
        info_frame = tk.Frame(plot_options_frame)
        info_frame.pack(padx=0, pady=10, fill='x', anchor='nw')
        # Configure the column width
        info_frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1 * 0.33)
        info_frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL2 * 0.33)
        # Create Button
        ttk.Button(info_frame, text="Info", command=self.display_info).grid(row=0, column=0, padx=10, pady=0,
                                                                            sticky='w')
        ttk.Button(info_frame, text="Tutorial", command=self.display_tutorial).grid(row=0, column=1, padx=10, pady=0,
                                                                                    sticky='w')
        #############
        # Adding a horizontal separator
        separator12 = ttk.Separator(plot_options_frame, orient='horizontal')
        separator12.pack(fill='x', padx=10, pady=5)

        # Label Plot Options
        plot_options_text = tk.Label(plot_options_frame, text="Plot options", font=GUI_Settings.FRAME_HEADER_FONT)
        plot_options_text.pack(anchor='nw')

        # Create Frame for plotting the system
        plot_system_frame = ttk.LabelFrame(plot_options_frame, text='Plot system')
        plot_system_frame.pack(padx=10, pady=10, fill='x', anchor='nw')
        # Configure the column width
        plot_system_frame.columnconfigure(0, minsize=GUI_Settings.FRAME_WIDTH_COL1 * 0.5)
        plot_system_frame.columnconfigure(1, minsize=GUI_Settings.FRAME_WIDTH_COL1 * 0.5)
        # Button and settings for plotting system with supports and loads
        ttk.Label(plot_system_frame, text="Show grid:").grid(row=0, column=0, sticky='w')
        self.show_grid_state = tk.BooleanVar(value=True)
        self.show_grid = ttk.Checkbutton(plot_system_frame, variable=self.show_grid_state, command=self.toggle_grid)
        self.show_grid.grid(row=0, column=1)
        ttk.Label(plot_system_frame, text="Show loads:").grid(row=1, column=0, sticky='w')
        self.show_loads_state = tk.BooleanVar(value=True)
        self.show_loads = ttk.Checkbutton(plot_system_frame, variable=self.show_loads_state, command=self.toggle_loads)
        self.show_loads.grid(row=1, column=1)
        ttk.Label(plot_system_frame, text="Show header:").grid(row=2, column=0, sticky='w')
        self.show_header_state = tk.BooleanVar(value=False)
        self.show_header = ttk.Checkbutton(plot_system_frame, variable=self.show_header_state,
                                           command=self.toggle_header)
        self.show_header.grid(row=2, column=1)
        ttk.Label(plot_system_frame, text="Label nodes:").grid(row=3, column=0, sticky='w')
        self.show_node_labels_state = tk.BooleanVar(value=False)
        self.label_nodes_checkbox = ttk.Checkbutton(plot_system_frame, variable=self.show_node_labels_state,
                                                    command=self.toggle_node_labels)
        self.label_nodes_checkbox.grid(row=3, column=1)
        ttk.Label(plot_system_frame, text="Label elements:").grid(row=4, column=0, sticky='w')
        self.show_element_labels_state = tk.BooleanVar(value=False)
        self.label_elements_checkbox = ttk.Checkbutton(plot_system_frame, variable=self.show_element_labels_state,
                                                       command=self.toggle_element_labels)
        self.label_elements_checkbox.grid(row=4, column=1)
        self.plot_button = ttk.Button(plot_system_frame, text="Plot system", command=self.plot_system, state='disabled')
        self.plot_button.grid(row=5, column=0, columnspan=2, pady=5, padx=10, sticky='ew')
        # Label Plot Results
        plot_results_text = tk.Label(plot_options_frame, text="Plot results", font=GUI_Settings.FRAME_HEADER_FONT)
        plot_results_text.pack(anchor='nw')
        # Create Frame for plotting the results of the linear calculation
        plot_linear_frame = ttk.LabelFrame(plot_options_frame, text='Linear calculation')
        plot_linear_frame.pack(padx=10, pady=10, fill='x', anchor='nw')
        # Button for plotting system and deformed system in red
        self.plot_linear_deformation = ttk.Button(plot_linear_frame, text="Plot deformed system",
                                                  command=lambda: self.plot_deformation_system(
                                                      self.linear_displacement),
                                                  state='disabled')
        self.plot_linear_deformation.pack(padx=10, pady=7, fill='x')
        # Button for plotting system and axial forces
        self.plot_linear_forces = ttk.Button(plot_linear_frame, text="Plot axial forces",
                                             command=lambda: self.plot_axial_forces('linear'), state='disabled')
        self.plot_linear_forces.pack(padx=10, pady=7, fill='x')

        # Create Frame for plotting the results of the nonlinear calculation
        plot_nonlinear_frame = ttk.LabelFrame(plot_options_frame, text='Nonlinear calculation')
        plot_nonlinear_frame.pack(padx=10, pady=10, fill='x', anchor='nw')
        # Button for plotting system and deformed system in red
        self.plot_nonlinear_deformation = ttk.Button(plot_nonlinear_frame, text="Plot deformed system",
                                                     command=lambda: self.plot_deformation_system(
                                                         self.nonlinear_displacement),
                                                     state='disabled')
        self.plot_nonlinear_deformation.pack(padx=10, pady=7, fill='x')
        # Button for plotting system and axial forces
        self.plot_nonlinear_forces = ttk.Button(plot_nonlinear_frame, text="Plot axial forces",
                                                command=lambda: self.plot_axial_forces('nonlinear'), state='disabled')
        self.plot_nonlinear_forces.pack(padx=10, pady=7, fill='x')
        # Adding a horizontal separator
        separator1 = ttk.Separator(plot_options_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10, pady=5)
        # Button to export the current plot
        self.export_plot = ttk.Button(plot_options_frame, text="Export plot", command=self.export_canvas,
                                      state='disabled')
        self.export_plot.pack(padx=10, pady=7, fill='x')
        # Adding a horizontal separator
        separator1 = ttk.Separator(plot_options_frame, orient='horizontal')
        separator1.pack(fill='x', padx=10, pady=5)

        # Initialize grid, Schedule toggle_grid to run after the mainloop starts
        self.after(100, self.toggle_grid)  # 100 milliseconds delay

        # Add coordinate system to canvas
        # Define starting point (top-left corner with some padding)
        start_x, start_y = 10, 10
        # Length of the arrows
        arrow_length = 40
        # Draw x-axis arrow
        self.canvas.create_line(start_x, start_y, start_x + arrow_length, start_y, arrow=tk.LAST)
        self.canvas.create_text(start_x + arrow_length - 5, start_y + 8, text="x", anchor="center", width=1.5,
                                font=GUI_Settings.ITALIC_FONT_1)
        # Draw y-axis arrow
        self.canvas.create_line(start_x, start_y, start_x, start_y + arrow_length, arrow=tk.LAST)
        self.canvas.create_text(start_x + 12, start_y + arrow_length - 8, text="y", anchor="center", width=1.5,
                                font=GUI_Settings.ITALIC_FONT_1)

    def draw_grid(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale, translate_x, translate_y, max_dimension = self.calculate_bounds_and_scale()
        center_x, center_y = self.scale_and_translate(0, 0)
        range_m = 100  # +/- range in meters
        grid_spacing_init = canvas_width / (4 * 5)  # Initial grid spacing when launching the program
        if max_dimension <= 10:
            tick_spacing = 0.5
        elif 10 < max_dimension <= 20:
            tick_spacing = 1
        elif 20 < max_dimension <= 40:
            tick_spacing = 2
        elif 40 < max_dimension <= 50:
            tick_spacing = 2.5
        elif 50 < max_dimension <= 100:
            tick_spacing = 5
        else:
            tick_spacing = 10
        if max_dimension > 0:
            grid_spacing = tick_spacing * scale
        else:
            grid_spacing = grid_spacing_init
        tick_length = 10  # Length of the ticks

        # Draw grid lines, labels, and ticks
        for i in range(-range_m, range_m + 1):
            offset = i * grid_spacing

            # Horizontal grid lines and ticks
            x = center_x + offset
            self.canvas.create_line(x, 0, x, canvas_height, fill='gray', tags='grid_line')
            self.canvas.create_line(x - offset / 2, 0, x - offset / 2, canvas_height, fill='gray79', tags='grid_line')
            self.canvas.create_line(x, center_y - tick_length // 2, x, center_y + tick_length // 2, fill='black',
                                    tags='grid_tick', width=2)

            # Vertical grid lines and ticks
            y = center_y + offset
            self.canvas.create_line(0, y, canvas_width, y, fill='gray', tags='grid_line')
            self.canvas.create_line(0, y - offset / 2, canvas_width, y - offset / 2, fill='gray79', tags='grid_line')
            self.canvas.create_line(center_x - tick_length // 2, y, center_x + tick_length // 2, y, fill='black',
                                    tags='grid_tick', width=2)
            # Labels
            self.canvas.create_text(x + 3, center_y + 3, text=f"{i * tick_spacing}m", fill='black',
                                    tags='grid_label', anchor='nw')
            # Avoid duplicating the center line label
            if i != 0:
                self.canvas.create_text(center_x + 3, y + 3, text=f"{i * tick_spacing}m", fill='black',
                                        tags='grid_label', anchor='nw')

        # Draw horizontal and vertical center lines
        self.canvas.create_line(center_x, 0, center_x, canvas_height, fill='black', tags='grid_line', width=2)
        self.canvas.create_line(0, center_y, canvas_width, center_y, fill='black', tags='grid_line', width=2)

    def clear_grid(self):
        # Remove all grid lines and labels
        self.canvas.delete("grid_line")
        self.canvas.delete("grid_label")
        self.canvas.delete("grid_tick")

    def toggle_grid(self):
        if self.show_grid_state.get():
            self.draw_grid()
        else:
            self.clear_grid()

    def display_info(self):
        # Create a top-level window
        info_window = tk.Toplevel(self)
        set_icon(info_window)
        info_window.geometry('600x300')
        info_window.resizable(False, False)
        center_window(info_window, 600, 300)
        info_window.title("Information")

        # Create a Text widget
        info_text_widget = tk.Text(info_window, wrap='word', height=15, width=70)
        info_text_widget.pack(padx=10, pady=10)

        # Insert the information text
        info_text = ("Truss FEM is a non-commercial FEM software to calculate the axial forces and displacements of "
                     "linear and nonlinear truss structures. Truss FEM is distributed in the hope that it will be "
                     "useful, but without and warranty; without even the implied warranty of merchantability or "
                     "fitness for a particular purpose.\n"
                     "If you find any errors or have suggestions for improvement, please feel free to contact us.\n\n")
        info_text += f"\nAuthors: {AUTHOR}\n"
        info_text += f"Contact: {CONTACT}\n"
        info_text += f"Version: {VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
        info_text += f"\nRelease: {RELEASE_DATE}\n"
        info_text += f"License: "
        info_text_widget.insert('1.0', info_text)

        # Add hyperlink text
        hyperlink_text = "GNU General Public License"
        info_text_widget.insert('end', hyperlink_text)  # Insert hyperlink text at the end
        start = "end-{}c".format(len(hyperlink_text) + 1)  # Calculate the start position of the hyperlink text
        info_text_widget.tag_add("hyperlink", start, "end")  # Apply the tag only to the hyperlink text
        info_text_widget.tag_config("hyperlink", foreground="blue", underline=True)

        # Function to open a hyperlink
        def open_hyperlink(url):
            try:
                webbrowser.open_new(url)
            except ValueError as e:
                # Show a warning message box
                messagebox.showwarning("Warning", "Could not open webbrowser! Maybe open the link "
                                                  "https://www.gnu.org/licenses/ manually.")

        info_text_widget.tag_bind("hyperlink", "<Button-1>", lambda e: open_hyperlink("https://www.gnu.org/licenses/"))

        # Make the text widget read-only
        info_text_widget.config(state='disabled')

    def display_tutorial(self):
        # Create a top-level window
        tutorial_window = tk.Toplevel(self)
        set_icon(tutorial_window)
        tutorial_window.geometry('600x300')
        tutorial_window.resizable(False, False)
        center_window(tutorial_window, 600, 300)
        tutorial_window.title("Tutorial")

        # Create a Text widget
        tutorial_text_widget = tk.Text(tutorial_window, wrap='word', height=15, width=70)
        tutorial_text_widget.pack(padx=10, pady=10)

        # Define tags for different font styles and sizes
        tutorial_text_widget.tag_configure('header1', font=('Helvetica', 14, 'bold'), justify="center")
        tutorial_text_widget.tag_configure('header2', font=('Helvetica', 12, 'bold'))
        tutorial_text_widget.tag_configure('text', font=('Helvetica', 12))

        # Insert the information text
        tutorial_header1 = "Tutorial TrussFEM\n\n"
        # tutorial_header2 = "General Information\n"
        tutorial_text1 = ("TrussFEM is a FEM-Software to calculate the axial forces and displacements of linear and "
                          "nonlinear 2D truss structures. The nonlinear material model has the following quadratic "
                          "stress-strain-relationship:\n\n")
        tutorial_equation1 = ("σ(ε) = (α ∙ ε ± β ∙ ε²) ∙ E_0 for |ε| ≤ ε_y\n"
                              "σ(ε) = σ_y for |ε| ≥ ε_y\n\n"
                              "where\n"
                              "σ       – Axial stress (N/mm²)\n"
                              "σ_y   – Limit axial stress (yield stress) (N/mm²)\n"
                              "ε        – Axial strain [ - ]\n"
                              "ε_y    – Limit axial strain (yield strain) [ - ]\n"
                              "α       – Linear coefficient\n"
                              "β       – Quadratic coefficient\n"
                              "E_0  – Young’s modulus (initial tangent stiffness)\n\n")
        tutorial_text2 = ("This stress-strain relationship is the same for compressive and tensile stresses and is "
                          "illustrated in the figure below. Due this circumstance, the input parameters ε_y, α and β "
                          "are not sign sensitive.\n\n")
        # Include image of stress-strain-relationship
        image_data = base64.b64decode(GUI_Settings.return_stress_strain_base64())
        stress_strain_photo = Image.open(BytesIO(image_data))
        stress_strain_photo = ImageTk.PhotoImage(stress_strain_photo)
        # Further explanation
        tutorial_text3 = ("Due to the non-linear material behavior, a linear calculation results in an imbalance in "
                          "the nodal forces. In order to determine the nodal forces for the equilibrium state, a "
                          "nonlinear problem must be solved. The nonlinear problem is solved by the classical "
                          "Newton-Raphson- or the modified Newton-Raphson-Method. In both methods, the calculation is "
                          "carried out iteratively, with the calculation running until either a termination criterion "
                          "(ΔF_max) for the maximal nodal force imbalance is met or the specified maximum number of "
                          "iterations is reached. During the calculation, the axial forces are updated in each step "
                          "based on the stress-strain relationship. The classic Newton-Raphson method also updates "
                          "the Young's modulus for each element. This method therefore exhibits quadratic "
                          "convergence. In the modified method, the Young's moduli are not updated, which reduces "
                          "the effort in each calculation step, but the procedure only converges linearly and "
                          "generally requires more iterations to reach the equilibrium state.\n\n")

        # Add text and apply tags
        tutorial_text_widget.insert('end', tutorial_header1, 'header1')
        # tutorial_text_widget.insert('end', tutorial_header2, 'header2')
        tutorial_text_widget.insert('end', tutorial_text1, 'text')
        tutorial_text_widget.insert('end', tutorial_equation1, 'text')
        tutorial_text_widget.insert('end', tutorial_text2, 'text')
        # Insert the image into the Text widget
        tutorial_text_widget.image_create('end', image=stress_strain_photo)
        # Add text and apply tags
        tutorial_text_widget.insert('end', tutorial_text3, 'text')

        # Keep a reference to the image to prevent garbage collection
        tutorial_text_widget.image = stress_strain_photo

        # Make the text read-only (optional)
        tutorial_text_widget.configure(state='disabled')

    def export_canvas(self):
        # Get canvas bounds
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Ask the user for a file name to save the image
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"),
                                                                                    ("JPG files", "*.jpg")])

        if filepath:
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot.save(filepath)

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
                if sup['c_x'] != 1:
                    c_x = sup['c_x']
                else:
                    c_x = '∞'
                if sup['c_y'] != 1:
                    c_y = sup['c_y']
                else:
                    c_y = '∞'
                info_text += (f"Support {sup['sup_number']}: Node = {sup['sup_node']}, c_x = {c_x} kN/m, "
                              f"c_y = {c_y} kN/m.\n")

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

    def update_calculation_information(self):
        info_text = "Calculation Results:\n"
        imbalance_info = ""
        info_text_calc = ""
        info_text_strain_nonlinear = ""
        strain_nonlinear_info = []
        imbalance_tag = None
        strain_nonlinear_tag = []

        if self.solution is not None:
            # Case: Nonlinear calculation
            if self.solution['node_displacements_nonlinear'] is not None:
                # Node Displacements - Linear Calculation
                info_text += "\nNode Displacements (Linear Calculation):\n"
                for node, displacement in enumerate(self.solution['node_displacements_linear']):
                    info_text += (f"Node {node}: u = {round(displacement[0] * 1000, 3)} mm, w = "
                                  f"{round(displacement[1] * 1000, 2)} mm.\n")

                # Node Displacements - Nonlinear Calculation
                info_text += "\nNode Displacements (Nonlinear Calculation):\n"
                for node, displacement in enumerate(self.solution['node_displacements_nonlinear']):
                    info_text += (f"Node {node}: u = {round(displacement[0] * 1000, 3)} mm, w = "
                                  f"{round(displacement[1] * 1000, 2)} mm.\n")

                # Axial Forces - Linear Calculation
                info_text += "\nAxial Forces (Linear Calculation):\n"
                for element, force in enumerate(self.solution['axial_forces_linear']):
                    info_text += f"Element {element}: N = {force} kN.\n"

                # Axial Forces - Nonlinear Calculation
                info_text += "\nAxial Forces (Nonlinear Calculation):\n"
                for element, force in enumerate(self.solution['axial_forces_nonlinear']):
                    info_text += f"Element {element}: N = {force} kN.\n"

                # Strains - Nonlinear Calculation
                info_text_strain_nonlinear += "\nElement strains (Nonlinear Calculation):\n"
                for element, strain in enumerate(self.solution['strains_nonlinear']):
                    eps_f_i = abs(self.input_elements[str(element)]['ele_eps_f'])
                    beta_i = abs(self.input_elements[str(element)]['ele_quad_coeff'])
                    if (abs(strain) <= eps_f_i) and (beta_i != 0):
                        strain_nonlinear_info.append(f"Element {element}: |ε| = {round(abs(strain[0]) * 100, 4)} "
                                                     f"≤ {eps_f_i * 100} [%].\n")
                        strain_nonlinear_tag.append("green_text")
                    elif abs(strain) > eps_f_i and (beta_i != 0):
                        strain_nonlinear_info.append(f"Element {element}: |ε| = {round(abs(strain[0]) * 100, 4)} "
                                                     f"> {eps_f_i * 100} [%].\n")
                        strain_nonlinear_tag.append("red_text")
                    elif beta_i == 0:
                        strain_nonlinear_info.append(f"Element {element}: |ε| = {round(abs(strain[0]) * 100, 4)} [%]"
                                                     f" (linear element).\n")
                        strain_nonlinear_tag.append("green_text")

                # Additional Information (iterations, force imbalance)
                max_nodal_force_imbalance = max(abs(self.solution['node_forces_mismatch']))
                delta_f_max = self.input_calc_param['delta_f_max']
                info_text_calc = "\nConvergence of the solution:\n"
                # Check nodal force imbalance and apply tag
                if max_nodal_force_imbalance < delta_f_max:
                    imbalance_info = (f"SUCCESS: Termination criterion ΔF = {max_nodal_force_imbalance[0]} kN < "
                                      f"ΔF_max = {delta_f_max} kN "
                                      f"met at iteration step {self.solution['iteration_break_number']}.")
                    imbalance_tag = "green_text"
                else:
                    imbalance_info = (f"WARNING: Termination criterion ΔF = {max_nodal_force_imbalance[0]} kN < "
                                      f"ΔF_max = {delta_f_max}  kN is not met! The iteration stopped after maximal "
                                      f"amount of {self.solution['iteration_break_number']} iterations.")
                    imbalance_tag = "red_text"
            else:
                # Node Displacements
                info_text += "\nNode Displacements (Linear Calculation):\n"
                for node, displacement in enumerate(self.solution['node_displacements_linear']):
                    info_text += (f"Node {node}: u = {round(displacement[0] * 1000, 3)} mm, w = "
                                  f"{round(displacement[1] * 1000, 2)} mm.\n")

                # Axial Forces - Linear Calculation
                info_text += "\nAxial Forces (Linear Calculation):\n"
                for element, force in enumerate(self.solution['axial_forces_linear']):
                    info_text += f"Element {element}: N = {force} kN.\n"

        else:
            info_text += "\nNo calculation results available."

        # Updating the text widget
        self.current_calculation_information.config(state='normal')
        self.current_calculation_information.delete(1.0, tk.END)
        self.current_calculation_information.insert(tk.END, info_text)
        if strain_nonlinear_tag:
            self.current_calculation_information.insert(tk.END, info_text_strain_nonlinear)
            for key, strain_text in enumerate(strain_nonlinear_info):
                self.current_calculation_information.insert(tk.END, strain_text, strain_nonlinear_tag[key])
        if imbalance_tag:
            self.current_calculation_information.insert(tk.END, info_text_calc)
            self.current_calculation_information.insert(tk.END, imbalance_info, imbalance_tag)

        self.current_calculation_information.config(state='disabled')

    def draw_coordinate_system(self):
        # Define starting point (top-left corner with some padding)
        start_x, start_y = 10, 10

        # Length of the arrows
        arrow_length = 40

        # Draw x-axis arrow
        self.canvas.create_line(start_x, start_y, start_x + arrow_length, start_y, arrow=tk.LAST)
        self.canvas.create_text(start_x + arrow_length - 5, start_y + 8, text="x", anchor="center", width=1.5,
                                font=GUI_Settings.ITALIC_FONT_1)

        # Draw y-axis arrow
        self.canvas.create_line(start_x, start_y, start_x, start_y + arrow_length, arrow=tk.LAST)
        self.canvas.create_text(start_x + 12, start_y + arrow_length - 8, text="y", anchor="center", width=1.5,
                                font=GUI_Settings.ITALIC_FONT_1)

    def calculate_bounds_and_scale(self):
        min_x = min([node[0] for element in self.input_elements.values() for node in
                     [element['ele_node_i'], element['ele_node_j']]], default=0)
        max_x = max([node[0] for element in self.input_elements.values() for node in
                     [element['ele_node_i'], element['ele_node_j']]], default=0)
        min_y = min([node[1] for element in self.input_elements.values() for node in
                     [element['ele_node_i'], element['ele_node_j']]], default=0)
        max_y = max([node[1] for element in self.input_elements.values() for node in
                     [element['ele_node_i'], element['ele_node_j']]], default=0)

        truss_width = max_x - min_x
        truss_height = max_y - min_y
        max_dimension = max(abs(truss_width), abs(truss_height))

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        scale_x = canvas_width / (truss_width if truss_width != 0 else 1)
        scale_y = canvas_height / (truss_height if truss_height != 0 else 1)

        scale = min(scale_x, scale_y) * 0.65  # 0.8 for padding

        translate_x = (canvas_width - scale * truss_width) / 2 - min_x * scale
        translate_y = (canvas_height - scale * truss_height) / 2 - min_y * scale

        return scale, translate_x, translate_y, max_dimension

    def scale_and_translate(self, x, y):
        scale, translate_x, translate_y, max_dimension = self.calculate_bounds_and_scale()
        return x * scale + translate_x, y * scale + translate_y

    def draw_element(self):
        # Draw Elements (Truss Members)
        for element in self.input_elements.values():
            hinge_radius = 7
            node_i = self.scale_and_translate(*element['ele_node_i'])
            node_j = self.scale_and_translate(*element['ele_node_j'])
            # Draw the line representing the truss element
            self.canvas.create_line(node_i[0], node_i[1], node_j[0], node_j[1], fill="black", width=2.5)
            # Draw hinge at node_i
            self.canvas.create_oval(node_i[0] - hinge_radius, node_i[1] - hinge_radius,
                                    node_i[0] + hinge_radius, node_i[1] + hinge_radius, outline="black", fill="white",
                                    width=2.5)

            # Draw hinge at node_j
            self.canvas.create_oval(node_j[0] - hinge_radius, node_j[1] - hinge_radius,
                                    node_j[0] + hinge_radius, node_j[1] + hinge_radius, outline="black", fill="white",
                                    width=2.5)

    def draw_support(self, color, displacement):
        # Draw Supports
        for support in self.input_supports.values():
            if displacement is None:
                node = self.scale_and_translate(*support['sup_node'])
            else:
                max_displacement = np.max(abs(displacement))
                deformation_scale = 0.4 / max_displacement
                node0 = support['sup_node']
                node_index = int(self.node_to_index[support['sup_node']])
                node_displacement = displacement[node_index]
                node = self.scale_and_translate(*(node0 + node_displacement * deformation_scale))
            hinge_radius = 7
            x, y = node
            dxy = 29  # Defines the size of the plotted support
            s_dx = 20
            s_dy = 15
            s_hline_dxy = 10
            dxy_hline = 36  # Defines the size of the horizontal line of
            # Support fixed in x- and y- direction:
            if support['c_x'] == '∞' and support['c_y'] == '∞':
                points = [(x, y), (x - dxy, y + dxy), (x + dxy, y + dxy), (x, y)]
                for i in range(len(points) - 1):
                    start = points[i]
                    end = points[i + 1]
                    self.canvas.create_line(start[0], start[1], end[0], end[1], fill=color, width=2.5)
            # Support fixed only in x-direction:
            if support['c_x'] == '∞' and support['c_y'] != '∞':
                points = [(x, y), (x + dxy, y - dxy), (x + dxy, y + dxy), (x, y)]
                points_hline = [(x + dxy_hline, y - dxy_hline), (x + dxy_hline, y + dxy_hline)]
                self.canvas.create_line(points_hline[0][0], points_hline[0][1], points_hline[1][0], points_hline[1][1],
                                        fill=color, width=2.5)
                for i in range(len(points) - 1):
                    start = points[i]
                    end = points[i + 1]
                    self.canvas.create_line(start[0], start[1], end[0], end[1], fill=color, width=2.5)
            # Support fixed only in y-direction:
            if support['c_x'] != '∞' and support['c_y'] == '∞':
                points = [(x, y), (x - dxy, y + dxy), (x + dxy, y + dxy), (x, y)]
                points_hline = [(x - dxy_hline, y + dxy_hline), (x + dxy_hline, y + dxy_hline)]
                self.canvas.create_line(points_hline[0][0], points_hline[0][1], points_hline[1][0], points_hline[1][1],
                                        fill=color, width=2.5)
                for i in range(len(points) - 1):
                    start = points[i]
                    end = points[i + 1]
                    self.canvas.create_line(start[0], start[1], end[0], end[1], fill=color, width=2.5)
            # Support elastic in y-direction and free in x-direction:
            if support['c_y'] != '∞':
                if support['c_y'] > 0:
                    points = [(x, y), (x + s_dx / 2, y + s_dy / 2), (x - s_dx / 2, y + s_dy),
                              (x + s_dx / 2, y + 1.5 * s_dy),
                              (x - s_dx / 2, y + 2 * s_dy), (x + s_dx / 2, y + 2.5 * s_dy),
                              (x - s_dx / 2, y + 2.5 * s_dy)]
                    points_hline = [(x - s_dx / 2 - s_hline_dxy, y + 2.5 * s_dy + s_hline_dxy / 2),
                                    (x + s_dx / 2 + s_hline_dxy, y + 2.5 * s_dy + s_hline_dxy / 2)]
                    self.canvas.create_line(points_hline[0][0], points_hline[0][1], points_hline[1][0],
                                            points_hline[1][1],
                                            fill=color, width=2.5)
                    for i in range(len(points) - 1):
                        start = points[i]
                        end = points[i + 1]
                        self.canvas.create_line(start[0], start[1], end[0], end[1], fill=color, width=2.5)
            # Support elastic in x-direction and free in y-direction:
            if support['c_x'] != '∞':
                if support['c_x'] > 0:
                    points = [(x, y), (x + s_dy / 2, y + s_dx / 2), (x + s_dy, y - s_dx / 2),
                              (x + 1.5 * s_dy, y + s_dx / 2),
                              (x + 2 * s_dy, y - s_dx / 2), (x + 2.5 * s_dy, y + s_dx / 2),
                              (x + 2.5 * s_dy, y - s_dx / 2)]
                    points_hline = [(x + 2.5 * s_dy + s_hline_dxy / 2, y - s_dx / 2 - s_hline_dxy),
                                    (x + 2.5 * s_dy + s_hline_dxy / 2, y + s_dx / 2 + s_hline_dxy)]
                    self.canvas.create_line(points_hline[0][0], points_hline[0][1], points_hline[1][0],
                                            points_hline[1][1],
                                            fill=color, width=2.5)
                    for i in range(len(points) - 1):
                        start = points[i]
                        end = points[i + 1]
                        self.canvas.create_line(start[0], start[1], end[0], end[1], fill=color, width=2.5)
            # Draw hinge at node
            self.canvas.create_oval(node[0] - hinge_radius, node[1] - hinge_radius,
                                    node[0] + hinge_radius, node[1] + hinge_radius, outline=color, fill="white",
                                    width=2.5)

    def draw_load(self):
        # Draw Loads
        dxy = 13
        arrow_shape = (10, 12, 5)  # Length, Length, Width of the arrow. Adjust as needed.
        self.max_force = 1
        # Determine max force for scaling
        for load in self.input_forces.values():
            f_x, f_y = load['f_x'], load['f_y']
            self.max_force = max(self.max_force, abs(f_x), abs(f_y))
        # Draw loads
        for load in self.input_forces.values():
            node = self.scale_and_translate(*load['force_node'])
            f_x, f_y = load['f_x'], load['f_y']
            scale_fx = np.max((abs(f_x / self.max_force) * 80, 20))
            scale_fy = np.max((abs(f_y / self.max_force) * 80, 20))

            if f_x != 0:
                if f_x > 0:
                    self.canvas.create_line(node[0] + dxy, node[1], node[0] + scale_fx + dxy, node[1], arrow=tk.LAST,
                                            width=2.5, fill="blue", arrowshape=arrow_shape, tags='load_arrow')
                else:
                    self.canvas.create_line(node[0] + scale_fx + dxy, node[1], node[0] + dxy, node[1], arrow=tk.LAST,
                                            width=2.5, fill="blue", arrowshape=arrow_shape, tags='load_arrow')
                f_x_label = f"H = {abs(f_x)} kN"
                label_offset_x = 18
                label_offset_y = -14.6
                self.canvas.create_text(node[0] + scale_fx + label_offset_x + dxy, node[1] + label_offset_y,
                                        text=f_x_label, fill="blue", font=GUI_Settings.STANDARD_FONT_1,
                                        tags='load_label')
            if f_y != 0:
                if f_y > 0:
                    self.canvas.create_line(node[0], node[1] - scale_fy - dxy, node[0], node[1] - dxy, arrow=tk.LAST,
                                            width=2.5, fill="blue", arrowshape=arrow_shape, tags='load_arrow')
                else:
                    self.canvas.create_line(node[0], node[1] - dxy, node[0], node[1] - scale_fy - dxy, arrow=tk.LAST,
                                            width=2.5, fill="blue", arrowshape=arrow_shape, tags='load_arrow')
                f_y_label = f"F = {abs(f_y)} kN"
                label_offset_x = 7.3
                label_offset_y = -13.1
                self.canvas.create_text(node[0] + label_offset_x, node[1] - scale_fy + label_offset_y - dxy,
                                        text=f_y_label, fill="blue", font=GUI_Settings.STANDARD_FONT_1,
                                        tags='load_label')

    def clear_load(self):
        # Remove all loads and labels
        self.canvas.delete("load_arrow")
        self.canvas.delete("load_label")

    def toggle_loads(self):
        if self.show_loads_state.get():
            self.draw_load()
        else:
            self.clear_load()

    def draw_reaction_forces(self, reactions):
        if reactions is not None:
            # Reshape input
            reactions = reactions.reshape(-1, 2)
            self.nodes = self.solution['nodes']
            self.max_reaction_force = np.max(abs(reactions))
            # Draw Loads
            dxy = 40
            arrow_shape = (10, 12, 5)  # Length, Length, Width of the arrow. Adjust as needed
            for index, reaction in enumerate(reactions):
                node = self.scale_and_translate(*self.nodes[index])
                f_x, f_y = reaction[0], reaction[1]
                scale_fx = np.max((abs(f_x / self.max_reaction_force) * 80, 20))
                scale_fy = np.max((abs(f_y / self.max_reaction_force) * 80, 20))
                if abs(f_x) > np.max((1, self.input_calc_param_init['delta_f_max'])):
                    if f_x > 0:
                        self.canvas.create_line(node[0] - dxy, node[1], node[0] - scale_fx - dxy, node[1],
                                                arrow=tk.LAST,
                                                width=2.5, fill="purple", arrowshape=arrow_shape, tags='reaction_arrow')
                    else:
                        self.canvas.create_line(node[0] - scale_fx - dxy, node[1], node[0] - dxy, node[1],
                                                arrow=tk.LAST,
                                                width=2.5, fill="purple", arrowshape=arrow_shape, tags='reaction_arrow')
                    f_x_label = f"R_x = {abs(f_x)} kN"
                    label_offset_x = 60
                    label_offset_y = -18.6
                    self.canvas.create_text(node[0] - scale_fx - label_offset_x, node[1] + label_offset_y,
                                            text=f_x_label, fill="purple", font=GUI_Settings.STANDARD_FONT_1,
                                            tags='reaction_label')
                if abs(f_y) > np.max((1, self.input_calc_param_init['delta_f_max'])):
                    if f_y > 0:
                        self.canvas.create_line(node[0], node[1] + scale_fy + dxy, node[0], node[1] + dxy,
                                                arrow=tk.LAST,
                                                width=2.5, fill="purple", arrowshape=arrow_shape, tags='reaction_arrow')
                    else:
                        self.canvas.create_line(node[0], node[1] + dxy, node[0], node[1] + scale_fy + dxy,
                                                arrow=tk.LAST,
                                                width=2.5, fill="purple", arrowshape=arrow_shape, tags='reaction_arrow')
                    f_y_label = f"R_y = {abs(f_y)} kN"
                    label_offset_x = 70
                    label_offset_y = 25
                    self.canvas.create_text(node[0] + label_offset_x, node[1] + scale_fy + label_offset_y,
                                            text=f_y_label, fill="purple", font=GUI_Settings.STANDARD_FONT_1,
                                            tags='reaction_label')

    def toggle_header(self):
        if self.show_header_state.get():
            self.canvas.create_text(self.canvas.winfo_width() - 10, 10, text=self.header_text, anchor='ne',
                                    fill="black",
                                    font=GUI_Settings.STANDARD_FONT_1, tags='header')
        else:
            self.canvas.delete("header")

    def label_nodes(self):
        for element in self.input_elements.values():
            # Check and add nodes to the list if they are not already in it
            if element['ele_node_i'] not in self.nodes:
                self.nodes.append(element['ele_node_i'])
            if element['ele_node_j'] not in self.nodes:
                self.nodes.append(element['ele_node_j'])

        # Create node label
        label_offset_x = 10
        label_offset_y = -17
        for index, node in enumerate(self.nodes):
            node = self.scale_and_translate(*node)
            self.canvas.create_text(node[0] + label_offset_x, node[1] + label_offset_y,
                                    text=f"N{index}", fill="dark orange", font=GUI_Settings.STANDARD_FONT_1,
                                    tags='node_label')

    def toggle_node_labels(self):
        if self.show_node_labels_state.get():
            self.label_nodes()
        else:
            self.canvas.delete("node_label")

    def label_elements(self):
        label_offset_x = 17
        label_offset_y = -17
        index = 0
        for element in self.input_elements.values():
            node_i = element['ele_node_i']
            node_j = element['ele_node_j']
            label_x = node_i[0] + (node_j[0] - node_i[0]) / 2
            label_y = node_i[1] + (node_j[1] - node_i[1]) / 2
            label_sign = np.sign((node_j[0] - node_i[0]) * (node_j[1] - node_i[1]))
            label_x, label_y = self.scale_and_translate(label_x, label_y)
            self.canvas.create_text(label_x + label_offset_x * label_sign, label_y + label_offset_y,
                                    text=f"E{index}", fill="dark orange", font=GUI_Settings.STANDARD_FONT_1,
                                    tags='element_label')
            index += 1

    def toggle_element_labels(self):
        if self.show_element_labels_state.get():
            self.label_elements()
        else:
            self.canvas.delete("element_label")

    def plot_deformation_system(self, displacement):
        # Clear existing canvas
        self.canvas.delete("all")
        # Create grid, if selected
        self.toggle_grid()
        # Draw coordinate system
        self.draw_coordinate_system()
        # Draw undeformed elements, supports, and loads
        self.draw_element()
        self.draw_support('black', None)
        # self.draw_load()
        self.toggle_loads()
        self.toggle_node_labels()

        # Deformation scale factor and max displacements
        max_displacement = np.max(abs(displacement))
        max_u_index = max(range(len(displacement)), key=lambda i: abs(displacement[i][0]))
        max_w_index = max(range(len(displacement)), key=lambda i: abs(displacement[i][1]))
        max_displacement_u = displacement[max_u_index][0] * 1000
        max_displacement_w = displacement[max_w_index][1] * 1000
        # deformation_scale = max_dimension * 0.1 / max_displacement
        deformation_scale = 0.4 / max_displacement
        # hinge_radius = 0.006 * max_dimension * scale
        hinge_radius = 7

        # Displaying the text on the canvas
        self.header_text = (f"Max. displacements: \nu = {max_displacement_u:.2f} mm (node {max_u_index})\nw = "
                            f"{max_displacement_w:.2f} mm (node {max_w_index})\nScaling factor: {deformation_scale:.2f}")
        self.toggle_header()

        # Draw deformed elements
        for element_id, element in self.input_elements.items():
            node_i_index = int(self.node_to_index[element['ele_node_i']])
            node_j_index = int(self.node_to_index[element['ele_node_j']])

            # Get the displacements for the nodes
            u_i, v_i = displacement[node_i_index]
            u_j, v_j = displacement[node_j_index]

            # Scale the displacements
            u_i_scaled, v_i_scaled = u_i * deformation_scale, v_i * deformation_scale
            u_j_scaled, v_j_scaled = u_j * deformation_scale, v_j * deformation_scale

            # Calculate the deformed positions of the nodes
            node_i_deformed = self.scale_and_translate(element['ele_node_i'][0] + u_i_scaled,
                                                       element['ele_node_i'][1] + v_i_scaled)
            node_j_deformed = self.scale_and_translate(element['ele_node_j'][0] + u_j_scaled,
                                                       element['ele_node_j'][1] + v_j_scaled)

            # Draw the deformed element
            self.canvas.create_line(node_i_deformed[0], node_i_deformed[1], node_j_deformed[0], node_j_deformed[1],
                                    fill="red", width=2.5)  # Use a different color to distinguish
            # Draw hinge at node_i
            self.canvas.create_oval(node_i_deformed[0] - hinge_radius, node_i_deformed[1] - hinge_radius,
                                    node_i_deformed[0] + hinge_radius, node_i_deformed[1] + hinge_radius, outline="red",
                                    fill="white", width=2.5)

            # Draw hinge at node_j
            self.canvas.create_oval(node_j_deformed[0] - hinge_radius, node_j_deformed[1] - hinge_radius,
                                    node_j_deformed[0] + hinge_radius, node_j_deformed[1] + hinge_radius, outline="red",
                                    fill="white", width=2.5)
            # Draw supports
            self.draw_support('red', displacement)

    def plot_axial_forces(self, calculation_type):
        # Clear existing canvas
        self.canvas.delete("all")
        # Create grid, if selected
        self.toggle_grid()

        # Choose the correct set of axial forces based on calculation type
        axial_forces = self.solution.get(
            'axial_forces_linear' if calculation_type == 'linear' else 'axial_forces_nonlinear', [])

        # Check if solution is available
        if axial_forces is None or all(x == 0 for x in axial_forces):
            messagebox.showwarning("Warning", "No axial forces data available.")
            return

        # Displaying the text on the canvas
        max_force = max(np.array(axial_forces))
        min_force = min(np.array(axial_forces))
        if calculation_type == 'linear':
            self.header_text = (f"Axial forces N_i [kN], Linear calculation\n"
                                f"N_max = {max_force:.2f} kN, N_min = {min_force:.2f} kN")
            reactions = self.solution['node_equilibrium_linear']
        else:
            self.header_text = (f"Axial forces N_i [kN], Nonlinear calculation\n"
                                f"N_max = {max_force:.2f} kN, N_min = {min_force:.2f} kN")
            reactions = self.solution['node_equilibrium_nonlinear']
        self.toggle_header()

        # Scaling and normalization
        max_abs_force = max(abs(np.array(axial_forces)))
        scale, translate_x, translate_y, max_dimension = self.calculate_bounds_and_scale()
        # force_scale = max_dimension * 0.14
        force_scale = 0.6
        axial_forces_norm = axial_forces / max_abs_force

        # Iterate over each element and its corresponding axial force
        for element_id, force in enumerate(axial_forces):
            if force == 0:
                continue  # Skip zero forces
            # Get element coordinates and initialize plot coordinates
            element = self.input_elements[str(element_id)]
            node_i = self.scale_and_translate(*element['ele_node_i'])
            node_j = self.scale_and_translate(*element['ele_node_j'])
            force_plot_coordinates = np.zeros((4, 2), np.float64)
            force_plot_coordinates[0][:] = node_i
            force_plot_coordinates[3][:] = node_j
            axial_forces_norm_i = axial_forces_norm[element_id]
            # Differentiate between positive and negative axial forces
            if axial_forces_norm_i >= 0:
                color = 'blue'
            else:
                color = 'red'
            # Angle and offset calculation
            dx, dy = node_j[0] - node_i[0], node_j[1] - node_i[1]
            alpha = np.arctan2(dy, dx)
            beta = np.pi / 2 - alpha
            delta_x = float(force_scale * axial_forces_norm_i * np.cos(beta))
            delta_y = float(-force_scale * axial_forces_norm_i * np.sin(beta))
            force_plot_coordinates[1][:] = force_plot_coordinates[0][:] - scale * np.array([delta_x, delta_y])
            force_plot_coordinates[2][:] = force_plot_coordinates[3][:] - scale * np.array([delta_x, delta_y])

            # Calculate coordinates for placing the axial force label
            label_x = (force_plot_coordinates[1][0] + force_plot_coordinates[2][0]) / 2
            label_y = (force_plot_coordinates[1][1] + force_plot_coordinates[2][1]) / 2
            if force_plot_coordinates[1][0] > force_plot_coordinates[0][0]:
                label_x = label_x + 50
            elif force_plot_coordinates[1][0] < force_plot_coordinates[0][0]:
                label_x = label_x - 50
            if force_plot_coordinates[1][1] > force_plot_coordinates[0][1]:
                label_y = label_y + 12
            elif force_plot_coordinates[1][1] < force_plot_coordinates[0][1]:
                label_y = label_y - 20

            # Draw the axial forces for each element
            self.canvas.create_line(float(force_plot_coordinates[0][0]), float(force_plot_coordinates[0][1]),
                                    float(force_plot_coordinates[1][0]), float(force_plot_coordinates[1][1]),
                                    fill=color, width=2.5)
            self.canvas.create_line(float(force_plot_coordinates[1][0]), float(force_plot_coordinates[1][1]),
                                    float(force_plot_coordinates[2][0]), float(force_plot_coordinates[2][1]),
                                    fill=color, width=2.5)
            self.canvas.create_line(float(force_plot_coordinates[2][0]), float(force_plot_coordinates[2][1]),
                                    float(force_plot_coordinates[3][0]), float(force_plot_coordinates[3][1]),
                                    fill=color, width=2.5)
            # Add a label showing the magnitude of the force
            self.canvas.create_text(float(label_x), float(label_y), text=f"{force:.2f} kN", fill=color,
                                    font=GUI_Settings.RESULTS_FONT_1)

        # Draw undeformed elements, supports, and loads
        self.draw_element()
        self.draw_support('black', None)
        # Draw coordinate system
        self.draw_coordinate_system()
        self.toggle_loads()
        self.draw_reaction_forces(reactions)
        self.toggle_node_labels()

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
        self.node_i_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=1)

        ttk.Label(frame, text="Node j (x, y) [m]:").grid(row=1, column=0, sticky='w')
        self.node_j_entry = ttk.Entry(frame)
        self.node_j_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=0)

        ttk.Label(frame, text="Cross-section area A [cm²]:").grid(row=2, column=0, sticky='w')
        self.area_entry = ttk.Entry(frame)
        self.area_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=1)

        ttk.Label(frame, text="Young's modulus E [MPa]:").grid(row=3, column=0, sticky='w')
        self.emod_entry = ttk.Entry(frame)
        self.emod_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=0)

        ttk.Label(frame, text="Linear coefficient α [-]:").grid(row=4, column=0, sticky='w')
        self.lin_coeff_entry = ttk.Entry(frame)
        self.lin_coeff_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=1)

        ttk.Label(frame, text="Quadratic coefficient β [-]:").grid(row=5, column=0, sticky='w')
        self.quad_coeff_entry = ttk.Entry(frame)
        self.quad_coeff_entry.grid(row=5, column=1, sticky='ew', padx=5, pady=0)

        ttk.Label(frame, text="Limit strain ε [-]:").grid(row=6, column=0, sticky='w')
        self.strain_entry = ttk.Entry(frame)
        self.strain_entry.grid(row=6, column=1, sticky='ew', padx=5, pady=1)

        # Create Button to edit an element
        ttk.Button(frame, text="Edit/Delete Element", command=self.edit_element).grid(row=7, column=0, pady=7, padx=17,
                                                                                      sticky='ew')
        # Create Button to add the element
        ttk.Button(frame, text="Add Element", command=self.add_element).grid(row=7, column=1, pady=7, padx=10,
                                                                             sticky='ew')

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
        self.support_node_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=1)

        ttk.Label(frame, text="Rigid in x-direction:").grid(row=1, column=0, sticky='w')
        self.support_rigid_cx_state = tk.BooleanVar(value=True)
        self.support_rigid_cx = ttk.Checkbutton(frame, variable=self.support_rigid_cx_state,
                                                command=self.toggle_stiffness_cx)
        self.support_rigid_cx.grid(row=1, column=1, sticky='w', padx=5)

        ttk.Label(frame, text="Rigid in y-direction:").grid(row=2, column=0, sticky='w')
        self.support_rigid_cy_state = tk.BooleanVar(value=True)
        self.support_rigid_cy = ttk.Checkbutton(frame, variable=self.support_rigid_cy_state,
                                                command=self.toggle_stiffness_cy)
        self.support_rigid_cy.grid(row=2, column=1, sticky='w', padx=5)

        ttk.Label(frame, text="Stiffness c_x [kN/m]:").grid(row=3, column=0, sticky='w')
        self.stiffness_cx_entry = ttk.Entry(frame)
        self.stiffness_cx_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=0)
        self.toggle_stiffness_cx()

        ttk.Label(frame, text="Stiffness c_y [kN/m]:").grid(row=4, column=0, sticky='w')
        self.stiffness_cy_entry = ttk.Entry(frame)
        self.stiffness_cy_entry.grid(row=4, column=1, sticky='ew', padx=5, pady=1)
        self.toggle_stiffness_cy()

        # Create Button to edit a support
        ttk.Button(frame, text="Edit/Delete Support", command=self.edit_support).grid(row=5, column=0, pady=7, padx=17,
                                                                                      sticky='ew')
        # Create Button to add the support
        ttk.Button(frame, text="Add Support", command=self.add_support).grid(row=5, column=1, pady=7, padx=10,
                                                                             sticky='ew')

    def toggle_stiffness_cx(self):
        if self.support_rigid_cx_state.get():
            self.stiffness_cx_entry.delete(0, tk.END)
            self.stiffness_cx_entry.insert(0, '∞')
            self.stiffness_cx_entry.configure(state='readonly')
        else:
            self.stiffness_cx_entry.configure(state='normal')
            self.stiffness_cx_entry.delete(0, tk.END)
            self.stiffness_cx_entry.insert(0, '0')

    def toggle_stiffness_cy(self):
        if self.support_rigid_cy_state.get():
            self.stiffness_cy_entry.delete(0, tk.END)
            self.stiffness_cy_entry.insert(0, '∞')
            self.stiffness_cy_entry.configure(state='readonly')
        else:
            self.stiffness_cy_entry.configure(state='normal')
            self.stiffness_cy_entry.delete(0, tk.END)
            self.stiffness_cy_entry.insert(0, '0')

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
        self.force_node_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=1)

        ttk.Label(frame, text="Force F_x [kN]:").grid(row=1, column=0, sticky='w')
        self.force_x_entry = ttk.Entry(frame)
        self.force_x_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=0)
        # self.force_x_entry.place(relx=0.9, rely=0.5)

        ttk.Label(frame, text="Force F_y [kN]:").grid(row=2, column=0, sticky='w')
        self.force_y_entry = ttk.Entry(frame)
        self.force_y_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=1)

        # Create Button to edit a load
        ttk.Button(frame, text="Edit/Delete Load", command=self.edit_load).grid(row=3, column=0, pady=7, padx=17,
                                                                                sticky='ew')
        # Create Button to add the load
        ttk.Button(frame, text="Add Load", command=self.add_load).grid(row=3, column=1, pady=7, padx=10,
                                                                       sticky='ew')

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
        self.method_combobox.grid(row=0, column=1, sticky='ew', padx=5, pady=1)
        self.method_combobox.current(0)  # Set default selection

        # Create Entry boxes and labels for element calculation parameters
        ttk.Label(frame, text="Max. number of iterations [-]:").grid(row=1, column=0, sticky='w')
        self.num_iterations_entry = ttk.Entry(frame)
        self.num_iterations_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=0)

        ttk.Label(frame, text="Max. deviation ΔF_max [kN]:").grid(row=2, column=0, sticky='w')
        self.delta_f_entry = ttk.Entry(frame)
        self.delta_f_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=1)

        ttk.Button(frame, text="Save Settings", command=self.calc_settings).grid(row=3, columnspan=2, pady=7)

    def add_element(self):
        try:
            # Parse the coordinates from the entry fields
            node_i = self.parse_coordinates(self.node_i_entry.get())
            node_j = self.parse_coordinates(self.node_j_entry.get())

            # Do not proceed further if the coordinates are invalid
            if node_i is None or node_j is None:
                return

            # Parse other fields like area, Young's modulus, coefficients, etc.
            if self.area_entry.get():
                if float(self.area_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the cross-section area A is negative! "
                                                      f"The value of A is automatically set to positive.")
                area = np.abs(float(self.area_entry.get()))
            else:
                messagebox.showwarning("Warning", f"Value of the cross-section area A is empty! "
                                                  f"Please insert a value A > 0!")
                return
            if self.emod_entry.get():
                if float(self.emod_entry.get()) < 0:
                    messagebox.showwarning("Error", f"Value of the Young's modulus E is negative! "
                                                    f"The value of E is automatically set to positive.")
                emod = np.abs(float(self.emod_entry.get()))
            else:
                messagebox.showwarning("Error", f"Value of the Young's modulus E is empty! "
                                                f"Please insert a value E > 0!")
                return
            if self.lin_coeff_entry.get():
                if float(self.lin_coeff_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the linear coefficient α is negative! "
                                                      f"The value of α is automatically set to positive.")
                lin_coeff = np.abs(float(self.lin_coeff_entry.get()))
            else:
                lin_coeff = 1
                messagebox.showwarning("Error", f"Value of the linear coefficient α is empty! "
                                                f"The coefficient is set to the default value α = 1. ")
            if self.quad_coeff_entry.get():
                if float(self.quad_coeff_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the quadratic coefficient β is negative! "
                                                      f"The value of β is automatically set to positive. The sign will "
                                                      f"automatically change in the calculation depending on whether "
                                                      f"the element is subjected to tensile or compressive stress.")
                quad_coeff = np.abs(float(self.quad_coeff_entry.get()))
            else:
                quad_coeff = 0
                messagebox.showwarning("Error", f"Value of the quadratic coefficient β is empty! "
                                                f"The coefficient is set to the default value β = 0 "
                                                f"(linear calculation). ")
            if self.strain_entry.get():
                if float(self.strain_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the limit strain ε is negative! "
                                                      f"The value of ε is automatically set to positive. The sign will "
                                                      f"automatically change in the calculation depending on whether "
                                                      f"the element is subjected to tensile or compressive stress.")
                strain_entry = np.abs(float(self.strain_entry.get()))
            else:
                strain_entry = 0
                messagebox.showwarning("Error", f"Value of the limit strain ε is empty! "
                                                f"The limit strain is set to the default value ε = 0 "
                                                f"(linear calculation). ")

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
            # Draw element on canvas
            self.canvas.delete("all")  # Clear the canvas
            self.plot_button.config(state='normal')
            # Create grid, if selected
            self.toggle_grid()
            self.draw_coordinate_system()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()

        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the element: {e} !")
            print(f"An error occurred while adding the element: {e}")
            return

    def edit_element(self):
        self.edit_window = tk.Toplevel(self)
        set_icon(self.edit_window)
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
        try:
            selected_index = self.element_dropdown.current()
            element_id = list(self.input_elements.keys())[selected_index]
            # Parse values from entry boxes
            node_i = self.parse_coordinates(self.edit_node_i_entry.get())
            node_j = self.parse_coordinates(self.edit_node_j_entry.get())

            # Parse other fields like area, Young's modulus, coefficients, etc.
            if self.edit_area_entry.get():
                if float(self.edit_area_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the cross-section area A is negative! "
                                                      f"The value of A is automatically set to positive.")
                area = np.abs(float(self.edit_area_entry.get()))
            else:
                messagebox.showwarning("Warning", f"Value of the cross-section area A is empty! "
                                                  f"Please insert a value A > 0!")
                return
            if self.edit_emod_entry.get():
                if float(self.edit_emod_entry.get()) < 0:
                    messagebox.showwarning("Error", f"Value of the Young's modulus E is negative! "
                                                    f"The value of E is automatically set to positive.")
                emod = np.abs(float(self.edit_emod_entry.get()))
            else:
                messagebox.showwarning("Error", f"Value of the Young's modulus E is empty! "
                                                f"Please insert a value E > 0!")
                return
            if self.edit_lin_coeff_entry.get():
                if float(self.edit_lin_coeff_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the linear coefficient α is negative! "
                                                      f"The value of α is automatically set to positive.")
                lin_coeff = np.abs(float(self.edit_lin_coeff_entry.get()))
            else:
                lin_coeff = 1
                messagebox.showwarning("Error", f"Value of the linear coefficient α is empty! "
                                                f"The coefficient is set to the default value α = 1. ")
            if self.edit_quad_coeff_entry.get():
                if float(self.edit_quad_coeff_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the quadratic coefficient β is negative! "
                                                      f"The value of β is automatically set to positive. The sign will "
                                                      f"automatically change in the calculation depending on whether "
                                                      f"the element is subjected to tensile or compressive stress.")
                quad_coeff = np.abs(float(self.edit_quad_coeff_entry.get()))
            else:
                quad_coeff = 0
                messagebox.showwarning("Error", f"Value of the quadratic coefficient β is empty! "
                                                f"The coefficient is set to the default value β = 0 "
                                                f"(linear calculation). ")
            if self.edit_strain_entry.get():
                if float(self.edit_strain_entry.get()) < 0:
                    messagebox.showwarning("Warning", f"Value of the limit strain ε is negative! "
                                                      f"The value of ε is automatically set to positive. The sign will "
                                                      f"automatically change in the calculation depending on whether "
                                                      f"the element is subjected to tensile or compressive stress.")
                strain_entry = np.abs(float(self.edit_strain_entry.get()))
            else:
                strain_entry = 0
                messagebox.showwarning("Error", f"Value of the limit strain ε is empty! "
                                                f"The limit strain is set to the default value ε = 0 "
                                                f"(linear calculation). ")

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
            # Draw elements, supports and loads on canvas
            self.canvas.delete("all")  # Clear the canvas
            # Create grid, if selected
            self.toggle_grid()
            self.draw_coordinate_system()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()
            # Close window
            self.edit_window.destroy()
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the element: {e}")
            print(f"An error occurred while adding the element: {e}")
            return

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
            new_input_elements[str(i)]['ele_number'] = i
        self.input_elements = new_input_elements
        # Update information window
        self.update_system_information()
        # Draw elements, supports and loads on canvas
        self.canvas.delete("all")  # Clear the canvas
        # Create grid, if selected
        self.toggle_grid()
        self.draw_coordinate_system()
        self.draw_element()
        self.draw_support('black', None)
        self.toggle_loads()
        self.toggle_node_labels()
        # Update the combobox options and entry fields
        self.update_element_dropdown()

    def add_load(self):
        try:
            # Parse the coordinates from the entry fields
            force_node = self.parse_coordinates(self.force_node_entry.get())

            # Do not proceed further if the coordinates are invalid
            if force_node is None:
                return

            if self.force_x_entry.get():
                force_x = float(self.force_x_entry.get())
            else:
                force_x = 0
            if self.force_y_entry.get():
                force_y = float(self.force_y_entry.get())
            else:
                force_y = 0
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
            # Draw elements, supports and loads on canvas
            self.canvas.delete("all")  # Clear the canvas
            self.toggle_grid()
            self.draw_coordinate_system()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the load: {e}")
            return

    def edit_load(self):
        self.edit_window_load = tk.Toplevel(self)
        set_icon(self.edit_window_load)
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
        try:
            selected_index = self.load_dropdown.current()
            force_id = list(self.input_forces.keys())[selected_index]
            # Parse values from entry boxes
            force_node = self.parse_coordinates(self.edit_force_node_entry.get())
            if self.edit_force_x_entry.get():
                f_x = float(self.edit_force_x_entry.get())
            else:
                f_x = 0
            if self.edit_force_y_entry.get():
                f_y = float(self.edit_force_y_entry.get())
            else:
                f_y = 0

            # Update the load in the input_elements dictionary
            self.input_forces[force_id] = {
                'force_number': int(force_id),
                'force_node': force_node,
                'f_x': f_x,
                'f_y': f_y}
            # Update information window
            self.update_system_information()
            # Draw elements, supports and loads on canvas
            self.canvas.delete("all")  # Clear the canvas
            self.toggle_grid()
            self.draw_coordinate_system()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()
            # Close window
            self.edit_window_load.destroy()
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the load: {e}")
            return

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
            new_input_loads[str(i)]['force_number'] = i

        self.input_forces = new_input_loads
        # Update information window
        self.update_system_information()
        # Draw elements, supports and loads on canvas
        self.canvas.delete("all")  # Clear the canvas
        self.toggle_grid()
        self.draw_coordinate_system()
        self.draw_element()
        self.draw_support('black', None)
        self.toggle_loads()
        self.toggle_node_labels()
        # Update the combobox options and entry fields
        self.update_load_dropdown()

    def add_support(self):
        try:
            # Parse the coordinates from the entry fields
            support_node = self.parse_coordinates(self.support_node_entry.get())
            # Do not proceed further if the coordinates are invalid
            if support_node is None:
                return
            # Parse stiffness
            if self.stiffness_cx_entry.get():
                if self.stiffness_cx_entry.get() != '∞':
                    if float(self.stiffness_cx_entry.get()) < 0:
                        messagebox.showwarning("Warning", f"Value of the spring stiffness c_x is negative! "
                                                          f"The value of c_x is automatically set to positive.")
                    c_x = abs(float(self.stiffness_cx_entry.get()))
                else:
                    c_x = self.stiffness_cx_entry.get()
            else:
                messagebox.showwarning("Warning", f"Value of the spring stiffness c_x is empty! "
                                                  f"The value of the spring stiffness is set to c_x = 0!")
                c_x = 0
            if self.stiffness_cy_entry.get():
                if self.stiffness_cy_entry.get() != '∞':
                    if float(self.stiffness_cy_entry.get()) < 0:
                        messagebox.showwarning("Warning", f"Value of the spring stiffness c_y is negative! "
                                                          f"The value of c_y is automatically set to positive.")
                    c_y = abs(float(self.stiffness_cy_entry.get()))
                else:
                    c_y = self.stiffness_cy_entry.get()
            else:
                messagebox.showwarning("Warning", f"Value of the spring stiffness c_y is empty! "
                                                  f"The value of the spring stiffness is set to c_y = 0!")
                c_y = 0

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
            # Draw elements, supports and loads on canvas
            self.canvas.delete("all")  # Clear the canvas
            self.toggle_grid()
            self.draw_coordinate_system()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()

        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the support: {e}")
            return

    def edit_support(self):
        self.edit_window_support = tk.Toplevel(self)
        set_icon(self.edit_window_support)
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

        ttk.Label(edit_frame, text="Rigid in x-direction:").grid(row=2, column=0, sticky='w')
        self.edit_support_rigid_cx_state = tk.BooleanVar(value=True)
        self.edit_support_rigid_cx = ttk.Checkbutton(edit_frame, variable=self.edit_support_rigid_cx_state,
                                                     command=self.toggle_edit_stiffness_cx)
        self.edit_support_rigid_cx.grid(row=2, column=1, sticky='w', padx=5)

        ttk.Label(edit_frame, text="Rigid in y-direction:").grid(row=3, column=0, sticky='w')
        self.edit_support_rigid_cy_state = tk.BooleanVar(value=True)
        self.edit_support_rigid_cy = ttk.Checkbutton(edit_frame, variable=self.edit_support_rigid_cy_state,
                                                     command=self.toggle_edit_stiffness_cy)
        self.edit_support_rigid_cy.grid(row=3, column=1, sticky='w', padx=5)

        ttk.Label(edit_frame, text="Stiffness c_x [kN/m]:").grid(row=4, column=0, sticky='w')
        self.edit_stiffness_cx_entry = ttk.Entry(edit_frame)
        self.edit_stiffness_cx_entry.grid(row=4, column=1, sticky='ew', padx=5)

        ttk.Label(edit_frame, text="Stiffness c_y [kN/m]:").grid(row=5, column=0, sticky='w')
        self.edit_stiffness_cy_entry = ttk.Entry(edit_frame)
        self.edit_stiffness_cy_entry.grid(row=5, column=1, sticky='ew', padx=5, pady=1)

        # Button for saving changes
        ttk.Button(edit_frame, text="Save Changes", command=self.save_support_changes).grid(row=6, column=1, padx=5,
                                                                                            pady=10)
        # Button for deleting the selected support
        ttk.Button(edit_frame, text="Delete Support", command=self.delete_support).grid(row=6, column=0, padx=5)

        # Initially populate the entry boxes with the current values of the first support
        self.populate_support_fields()

        # Call update_support_dropdown to initialize the combobox values
        self.update_support_dropdown()

    def toggle_edit_stiffness_cx(self):
        if self.edit_support_rigid_cx_state.get():
            self.edit_stiffness_cx_entry.delete(0, tk.END)
            self.edit_stiffness_cx_entry.insert(0, '∞')
            self.edit_stiffness_cx_entry.configure(state='readonly')
        else:
            self.edit_stiffness_cx_entry.configure(state='normal')
            self.edit_stiffness_cx_entry.delete(0, tk.END)
            self.edit_stiffness_cx_entry.insert(0, str(self.edit_cx))

    def toggle_edit_stiffness_cy(self):
        if self.edit_support_rigid_cy_state.get():
            self.edit_stiffness_cy_entry.delete(0, tk.END)
            self.edit_stiffness_cy_entry.insert(0, '∞')
            self.edit_stiffness_cy_entry.configure(state='readonly')
        else:
            self.edit_stiffness_cy_entry.configure(state='normal')
            self.edit_stiffness_cy_entry.delete(0, tk.END)
            self.edit_stiffness_cy_entry.insert(0, str(self.edit_cy))

    def populate_support_fields(self, event=None):
        selected_index = self.support_dropdown.current()
        support_id = list(self.input_supports.keys())[selected_index]
        support = self.input_supports[support_id]
        self.edit_support_node_entry.delete(0, tk.END)
        self.edit_support_node_entry.insert(0, f"{support['sup_node'][0]}, {support['sup_node'][1]}")

        self.edit_stiffness_cx_entry.delete(0, tk.END)
        self.edit_stiffness_cx_entry.insert(0, f"{support['c_x']}")
        if support['c_x'] == '∞':
            self.edit_stiffness_cx_entry.configure(state='readonly')
            self.edit_support_rigid_cx_state.set(True)
        else:
            self.edit_stiffness_cx_entry.configure(state='normal')
            self.edit_support_rigid_cx_state.set(False)
            self.edit_cx = support['c_x']

        self.edit_stiffness_cy_entry.delete(0, tk.END)
        self.edit_stiffness_cy_entry.insert(0, f"{support['c_y']}")
        if support['c_y'] == '∞':
            self.edit_stiffness_cy_entry.configure(state='readonly')
            self.edit_support_rigid_cy_state.set(True)
        else:
            self.edit_stiffness_cy_entry.configure(state='normal')
            self.edit_support_rigid_cy_state.set(False)
            self.edit_cy = support['c_y']

        self.toggle_edit_stiffness_cx()
        self.toggle_edit_stiffness_cy()

    def save_support_changes(self):
        try:
            selected_index = self.support_dropdown.current()
            support_id = list(self.input_supports.keys())[selected_index]
            # Parse values from entry boxes
            support_node = self.parse_coordinates(self.edit_support_node_entry.get())
            if self.edit_stiffness_cx_entry.get():
                if self.edit_stiffness_cx_entry.get() != '∞':
                    if float(self.edit_stiffness_cx_entry.get()) < 0:
                        messagebox.showwarning("Warning", f"Value of the spring stiffness c_x is negative! "
                                                          f"The value of c_x is automatically set to positive.")
                    c_x = abs(float(self.edit_stiffness_cx_entry.get()))
                else:
                    c_x = self.edit_stiffness_cx_entry.get()
            else:
                messagebox.showwarning("Warning", f"Value of the spring stiffness c_x is empty! "
                                                  f"The of the spring stiffness is set to c_x = 0!")
                c_x = 0
            if self.edit_stiffness_cy_entry.get():
                if self.edit_stiffness_cy_entry.get() != '∞':
                    if float(self.edit_stiffness_cy_entry.get()) < 0:
                        messagebox.showwarning("Warning", f"Value of the spring stiffness c_y is negative! "
                                                          f"The value of c_y is automatically set to positive.")
                    c_y = abs(float(self.edit_stiffness_cy_entry.get()))
                else:
                    c_y = self.edit_stiffness_cy_entry.get()
            else:
                messagebox.showwarning("Warning", f"Value of the spring stiffness c_y is empty! "
                                                  f"The of the spring stiffness is set to c_y = 0!")
                c_y = 0

            # Update the load in the input_elements dictionary
            self.input_supports[support_id] = {
                'sup_number': int(support_id),
                'sup_node': support_node,
                'c_x': c_x,
                'c_y': c_y}
            # Update information window
            self.update_system_information()
            # Draw elements, supports and loads on canvas
            self.canvas.delete("all")  # Clear the canvas
            self.toggle_grid()
            self.draw_coordinate_system()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()
            # Close window
            self.edit_window_support.destroy()
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while adding the support: {e}")
            return

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
            new_input_supports[str(i)]['sup_number'] = i

        self.input_supports = new_input_supports
        # Update information window
        self.update_system_information()
        # Draw elements, supports and loads on canvas
        self.canvas.delete("all")  # Clear the canvas
        self.toggle_grid()
        self.draw_coordinate_system()
        self.draw_element()
        self.draw_support('black', None)
        self.toggle_loads()
        self.toggle_node_labels()
        # Update the combobox options and entry fields
        self.update_support_dropdown()

    def calc_settings(self):
        try:
            # Get settings from calc setting form
            method = str(self.method_dict[self.method_combobox.get()])
            if method != 'linear':
                try:
                    number_of_iterations = abs(int(self.num_iterations_entry.get()))
                    delta_f = abs(float(self.delta_f_entry.get()))
                except ValueError as e:
                    # Show a warning message box
                    messagebox.showwarning("Warning", "Number of iterations must be an integer!")
                    return
            else:
                number_of_iterations = 0
                delta_f = 0

            # Add the new load to the input_forces dictionary
            self.input_calc_param = {'calc_method': method,
                                     'number_of_iterations': number_of_iterations,
                                     'delta_f_max': delta_f}
            # Set calculation parameter initializer to 1, required to overwrite initial parameters properly
            self.add_calc_initialise = 1
            # Update information window
            self.update_system_information()
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while saving the calculation settings: {e}")
            return

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
        try:
            # Check Input parameters for errors:
            ele_quad_coeff = []
            for ele_id, ele_values in self.input_elements.items():
                ele_quad_coeff.append(abs(ele_values['ele_quad_coeff']))
            if (self.input_calc_param['calc_method'] in 'NR' or self.input_calc_param[
                'calc_method'] in 'modNR') and sum(
                ele_quad_coeff) == 0:
                messagebox.showwarning("Warning", f"You selected a nonlinear Newton-Raphson calculation, "
                                                  f"but you set the nonlinear parameter β of all elements to 0! "
                                                  f"Calculating linear...")
                self.input_calc_param['calc_method'] = 'linear'
                self.method_combobox.current(0)
            # Run Calculation
            calculation = Calculation(self.input_elements, self.input_supports, self.input_forces,
                                      self.input_calc_param)
            self.solution = calculation.return_solution()
            if self.solution is not None and self.solution['error_linalg'] is None:
                # Check if the linear calculation results are available
                if 'node_displacements_linear' in self.solution and self.solution[
                    'node_displacements_linear'] is not None:
                    # Enable the plot_linear_deformation button
                    self.plot_linear_deformation.config(state='normal')
                    self.plot_linear_forces.config(state='normal')
                    self.export_plot.config(state='normal')
                    # Create a mapping from node tuples to their index in the global_nodes_list
                    self.node_to_index = {node: index for index, node in enumerate(self.solution['nodes'])}
                    # Copy linear displacements for plotting
                    self.linear_displacement = self.solution['node_displacements_linear']
                    print('The axial forces of the linear elastic calculation are:')
                    print(self.solution['axial_forces_linear'])
                    print('The global forces equilibrium (linear support reaction forces) are:')
                    print(self.solution['node_equilibrium_linear'])
                else:
                    # Disable the button if linear results are not available
                    self.plot_linear_deformation.config(state='disabled')
                if 'NR' in self.input_calc_param['calc_method'] or 'modNR' in self.input_calc_param['calc_method']:
                    self.plot_nonlinear_deformation.config(state='normal')
                    self.plot_nonlinear_forces.config(state='normal')
                    # Copy linear displacements for plotting
                    self.nonlinear_displacement = self.solution['node_displacements_nonlinear']
                    print('The axial forces of the nonlinear elastic / ideal plastic calculation are:')
                    print(self.solution['axial_forces_nonlinear'])
                    print('The global forces equilibrium (nonlinear support reaction forces) are:')
                    print(self.solution['node_equilibrium_nonlinear'])

                self.update_calculation_information()

            elif self.solution is not None and self.solution['error_linalg'] is not None:
                # Handle error in calculation
                messagebox.showerror("Error", f"An error occurred while solving the system of equations: "
                                              f"{self.solution['error_linalg']}. Please check if your system is statically "
                                              f"determined and that all truss elements are connected.")
                # Ensure the button remains disabled if the calculation failed
                self.plot_linear_deformation.config(state='disabled')
        except Exception as e:
            # Show a warning message box
            messagebox.showerror("Error", f"An error occurred while running the calculation: {e}")
            return

    def clear_all(self):
        self.canvas.delete("all")  # Clear the canvas
        self.draw_coordinate_system()
        self.input_elements = copy.deepcopy(self.input_elements_init)
        self.input_supports = copy.deepcopy(self.input_supports_init)
        self.input_forces = copy.deepcopy(self.input_forces_init)
        self.input_calc_param = copy.deepcopy(self.input_calc_param_init)
        self.add_element_initialise = 0
        self.add_support_initialise = 0
        self.add_load_initialise = 0
        self.add_calc_initialise = 0
        self.ele_number = 0
        self.force_number = 0
        self.support_number = 0
        self.edit_cx = 0
        self.edit_cy = 0
        self.max_force = 1
        self.nodes = []
        self.solution = None
        self.plot_linear_deformation.config(state='disabled')
        self.plot_linear_forces.config(state='disabled')
        self.export_plot.config(state='disabled')
        self.plot_nonlinear_deformation.config(state='disabled')
        self.plot_nonlinear_forces.config(state='disabled')
        self.num_iterations_entry.delete(0, tk.END)
        self.delta_f_entry.delete(0, tk.END)
        self.method_combobox.current(0)
        self.show_grid_state.set(True)
        self.show_loads_state.set(True)
        self.show_header_state.set(False)
        self.show_node_labels_state.set(False)
        self.show_element_labels_state.set(False)
        # Update information window
        self.update_system_information()
        # Update information window
        self.update_calculation_information()
        self.toggle_grid()

    def save_to_file(self):
        data = {
            'input_elements': self.input_elements,
            'input_supports': self.input_supports,
            'input_forces': self.input_forces,
            'input_calc_param': self.input_calc_param
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            messagebox.showinfo("Save File", "Input parameters successfully saved to file.")

    def load_from_file(self):
        self.clear_all()
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                data = json.load(file)
            # Convert lists back to tuples for nodes
            if 'input_elements' in data:
                self.add_element_initialise = 1
                self.ele_number = 0
                for key, element in data['input_elements'].items():
                    self.ele_number += 1
                    if 'ele_node_i' in element:
                        element['ele_node_i'] = tuple(element['ele_node_i'])
                    if 'ele_node_j' in element:
                        element['ele_node_j'] = tuple(element['ele_node_j'])

            if 'input_supports' in data:
                self.add_support_initialise = 1
                self.support_number = 0
                for key, support in data['input_supports'].items():
                    self.support_number += 1
                    if 'sup_node' in support:
                        support['sup_node'] = tuple(support['sup_node'])

            if 'input_forces' in data:
                self.add_load_initialise = 1
                self.force_number = 0
                for key, force in data['input_forces'].items():
                    self.force_number += 1
                    if 'force_node' in force:
                        force['force_node'] = tuple(force['force_node'])
            if 'input_calc_param' in data:
                self.add_calc_initialise = 1
                self.num_iterations_entry.delete(0, tk.END)
                self.num_iterations_entry.insert(0, f"{data['input_calc_param']['number_of_iterations']}")
                self.delta_f_entry.delete(0, tk.END)
                self.delta_f_entry.insert(0, f"{data['input_calc_param']['delta_f_max']}")
                loaded_method = data['input_calc_param']['calc_method']
                method_index = self.methods.index(loaded_method) if loaded_method in self.methods else 0
                self.method_combobox.current(method_index)
            self.input_elements = data.get('input_elements', {})
            self.input_supports = data.get('input_supports', {})
            self.input_forces = data.get('input_forces', {})
            self.input_calc_param = data.get('input_calc_param', {})
            # Update the UI with loaded data
            self.update_system_information()
            messagebox.showinfo("Load File", "Input parameters successfully loaded from file.")
            # Draw elements, supports and loads on canvas
            self.canvas.delete("all")  # Clear the canvas
            self.plot_button.config(state='normal')
            self.draw_coordinate_system()
            self.toggle_grid()
            self.draw_element()
            self.draw_support('black', None)
            self.toggle_loads()
            self.toggle_node_labels()

    def plot_system(self):
        # Clear existing canvas
        self.canvas.delete("all")
        # Draw coordinate system
        self.draw_coordinate_system()
        # Draw elements, supports, and loads
        self.toggle_grid()
        self.draw_element()
        self.draw_support('black', None)
        self.toggle_loads()
        self.toggle_node_labels()


# Run the application
if __name__ == "__main__":
    app = TrussAnalysisApp()
    app.mainloop()
