"""Preset sources loader.

This module loads preset RSS sources from the presets directory.
"""

import json
import logging
import os

from app.database import SessionLocal
from app.models import Source


logger = logging.getLogger(__name__)


def get_preset_sources_path() -> str:
    """
    Get the path to the preset sources JSON file.

    Returns:
        Path to presets/sources.json
    """
    # Get the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels: services -> app -> project root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    # Return path to presets/sources.json
    return os.path.join(project_root, "presets", "sources.json")


def load_preset_sources() -> int:
    """
    Load preset sources from JSON file.

    Only loads sources on first run (when database is empty).

    Returns:
        Number of sources loaded
    """
    db = SessionLocal()
    try:
        # Check if any sources already exist (skip on subsequent runs)
        existing_count = db.query(Source).count()
        if existing_count > 0:
            logger.debug("Preset sources already loaded, skipping")
            return 0

        # Get preset sources file path
        preset_path = get_preset_sources_path()

        if not os.path.exists(preset_path):
            logger.warning(f"Preset sources file not found: {preset_path}")
            return 0

        # Load preset sources
        with open(preset_path, "r", encoding="utf-8") as f:
            presets = json.load(f)

        sources_added = 0

        for preset in presets.get("sources", []):
            # Create new source
            source = Source(
                name=preset["name"],
                url=preset["url"],
                tags=preset.get("tags", []),
                enabled=preset.get("enabled", True),
                fetch_interval=preset.get("fetch_interval", 300),
            )
            db.add(source)
            sources_added += 1

        db.commit()

        if sources_added > 0:
            logger.info(f"Loaded {sources_added} preset sources on first run")

        return sources_added

    except Exception as e:
        db.rollback()
        logger.error(f"Error loading preset sources: {e}")
        return 0
    finally:
        db.close()
