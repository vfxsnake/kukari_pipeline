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
        self._ensure_connected()

        uploaded_file = self.manager.instance.upload(
            entity_type="Project",
            entity_id=project_id,
            path=file_path,
        )
        return uploaded_file
    
    def download_attachment(self, attachment_id:int, target_path):
        self._ensure_connected()
        self.manager.instance.download_attachment(
            attachment_id=attachment_id,
            file_path=target_path
        )

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
    flow.connect()
    attachment_manager = AttachmentManager(shotgun_instance=flow)
    # uploaded_attachment = file_manager.upload_attachment_to_project(project_id=124, file_path="/mnt/c/Projects/kukari_projects/CianLu_V02.abc")
    uploaded_attachment = attachment_manager.get_attachment(attachment_id=746)
    
    logger.info(f"upload_file =  {uploaded_attachment}")
    flow.disconnect()

    # upload_file= {
    #     'type': 'Attachment', 'id': 746, 'file_size': None, 'attachment_reference_links': [], 'cached_display_name': 'CianLu_V02.abc', 
    #     'original_fname': 'CianLu_V02.abc', 'local_storage': None, 'image_source_entity': None, 
    #     'attachment_links': [
    #         {'id': 5947, 'name': '002_Modeling', 'type': 'Task'}, 
    #         {'id': 77, 'name': 'CianLu_V02.v004', 'type': 'PublishedFile'}, 
    #         {'id': 7031, 'name': 'generic_prop_1_002_Modeling_v004', 'type': 'Version'}
    #         ], 
    #     'this_file': {'url': 'https://sg-media-usor-01.s3-accelerate.amazonaws.com/91c83671abbd16b6a4f171197665dad9033511d4/19784f52326e76cd283008a10bfc7f6250735285/CianLu_V02.abc?response-content-disposition=filename%3D%22CianLu_V02.abc%22&x-amz-meta-user-id=1&x-amz-meta-user-type=ApiUser&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYJG6Z4JI6AZDZGAY%2F20251128%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20251128T201100Z&X-Amz-SignedHeaders=host&X-Amz-Expires=900&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEPT%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQDVTpIu9zVPigrUlARuV3MWbyh9raf36Q2a6OghBW4b2AIgO53dAHakuS%2BG1TpfqAiLrdeilegSBc%2BZ8SpawxWSvQIqoQIIvf%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FARAAGgw1Njk1NTA0MzA4MDEiDDtTTLpYOMLEWpiVkCr1AdU%2BcRYSMUasJVhtB3fbcOxZ0ZEMtVvo%2FdQHB2172c6b9Ae63Ui1K5TN4u8H3rWeOvsCGCJUu4niJrtcc6aT4KUqXSVvPjr1fJ26s6t2th5fKv2OFJYzGtCJtD4ERNObvZO6NzNinGj1hQFtysKXjuEG%2FSZ0qzwKK1aZHPfrst9rEgJ3%2F5gHsU%2F4qlxEtTDVlvM3LFLPXB7fVrBpH1RR0v9hruzLVIXtQ8olR6TnkqfFoitkH9FncvV0vgp1vDPkuLWH5jgoYPFum6EtrXZu4MAOcOWPjgr5dNCPUOlD00u%2B6xZPKRwE%2BmLMbukGsRYDij7vGX5jMLv7p8kGOp0B71mc%2Bk0tF10sECzal9RbRvfBWx2%2B7ApW6mBUKfMRawPLP4M5QXSaB6iYe8IryOT6OGKkFebW%2FJbgguh3fHPXbtQ3y6A1SM6a2J1DMrX2WZf15X2%2FaLgkggDTFs%2BgLigtqNZHlmDltG5viKf2e1jvRB1iUalWqeO5Mc16bi7B3xGnvjrMrY5w1hMG2sngmDfklgRwZPZkwvMePrPK2Q%3D%3D&X-Amz-Signature=89c72834a5bc816de9399466e09cc9bb6808f7aaa1605137b2f12ce4ef365f51', 'name': 'CianLu_V02.abc', 'content_type': 'application/octet-stream', 'link_type': 'upload', 'type': 'Attachment', 'id': 746}, 
    #     'project': {'id': 124, 'name': 'SandBox', 'type': 'Project'}, 
    #     'file_extension': None, 'description': None, 'filename': 'CianLu_V02.abc', 'display_name': 'CianLu_V02.abc', 'sg_type': None, 
    #     # 'created_at': datetime.datetime(2025, 11, 28, 15, 10, 14, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7e45ef79bd50>)
    #     }