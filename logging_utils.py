"""Logger simples para automacoes desktop."""

import os
from datetime import datetime


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


class Logger:
    """Centraliza logs na interface, console e arquivo."""

    def __init__(self, log_callback=None):
        self.logs = []
        self.log_callback = log_callback
        self.log_file = None

    def set_log_file(self, path):
        self.log_file = path
        if not path:
            return

        pasta = os.path.dirname(path)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

        with open(path, "a", encoding="utf-8") as arquivo:
            arquivo.write("=" * 80 + "\n")
            arquivo.write(f"Inicio da automacao: {datetime.now():%d/%m/%Y %H:%M:%S}\n")
            arquivo.write("=" * 80 + "\n")

    def log(self, mensagem, tipo="INFO"):
        entrada = f"[{_ts()}] [{tipo}] {mensagem}"
        self.logs.append(entrada)

        if self.log_callback:
            self.log_callback(entrada, tipo)

        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as arquivo:
                    arquivo.write(entrada + "\n")
            except Exception:
                pass

        print(entrada)

    def get_logs(self):
        return "\n".join(self.logs)
