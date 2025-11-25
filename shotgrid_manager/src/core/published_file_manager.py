from core.base_manager import BaseManager
from core.path_builder import PathBuilder
from utils.logger import setup_logging
from typing import List, Tuple
import logging


class PublishedFileManager(BaseManager):
    entity = "PublishedFile"
    entity_fields =  [
            'code','name', 'sg_status_list', 'created_at', 'project', 'id',
            'entity', 'entity.sg_asset_type', 'entity.sg_shot_type', 'version','task',
        ]
    
    def get_published_files_from_task(self, task_id)->List[dict]:
        filters = [["task", "is", {"type":"Task", 'id': task_id}]]
        return self.get_entities(filters=filters, fields=self.entity_fields)

    def get_published_files_from_version(self, version_id)->List[dict]:
        filters = [["task", "is", {"type":"Version", 'id': version_id}]]
        return self.get_entities(filters=filters, fields=self.entity_fields)
    
    def get_published_files_from_project(self, project_id)->List[dict]:
        filters = [["project", "is", {"type":"Project", "id":project_id}]]
        return self.get_entities(filters=filters, fields=self.entity_fields)
    
    def create_publish_file(self, version_id:int, task_id, name:str, file_code:str, project_id:int)->tuple[dict, dict]:
        published_file = self.create_entity(
            data= {
                "project":{"type":"Project", "id":project_id},
                "version":{"type":"Version", "id":version_id},
                "task":{"type":"Task", "id":task_id},
                "name":name,
                "code":file_code,
            }
        )
        return published_file
    

if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    file_manager = PublishedFileManager(shotgun_instance=flow)

    flow.open_connection()     
    # upload_file = flow.instance.upload( 
    #         entity_type="PublishedFile",
    #         entity_id= 36, 
    #         path="/mnt/c/Users/jazzj/Documents/Projects/shot_grid_test/CianLu_V02.abc",
    #         display_name="CianLu_V03"
    #     )
    flow.close_connection()
    # data = version_manager.update_version(version_id=6990, data=_data)
    # logger.info(f"published_file: {published_file}")
    logger.info(f"upload_file: {upload_file}")



# Attachment_673 = {
#         'type': 'Attachment', 
#         'id': 673, 
#         'cached_display_name': 'CianLu_V03', 
#         'original_fname': 'CianLu_V02.abc', 
#         'open_notes_count': 0,
#         'attachment_links': [{'id': 36, 'name': 'Cinalu_V02.abc', 'type': 'PublishedFile'}],
#         'attachment_reference_links':[{}],
#         'this_file': {
#             'url': 'https://sg-media-usor-01.s3-accelerate.amazonaws.com/91c83671abbd16b6a4f171197665dad9033511d4/d37e62252cb9c088b2b77d36c5ee60fbec65a714/CianLu_V02.abc?response-content-disposition=filename%3D%22CianLu_V02.abc%22&x-amz-meta-user-id=1&x-amz-meta-user-type=ApiUser&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYJG6Z4JI2AIQWLOI%2F20251117%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20251117T013832Z&X-Amz-SignedHeaders=host&X-Amz-Expires=900&X-Amz-Security-Token=IQoJb3JpZ2luX2VjENr%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJGMEQCIDsKMv1yRXKAS%2B5ok%2FY9%2FlvUppu%2FoA1bpaO75Pb48oADAiAciZlwKTFuQPV%2FtweZE6cAqmQbM7KwioW7sjdHaclWsSqhAgij%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAAaDDU2OTU1MDQzMDgwMSIMv262Vi9RQKxCZQYnKvUBKXw37%2BQ7f0gCHL%2FqGflasWF6sQvIpiBY2ALunxC%2B6aewo%2F%2F%2BFdKJMM4Fa%2BvDT%2F5Q7sIdnXgaM2zTiUz%2FpFyyDLBZx9ut99X4zjb9Oq66nXRrUpUFzWPTZ%2BmccO%2FAszxdEOmqlXMTeo4aOCYhve4dITbabnmd1RHsvgg06pfnIxIt6TMC5k2qIWfV4%2Bt0kPrW4WNOS%2F8QA2H477tUxeuq%2Fz6oKfm%2BE2HwXm5Zuic5WJwHIFLPsBWsBzCI5bigjgR5o8UE8BYX%2Bjt8kpIh9DR3jpwu406DpNPzLCDGBVlbAUNF%2F8CzTvObgLCG7FbmGzga3o1bOO4wmPnpyAY6ngEuI9L9U%2Fc4pfEs36U2Qe8Zae0UMO3V2Eq4CB%2FzDknnD3yoBVOypf63xQeMa8gIpiGhdoKRb1ZoGhHE0cC8Nc%2B6C185o%2B9W%2Fx9n0k6KSj25vg4DXqtGKPbQOj3DEEH9N1EBOa4I80qjf%2BwXlB7yT1o9jKl5dLye116wOcRPnk8UYS8CCGJQjt%2FPhKT7cBAyXOEn9pzsesALSBi3SFEGXQ%3D%3D&X-Amz-Signature=04809e0d4442f3e7f80fff70b4f3f9d376225fd7d8c0b27ded722d144fa9b662', 
#             'name': 'CianLu_V03', 
#             'content_type': 'application/octet-stream', 
#             'link_type': 'upload', 
#             'type': 'Attachment', 
#             'id': 673
#         }, 
#         'updated_at': datetime.datetime(2025, 11, 16, 0, 6, 49, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7ffbfaae4510>),  
#         'created_by': {'id': 1, 'name': 'ShotgunManager 1.0', 'type': 'ApiUser'}, 
#         'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
#         'updated_by': {'id': 1, 'name': 'ShotgunManager 1.0', 'type': 'ApiUser'}, 
#         'filename': 'CianLu_V02.abc', 
#         'display_name': 'CianLu_V03', 
#         'created_at': datetime.datetime(2025, 11, 16, 0, 6, 47, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7ffbfaae4510>), 
#     }

    # data = [
    #     {'type': 'Task', 'id': 5959, 'content': '01_Layout', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5960, 'content': '00_Animatic', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5961, 'content': '02_Animacion', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5962, 'content': '06_Comp', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5963, 'content': '03_Assembly', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5964, 'content': '04_Lighting', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5965, 'content': '08_Output', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5966, 'content': '05_Render', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'}, 
    #     {'type': 'Task', 'id': 5967, 'content': '07_Fx', 'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 'due_date': None, 'sg_priority_1': None, 'entity': {'id': 1174, 'name': 'generic_shot_00', 'type': 'Shot'}, 'sg_status_list': 'wtg'},
    #     ]