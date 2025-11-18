# ShotGrid Configuration Manager - Specification

## Overview
Configuration management system for ShotGrid pipeline, handling dynamic path templates and entity mappings on a per-project basis.

## Use Case
Manage folder structures and entity mappings for ShotGrid projects with templated paths like:
```
${Project}/{Assets|Shots}/{AssetType/AssetName}|{ShotName}/{Task}
```

Where:
- `Assets|Shots` - Decided by entity type (Asset → Assets, Shot → Shots)
- `AssetType/AssetName` - Mapped by `sg_asset_type` (Character → Characters, Environment → Environments)
- Requires flexible entity and entity type mappings

## Design Decisions

### Configuration Format
**Selected: YAML**

Reasons:
- High readability for humans
- Native support for nested data structures
- Inline comments for documentation
- Industry standard in VFX/Pipeline tools
- Easy manual editing

### Configuration Structure
```
config/
├── defaults/
│   ├── path_templates.yml
│   ├── entity_mappings.yml
│   └── asset_type_mappings.yml
└── projects/
    └── {project_name}/
        ├── path_templates.yml      # Project-specific overrides
        ├── entity_mappings.yml
        └── asset_type_mappings.yml
```

**Two-tier approach:**
- Base defaults in `config/defaults/`
- Project-specific overrides in `config/projects/{project_name}/`
- NO fallback to defaults - missing values raise errors explicitly

## Technical Requirements

### API Design
```python
import config

# Access patterns
asset_type_map = config.get("asset_type_map")
character = asset_type_map.get(data.get('sg_asset_type'))

# Or dot notation
value = config.get("config.asset_type_map")
```

### Environment Variables
- `PROJECT_NAME` or `SHOTGRID_PROJECT` - Current project identifier
- `CONFIG_PATH` - Base path to configuration files
- `CONFIG_RELOAD_INTERVAL` (optional) - Check interval for file changes

### Core Features

#### 1. Configuration Loading
- Parse YAML configuration files
- Merge project-specific overrides (no fallback to defaults)
- Cache loaded configurations
- Raise explicit errors for missing keys/files

#### 2. Hot Reload
- **Strategy: Reload on next access**
- Monitor config files for changes using file system events
- Thread-safe reload mechanism
- Don't interrupt active operations
- Clear cache and reload when files are modified

#### 3. Validation
- Schema validation on load
- Fail fast with clear error messages
- Validate all project configs in test suite
- Use `jsonschema` or `pydantic` for schema definitions

#### 4. Error Handling
- NO fallback behavior
- Missing keys → `KeyError` or `ConfigKeyError`
- Missing project config → Error on initialization
- Invalid YAML → Parse error with file/line info
- Schema violations → Validation error with details

### Package Structure
```
config/
├── __init__.py          # Main config singleton/module interface
├── loader.py            # YAML loading + hot reload logic
├── validator.py         # Schema validation layer
├── schema.py            # Configuration schemas definition
└── tests/
    └── test_config.py   # Config validation test suite
```

### Dependencies
- `PyYAML` or `ruamel.yaml` - YAML parsing
- `watchdog` - File system monitoring for hot reload
- `jsonschema` or `pydantic` - Schema validation
- `threading` (stdlib) - Thread-safe reload operations

### Template System Considerations
- Support token syntax: `${Variable}`, `{Option1|Option2}`
- Consider using existing template engines (Jinja2) vs custom parser
- Jinja2 provides conditionals and filters but may be overkill
- Simple variable substitution may be sufficient initially

## Implementation Notes

### Hot Reload Mechanism
1. Use `watchdog` to monitor config directory
2. On file change event, set reload flag
3. On next `config.get()` call, check reload flag
4. If flag set, reload configs and clear cache
5. Thread-safe using locks

### Validation Strategy
1. Define schemas for each config type
2. Validate on initial load
3. Validate on reload
4. Test suite validates all project configs on CI/CD

### Access Pattern
1. Singleton or module-level instance
2. Dot notation support for nested keys
3. Dictionary-style access for dynamic keys
4. Type hints for better IDE support

## Future Considerations
- Template string expansion/resolution
- Config inheritance beyond two tiers
- Config migration tools for schema changes
- Performance optimization for large configs
- Audit logging for config access/changes

## Success Criteria
- Clean, intuitive API for config access
- Automatic reload without restart
- Clear error messages for debugging
- Easy to add new projects
- Maintainable by future team members