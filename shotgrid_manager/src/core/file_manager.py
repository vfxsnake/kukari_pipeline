from core.base_manager import BaseManager
from core.path_builder import PathBuilder
from utils.logger import setup_logging
from typing import List, Tuple
import logging


class FileManager(BaseManager):
    entity = "PublishedFile"
    
    def get_published_files(self, task_id)->List[dict]:
        filters = [["task", "is", {type:"Task", 'id': task_id}]]
        fields = [
            'code','name', 'sg_versions', 'sg_status_list', 'created_at', 'project', 'id',
            'entity', 'entity.sg_asset_type', 'entity.sg_shot_type' 
        ]
        return self.get_entities(filters=filters, fields=fields)


    def get_attachments(self, published_file_id:int):
        filters = [['attachment_links', 'is', {'type': self.entity, 'id': published_file_id}]]
    
        fields = ['cached_display_name', 'original_fname', 'id',
            'attachment_links', 'this_file', 'updated_at',
            'file_extension', 'description', 'filename', 'display_name', 'created_at'
        ]
        self.connect()
        
        attachments = self.manager.instance.find(entity_type="Attachment", filters=filters, fields=fields)
        
        self.close()

        return attachments

    def create_publish_file(self, version_id:int, name:str, file_code:str, project_id:int, file_path:str)->tuple[dict, dict]:
        published_file = self.create_entity(
            data= {
                "project":{"type":"Project", "id":project_id},
                "version":{"type":"Version", "id":version_id},
                "name":name,
                "code":file_code,
            }
        )
        uploaded_file = self.upload_attachment(published_file_id=published_file.get("id", -1), file_path=file_path)
        return published_file, uploaded_file
    
    def upload_attachment(self, published_file_id:int, file_path:str)-> int:
        self.connect()

        uploaded_file = self.manager.instance.upload(
            entity_type=self.entity,
            entity_id=published_file_id,
            path=file_path,
        )
        self.close()
        return uploaded_file
    
    def download_attachment(self, attachment_id:int, target_path):
        self.connect(0)
        self.manager.instance.download_attachment( 
            attachment_id=attachment_id, 
            file_path=target_path
        )
        self.close()

    def download_attachments(self, published_file_id, path_builder:PathBuilder):
        
        published_file = self.get_entity(
            filters=[["id", 'is', published_file_id]],
            fields= ['id', 'project', 'version', "version_number",'task']
        )
        if not published_file.get("task", {}):
            self.logger.info("no valid task found to create path")
            return
        
        task_path = path_builder.get_path_from_task(published_file.get("task"))

        if published_file:
            attachments = self.get_attachments(published_file_id=published_file.get('id', -1))
            for attachment in attachments:
                self.download_attachment(
                    attachment.get('id', -1),
                    target_path=f"{task_path}/{published_file.get('name')}__{published_file.get("version_number")}.{attachment.get("file_extension")}"
                )
        self.close()    

if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    file_manager = FileManager(shotgun_instance=flow)

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