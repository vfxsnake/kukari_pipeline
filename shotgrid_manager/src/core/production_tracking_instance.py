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
    sbox_data = {"type": "Project", "id": int(os.getenv("KKR_SBOX_ID"))}

    filters = [
        ['id', 'is', sbox_data.get("id")]
        ]
    data_found = flow_instance.find(entity_type=sbox_data.get("type", "Project"), filters=filters, fields=["id", "code", "name"])
    print(data_found)
    for found_dict in data_found:
        print(found_dict.get('name'), found_dict.get('id'))

