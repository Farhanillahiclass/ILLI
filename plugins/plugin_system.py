"""
Plugin System
Manages plugin loading, registration, and lifecycle.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from pathlib import Path
import importlib.util
import sys
import hashlib

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Plugin status"""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    id: str
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    api_version: str = "1.0.0"
    category: str = "general"


@dataclass
class Plugin:
    """A plugin instance"""
    metadata: PluginMetadata
    path: str
    status: PluginStatus = PluginStatus.LOADED
    instance: Optional[Any] = None
    loaded_at: Optional[datetime] = None
    error: Optional[str] = None


class PluginSystem:
    """
    Main plugin system for managing extensions.
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[Callable]] = {}
        self._api: Dict[str, Any] = {}
        self._initialized = False
        
    async def initialize(self):
        """Initialize the plugin system"""
        logger.info("Initializing Plugin System...")
        
        # Set up plugin API
        await self._setup_api()
        
        # Load plugins
        await self._load_plugins()
        
        self._initialized = True
        logger.info("Plugin System initialized")
    
    async def _setup_api(self):
        """Set up the plugin API"""
        self._api = {
            "register_hook": self.register_hook,
            "call_hook": self.call_hook,
            "get_config": self._get_plugin_config,
            "set_config": self._set_plugin_config,
            "log": self._plugin_log
        }
    
    async def _load_plugins(self):
        """Load all plugins from the plugin directory"""
        for plugin_path in self.plugin_dir.iterdir():
            if plugin_path.is_dir() and not plugin_path.name.startswith('_'):
                await self.load_plugin(plugin_path)
    
    async def load_plugin(self, plugin_path: Path) -> Optional[Plugin]:
        """
        Load a plugin from a directory.
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            Loaded plugin or None
        """
        try:
            # Load plugin metadata
            metadata_file = plugin_path / "plugin.json"
            if not metadata_file.exists():
                logger.warning(f"No plugin.json found in {plugin_path}")
                return None
            
            with open(metadata_file, 'r') as f:
                metadata_data = json.load(f)
            
            metadata = PluginMetadata(**metadata_data)
            
            # Load plugin module
            module_file = plugin_path / "main.py"
            if not module_file.exists():
                logger.warning(f"No main.py found in {plugin_path}")
                return None
            
            # Add plugin directory to path
            if str(plugin_path) not in sys.path:
                sys.path.insert(0, str(plugin_path))
            
            # Import module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.id}",
                module_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create plugin instance
            if hasattr(module, 'Plugin'):
                plugin_instance = module.Plugin(self._api)
            else:
                logger.warning(f"Plugin {metadata.id} has no Plugin class")
                return None
            
            # Initialize plugin
            if hasattr(plugin_instance, 'initialize'):
                await plugin_instance.initialize()
            
            plugin = Plugin(
                metadata=metadata,
                path=str(plugin_path),
                instance=plugin_instance,
                status=PluginStatus.ACTIVE,
                loaded_at=datetime.now()
            )
            
            self._plugins[metadata.id] = plugin
            logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            
            return plugin
            
        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_path}: {e}")
            return None
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if unloaded successfully
        """
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        
        try:
            # Call cleanup if available
            if plugin.instance and hasattr(plugin.instance, 'cleanup'):
                await plugin.instance.cleanup()
            
            del self._plugins[plugin_id]
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
    
    async def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if activated successfully
        """
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        
        try:
            if plugin.instance and hasattr(plugin.instance, 'activate'):
                await plugin.instance.activate()
            
            plugin.status = PluginStatus.ACTIVE
            logger.info(f"Activated plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating plugin {plugin_id}: {e}")
            plugin.status = PluginStatus.ERROR
            plugin.error = str(e)
            return False
    
    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if deactivated successfully
        """
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        
        try:
            if plugin.instance and hasattr(plugin.instance, 'deactivate'):
                await plugin.instance.deactivate()
            
            plugin.status = PluginStatus.INACTIVE
            logger.info(f"Deactivated plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_id}: {e}")
            return False
    
    async def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID"""
        return self._plugins.get(plugin_id)
    
    async def list_plugins(self, status: Optional[PluginStatus] = None) -> List[Plugin]:
        """
        List plugins.
        
        Args:
            status: Filter by status
            
        Returns:
            List of plugins
        """
        plugins = list(self._plugins.values())
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        return plugins
    
    async def register_hook(self, hook_name: str, callback: Callable):
        """
        Register a hook callback.
        
        Args:
            hook_name: Name of the hook
            callback: Callback function
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        self._hooks[hook_name].append(callback)
        logger.debug(f"Registered hook: {hook_name}")
    
    async def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all callbacks for a hook.
        
        Args:
            hook_name: Name of the hook
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            List of results from callbacks
        """
        if hook_name not in self._hooks:
            return []
        
        results = []
        for callback in self._hooks[hook_name]:
            try:
                result = await callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error calling hook {hook_name}: {e}")
        
        return results
    
    async def _get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """Get plugin configuration"""
        config_file = self.plugin_dir / plugin_id / "config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        return {}
    
    async def _set_plugin_config(self, plugin_id: str, config: Dict[str, Any]):
        """Set plugin configuration"""
        config_file = self.plugin_dir / plugin_id / "config.json"
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    async def _plugin_log(self, plugin_id: str, level: str, message: str):
        """Log from plugin"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{plugin_id}] {message}")
    
    async def install_plugin(self, plugin_package: str) -> bool:
        """
        Install a plugin from a package.
        
        Args:
            plugin_package: Plugin package path or URL
            
        Returns:
            True if installed successfully
        """
        # This would implement plugin installation from a package
        # For now, just log
        logger.info(f"Installing plugin from: {plugin_package}")
        return True
    
    async def create_plugin_template(self, plugin_id: str, name: str) -> Path:
        """
        Create a plugin template.
        
        Args:
            plugin_id: Plugin ID
            name: Plugin name
            
        Returns:
            Path to created plugin directory
        """
        plugin_path = self.plugin_dir / plugin_id
        plugin_path.mkdir(exist_ok=True)
        
        # Create plugin.json
        metadata = {
            "id": plugin_id,
            "name": name,
            "version": "0.1.0",
            "description": f"{name} plugin",
            "author": "ILLI User",
            "dependencies": [],
            "permissions": [],
            "api_version": "1.0.0",
            "category": "general"
        }
        
        with open(plugin_path / "plugin.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create main.py
        main_py = f'''"""
{name} Plugin
"""

class Plugin:
    """Plugin main class"""
    
    def __init__(self, api):
        self.api = api
        self.config = {{}}
    
    async def initialize(self):
        """Initialize the plugin"""
        await self.api.log("{plugin_id}", "info", "Plugin initialized")
        self.config = await self.api.get_config("{plugin_id}")
    
    async def activate(self):
        """Activate the plugin"""
        await self.api.log("{plugin_id}", "info", "Plugin activated")
    
    async def deactivate(self):
        """Deactivate the plugin"""
        await self.api.log("{plugin_id}", "info", "Plugin deactivated")
    
    async def cleanup(self):
        """Cleanup the plugin"""
        await self.api.log("{plugin_id}", "info", "Plugin cleaned up")
'''
        
        with open(plugin_path / "main.py", 'w') as f:
            f.write(main_py)
        
        # Create config.json
        with open(plugin_path / "config.json", 'w') as f:
            json.dump({}, f, indent=2)
        
        logger.info(f"Created plugin template: {plugin_id}")
        return plugin_path
    
    async def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin information
        """
        plugin = await self.get_plugin(plugin_id)
        if not plugin:
            return None
        
        return {
            "metadata": {
                "id": plugin.metadata.id,
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "author": plugin.metadata.author,
                "category": plugin.metadata.category
            },
            "status": plugin.status.value,
            "loaded_at": plugin.loaded_at.isoformat() if plugin.loaded_at else None,
            "error": plugin.error,
            "config": await self._get_plugin_config(plugin_id)
        }
    
    async def stop(self):
        """Stop the plugin system"""
        # Deactivate all plugins
        for plugin_id in list(self._plugins.keys()):
            await self.deactivate_plugin(plugin_id)
        
        logger.info("Plugin System stopped")


class Marketplace:
    """
    Plugin marketplace for discovering and installing plugins.
    """
    
    def __init__(self, plugin_system: PluginSystem):
        self.plugin_system = plugin_system
        self._registry: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the marketplace"""
        # Load plugin registry
        await self._load_registry()
    
    async def _load_registry(self):
        """Load plugin registry from file"""
        registry_file = Path("config/plugin_registry.json")
        
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                self._registry = json.load(f)
        else:
            # Default registry
            self._registry = {
                "example_plugin": {
                    "name": "Example Plugin",
                    "version": "1.0.0",
                    "description": "An example plugin",
                    "author": "ILLI",
                    "url": "https://github.com/illi/example-plugin",
                    "category": "example"
                }
            }
    
    async def search_plugins(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for plugins.
        
        Args:
            query: Search query
            
        Returns:
            List of matching plugins
        """
        results = []
        query_lower = query.lower()
        
        for plugin_id, plugin_info in self._registry.items():
            if (query_lower in plugin_info["name"].lower() or
                query_lower in plugin_info["description"].lower() or
                query_lower in plugin_info.get("category", "").lower()):
                results.append({
                    "id": plugin_id,
                    **plugin_info
                })
        
        return results
    
    async def list_plugins(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available plugins.
        
        Args:
            category: Filter by category
            
        Returns:
            List of plugins
        """
        plugins = []
        
        for plugin_id, plugin_info in self._registry.items():
            if category is None or plugin_info.get("category") == category:
                plugins.append({
                    "id": plugin_id,
                    **plugin_info
                })
        
        return plugins
    
    async def get_plugin_details(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin details
        """
        return self._registry.get(plugin_id)
    
    async def install_plugin(self, plugin_id: str) -> bool:
        """
        Install a plugin from the marketplace.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if installed successfully
        """
        plugin_info = await self.get_plugin_details(plugin_id)
        if not plugin_info:
            return False
        
        # Download and install plugin
        # This would implement actual download logic
        url = plugin_info.get("url")
        
        logger.info(f"Installing plugin {plugin_id} from {url}")
        
        # For now, create a template
        await self.plugin_system.create_plugin_template(
            plugin_id,
            plugin_info["name"]
        )
        
        return True
    
    async def register_plugin(self, plugin_id: str, plugin_info: Dict[str, Any]):
        """
        Register a plugin in the marketplace.
        
        Args:
            plugin_id: Plugin ID
            plugin_info: Plugin information
        """
        self._registry[plugin_id] = plugin_info
        
        # Save registry
        registry_file = Path("config/plugin_registry.json")
        registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(registry_file, 'w') as f:
            json.dump(self._registry, f, indent=2)
        
        logger.info(f"Registered plugin: {plugin_id}")
