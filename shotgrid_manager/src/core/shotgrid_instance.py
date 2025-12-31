'''
    Manages persistent connection to Shotgun.
    Connection is opened once and maintained throughout the application lifecycle.
    All managers share the same connection instance via composition pattern.
'''
import os
import shotgun_api3 as sg
import logging
from utils.logger import setup_logging

class ShotgridInstance():

    logger = logging.getLogger(__name__)

    def __init__(self):
        setup_logging()
        self.instance = None
        self._is_connected = False

    def connect(self):
        """
        Establish persistent connection to Shotgun.
        Should be called once at application startup.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            ValueError: If environment variables are missing
            ConnectionError: If unable to connect to Shotgun
        """
        # If already connected, return success
        if self._is_connected and self.instance:
            self.logger.info("Already connected to Shotgun")
            return True

        # Get credentials from environment
        url = os.getenv('SG_URL')
        script_name = os.getenv('SG_SCRIPT_NAME')
        api_key = os.getenv('SG_SCRIPT_KEY')

        # Validate credentials exist
        if not (url and script_name and api_key):
            self.logger.error("Missing Shotgun credentials in environment variables")
            raise ValueError(
                "Missing required environment variables: SG_URL, SG_SCRIPT_NAME, SG_SCRIPT_KEY"
            )

        # Attempt connection
        try:
            self.instance = sg.shotgun.Shotgun(
                base_url=url,
                script_name=script_name,
                api_key=api_key
            )
            self._is_connected = True
            self.logger.info(f"Successfully connected to Shotgun: {url}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Shotgun: {e}")
            raise ConnectionError(f"Unable to connect to {url}: {str(e)}")

    def disconnect(self):
        """
        Close Shotgun connection.
        Should be called once at application shutdown.
        """
        if self.instance and self._is_connected:
            try:
                self.instance.close()
                self._is_connected = False
                self.logger.info("Shotgun connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
        else:
            self.logger.warning("No active connection to close")

    def is_connected(self):
        """
        Check if connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected and self.instance is not None

    def ensure_connected(self):
        """
        Ensure connection is active, connect if not.

        Raises:
            ConnectionError: If not connected and unable to connect
        """
        if not self.is_connected():
            raise ConnectionError(
                "Not connected to Shotgun. Call connect() first."
            )


if __name__ == "__main__":
    import requests
    import shutil

    setup_logging()
    logger = logging.getLogger(__name__)

    # Test persistent connection pattern
    sg_instance = ShotgridInstance()

    # Connect once at startup
    sg_instance.connect()

    # Verify connection
    print(f"Connected: {sg_instance.is_connected()}")

    # getting schemas
    # schemas = sg_instance.instance.schema_field_read(entity_type="Step")
    # print(schemas)

    # getting entities - no connect/disconnect needed
    entities = sg_instance.instance.find(
        entity_type="Step",
        filters=[],
        fields= [
            'code', 'description', 'color', 'short_name', 'department', 'list_order', 'entity_type',
            'cached_display_name', 'updated_by', 'created_by', 'created_at', 'updated_at', 'id'
        ]
    )
    print(f"Found {len(entities)} assets")
    print(entities)

    # update entities
    # data = {'sg_asset_type': 'Character'}
    # updated_entity = sg_instance.instance.update(entity_type="Asset", entity_id=1445, data=data)
    # print(updated_entity)

    # Disconnect once at shutdown
    sg_instance.disconnect()


    # data = [
    #     {'type': 'Step', 'id': 2, 'code': 'Online', 'description': None, 'color': '213,213,213', 'short_name': 'ONL', 'department': None, 'list_order': 5, 'entity_type': 'Shot', 'cached_display_name': 'Online', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 54, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 6, 'code': 'FX', 'description': None, 'color': '253,188,0', 'short_name': 'FX', 'department': None, 'list_order': 11, 'entity_type': 'Shot', 'cached_display_name': 'FX', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 7, 'code': 'Light', 'description': None, 'color': '25,118,27', 'short_name': 'LGT', 'department': None, 'list_order': 12, 'entity_type': 'Shot', 'cached_display_name': 'Light', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 8, 'code': 'Comp', 'description': None, 'color': '0,126,174', 'short_name': 'CMP', 'department': None, 'list_order': 13, 'entity_type': 'Shot', 'cached_display_name': 'Comp', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 13, 'code': 'Art', 'description': None, 'color': '253,94,99', 'short_name': 'ART', 'department': None, 'list_order': 7, 'entity_type': 'Asset', 'cached_display_name': 'Art', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 14, 'code': 'Model', 'description': None, 'color': '254,173,146', 'short_name': 'MDL', 'department': None, 'list_order': 8, 'entity_type': 'Asset', 'cached_display_name': 'Model', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 15, 'code': 'Rig', 'description': None, 'color': '161,236,154', 'short_name': 'RIG', 'department': None, 'list_order': 9, 'entity_type': 'Asset', 'cached_display_name': 'Rig', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 16, 'code': 'Texture', 'description': None, 'color': '253,254,152', 'short_name': 'TXT', 'department': None, 'list_order': 10, 'entity_type': 'Asset', 'cached_display_name': 'Texture', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2009, 12, 11, 23, 40, 56, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 32, 'code': 'Animation', 'description': None, 'color': '192,97,253', 'short_name': 'ANM', 'department': None, 'list_order': 12, 'entity_type': 'Asset', 'cached_display_name': 'Animation', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2012, 11, 26, 16, 22, 44, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 35, 'code': 'Layout', 'description': None, 'color': '183,0,188', 'short_name': 'LAY', 'department': None, 'list_order': 8, 'entity_type': 'Shot', 'cached_display_name': 'Layout', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2015, 11, 2, 14, 55, 45, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 106, 'code': 'Animation', 'description': None, 'color': '252,47,140', 'short_name': 'ANM', 'department': None, 'list_order': 9, 'entity_type': 'Shot', 'cached_display_name': 'Animation', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': None, 'created_at': datetime.datetime(2015, 12, 17, 10, 28, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 119, 'code': 'Concept', 'description': None, 'color': '252,47,140', 'short_name': 'CPT', 'department': None, 'list_order': 1, 'entity_type': 'Level', 'cached_display_name': 'Concept', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 57, 59, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 28, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 120, 'code': 'Level Design', 'description': None, 'color': '254,125,179', 'short_name': 'LD', 'department': None, 'list_order': 2, 'entity_type': 'Level', 'cached_display_name': 'Level Design', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 58, 18, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 30, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 121, 'code': 'Modeling', 'description': None, 'color': '255,181,76', 'short_name': 'MDL', 'department': None, 'list_order': 3, 'entity_type': 'Level', 'cached_display_name': 'Modeling', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 58, 25, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 32, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 122, 'code': 'Level Art', 'description': None, 'color': '254,205,138', 'short_name': 'LA', 'department': None, 'list_order': 4, 'entity_type': 'Level', 'cached_display_name': 'Level Art', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 58, 34, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 34, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 123, 'code': 'Lighting', 'description': None, 'color': '253,252,100', 'short_name': 'LTG', 'department': None, 'list_order': 5, 'entity_type': 'Level', 'cached_display_name': 'Lighting', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 58, 41, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 36, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 124, 'code': 'Animation', 'description': None, 'color': '253,254,152', 'short_name': 'ANM', 'department': None, 'list_order': 6, 'entity_type': 'Level', 'cached_display_name': 'Animation', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 58, 49, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 41, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 125, 'code': 'FX', 'description': None, 'color': '103,226,102', 'short_name': 'FX', 'department': None, 'list_order': 7, 'entity_type': 'Level', 'cached_display_name': 'FX', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 58, 55, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 43, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 126, 'code': 'Gameplay', 'description': None, 'color': '161,236,154', 'short_name': 'GPL', 'department': None, 'list_order': 8, 'entity_type': 'Level', 'cached_display_name': 'Gameplay', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 59, 1, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 46, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 127, 'code': 'QA', 'description': None, 'color': '50,149,253', 'short_name': 'QA', 'department': None, 'list_order': 9, 'entity_type': 'Level', 'cached_display_name': 'QA', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 59, 7, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 47, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 128, 'code': 'Integration', 'description': None, 'color': '129,183,255', 'short_name': 'INT', 'department': None, 'list_order': 10, 'entity_type': 'Level', 'cached_display_name': 'Integration', 'updated_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2016, 12, 12, 17, 59, 17, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2018, 12, 3, 20, 26, 50, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 129, 'code': 'Design', 'description': None, 'color': '254,125,179', 'short_name': 'DSN', 'department': None, 'list_order': 6, 'entity_type': 'Asset', 'cached_display_name': 'Design', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 3, 21, 11, 19, 48, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 131, 'code': 'Visualization', 'description': None, 'color': '2,149,216', 'short_name': 'VIZ', 'department': None, 'list_order': 14, 'entity_type': 'Asset', 'cached_display_name': 'Visualization', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 3, 21, 11, 20, 50, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 132, 'code': 'Class-A', 'description': None, 'color': '222,182,255', 'short_name': 'CSA', 'department': None, 'list_order': 15, 'entity_type': 'Asset', 'cached_display_name': 'Class-A', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 3, 21, 11, 21, 26, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 133, 'code': 'Tracking', 'description': None, 'color': '50,149,253', 'short_name': 'TRK', 'department': None, 'list_order': 6, 'entity_type': 'Shot', 'cached_display_name': 'Tracking', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 4, 26, 12, 33, 29, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 134, 'code': 'Roto', 'description': None, 'color': '156,1,255', 'short_name': 'RTO', 'department': None, 'list_order': 7, 'entity_type': 'Shot', 'cached_display_name': 'Roto', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 4, 26, 12, 41, 4, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 136, 'code': 'Character FX', 'description': None, 'color': '253,94,99', 'short_name': 'CFX', 'department': None, 'list_order': 10, 'entity_type': 'Shot', 'cached_display_name': 'Character FX', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 4, 26, 18, 20, 11, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 137, 'code': 'Character FX', 'description': None, 'color': '129,183,255', 'short_name': 'CFX', 'department': None, 'list_order': 11, 'entity_type': 'Asset', 'cached_display_name': 'Character FX', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 24, 'name': 'ShotGrid Support', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2019, 10, 11, 14, 0, 51, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 142, 'code': 'Surfacing', 'description': None, 'color': None, 'short_name': 'SF', 'department': None, 'list_order': 5, 'entity_type': 'Asset', 'cached_display_name': 'Surfacing', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 3, 21, 2, 1, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 175, 'code': 'Previs', 'description': None, 'color': '94,0,0', 'short_name': 'PRE', 'department': None, 'list_order': 4, 'entity_type': 'Shot', 'cached_display_name': 'Previs', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 0, 12, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 176, 'code': 'LightRig', 'description': None, 'color': '184,178,4', 'short_name': 'LGR', 'department': None, 'list_order': 4, 'entity_type': 'Asset', 'cached_display_name': 'LightRig', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 1, 56, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 177, 'code': 'Delivery', 'description': None, 'color': '161,236,154', 'short_name': 'DEL', 'department': None, 'list_order': 3, 'entity_type': 'Shot', 'cached_display_name': 'Delivery', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 3, 16, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 178, 'code': 'Assembly', 'description': None, 'color': '253,252,100', 'short_name': 'ASB', 'department': None, 'list_order': 2, 'entity_type': 'Shot', 'cached_display_name': 'Assembly', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 4, 31, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 179, 'code': 'Render', 'description': None, 'color': '0,230,254', 'short_name': 'RDR', 'department': None, 'list_order': 1, 'entity_type': 'Shot', 'cached_display_name': 'Render', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 5, 21, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 180, 'code': 'Render', 'description': None, 'color': '0,230,254', 'short_name': 'RDR', 'department': None, 'list_order': 3, 'entity_type': 'Asset', 'cached_display_name': 'Render', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 7, 9, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}, 
    #     {'type': 'Step', 'id': 181, 'code': 'Comp', 'description': None, 'color': '255,218,137', 'short_name': 'COMP', 'department': None, 'list_order': 2, 'entity_type': 'Asset', 'cached_display_name': 'Comp', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 7, 35, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)},
    #     {'type': 'Step', 'id': 182, 'code': 'Delivery', 'description': None, 'color': '161,236,154', 'short_name': 'DEL', 'department': None, 'list_order': 1, 'entity_type': 'Asset', 'cached_display_name': 'Delivery', 'updated_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_by': {'id': 88, 'name': 'kukari animation', 'type': 'HumanUser'}, 'created_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>), 'updated_at': datetime.datetime(2025, 11, 17, 13, 7, 57, tzinfo=<shotgun_api3.lib.sgtimezone.LocalTimezone object at 0x7da0156144d0>)}
    # ]

    # shots = [
    #     {'type': 'Shot', 'id': 1207, 'code': 'sq010_010', 
    #      'tasks': [
    #          {'id': 6059, 'name': '00_Animatic', 'type': 'Task'}, 
    #          {'id': 6058, 'name': '01_Layout', 'type': 'Task'}, 
    #          {'id': 6060, 'name': '02_Animacion', 'type': 'Task'}, 
    #          {'id': 6062, 'name': '03_Assembly', 'type': 'Task'}, 
    #          {'id': 6063, 'name': '04_Lighting', 'type': 'Task'}, 
    #          {'id': 6065, 'name': '05_Render', 'type': 'Task'}, 
    #          {'id': 6061, 'name': '06_Comp', 'type': 'Task'}, 
    #          {'id': 6066, 'name': '07_Fx', 'type': 'Task'}, 
    #          {'id': 6064, 'name': '08_Output', 'type': 'Task'}
    #     ], 'assets': [], 'sg_versions': [], 'sg_published_files': []}]


