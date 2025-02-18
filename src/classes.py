from dataclasses import dataclass
from typing import List, Optional



## config toml classes
@dataclass
class RepoConfig:
    cache_path: str
    remote_url: str
    branch: str
    force_clone: bool = False # Set to True to wipe local cache and force new clone on startup
    desc: Optional[str] = None
    last_updated: Optional[int] = 0
    latest_commit: Optional[str] = None

@dataclass
class Config:
    sync_interval: int
    enable_status_server: bool = False
    status_server_port: int = 8000
    repos: Optional[List[RepoConfig]] = None
    use_bootstrap: bool = False