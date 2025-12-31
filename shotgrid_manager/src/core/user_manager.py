from core.base_manager import BaseManager
from utils.logger import setup_logging
import logging



class UserManager(BaseManager):
    entity = "HumanUser"
    entity_fields = [
            "projects", "id", 
            "sg_status_list", # ['act', 'dis']
            "name", "lastname", "firstname",
        ]

    def create_user(self, last_name:str, first_name:str, status:str="dis")->dict:
        """
        Args:
            last_name: 
            first_name: 
            status: can be active ('act') or disable ('dis')
        """
        user_data = {
            'sg_status_list': status,
            'firstname': first_name,
            'lastname': last_name
        }
        
        return self.create_entity(data = user_data)
    
    def get_all_users(self):
        """
        gets all users from the shot gun instance
        """
        return self.get_entities(
            filters=[],
            fields=self.entity_fields
        )


if __name__ == "__main__":
    """
    Test AssetManager with persistent connection pattern.

    SandBox project:
    {'id': 124, 'name': 'SandBox', 'type': 'Project'}

    Kukari Task templates:
    [
        {'type': 'TaskTemplate', 'id': 46, 'code': 'Kukari_Animation_Assets'},
        {'type': 'TaskTemplate', 'id': 47, 'code': 'Kukari_Animation_Shots'}
    ]
    """
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    # Connect once at startup
    sg_instance = ShotgridInstance()
    sg_instance.connect()

    # Create asset manager with shared connection
    user_manager = UserManager(shotgun_instance=sg_instance)
    # user = user_manager.create_user(last_name="pipeline", first_name="dev", status="dis")
    users = user_manager.get_all_users()

    print(f"users: {users}")

    
    # Disconnect once at shutdown
    sg_instance.disconnect()

    # users = [
    #     {'type': 'HumanUser', 'id': 3, 'projects': [], 'sg_status_list': 'dis', 'name': 'Template User', 'lastname': 'User', 'firstname': 'Template'}, 
    #     {'type': 'HumanUser', 'id': 17, 'projects': [], 'sg_status_list': 'dis', 'name': 'Ulises Virgen', 'lastname': 'Virgen', 'firstname': 'Ulises'}, 
    #     {'type': 'HumanUser', 'id': 18, 'projects': [], 'sg_status_list': 'dis', 'name': 'Artist 2', 'lastname': '2', 'firstname': 'Artist'}, 
    #     {'type': 'HumanUser', 'id': 19, 'projects': [], 'sg_status_list': 'dis', 'name': 'Artist 1', 'lastname': '1', 'firstname': 'Artist'}, 
    #     {'type': 'HumanUser', 'id': 21, 'projects': [], 'sg_status_list': 'dis', 'name': 'Vendor 1', 'lastname': '1', 'firstname': 'Vendor'}, 
    #     {'type': 'HumanUser', 'id': 24, 'projects': [{'id': 89, 'name': 'Animation Template', 'type': 'Project'}, {'id': 88, 'name': 'Automotive Design Template', 'type': 'Project'}, {'id': 87, 'name': 'Demo: Automotive', 'type': 'Project'}, {'id': 86, 'name': 'Game Outsourcing Template', 'type': 'Project'}], 'sg_status_list': 'act', 'name': 'ShotGrid Support', 'lastname': 'Support', 'firstname': 'ShotGrid'}, 
    #     {'type': 'HumanUser', 'id': 58, 'projects': [], 'sg_status_list': 'dis', 'name': 'Vendor 2', 'lastname': '2', 'firstname': 'Vendor'}, 
    #     {'type': 'HumanUser', 'id': 59, 'projects': [], 'sg_status_list': 'dis', 'name': 'Vendor 3', 'lastname': '3', 'firstname': 'Vendor'}, 
    #     {'type': 'HumanUser', 'id': 66, 'projects': [], 'sg_status_list': 'dis', 'name': 'Manager 1', 'lastname': '1', 'firstname': 'Manager'}, 
    #     {'type': 'HumanUser', 'id': 67, 'projects': [], 'sg_status_list': 'dis', 'name': 'Manager 2', 'lastname': '2', 'firstname': 'Manager'}, 
    #     {'type': 'HumanUser', 'id': 68, 'projects': [], 'sg_status_list': 'dis', 'name': 'Manager 3', 'lastname': '3', 'firstname': 'Manager'}, 
    #     {'type': 'HumanUser', 'id': 88, 'projects': [{'id': 157, 'name': 'My Animation Project', 'type': 'Project'}, {'id': 158, 'name': 'Norwegian', 'type': 'Project'}, {'id': 124, 'name': 'SandBox', 'type': 'Project'}, {'id': 91, 'name': 'SIAMES', 'type': 'Project'}], 'sg_status_list': 'act', 'name': 'kukari animation', 'lastname': 'animation', 'firstname': 'kukari'}, 
    #     {'type': 'HumanUser', 'id': 121, 'projects': [], 'sg_status_list': 'dis', 'name': 'dev pipeline', 'lastname': 'pipeline', 'firstname': 'dev'}, 
    #     {'type': 'HumanUser', 'id': 154, 'projects': [{'id': 158, 'name': 'Norwegian', 'type': 'Project'}, {'id': 124, 'name': 'SandBox', 'type': 'Project'}], 'sg_status_list': 'dis', 'name': 'Daniel Bolanos', 'lastname': 'Bolanos', 'firstname': 'Daniel'}, 
    #     {'type': 'HumanUser', 'id': 155, 'projects': [{'id': 158, 'name': 'Norwegian', 'type': 'Project'}, {'id': 124, 'name': 'SandBox', 'type': 'Project'}, {'id': 91, 'name': 'SIAMES', 'type': 'Project'}], 'sg_status_list': 'dis', 'name': 'Beto Juarez', 'lastname': 'Juarez', 'firstname': 'Beto'}
    # ]
