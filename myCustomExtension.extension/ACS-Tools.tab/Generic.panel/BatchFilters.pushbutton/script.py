# -*- coding: utf-8 -*-
__title__ = "Batch View Filters"
__author__ = "Ryan Coulman"
__version__ = "Version: 1.0"

# ====================================== Imports =============================================== # 

import os, traceback
from Autodesk.Revit.DB import *

#pyRevit
from pyrevit import forms

# .NET IMPORTS
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System")
from System.Collections.Generic import List
from System.Windows.Window import DragMove
from System.Windows.Input import MouseButtonState
from System.Windows import Window
from enum import Enum
import wpf


PATH_SCRIPT = os.path.dirname(__file__)
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
doc   = __revit__.ActiveUIDocument.Document
app_year = int(app.VersionNumber)
active_view = doc.ActiveView

class CheckBoxState(Enum):
    CHECKED = True
    UNCHECKED = False
    INDETERMINATE = None 

class ListItem:
    """Helper Class for displaying selected sheets in custom GUI form"""
    def __init__(self,  Name='Unnamed', element = None, checked = False, IsThreeWay = CheckBoxState.UNCHECKED):
        self.Name       = Name
        self.IsChecked  = checked
        self.ThreeWayState = IsThreeWay  
        self.element    = element

def create_List(dict_elements):
    """Function to create a List<ListItem> to parse it in GUI ComboBox.
    :param dict_elements:   dict of views ({name:view})
    :return:                List<ListItem>"""
    list_of_views = List[type(ListItem())]()
    for name, view in sorted(dict_elements.items()):
        list_of_views.Add(ListItem(name, view))
    return list_of_views

class ViewHandler:
    def __init__(self):
        # Collect all views in project (including view templates) and on sheet 
        all_views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).ToElements()
        views_on_sheet = FilteredElementCollector(doc, active_view.Id).OfClass(Viewport).ToElements()
        # Filter views to only contain views with filters and remove view templates 
        all_views_with_filters      = [v for v in all_views if v.GetFilters() and not v.IsTemplate]
        views_on_current_sheet = [doc.GetElement(v.ViewId) for v in views_on_sheet if doc.GetElement(v.ViewId).ViewType != ViewType.Legend and doc.GetElement(v.ViewId).ViewType != ViewType.Schedule]
        # Check there is at least one view else exit script
        self.check_if_views(all_views_with_filters)
        # Create Dict of Views
        dict_all_views = self.get_dict_views(all_views_with_filters)
        dict_views_on_sheet = self.get_dict_views(views_on_current_sheet)
        # Convert Dict into List[ListItem]() for ListBox
        self.List_all_views = create_List(dict_all_views)
        self.List_views_on_sheet = create_List(dict_views_on_sheet)

    def check_if_views(self, all_views_with_filters):
        if not all_views_with_filters:
            forms.alert("There are no Views or ViewTemplates with Filters applied to them! "
                        "\nPlease add some View Filters and Try Again.", exitscript=True)
            
    def get_dict_views(self, view_selection):
        """ Function to get and sort Views in a dict based on a mode setting.
            return:     dict of views with [ViewType] as a prefix."""
        
        dict_views = {}

        for view in view_selection:
            if view.ViewType == ViewType.FloorPlan:
                dict_views['[FLOOR] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.CeilingPlan:
                dict_views['[CEIL] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.ThreeD:
                dict_views['[3D] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Section:
                dict_views['[SEC] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Elevation:
                dict_views['[EL] {}'.format(view.Name)] = view

            elif view.ViewType ==ViewType.DraftingView:
                dict_views['[DRAFT] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.AreaPlan:
                dict_views['[AREA] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Rendering:
                dict_views['[CAM] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Legend:
                dict_views['[LEG] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.EngineeringPlan:
                dict_views['[STR] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Walkthrough:
                dict_views['[WALK] {}'.format(view.Name)] = view

            else:
                dict_views['[?] {}'.format(view.Name)] = view

        return dict_views
    
    def return_views_on_sheet(self):
        return self.List_views_on_sheet
    
    def return_all_views(self):
        return self.List_all_views


class SelectFilters(Window):
    view_handler = ViewHandler()
    views = view_handler.return_views_on_sheet() # Upon form initialisation 'views' will be displayed in first ListBox 

    def __init__(self):
        # Load Resources for WPF form 
        path_xaml_file = os.path.join(PATH_SCRIPT, 'CopyFilters.xaml')
        wpf.LoadComponent(self, path_xaml_file)

        # Update Text
        self.main_title.Text     = __title__
        self.footer_version.Text = __version__

        # Update first ListBoxes with views 
        self.UI_ListBox_Src_Views.ItemsSource = self.views

        # Populate the second ListBoxes with all filters in project 
        all_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()
        dict_filters = {f.Name: f for f in all_filters}
        List_filters = create_List(dict_filters)
        self.UI_ListBox_Filters.ItemsSource = List_filters

        # REVIT
        self.ShowDialog()

    # ====================== GUI ELEMENTS =========================== #

    def button_close(self, sender, e):
        """Stop application by clicking on a <Close> button in the top right corner."""
        self.Close()

    def header_drag(self, sender, e):
        """Drag window by holding LeftButton on the header."""
        if e.LeftButton == MouseButtonState.Pressed:
            DragMove(self)

    def HandleThirdState(self, sender, e):
        print('whey')


    def UI_event_checked_views(self, sender, e):
        """EventHandler for 'Only views on Sheet' checkbox"""
        # VIEWS ON SHEET (DEFAULT)
        if self.UI_checkbox_views.IsChecked:
            self.views = self.view_handler.return_views_on_sheet()
        # ALL VIEWS
        elif not self.UI_checkbox_views.IsChecked:
            self.views = self.view_handler.return_all_views()
        # NONE
        else:
            self.views = {}

        #UPDATE LISTBOX
        self.UI_ListBox_Src_Views.ItemsSource = self.views

    def UI_text_filter_updated(self, sender, e):
        """Function to filter items in the UI_ListBox_Views."""
        filtered_list_of_items = List[type(ListItem())]()
        filter_keyword = self.textbox_filter.Text

        #RESTORE ORIGINAL LIST
        if not filter_keyword:
            self.UI_ListBox_Src_Views.ItemsSource = self.views
            return

        # FILTER ITEMS
        for item in self.views:
            if filter_keyword.lower() in item.Name.lower():
                filtered_list_of_items.Add(item)

        # UPDATE LIST OF ITEMS
        self.UI_ListBox_Src_Views.ItemsSource = filtered_list_of_items
    

    def select_mode(self, mode):
        """Helper function for following buttons:
        - button_select_all
        - button_select_none"""

        list_of_items = List[type(ListItem())]()
        checked = True if mode=='all' else False
        for item in self.UI_ListBox_Src_Views.ItemsSource:
            item.IsChecked = checked
            list_of_items.Add(item)

        self.UI_ListBox_Src_Views.ItemsSource = list_of_items

    def button_select_all(self, sender, e):
        self.select_mode(mode='all')

    def button_select_none(self, sender, e):
        self.select_mode(mode='none')

    # ===================== RUN ============================= # 

    def collect_states(self):
        """Collect final states of filters and views when Apply button is clicked."""
        selected_filters = {} # Format: {name: [item element, Selected, Visibility]}
        selected_views = []

        for item in self.UI_ListBox_Src_Views.Items:
            # Check if the checkbox is checked
            if item.IsChecked:
                selected_views.append(item.element)  # Store the associated element

        for item in self.UI_ListBox_Filters.Items:
            # Get the name of the filter
            filter_name = item.Name
            # Get the state of the first checkbox
            checkbox1_state = item.ThreeWayState  
            # Get the state of the second checkbox
            checkbox2_state = item.IsChecked  
            
            # If any checkbox1 (selected) is selected, add to selected filters
            if checkbox1_state != CheckBoxState.UNCHECKED:
                if checkbox1_state == CheckBoxState.CHECKED or checkbox1_state is True:
                    keep_add = True
                else:
                    keep_add = False
                selected_filters[filter_name] = [item.element, keep_add, checkbox2_state]  # [First Checkbox State, Second Checkbox State]

        return selected_views, selected_filters

    # Activates when 'Apply' Button pressed 
    def button_run(self, sender, e):
        self.Close()

        selected_views, selected_filters = self.collect_states()

        print('*** Source Views: ***')
        for view in selected_views:
            print(view.Name)

        print('*** Selected Filters: ***')
        for f_name in selected_filters.keys():
            keep_remove = 'Keep / Add' if selected_filters[f_name][1] else 'Remove'
            print('{} {} - Visible: {} '.format(keep_remove, f_name, selected_filters[f_name][1]))

        with Transaction(doc, __title__) as t:
            t.Start()
            for view in selected_views:
                for filter in selected_filters.values():
                    filter_id = filter[0].Id
                    add_remove = filter[1]
                    visible = filter[2]
                    try:
                        if add_remove:
                            # Add the filter if not applied in view 
                            if not view.IsFilterApplied(filter_id):
                                view.AddFilter(filter_id)
                            # Set the filter's visibility to that selected 
                            view.SetFilterVisibility(filter_id, visible)
                        else:
                            # Remove filter if applied to the view
                            if view.IsFilterApplied(filter_id):
                                view.RemoveFilter(filter_id)

                    except:
                        print(traceback.format_exc())
            t.Commit()

        print('\nExecution Completed.')


# ===================== MAIN ============================= # 

if __name__ == '__main__':
    SelectFilters()