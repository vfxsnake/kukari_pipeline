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
    # schemas = sg_instance.instance.schema_field_read(entity_type="Attachment")
    # print(schemas)

    # getting entities - no connect/disconnect needed
    entities = sg_instance.instance.find(
        entity_type="Asset",
        filters=[["project", "is", {'id': 124, 'name': 'SandBox', 'type': 'Project'}]],
        fields= ['code', 'sg_asset_type', "tasks"]
    )
    print(f"Found {len(entities)} assets")
    print(entities)

    # update entities
    # data = {'sg_asset_type': 'Character'}
    # updated_entity = sg_instance.instance.update(entity_type="Asset", entity_id=1445, data=data)
    # print(updated_entity)

    # Disconnect once at shutdown
    sg_instance.disconnect()



