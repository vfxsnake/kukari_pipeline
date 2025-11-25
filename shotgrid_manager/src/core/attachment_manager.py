from core.base_manager import BaseManager
from core.path_builder import PathBuilder
from utils.logger import setup_logging
from typing import List, Tuple
import logging


class AttachmentManager(BaseManager):
    entity = "Attachment"
    entity_fields =  [
        'file_size', 'attachment_reference_links','cached_display_name', 'original_fname', 'id',
        'local_storage', 'image_source_entity', 'attachment_links', 'this_file', 'project',
        'file_extension', 'description', 'filename', 'display_name', 'sg_type', 'created_at'
    ]

    def get_attachment(self, attachment_id:int):
        return self.get_entity(
            filters=[["id", "is", attachment_id]],
            fields=self.entity_fields
        )
    
    def get_attachments_from_project(self, project_id:int):
        attachments = self.get_entities(
            filters=[["project", "is", {"type":"Project", "id":project_id}]],
            fields=self.entity_fields
        )
        return attachments

    def get_attachments_from_version(self, version_id:int):
        attachments = self.get_entities(
            filters=[["attachment_reference_links", "is", {"type":"Version", "id":version_id}]],
            fields=self.entity_fields
        )
        return attachments
    
    def get_attachments_from_asset(self, asset_id:int):
        attachments = self.get_entities(
            filters=[["attachment_reference_links", "is", {"type":"Asset", "id":asset_id}]],
            fields=self.entity_fields
        )
        return attachments

    def get_attachments_from_shot(self, shot_id:int):
        attachments = self.get_entities(
            filters=[["attachment_reference_links", "is", {"type":"Version", "id":shot_id}]],
            fields=self.entity_fields
        )
        return attachments

    def upload_attachment_to_project(self, project_id:int, file_path:str)-> int:
        self.connect()

        uploaded_file = self.manager.instance.upload(
            entity_type="Project",
            entity_id=project_id,
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
        pass

    def set_data_to_attachment(
        self, attachment_id, published_file_id:int, original_name, extension_name:str, file_name:str
    )-> dict:
        data = {
            "original_fname":original_name,
            "file_extension":extension_name,
            "attachment_links":[{"type":"PublishedFile", "id":published_file_id}],
            "filename":file_name
        }
        return self.update_entity(entity_id=attachment_id, data=data)


if __name__ == "__main__":
    from core.shotgrid_instance import ShotgridInstance
    setup_logging()
    logger = logging.getLogger(__name__)

    flow = ShotgridInstance()
    attachment_manager = AttachmentManager(shotgun_instance=flow)
    # uploaded_attachment = file_manager.upload_attachment_to_project(project_id=124, file_path="/mnt/c/Projects/kukari_projects/CianLu_V02.abc")
    uploaded_attachment = attachment_manager.get_attachment(attachment_id=704)
    
    logger.info(f"upload_file: {uploaded_attachment}")

    # attachment id: 704

    # upload_file={
    #     'type': 'Attachment', 
    #     'id': 704, 
    #     'file_size': None, 
    #     'attachment_reference_links': [], 
    #     'cached_display_name': 'CianLu_V02.abc', 
    #     'original_fname': 'CianLu_V02.abc', 
    #     'local_storage': None, 
    #     'image_source_entity': None, 
    #     'attachment_links': [{'id': 124, 'name': 'SandBox', 'type': 'Project'}], 
    #     # 'this_file': {'url': 'https://sg-media-usor-01.s3-accelerate.amazonaws.com/91c83671abbd16b6a4f171197665dad9033511d4/6e69f7d9a7e5638b120ebec0a77b264fead4333b/CianLu_V02.abc?response-content-disposition=filename%3D%22CianLu_V02.abc%22&x-amz-meta-user-id=1&x-amz-meta-user-type=ApiUser&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYJG6Z4JIQAQT7PLG%2F20251124%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20251124T031443Z&X-Amz-SignedHeaders=host&X-Amz-Expires=900&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEIT%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCj1PxD3b%2FHwf5UaA%2Fi3RFigoTDykK9g5PnHbFzTpMI4gIgRjUtJT2fD2hICwkeikicEE2syGSXzgzI%2BZOOq1HjcacqmAIITBAAGgw1Njk1NTA0MzA4MDEiDEp%2BbvGcYBBA3zt34yr1Ael8IYw6zrvouzPLH4k1yNn3Y90EQ67dmDuauUKNA58o7i5qHRv%2FYAlUwQxRYy2i%2BPLC5P7%2FVYP57tUYoyn5mfNEdbkn5CczrXYqbz8Ay%2F4h5HnYTvvtSGbEM2haXCSZZlzTpTKTqNkk%2B3ILis1yEFB6FcRiYVmWPH%2F%2ByLhnQVRfrJb90pjISycUCK4frGgk82hTWG6Tizk%2FqzJ6DF521mj0SERkIb56BLy99tT6ueRtYz0CPRIP%2Fsw0bMRsLI%2BDCSMbVYpabk26%2FG4s5Qx2oLMNpQWw2hLLgXZnjOYuhdJroi7AXyImt84F6cJ2WZWI3a2xNRljMKObj8kGOp0BGkOeiFwWXu5fNT%2Bey9U1lPittQna9Zzm0Kdjg8B6irvUQsLUa91Vicvv84cgDnh83pOKOR3o4nXYwFdmxl%2B%2F1t%2Fr1UDJLgM7Q3Y52KVaykQmX3d7MC%2Fh6kCRLBoMbSqL6sKzM5cXE9AY9l%2FUXKEBlXEiYeoZAdVNUiq8tnHzLY1jOyuOLbCyCzn8lTqBCpTw%2B50kj41QQZEGn2xOuA%3D%3D&X-Amz-Signature=6e1dec8e8df156f62ff796ce5eadf7aa29a752983d7821e89f924ced0b7bc3c8', 'name': 'CianLu_V02.abc', 'content_type': 'application/octet-stream', 'link_type': 'upload', 'type': 'Attachment', 'id': 704},
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'file_extension': None, 
    #     'description': None, 
    #     'filename': 'CianLu_V02.abc', 
    #     'display_name': 'CianLu_V02.abc', 
    #     'sg_type': None, 
    #     # 'created_at': datetime.datetime(2025, 11, 23, 21, 42, 41, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x716e93e6f650>)
    # }