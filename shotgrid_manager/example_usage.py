"""
Example Usage - Shotgrid Manager with Persistent Connection

This example demonstrates the correct usage pattern for the Shotgrid Manager.
Key concept: One persistent connection shared across all managers.

Connection Lifecycle:
1. Connect ONCE at application startup
2. Create all managers with the shared connection
3. Perform operations (no connection management needed)
4. Disconnect ONCE at application shutdown
"""

from core.shotgrid_instance import ShotgridInstance
from core.asset_manager import AssetManager
from core.shot_manager import ShotManager
from core.task_manager import TaskManager
from core.path_builder import PathBuilder
from utils.logger import setup_logging
import logging


def main():
    """Demonstrate proper connection management pattern"""

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Shotgrid Manager - Connection Pattern Example")
    logger.info("=" * 60)

    # ========================================================================
    # STEP 1: Connect ONCE at application startup
    # ========================================================================
    logger.info("\n[STEP 1] Connecting to Shotgun...")

    sg_instance = ShotgridInstance()

    try:
        sg_instance.connect()
        logger.info(f"✓ Connected: {sg_instance.is_connected()}")
    except (ValueError, ConnectionError) as e:
        logger.error(f"✗ Connection failed: {e}")
        logger.error("Please check your environment variables: SG_URL, SG_SCRIPT_NAME, SG_SCRIPT_KEY")
        return

    # ========================================================================
    # STEP 2: Create all managers with shared connection
    # ========================================================================
    logger.info("\n[STEP 2] Creating managers with shared connection...")

    # All managers share the SAME connection - no duplicate connections!
    asset_manager = AssetManager(shotgun_instance=sg_instance)
    shot_manager = ShotManager(shotgun_instance=sg_instance)
    task_manager = TaskManager(shotgun_instance=sg_instance)
    path_builder = PathBuilder(shotgun_instance=sg_instance)

    logger.info("✓ Created AssetManager")
    logger.info("✓ Created ShotManager")
    logger.info("✓ Created TaskManager")
    logger.info("✓ Created PathBuilder")
    logger.info("All managers share one persistent connection!")

    # ========================================================================
    # STEP 3: Perform operations - NO connection management needed
    # ========================================================================
    logger.info("\n[STEP 3] Performing operations...")

    # Example 1: Query assets
    logger.info("\nExample 1: Querying assets from project...")
    try:
        assets = asset_manager.get_assets_from_project(project_id=124)
        logger.info(f"✓ Found {len(assets)} assets")

        if assets:
            for asset in assets[:3]:  # Show first 3
                logger.info(f"  - {asset.get('code')} ({asset.get('sg_asset_type')})")
    except Exception as e:
        logger.error(f"✗ Query failed: {e}")

    # Example 2: Get tasks (using same connection)
    logger.info("\nExample 2: Getting tasks...")
    try:
        tasks = task_manager.get_entities(
            filters=[["project", "is", {"type": "Project", "id": 124}]],
            fields=["id", "content", "entity", "sg_status_list"]
        )
        logger.info(f"✓ Found {len(tasks)} tasks")

        if tasks:
            for task in tasks[:3]:  # Show first 3
                logger.info(f"  - Task #{task.get('id')}: {task.get('content')}")
    except Exception as e:
        logger.error(f"✗ Query failed: {e}")

    # Example 3: Build paths (using same connection)
    logger.info("\nExample 3: Building file paths...")
    try:
        if tasks:
            task_id = tasks[0]['id']
            task_path = path_builder.get_path_from_task(task_id)

            if task_path:
                logger.info(f"✓ Built path for task {task_id}:")
                logger.info(f"  {task_path}")
            else:
                logger.warning(f"Could not build path for task {task_id}")
    except Exception as e:
        logger.error(f"✗ Path building failed: {e}")

    # Example 4: Multiple operations in sequence (same connection!)
    logger.info("\nExample 4: Multiple operations with one connection...")
    try:
        # All these use the SAME connection - efficient!
        assets_count = len(asset_manager.get_assets_from_project(124))
        tasks_count = len(task_manager.get_entities(
            filters=[["project", "is", {"type": "Project", "id": 124}]],
            fields=["id"]
        ))

        logger.info(f"✓ Project summary:")
        logger.info(f"  Assets: {assets_count}")
        logger.info(f"  Tasks: {tasks_count}")
        logger.info("  All queries used the same persistent connection!")
    except Exception as e:
        logger.error(f"✗ Operations failed: {e}")

    # ========================================================================
    # STEP 4: Disconnect ONCE at application shutdown
    # ========================================================================
    logger.info("\n[STEP 4] Disconnecting from Shotgun...")
    sg_instance.disconnect()
    logger.info(f"✓ Disconnected: {not sg_instance.is_connected()}")

    logger.info("\n" + "=" * 60)
    logger.info("Example completed successfully!")
    logger.info("=" * 60)


def example_bad_pattern():
    """
    ❌ BAD PATTERN - DO NOT DO THIS ❌

    This shows what NOT to do (the old pattern that was slow)
    """
    logger = logging.getLogger(__name__)
    logger.warning("\n⚠️  ANTI-PATTERN - DO NOT USE ⚠️")
    logger.warning("This is how the OLD code worked (inefficient):")
    logger.warning("""
    # BAD: Opens/closes connection for EVERY operation
    def get_assets(self):
        self.connect()      # ❌ Open connection
        result = self.sg.find(...)
        self.close()        # ❌ Close connection
        return result

    # If you call this 10 times, you open/close 10 times!
    # Massive performance overhead!
    """)


def example_correct_pattern():
    """
    ✅ CORRECT PATTERN - USE THIS ✅
    """
    logger = logging.getLogger(__name__)
    logger.info("\n✅ CORRECT PATTERN - USE THIS ✅")
    logger.info("""
    # GOOD: One persistent connection

    # At app startup:
    sg_instance = ShotgridInstance()
    sg_instance.connect()  # Connect ONCE

    # Create managers:
    asset_manager = AssetManager(sg_instance)
    task_manager = TaskManager(sg_instance)

    # Use them freely - NO connection management:
    assets = asset_manager.get_assets_from_project(124)
    tasks = task_manager.get_entities(filters, fields)

    # At app shutdown:
    sg_instance.disconnect()  # Disconnect ONCE

    # Result: Same connection reused for all operations!
    # Much faster and more efficient!
    """)


if __name__ == "__main__":
    # Run the example
    main()

    # Show pattern comparison
    print("\n" + "=" * 60)
    print("PATTERN COMPARISON")
    print("=" * 60)
    example_bad_pattern()
    example_correct_pattern()
