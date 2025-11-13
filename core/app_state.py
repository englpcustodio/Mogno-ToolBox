# mogno_app/core/app_state.py

from typing import Any, Dict, Optional
from threading import RLock
from datetime import datetime

class AppState:
    """
    Estado global da aplicação, thread-safe.
    Usa RLock para garantir operações atômicas onde necessário.
    """

    def __init__(self):
        self._lock = RLock()
        self._state: Dict[str, Any] = {
            "executando_requisicoes": False,
            "tempo_inicio_requisicoes": None,
            "jwt_token": None,
            "user_login": None,
            "user_id": None,
            "token_expiry": None,
            "cookie_dict": None,
            "serials_carregados": [],
            "csv_filepath": None,
            "dados_atuais": {},
            "scheduler": None,
            "active_requests_count": 0
        }

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            return self._state.get(key)

    def __setitem__(self, key: str, value: Any):
        with self._lock:
            self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def set(self, key: str, value: Any):
        with self._lock:
            self._state[key] = value

    def increment_active_requests(self):
        with self._lock:
            self._state["active_requests_count"] += 1
            return self._state["active_requests_count"]

    def decrement_active_requests(self):
        with self._lock:
            self._state["active_requests_count"] -= 1
            if self._state["active_requests_count"] < 0:
                self._state["active_requests_count"] = 0
            return self._state["active_requests_count"]

    def get_active_requests_count(self) -> int:
        with self._lock:
            return int(self._state["active_requests_count"])

    def set_jwt_token(self, token: str, expiry: Optional[datetime] = None):
        with self._lock:
            self._state["jwt_token"] = token
            self._state["token_expiry"] = expiry

    def get_jwt_token(self) -> Optional[str]:
        with self._lock:
            return self._state["jwt_token"]

    def get_token_expiry(self) -> Optional[datetime]:
        with self._lock:
            return self._state["token_expiry"]

    def set_user_info(self, login: str, user_id: str):
        with self._lock:
            self._state["user_login"] = login
            self._state["user_id"] = user_id

    def get_user_info(self):
        with self._lock:
            return self._state["user_login"], self._state["user_id"]

    def add_dados_atuais(self, chave: str, dados: Any):
        with self._lock:
            self._state["dados_atuais"][chave] = dados

    def get_dados_atuais(self, chave: str) -> Any:
        with self._lock:
            return self._state["dados_atuais"].get(chave)

    def get_all_dados_atuais(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state["dados_atuais"])

    def clear_dados_atuais(self):
        with self._lock:
            self._state["dados_atuais"].clear()

    def get_state_dict(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)
