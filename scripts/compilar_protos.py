import os
import subprocess
import shutil
import sys

PROTO_DIR = 'protos'
COMPILED_DIR = 'compiled_protos'


def localizar_protoc():
    """
    Localiza o executável do protoc.
    """
    path_protoc = shutil.which('protoc')
    if path_protoc:
        print(f"✅ 'protoc' encontrado no PATH: {path_protoc}")
        return path_protoc

    caminhos_comuns = [
        r"C:\protobuf\bin\protoc.exe",
        r"C:\Program Files\protobuf\bin\protoc.exe",
        r"C:\Program Files (x86)\protobuf\bin\protoc.exe"
    ]
    for caminho in caminhos_comuns:
        if os.path.isfile(caminho):
            print(f"✅ 'protoc' encontrado em caminho comum: {caminho}")
            return caminho

    print("❌ Não foi possível localizar o executável 'protoc'.")
    sys.exit(1)


def listar_arquivos_proto(diretorio):
    """
    Lista todos os arquivos .proto encontrados (recursivamente).
    """
    print(f"📂 Procurando arquivos .proto em: {os.path.abspath(diretorio)}")
    encontrados = []
    for raiz, _, arquivos in os.walk(diretorio):
        for arquivo in arquivos:
            if arquivo.endswith(".proto"):
                caminho = os.path.join(raiz, arquivo)
                encontrados.append(caminho)
                print(f"  🔹 Encontrado: {caminho}")
    if not encontrados:
        print("⚠️ Nenhum arquivo .proto encontrado!")
    return encontrados


def limpar_destino(destino):
    """
    Remove arquivos .py antigos na pasta de destino.
    """
    os.makedirs(destino, exist_ok=True)
    for arquivo in os.listdir(destino):
        if arquivo.endswith('.py'):
            os.remove(os.path.join(destino, arquivo))
            print(f"🧹 Removido antigo: {arquivo}")


def compilar_protos():
    """
    Compila os .proto em .py e cria o pacote Python.
    """
    protoc = localizar_protoc()
    limpar_destino(COMPILED_DIR)

    arquivos_proto = listar_arquivos_proto(PROTO_DIR)
    if not arquivos_proto:
        print("❌ Nenhum arquivo .proto encontrado. Abortando.")
        sys.exit(1)

    print("\n🚀 Iniciando compilação dos protos...\n")

    for caminho_proto in arquivos_proto:
        print(f"▶️ Compilando: {caminho_proto}")
        comando = [
            protoc,
            f'--proto_path={PROTO_DIR}',
            f'--python_out={COMPILED_DIR}',
            caminho_proto
        ]
        print(f"   Comando: {' '.join(comando)}")

        try:
            resultado = subprocess.run(
                comando,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"   ✅ Compilado com sucesso: {os.path.basename(caminho_proto)}")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ ERRO ao compilar {caminho_proto}")
            print(f"   STDOUT: {e.stdout}")
            print(f"   STDERR: {e.stderr}")

    init_path = os.path.join(COMPILED_DIR, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write("# Pacote de protos compilados\n")
        print(f"📦 Criado: {init_path}")
    else:
        print(f"📦 Já existe: {init_path}")

    print("\n🔍 Verificando importações geradas...\n")
    for arquivo in os.listdir(COMPILED_DIR):
        if arquivo.endswith('_pb2.py'):
            caminho = os.path.join(COMPILED_DIR, arquivo)
            with open(caminho, 'r', encoding='utf-8') as f:
                linhas = f.read().splitlines()
            for linha in linhas[:40]:  # só as primeiras linhas
                if "import rev_geo_pb2" in linha or "from . import rev_geo_pb2" in linha:
                    print(f"   📘 {arquivo}: {linha}")


if __name__ == "__main__":
    print("🔧 Iniciando verificação e compilação...\n")
    compilar_protos()
    print("\n🏁 Processo concluído.")
