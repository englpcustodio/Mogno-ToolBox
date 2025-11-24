# core/credential_manager.py
import os
import json
from cryptography.fernet import Fernet
from utils.logger import adicionar_log

class CredentialManager:
    """
    Gerencia o salvamento e carregamento seguro de credenciais de login.
    Utiliza criptografia Fernet para proteger os dados.
    """
    def __init__(self, app_name="MognoToolbox"):
        self.app_name = app_name
        self.key_file = os.path.join(self._get_app_data_dir(), f"{app_name}_key.key")
        self.cred_file = os.path.join(self._get_app_data_dir(), f"{app_name}_credentials.json")
        self._key = self._load_or_generate_key()
        self._fernet = Fernet(self._key)

    def _get_app_data_dir(self):
        """Retorna o diretório de dados da aplicação (OS-agnóstico)."""
        if os.name == 'nt':  # Windows
            app_data_dir = os.path.join(os.environ['APPDATA'], self.app_name)
        else:  # Linux, macOS
            app_data_dir = os.path.join(os.path.expanduser('~'), f".{self.app_name}")

        os.makedirs(app_data_dir, exist_ok=True)
        return app_data_dir

    def _load_or_generate_key(self):
        """Carrega a chave de criptografia ou gera uma nova se não existir."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
            #adicionar_log(f"🔑 Chave de criptografia carregada de: {self.key_file}")
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            adicionar_log(f"🔑 Nova chave de criptografia gerada e salva em: {self.key_file}")
        return key

    # ========================================================
    # 🎯 Função pública para limpar credenciais via terminal
    # ========================================================
    def clear_credentials(self):
        """Limpa credenciais manualmente (uso em terminal)."""
        self._clear_credentials_file()
        adicionar_log("🧹 Credenciais apagadas manualmente pelo usuário.")

    def save_credentials(self, username, password, remember_user, remember_password):
        """Salva as credenciais criptografadas."""
        if not remember_user:
            self._clear_credentials_file()
            adicionar_log("🗑️ Credenciais não salvas (opção 'Lembrar usuário' desmarcada).")
            return

        data = {
            "username": self._fernet.encrypt(username.encode()).decode(),
            "password": self._fernet.encrypt(password.encode()).decode() if remember_password else ""
        }

        try:
            with open(self.cred_file, 'w') as f:
                json.dump(data, f)
            adicionar_log(f"💾 Credenciais salvas (usuário: {remember_user}, senha: {remember_password}).")
        except Exception as e:
            adicionar_log(f"❌ Erro ao salvar credenciais: {e}")

    def load_credentials(self):
        """Carrega e descriptografa as credenciais."""
        # -------------------------------------------
        # PRIMEIRA EXECUÇÃO — arquivo ainda não existe
        # -------------------------------------------
        if not os.path.exists(self.cred_file):
            adicionar_log("ℹ️ Nenhuma credencial salva ainda (primeira execução).")
            return "", "", False, False

        try:
            with open(self.cred_file, 'r') as f:
                data = json.load(f)

            username_enc = data.get('username', "")
            password_enc = data.get('password', "")

            username = self._fernet.decrypt(username_enc.encode()).decode() if username_enc else ""
            password = self._fernet.decrypt(password_enc.encode()).decode() if password_enc else ""

            remember_user = bool(username_enc)
            remember_password = bool(password_enc)

            adicionar_log("📂 Credenciais carregadas com sucesso.")
            return username, password, remember_user, remember_password

        except Exception as e:
            adicionar_log(f"❌ Erro ao carregar credenciais: {e}. Limpando credenciais...")
            self._clear_credentials_file()
            return "", "", False, False

    # ========================================================
    # Remove credenciais (interno)
    # ========================================================
    def _clear_credentials_file(self):
        """Remove o arquivo de credenciais sem erro se já não existir."""
        try:
            if os.path.exists(self.cred_file):
                os.remove(self.cred_file)
                adicionar_log("🗑️ Arquivo de credenciais removido.")
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao remover arquivo de credenciais: {e}")


# APAGAR AS CREDENCIAIS NO TERMINAL PYTHON:
# ACESSAR O PYTHON INTERATIVO: python
"""
from core.credential_manager import CredentialManager

manager = CredentialManager()
manager.clear_credentials()
"""