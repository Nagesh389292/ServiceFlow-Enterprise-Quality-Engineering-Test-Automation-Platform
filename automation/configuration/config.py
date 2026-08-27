import os
import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """Environment configuration manager reading configuration from test_config.yaml."""

    def __init__(self, env: str = None):
        if not env:
            env = os.getenv("ENV", os.getenv("ENVIRONMENT", "local")).lower()

        self.env_name = env
        config_path = Path(__file__).parent / "test_config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            all_configs = yaml.safe_load(f)

        if env not in all_configs:
            raise KeyError(f"Environment '{env}' not defined in {config_path}. Available: {list(all_configs.keys())}")

        self._config: Dict[str, Any] = all_configs[env]

        # Environment variable overrides
        self.base_url = os.getenv("BASE_URL", self._config.get("base_url"))
        self.api_url = os.getenv("API_URL", self._config.get("api_url"))
        self.db_host = os.getenv("DB_HOST", self._config.get("db_host"))
        self.db_port = int(os.getenv("DB_PORT", self._config.get("db_port", 5432)))
        self.db_name = os.getenv("DB_NAME", self._config.get("db_name"))
        self.db_user = os.getenv("DB_USER", self._config.get("db_user"))
        self.db_password = os.getenv("DB_PASSWORD", self._config.get("db_password"))
        self.browser = os.getenv("BROWSER", self._config.get("browser", "chrome"))
        
        headless_env = os.getenv("HEADLESS")
        if headless_env is not None:
            self.headless = headless_env.lower() in ("true", "1", "yes")
        else:
            self.headless = bool(self._config.get("headless", False))

        self.explicit_wait = int(self._config.get("explicit_wait", 10))
        self.implicit_wait = int(self._config.get("implicit_wait", 0))

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
