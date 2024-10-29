from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, ElementId
from pyrevit import revit, DB

doc = revit.doc

def get_family_types(family_name):
    """Retrieve all family types for a specific family."""
    collector = FilteredElementCollector(doc)
    family_types = collector.OfClass(FamilySymbol).ToElements()
    return [ft for ft in family_types if ft.Family.Name == family_name]

def change_valve_size(valve, target_size):
    """Change the family type of a valve to match the desired size."""
    # Get the family name of the valve
    family_name = valve.Symbol.Family.Name

    # Get all available family types for the valve's family
    family_types = get_family_types(family_name)

    # Find the family type that matches the target size
    new_family_type = None
    for family_type in family_types:
        if str(target_size) in str(family_type.LookupParameter("Size").AsValueString()):
            new_family_type = family_type
            break

    if new_family_type:
        # Start a transaction to change the family type
        with revit.Transaction("Change Valve Size"):
            valve.Symbol = new_family_type
        print("Changed valve to size {}".format(target_size))
    else:
        print("No family type found for size {} in {}".format(target_size, family_name))

def main():
    # Get all valves (Pipe Accessories) in the model
    collector = FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipeAccessory).WhereElementIsNotElementType()
    
    for el in collector:
        # Example: You would replace this with the actual size logic based on pipes
        target_size = "3/4\""  # Replace with the actual desired size

        # Call the function to change the size of the valve
        change_valve_size(el, target_size)

main()
