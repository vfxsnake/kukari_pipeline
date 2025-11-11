'''
    Opens the connection to shotgun
    and returns the shotgun Object ready to start working with

'''
import os
import shotgun_api3 as sg


def get_flow_instance() -> sg.shotgun.Shotgun:
    """
        return a shotgun instance from environment variables: SG_URL, SG_SCRIPT_NAME, SG_SCRIPT_KEY
    """
        
    _sg = sg.shotgun.Shotgun(
        base_url=os.getenv('SG_URL'),
        script_name=os.getenv('SG_SCRIPT_NAME'),
        api_key=os.getenv('SG_SCRIPT_KEY')
    )
    return _sg
    


if __name__ == "__main__":
    flow_instance = get_flow_instance()
    
    # get fields from entities
    # schema = flow_instance.schema_field_read("TaskTemplate")
    # for attr, value in schema.items():
    #     print(attr, value)

    # find templates
    templates = flow_instance.find("TaskTemplate", filters=[], fields=['type', 'id', 'name', 'code', 'tasks', 'task_count'])

    for template in templates:
        print(template)