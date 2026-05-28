"""
Security Layer
Manages permissions, sandboxing, and secure operations.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from pathlib import Path
import hashlib
from cryptography.fernet import Fernet
import secrets

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels"""
    DENY = "deny"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class ResourceType(Enum):
    """Types of resources that can be protected"""
    FILE = "file"
    DIRECTORY = "directory"
    NETWORK = "network"
    PROCESS = "process"
    SYSTEM = "system"
    MEMORY = "memory"
    CONTROL = "control"


@dataclass
class Permission:
    """A permission rule"""
    resource_type: ResourceType
    resource_path: str
    level: PermissionLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires: Optional[datetime] = None


@dataclass
class SecurityEvent:
    """A security event"""
    timestamp: datetime
    event_type: str
    resource: str
    action: str
    granted: bool
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityLayer:
    """
    Main security layer that manages permissions and secure operations.
    """
    
    def __init__(self, config_dir: str = "config/security"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._permissions: List[Permission] = []
        self._security_events: List[SecurityEvent] = []
        self._encryption_key: Optional[bytes] = None
        self._cipher: Optional[Fernet] = None
        self._safe_mode = True
        self._initialized = False
        
    async def initialize(self):
        """Initialize the security layer"""
        logger.info("Initializing Security Layer...")
        
        # Load or generate encryption key
        await self._init_encryption()
        
        # Load permissions
        await self._load_permissions()
        
        # Load security events
        await self._load_events()
        
        self._initialized = True
        logger.info("Security Layer initialized")
    
    async def _init_encryption(self):
        """Initialize encryption"""
        key_file = self.config_dir / "encryption.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            self._encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
            key_file.chmod(0o600)  # Restrict permissions
        
        self._cipher = Fernet(self._encryption_key)
        logger.info("Encryption initialized")
    
    async def _load_permissions(self):
        """Load permissions from file"""
        perm_file = self.config_dir / "permissions.json"
        
        if perm_file.exists():
            with open(perm_file, 'r') as f:
                data = json.load(f)
                self._permissions = [
                    Permission(
                        resource_type=ResourceType(p['resource_type']),
                        resource_path=p['resource_path'],
                        level=PermissionLevel(p['level']),
                        conditions=p.get('conditions', {}),
                        expires=datetime.fromisoformat(p['expires']) if p.get('expires') else None
                    )
                    for p in data
                ]
            logger.info(f"Loaded {len(self._permissions)} permissions")
        else:
            # Default permissions
            await self._set_default_permissions()
    
    async def _set_default_permissions(self):
        """Set default security permissions"""
        # Allow read access to most directories
        self._permissions = [
            Permission(
                resource_type=ResourceType.FILE,
                resource_path="*",
                level=PermissionLevel.READ
            ),
            Permission(
                resource_type=ResourceType.DIRECTORY,
                resource_path="*",
                level=PermissionLevel.READ
            ),
            Permission(
                resource_type=ResourceType.CONTROL,
                resource_path="*",
                level=PermissionLevel.DENY
            )
        ]
        await self._save_permissions()
    
    async def _save_permissions(self):
        """Save permissions to file"""
        perm_file = self.config_dir / "permissions.json"
        
        data = [
            {
                "resource_type": p.resource_type.value,
                "resource_path": p.resource_path,
                "level": p.level.value,
                "conditions": p.conditions,
                "expires": p.expires.isoformat() if p.expires else None
            }
            for p in self._permissions
        ]
        
        with open(perm_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _load_events(self):
        """Load security events from file"""
        event_file = self.config_dir / "events.json"
        
        if event_file.exists():
            with open(event_file, 'r') as f:
                data = json.load(f)
                self._security_events = [
                    SecurityEvent(
                        timestamp=datetime.fromisoformat(e['timestamp']),
                        event_type=e['event_type'],
                        resource=e['resource'],
                        action=e['action'],
                        granted=e['granted'],
                        reason=e.get('reason'),
                        metadata=e.get('metadata', {})
                    )
                    for e in data
                ]
    
    async def _save_events(self):
        """Save security events to file"""
        event_file = self.config_dir / "events.json"
        
        data = [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "resource": e.resource,
                "action": e.action,
                "granted": e.granted,
                "reason": e.reason,
                "metadata": e.metadata
            }
            for e in self._security_events[-1000:]  # Keep last 1000 events
        ]
        
        with open(event_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def check_permission(self, resource_type: ResourceType, 
                               resource_path: str, 
                               action: str) -> tuple[bool, Optional[str]]:
        """
        Check if an action is permitted.
        
        Args:
            resource_type: Type of resource
            resource_path: Path to resource
            action: Action to perform
            
        Returns:
            Tuple of (granted, reason)
        """
        if self._safe_mode:
            # In safe mode, require explicit approval for dangerous actions
            if action in ['delete', 'format', 'execute', 'control']:
                event = SecurityEvent(
                    timestamp=datetime.now(),
                    event_type="permission_check",
                    resource=resource_path,
                    action=action,
                    granted=False,
                    reason="Safe mode enabled - requires explicit approval"
                )
                self._security_events.append(event)
                await self._save_events()
                return False, "Safe mode enabled - requires explicit approval"
        
        # Check permissions
        for perm in self._permissions:
            if self._matches_permission(perm, resource_type, resource_path):
                if perm.level == PermissionLevel.DENY:
                    event = SecurityEvent(
                        timestamp=datetime.now(),
                        event_type="permission_denied",
                        resource=resource_path,
                        action=action,
                        granted=False,
                        reason="Permission denied"
                    )
                    self._security_events.append(event)
                    await self._save_events()
                    return False, "Permission denied"
                
                if perm.level == PermissionLevel.READ and action in ['write', 'delete', 'execute']:
                    event = SecurityEvent(
                        timestamp=datetime.now(),
                        event_type="permission_denied",
                        resource=resource_path,
                        action=action,
                        granted=False,
                        reason="Read-only permission"
                    )
                    self._security_events.append(event)
                    await self._save_events()
                    return False, "Read-only permission"
                
                if perm.level == PermissionLevel.WRITE and action in ['delete', 'execute']:
                    event = SecurityEvent(
                        timestamp=datetime.now(),
                        event_type="permission_denied",
                        resource=resource_path,
                        action=action,
                        granted=False,
                        reason="Write-only permission"
                    )
                    self._security_events.append(event)
                    await self._save_events()
                    return False, "Write-only permission"
        
        # Permission granted
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type="permission_granted",
            resource=resource_path,
            action=action,
            granted=True
        )
        self._security_events.append(event)
        await self._save_events()
        return True, None
    
    def _matches_permission(self, perm: Permission, resource_type: ResourceType, 
                            resource_path: str) -> bool:
        """Check if a permission matches the resource"""
        if perm.resource_type != resource_type:
            return False
        
        # Simple wildcard matching
        if perm.resource_path == "*":
            return True
        
        if perm.resource_path in resource_path:
            return True
        
        return False
    
    async def grant_permission(self, resource_type: ResourceType, 
                               resource_path: str, 
                               level: PermissionLevel,
                               expires: Optional[datetime] = None):
        """
        Grant a permission.
        
        Args:
            resource_type: Type of resource
            resource_path: Path to resource
            level: Permission level
            expires: Optional expiration time
        """
        # Remove existing permission for this resource
        self._permissions = [
            p for p in self._permissions
            if not (p.resource_type == resource_type and p.resource_path == resource_path)
        ]
        
        # Add new permission
        perm = Permission(
            resource_type=resource_type,
            resource_path=resource_path,
            level=level,
            expires=expires
        )
        self._permissions.append(perm)
        
        await self._save_permissions()
        logger.info(f"Granted {level.value} permission for {resource_type.value}:{resource_path}")
    
    async def revoke_permission(self, resource_type: ResourceType, resource_path: str):
        """
        Revoke a permission.
        
        Args:
            resource_type: Type of resource
            resource_path: Path to resource
        """
        self._permissions = [
            p for p in self._permissions
            if not (p.resource_type == resource_type and p.resource_path == resource_path)
        ]
        
        await self._save_permissions()
        logger.info(f"Revoked permission for {resource_type.value}:{resource_path}")
    
    async def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        if not self._cipher:
            raise RuntimeError("Encryption not initialized")
        
        return self._cipher.encrypt(data)
    
    async def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        if not self._cipher:
            raise RuntimeError("Encryption not initialized")
        
        return self._cipher.decrypt(encrypted_data)
    
    async def encrypt_string(self, text: str) -> str:
        """
        Encrypt a string.
        
        Args:
            text: Text to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        import base64
        encrypted = await self.encrypt(text.encode())
        return base64.b64encode(encrypted).decode()
    
    async def decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted_text: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted string
        """
        import base64
        encrypted = base64.b64decode(encrypted_text.encode())
        decrypted = await self.decrypt(encrypted)
        return decrypted.decode()
    
    def set_safe_mode(self, enabled: bool):
        """
        Enable or disable safe mode.
        
        Args:
            enabled: Whether to enable safe mode
        """
        self._safe_mode = enabled
        logger.info(f"Safe mode {'enabled' if enabled else 'disabled'}")
    
    def is_safe_mode(self) -> bool:
        """Check if safe mode is enabled"""
        return self._safe_mode
    
    async def get_security_events(self, limit: int = 100) -> List[SecurityEvent]:
        """
        Get security events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of security events
        """
        return self._security_events[-limit:]
    
    async def get_permissions(self) -> List[Permission]:
        """Get all permissions"""
        return self._permissions.copy()
    
    async def audit_access(self, resource: str, action: str, 
                          user: str = "system") -> Dict[str, Any]:
        """
        Perform an access audit.
        
        Args:
            resource: Resource being accessed
            action: Action being performed
            user: User performing the action
            
        Returns:
            Audit result
        """
        # Log audit event
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type="audit",
            resource=resource,
            action=action,
            granted=True,
            metadata={"user": user}
        )
        self._security_events.append(event)
        await self._save_events()
        
        return {
            "timestamp": event.timestamp.isoformat(),
            "resource": resource,
            "action": action,
            "user": user,
            "safe_mode": self._safe_mode,
            "status": "logged"
        }
    
    async def generate_token(self, purpose: str, expires_hours: int = 24) -> str:
        """
        Generate a secure token.
        
        Args:
            purpose: Purpose of the token
            expires_hours: Token expiration in hours
            
        Returns:
            Secure token
        """
        token_data = {
            "purpose": purpose,
            "expires": (datetime.now().timestamp() + expires_hours * 3600),
            "random": secrets.token_hex(32)
        }
        
        token_string = json.dumps(token_data)
        encrypted = await self.encrypt_string(token_string)
        
        logger.info(f"Generated token for purpose: {purpose}")
        return encrypted
    
    async def validate_token(self, token: str, purpose: str) -> bool:
        """
        Validate a token.
        
        Args:
            token: Token to validate
            purpose: Expected purpose
            
        Returns:
            True if token is valid
        """
        try:
            decrypted = await self.decrypt_string(token)
            token_data = json.loads(decrypted)
            
            if token_data["purpose"] != purpose:
                return False
            
            if datetime.now().timestamp() > token_data["expires"]:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    async def stop(self):
        """Stop the security layer"""
        await self._save_events()
        logger.info("Security Layer stopped")


class Sandbox:
    """
    Provides sandboxed execution environment.
    """
    
    def __init__(self, security_layer: SecurityLayer):
        self.security_layer = security_layer
        self._active_sandboxes: Dict[str, Dict[str, Any]] = {}
        
    async def create_sandbox(self, sandbox_id: str, 
                            allowed_paths: List[str] = None,
                            network_access: bool = False) -> bool:
        """
        Create a sandboxed environment.
        
        Args:
            sandbox_id: Unique sandbox identifier
            allowed_paths: List of allowed file paths
            network_access: Whether to allow network access
            
        Returns:
            True if sandbox created successfully
        """
        self._active_sandboxes[sandbox_id] = {
            "allowed_paths": allowed_paths or [],
            "network_access": network_access,
            "created_at": datetime.now(),
            "processes": []
        }
        
        logger.info(f"Created sandbox: {sandbox_id}")
        return True
    
    async def execute_in_sandbox(self, sandbox_id: str, 
                                 command: str) -> Dict[str, Any]:
        """
        Execute a command within a sandbox.
        
        Args:
            sandbox_id: Sandbox identifier
            command: Command to execute
            
        Returns:
            Execution result
        """
        if sandbox_id not in self._active_sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        
        sandbox = self._active_sandboxes[sandbox_id]
        
        # Check security
        granted, reason = await self.security_layer.check_permission(
            ResourceType.PROCESS,
            command,
            "execute"
        )
        
        if not granted:
            return {"success": False, "error": reason}
        
        # In a real implementation, this would use actual sandboxing
        # For now, simulate execution
        logger.info(f"Executing in sandbox {sandbox_id}: {command}")
        
        return {
            "success": True,
            "output": f"[SANDBOX] Executed: {command}",
            "sandbox_id": sandbox_id
        }
    
    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """
        Destroy a sandbox.
        
        Args:
            sandbox_id: Sandbox identifier
            
        Returns:
            True if sandbox destroyed successfully
        """
        if sandbox_id in self._active_sandboxes:
            del self._active_sandboxes[sandbox_id]
            logger.info(f"Destroyed sandbox: {sandbox_id}")
            return True
        
        return False
    
    def get_active_sandboxes(self) -> List[str]:
        """Get list of active sandbox IDs"""
        return list(self._active_sandboxes.keys())
