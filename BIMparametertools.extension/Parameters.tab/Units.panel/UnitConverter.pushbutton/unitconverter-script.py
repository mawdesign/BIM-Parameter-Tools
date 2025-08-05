# -*- coding: utf-8 -*-
"""
BIM Parameter Tools - Unit Converter
"""
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# Imprt required namespaces
import clr
clr.AddReference('WindowsBase')
clr.AddReference('System.Windows')
clr.AddReference('PresentationFramework')

# Import necessary components from pyRevit and standard libraries
from pyrevit import forms
# from pyrevit.forms import WPFWindow, alert
from pyrevit import revit, script

# Import WPF libraries for UI controls
from System.Windows import Controls
from System.Windows.Controls import TreeViewItem

# Import Revit API components for unit conversion
from Autodesk.Revit.DB import UnitUtils, ForgeTypeId, UnitFormatUtils


import os
import re
from decimal import Decimal

# Import our custom library functions to get live data from Revit
import revit_unit_lib as unit_lib

# WPF_HIDDEN = framework.Windows.Visibility.Hidden
# WPF_COLLAPSED = framework.Windows.Visibility.Collapsed
# WPF_VISIBLE = framework.Windows.Visibility.Visible

# ------------------------------------------------------------------------------
# Helper Class for UI Data
# ------------------------------------------------------------------------------
class UnitItem(object):
    """A simple class to hold unit data for display in the UI.
    This allows us to attach the underlying ForgeTypeId data to each UI item.
    """

    def __init__(self, display_name, spec_id, unit_id):
        self.display_name = display_name
        self.spec_id = spec_id
        self.unit_id = unit_id

    def __str__(self):
        # This controls what text is shown in the ComboBox
        return self.display_name


# ------------------------------------------------------------------------------
# The Main Window Class
# ------------------------------------------------------------------------------
class UnitConverterWindow(forms.WPFWindow):
    """
    This class represents the main window for the Unit Converter tool.
    It loads the XAML file and handles the UI logic and events.
    """

    def __init__(self, xaml_file_path):
        """
        Initializes a new instance of the UnitConverterWindow.

        Args:
            xaml_file_path (str): The full path to the .xaml file defining the UI.
        """
        # --- Load the XAML file from the specified path ---
        # This function parses the XAML and creates the UI elements as objects.
        forms.WPFWindow.__init__(self, xaml_file_path)
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "icon.png"
        )
        if os.path.exists(icon_path):
            self.set_icon(icon_path)

        # --- Data Loading and Initialization ---
        # Get live data directly from the Revit API via our library functions.
        # This ensures the data is always accurate for the current Revit version.
        try:
            self.specs_data = unit_lib.get_revit_specs()
            self.units_map = unit_lib.get_revit_units()
            self.symbols_map = unit_lib.create_reverse_unit_lookup(self.specs_data, self.units_map)
        except Exception as e:
            forms.alert(
                "Failed to enumerate units and specs from the Revit API.\n\n"
                "Error: {}".format(e),
                title="API Error",
            )
            self.Close()
            return
        self.grouped_specs = self._group_specs_by_discipline(self.specs_data)

        # --- State Management Variables ---
        self.from_unit_id = None
        self.to_unit_id = None
        self.history_tag = None
        self.current_history_tag = None

        # --- State for remembering the user's last manual filter ---
        self.last_manual_filter_text = ""
        self.is_auto_filtered = False

        self._populate_all_controls()
        self._wire_up_events()

        # --- Display the window ---
        # We use 'Show()' to make the window NON-MODAL. This allows the user
        # to continue to work in Revit
        self.Show()
        self.InputValueTextBox.Focus()

    def _apply_filter_to_input_view(self, filter_text, unit_id = None):
        """
        Filters the TreeView by toggling item visibility.
        """
        filter_text_lower = filter_text.lower()

        # First, check if the filter is an exact discipline name
        if filter_text in self.grouped_specs:
            # print("Selected Discipline: {}".format(filter_text))
            for discipline_node in self.InputTreeView.Items:
                discipline_visible = discipline_node.Header == filter_text
                for spec_node in discipline_node.Items:
                    for unit_node in spec_node.Items:
                        (
                            self.show_element(unit_node)
                            if discipline_visible
                            else self.hide_element(unit_node)
                        )
                    (
                        self.show_element(spec_node)
                        if discipline_visible
                        else self.hide_element(spec_node)
                    )
                if discipline_visible:
                    discipline_node.IsExpanded = True
                    self.show_element(discipline_node)
                else:
                    self.hide_element(discipline_node)

        else:
            # Iterate through all existing items and toggle their visibility
            discipline_count = 0
            only_discipline = None
            has_first_unit = False
            first_unit = None
            first_spec = None
            first_discipline = None
            for discipline_node in self.InputTreeView.Items:
                discipline_visible = False
                spec_count = 0
                only_spec = None
                for spec_node in discipline_node.Items:
                    spec_visible = False
                    unit_count = 0
                    only_unit = None
                    for unit_node in spec_node.Items:
                        unit_visible = False
                        if unit_id:
                            if unit_node.Tag.unit_id == unit_id:
                                unit_visible = True
                                if not has_first_unit:
                                    first_unit = unit_node
                                    first_spec = spec_node
                                    first_discipline = discipline_node
                                    has_first_unit = True
                        elif not filter_text:
                            # If no filter, everything is visible
                            unit_visible = True
                        else:
                            # Check against filter text
                            unit_data = unit_node.Tag
                            spec_name = spec_node.Header.lower()
                            unit_name = unit_data.display_name.lower()

                            if (
                                filter_text_lower in spec_name
                                or filter_text_lower in unit_name
                            ):
                                unit_visible = True

                        # Use the safe pyRevit methods to toggle visibility
                        if unit_visible:
                            self.show_element(unit_node)
                            spec_visible = True
                            unit_count += 1
                            if unit_count == 1:
                                only_unit = unit_node
                        else:
                            self.hide_element(unit_node)
                    if unit_count == 1 and only_unit:
                        only_unit.IsExpanded = True

                    if spec_visible:
                        self.show_element(spec_node)
                        discipline_visible = True
                        spec_count += 1
                        if spec_count == 1:
                            only_spec = spec_node
                    else:
                        self.hide_element(spec_node)
                if spec_count == 1 and only_spec:
                    only_spec.IsExpanded = True

                if discipline_visible:
                    self.show_element(discipline_node)
                    discipline_count += 1
                    if discipline_count == 1:
                        only_discipline = discipline_node
                else:
                    self.hide_element(discipline_node)
            if discipline_count == 1 and only_discipline:
                only_discipline.IsExpanded = True
            
            if has_first_unit:
                first_unit.IsExpanded = True
                first_unit.IsSelected = True
                first_spec.IsExpanded = True
                first_discipline.IsExpanded = True

    def _apply_filter_to_output_view(self, spec_id, unit_id):
        """
        Filters the TreeView by toggling item visibility.
        """
        units_list = []
        unit_count = 0
        only_unit = None
        # print("Spec '{}'".format(spec_id))
        for spec in self.specs_data:
            this_spec_id = spec.get("ForgeTypeId", None)
            if this_spec_id == spec_id:
                units_list.extend(spec.get("ValidUnits", []))
                # print("Units '{}'".format(spec.get("ValidUnits", [])))
            if unit_id in spec.get("ValidUnits", []):
                units_list.extend(spec.get("ValidUnits", []))

        if unit_id in units_list:
            units_list.remove(unit_id)

        for unit_node in self.OutputTreeView.Items:
            unit_visible = False
            if not spec_id and not unit_id:
                # print("No spec")
                # If no filter, everything is visible
                unit_visible = True
                unit_count += 1
            else:
                # Check against filter text
                unit_data = unit_node.Tag
                unit_id = unit_data.unit_id

                if unit_id in units_list:
                    unit_visible = True 
                    unit_count += 1
                    if unit_count == 1:
                        only_unit = unit_node

            # Use the safe pyRevit methods to toggle visibility
            (
                self.show_element(unit_node)
                if unit_visible
                else self.hide_element(unit_node)
            )
        if unit_count == 1 and only_unit:
            only_unit.IsSelected = True

    def _group_specs_by_discipline(self, specs_list):
        """Groups a list of specs into a dictionary keyed by discipline."""
        grouped = {}
        for spec in specs_list:
            discipline = spec.get("Discipline", "Other")
            if discipline not in grouped:
                grouped[discipline] = []
            grouped[discipline].append(spec)
        return grouped

    def _get_input_value_unit_tag(self):
        """ Spec
        Get the content from the InputValueTextBox and extract the value and, if
        available, any entered unit and/or tag.
        """
        # Global import gave name error, so trying local import for now
        import re
        from pyrevit import revit
        from Autodesk.Revit.DB import Units, UnitSystem, ForgeTypeId, UnitFormatUtils
        from decimal import Decimal

        return_data = {"spec_id":None, "unit_id":None, "tag":None, "value":None, "value_with_unit":None,}
        input_text = self.InputValueTextBox.Text
        if not input_text:
            return None

        # Pattern 1: Handle complex imperial feet-and-inches like "25' - 12 3/4""
        imperial_pattern = r"((?P<feet>\d+(\.\d+)?)')?(\s?-?\s?(?P<inches>\d+(\s\d+(\/\d+)|\.\d+)?)\s*\")?"
        match = re.search(imperial_pattern, input_text)
        if match and (match.group('feet') or match.group('inches')):
            feet = match.group('feet') if match.group('feet') else ""
            inch = match.group('inches') if match.group('inches') else ""
            # print("It's Imperial {} feet {} inches".format(feet, inch))
            imperial_string = match.group(0)
            # Use Revit's parser for imperial strings
            units = Units(UnitSystem.Imperial)
            input_unit = self.symbols_map["'"][0][1]
            input_spec = self.symbols_map["'"][0][0]
            success, value_in_feet = UnitFormatUtils.TryParse(units, ForgeTypeId(input_spec), imperial_string)
            if success:
                return_data["spec_id"] = input_spec
                return_data["unit_id"] = input_unit
                return_data["tag"] = input_text.replace(imperial_string, "").strip()
                return_data["value"] = value_in_feet
                return_data["value_with_unit"] = imperial_string
                return return_data

        # Pattern 2: Handle general numbers and unit symbols (prefix or suffix)
        # Find the first valid number in the string
        value_match = re.search(r'-?\d+(\.\d+)?', input_text)
        if not value_match:
            return None

        return_data["value"] = float(Decimal(value_match.group(0)))
        remaining_text = input_text.replace(value_match.group(0), "", 1).strip()

        found_symbol = None
        # Sort symbols by length to find "mm" before "m"
        sorted_symbols = sorted(self.symbols_map.keys(), key=len, reverse=True)
        for symbol in sorted_symbols:
            # Escape special regex characters in the symbol
            escaped_symbol = re.escape(symbol)
            if re.search(r'(^|\s)' + escaped_symbol + r'(\s|$)', remaining_text):
                found_symbol = symbol
                remaining_text = remaining_text.replace(symbol, "").strip()
                break

        return_data["spec_id"] = self.symbols_map[found_symbol][0][0] if found_symbol and len(self.symbols_map[found_symbol]) else None
        return_data["unit_id"] = self.symbols_map[found_symbol][0][1] if found_symbol and len(self.symbols_map[found_symbol]) else None
        return_data["tag"] = remaining_text
        return_data["value_with_unit"] = input_text.replace(remaining_text, "", 1).strip()
        return return_data

    def _handle_convert_click(self, sender, args):
        """Event handler for clicking the convert button"""
        silent = False
        self._perform_unit_conversion(silent)

    def _handle_input_changed(self, sender, args):
        """Dynamically filters the 'FROM' treeview based on detected units in input."""
        from System.Windows.Input import Key

        try:
            if args.Key == Key.Enter:
                self._perform_unit_conversion(silent = True)
        except Exception as e:
            pass # fail quietly
        input_data = self._get_input_value_unit_tag()
        unit_id = input_data["unit_id"] if input_data else None
        if unit_id:
            # A unit was detected, so we are now in an auto-filtered state.
            self.is_auto_filtered = True
            self._apply_filter_to_input_view("", unit_id = unit_id)
            self._apply_filter_to_output_view(None, unit_id)
        elif self.is_auto_filtered:
            # No unit is detected, and we WERE in an auto-filtered state.
            # Revert to the user's last manual filter.
            self.is_auto_filtered = False
            self._apply_filter_to_input_view(self.last_manual_filter_text)
            self._apply_filter_to_output_view(None, unit_id)

    def _handle_filter_change(self, sender, args):
        """Event handler for both ComboBox selection and text entry."""
        filter_text = (
            sender.SelectedItem.ToString() if sender.SelectedItem else sender.Text
        )
        # print("{} filter changed to '{}'".format(sender.Name, filter_text))
        # This is a manual action, so update the last manual filter state.
        self.last_manual_filter_text = filter_text
        self.is_auto_filtered = False
        # if sender.Name == "FromUnitComboBox":
            # self._apply_filter_to_input_view(filter_text)
        self._apply_filter_to_input_view(filter_text)

    def _handle_tree_view_selection(self, sender, args):
        """Handles selecting a unit, but does not repopulate the combobox."""
        selected_item = args.NewValue
        if (
            not selected_item
            or not hasattr(selected_item, "Tag")
            or not selected_item.Tag
        ):
            return

        unit_data = selected_item.Tag
        # print(
            # "Selected Unit: '{}', Spec: '{}', Side: {}".format(
                # unit_data.unit_id, unit_data.spec_id, sender.Name
            # )
        # )
        if sender.Name == "InputTreeView":
            self._apply_filter_to_output_view(unit_data.spec_id, unit_data.unit_id)
            self.from_unit_id = unit_data.unit_id
        elif sender.Name == "OutputTreeView":
            self.to_unit_id = unit_data.unit_id
        # print([self.from_unit_id, self.to_unit_id])

    def _handle_window_closing(self, sender, args):
        """
        This method is the central handler for when the window is about to close,
        regardless of how the close was triggered (button, 'X', or Esc key).
        Any cleanup logic, like saving settings, should go here.
        """
        pass
        # print("Window is closing. Performing cleanup actions...")
        # (Future cleanup code would go here)

    def _perform_unit_conversion(self, silent = False):
        """
        Gets values from UI, performs conversion, and updates the UI.

        Args:
            silent: Don't pop up an alert when conversion not specifically requested
                    by the user.
        """
        # from pyrevit import revit
        from pyrevit import forms

        # Import Revit API components for unit conversion
        from Autodesk.Revit.DB import Units, UnitSystem, UnitUtils, ForgeTypeId, UnitFormatUtils, FormatOptions, FormatValueOptions

        # Get the input value
        input_data = self._get_input_value_unit_tag()
        if not input_data:
            return
        if not input_data["value"]:
            if not silent:
                forms.alert("Please enter a value to convert.")
            return
        if not silent and input_data["tag"]:
            self.history_tag = input_data["tag"]

        # Get the selected "from" and "to" units from the TreeViews.
        if not self.from_unit_id and input_data["unit_id"]:
            self.from_unit_id = input_data["unit_id"]
        if not self.from_unit_id or not self.to_unit_id:
            if not silent:
                forms.alert("Please select both a 'From' and 'To' unit.")
            return

        # Check if the specs are compatible for conversion
        spec_id = None
        for spec in self.specs_data:
            if self.from_unit_id in spec["ValidUnits"] and self.to_unit_id in spec["ValidUnits"]:
                spec_id = spec["ForgeTypeId"]
                break
        if not spec_id:
            if not silent:
                forms.alert("Units must be of the same type (e.g., both Length).")
            return

        # Parse and validate the user's input.
        try:
            input_value = float(input_data["value"])
            decimal_places = int(3)
            spec_type_id = ForgeTypeId(spec_id)
            unit_type_id = ForgeTypeId(self.from_unit_id)
            to_unit_forgeid = ForgeTypeId(self.to_unit_id)
            suppress_trailing_zeros = True
            input_value_revit_units = UnitUtils.ConvertToInternalUnits(input_value, unit_type_id)
        except (ValueError, TypeError) as e:
            forms.alert("Invalid input. Please ensure the value and decimals are numbers and the IDs are correct.\n\nError: {}".format(e))
            return

        # Create and configure the FormatOptions object.
        # This object tells the API how we want the final string to look.
        try:
            # Get the default format options for the specified unit
            units = Units(UnitSystem.Metric) # revit.doc.GetUnits()
            format_options = units.GetFormatOptions(spec_type_id)

            # We must set UseDefault to False to apply our custom settings.
            format_options.UseDefault = False
            # https://www.revitapidocs.com/2022/4b317c87-727e-b8e9-3f0b-2b5479090fb7.htm
            format_options.SetUnitTypeId(to_unit_forgeid)
            
            # Set the rounding precision
            unit_accuracy = 1.0 / (10 ** decimal_places)
            if "fractionalinches" in str(to_unit_forgeid.TypeId.lower()):
                unit_accuracy = 1.0 / (2 ** decimal_places) / 12
            elif "minutes" in str(to_unit_forgeid.TypeId.lower()):
                unit_accuracy = (1 / (10 ** decimal_places)) / 3600
            if format_options.IsValidAccuracy(unit_accuracy):
                format_options.Accuracy = unit_accuracy
            # print([to_unit_forgeid.TypeId.lower(), unit_accuracy])

            # Set other common formatting properties
            format_options.UseDigitGrouping = True
            if format_options.CanSuppressTrailingZeros():
                format_options.SuppressTrailingZeros = suppress_trailing_zeros
            if format_options.CanSuppressLeadingZeros():
                format_options.SuppressLeadingZeros = False

            # Check if the unit can have a symbol and, if so, apply the first one.
            # This is the key to showing units like "mm", "m²", etc.
            if format_options.CanHaveSymbol():
                # GetValidSymbols() returns a list of ForgeTypeIds for symbols
                valid_symbols = format_options.GetValidSymbols()
                if valid_symbols and valid_symbols.Count > 1:
                    # Set the symbol to the first one in the list
                    format_options.SetSymbolTypeId(valid_symbols[1])
                    # print("Applied symbol: {}".format(valid_symbols[1].TypeId))
                # else:
                    # print("Unit can have a symbol, but none were found.")
            # else:
                # print("This unit type does not support symbols.")
        except Exception as e:
            forms.alert("Failed to create or configure FormatOptions.\n"
                  "Please check if the Unit ID is valid.\n\nError: {}".format(e))
            # raise e
            return

        # Call the main formatting function from the Revit API.
        try:
            # The 'forEditing' argument is a boolean that is True if the formatting
            # should be modified as necessary so that the formatted string can be successfully
            # parsed, for example by suppressing digit grouping. False if unmodified settings
            # should be used, suitable for display only.
            format_value_options = FormatValueOptions()
            format_value_options.SetFormatOptions(format_options)
            converted_value = UnitFormatUtils.Format(
                units,
                spec_type_id,
                input_value_revit_units,
                False, # forEditing
                format_value_options # FormatValueOptions
            )
        except Exception as e:
            forms.alert("An error occurred during formatting.\n"
                  "Please ensure the Spec ID is compatible with the Unit ID.\n\n"
                  "Error: {}".format(e))
            # raise e

        # Display the result and update history
        try:
            # print("Conversion from {} to {}".format(self.from_unit_id, self.to_unit_id))
            # print("Conversion from {} to {}".format(input_data["value_with_unit"], converted_value))
            self.OutputValueTextBox.Text = str(converted_value)
            self._update_history(input_data["value_with_unit"], converted_value, input_data["tag"])
        except Exception as e:
            print("Error: {}".format(e))
            return

    def _populate_all_controls(self):
        """Populates the entire UI on startup."""
        # Populate filter comboboxes with discipline names
        self.FromUnitComboBox.ItemsSource = sorted(self.grouped_specs.keys())

        # Initial population of the input tree view with a hierarchical list of
        # Disciplines -> Specs -> Units.
        self.InputTreeView.Items.Clear()

        for discipline_name in sorted(self.grouped_specs.keys()):
            discipline_node = TreeViewItem()
            discipline_node.Header = discipline_name

            # Sort specs within the discipline alphabetically
            sorted_specs = sorted(
                self.grouped_specs[discipline_name], key=lambda x: x["Name"]
            )

            for spec_info in sorted_specs:
                spec_node = TreeViewItem()
                spec_node.Header = spec_info["Name"]

                for unit_urn in spec_info["ValidUnits"]:
                    unit_info = self.units_map.get(unit_urn)
                    if not unit_info:
                        continue

                    symbol = (
                        unit_info["UnitSymbols"][0]
                        if unit_info.get("UnitSymbols")
                        else ""
                    )
                    display_name = (
                        "{} ({})".format(unit_info["UnitName"], symbol)
                        if symbol
                        else unit_info["UnitName"]
                    )

                    unit_node = TreeViewItem()
                    unit_node.Header = display_name
                    unit_node.Tag = UnitItem(
                        display_name, spec_info["ForgeTypeId"], unit_urn
                    )

                    spec_node.Items.Add(unit_node)

                discipline_node.Items.Add(spec_node)
            self.InputTreeView.Items.Add(discipline_node)

        # Initial population of the output tree view with a list of Units.
        self.OutputTreeView.Items.Clear()

        for unit_urn, unit_info in self.units_map.items():
            symbol = unit_info["UnitSymbols"][0] if unit_info.get("UnitSymbols") else ""
            display_name = (
                "{} ({})".format(unit_info["UnitName"], symbol)
                if symbol
                else unit_info["UnitName"]
            )

            unit_node = TreeViewItem()
            unit_node.Header = display_name
            unit_node.Tag = UnitItem(display_name, None, unit_urn)
            self.OutputTreeView.Items.Add(unit_node)

    def _update_history(self, from_val, to_val, history_tag):
        """Appends a new entry to the history text box."""
        history_entry = ""
        if not history_tag and self.history_tag:
            history_tag = self.history_tag
        if history_tag and history_tag != self.current_history_tag:
            self.current_history_tag = history_tag
            history_entry = "-"*12 + "\n{}\n".format(history_tag)
        elif not history_tag:
            self.current_history_tag = None

        history_entry += "{} -> {}\n".format(from_val, to_val)
        # Prepend the new entry to the top of the history log
        self.HistoryTextBox.Text = self.HistoryTextBox.Text + history_entry
        self.HistoryTextBox.ScrollToEnd()

    def _wire_up_events(self):
        """Centralizes all event handler wiring."""
        self.Closing += self._handle_window_closing

        # Connect button click events
        self.ConvertButton.Click += self._handle_convert_click
        self.CloseButton.Click += lambda s, e: self.Close()

        # Connect value entry actions
        self.InputValueTextBox.KeyUp += self._handle_input_changed
        self.FromUnitComboBox.KeyUp += self._handle_filter_change
        self.FromUnitComboBox.SelectionChanged += self._handle_filter_change
        self.InputTreeView.SelectedItemChanged += self._handle_tree_view_selection
        self.OutputTreeView.SelectedItemChanged += self._handle_tree_view_selection


# ------------------------------------------------------------------------------
# Main Script Execution
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Define the path to the XAML file.
    xaml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "UnitConverterWindow.xaml"
    )

    # Check if the XAML file actually exists before trying to load it.
    if not os.path.exists(xaml_path):
        forms.alert(
            "Could not find the XAML file for the UI.\nExpected at: {}".format(
                xaml_path
            ),
            title="UI File Not Found",
            exitscript=True,
        )

    # Create an instance of our window class.
    # This will load the XAML and prepare the window for display.
    try:
        UnitConverterWindow(xaml_path)
    except Exception as e:
        # If any error occurs during window creation or display, show an alert.
        print("Error creating or showing the Unit Converter window: {}".format(e))
        forms.alert(
            "An unexpected error occurred while launching the tool.\n\nError: {}".format(
                e
            ),
            title="Tool Error",
        )
