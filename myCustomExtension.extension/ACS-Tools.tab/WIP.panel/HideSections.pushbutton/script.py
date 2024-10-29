from Autodesk.Revit.DB import FilteredElementCollector, ViewSection, View, Transaction, ElementId, ViewSheet, ViewSchedule, ViewType, Viewport
from pyrevit import forms, revit, DB
from get_viewSheet import GetViewSheet
from System.Collections.Generic import List  # Import the .NET List class

doc = __revit__.ActiveUIDocument.Document
active_view = doc.ActiveView


def get_views_on_sheet(doc, view):
    """Get views placed on the given sheet view."""
    viewports = FilteredElementCollector(doc, view.Id).OfClass(Viewport).ToElements()
    views_on_sheet = []
    for viewport in viewports:
        view_id = viewport.ViewId
        view_element = doc.GetElement(view_id)

        # Exclude schedules and legends
        if view_element is not None and not isinstance(view_element, ViewSchedule):
            if view_element.ViewType != ViewType.Legend:  # Check the ViewType
                views_on_sheet.append(view_element)

    return views_on_sheet

def hide_sections_not_on_sheets(main_view):
    """Hide section lines in the main view for sections not placed on sheets."""
    # Start a transaction to modify the view
    with Transaction(doc, "Hide Unplaced Sections") as t:
        t.Start()
        # Initialise getViewSheet class 
        get_view_sheet = GetViewSheet(active_view, doc, print_sheet=True)
        

        # Get the sheet view of the active view
        sheet_view = get_view_sheet.get_sheet()
        # Collect all section views
        all_sections = FilteredElementCollector(doc)\
            .OfClass(ViewSection)\
            .WhereElementIsNotElementType()\
            .ToElements()
        

        # Get all views on the current sheet
        if sheet_view:
            views_on_sheets = get_views_on_sheet(doc, sheet_view)
            views_on_sheets_ids = [view.Id for view in views_on_sheets]

            # Create a .NET List to hold section IDs
            sections_to_hide = List[ElementId]()

            # Hide sections not on sheets
            for section in all_sections:
                try:
                    if section.Id in views_on_sheets_ids:
                        # Check if the section is visible in the main view
                        if section.CanBeHidden(active_view) and not section.IsHidden(active_view):
                            # Add the section Id to the .NET List
                            # For some reason, at least in 2023, section view id one off that given when get id of section object in revit (GET PROPER OBJECT)
                            #Bit of a hack for now
                            sections_to_hide.Add(ElementId(section.Id.IntegerValue - 1))
                            print("Prepared to hide section: {}, ID: {}".format(section.Name, section.Id))
                except Exception as exp:
                    print("Error occurred:", exp)
        

            # Hide all sections at once
            if sections_to_hide.Count > 0:  # Only hide if there are sections to hide
                active_view.HideElements(sections_to_hide[:-20])  # Pass the .NET List of ElementIds
                print("Hid {} sections not placed on sheets.".format(sections_to_hide.Count))
            else:
                print("No sections to hide.")

        else:
            print("The active view is not placed on a sheet.")

        print("Completed hiding sections not placed on sheets.")

        t.Commit()

# Check if the active view is a plan view or viewport
if not isinstance(active_view, ViewSheet):
    hide_sections_not_on_sheets(active_view)
else:
    forms.alert("The active view is a sheet. Please open a viewport to run this script.", exitscript=True)
