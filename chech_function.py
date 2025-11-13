import os, importlib.util, sys

path = r"C:\Users\luis.custodio\Desktop\Mogno_ToolBox\reports\report_last_position_redis.py"
print(f"📄 Lendo diretamente: {path}\n")

if not os.path.exists(path):
    print("❌ Arquivo não encontrado nesse caminho!")
    sys.exit(1)

# Mostra as 30 primeiras linhas reais do arquivo em disco
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=== Primeiras linhas reais no disco ===")
for i, line in enumerate(lines[:30], 1):
    print(f"{i:02d}| {line.rstrip()}")

print("\n=== Carregando via importlib ===")
spec = importlib.util.spec_from_file_location("manual_report_module", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("📦 Módulo carregado de:", mod.__file__)
print("Funções definidas:", [n for n in dir(mod) if not n.startswith('__')])
print("Tem gerar_relatorio?:", hasattr(mod, "gerar_relatorio"))
