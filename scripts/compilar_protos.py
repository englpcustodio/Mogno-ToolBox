import os
import subprocess

# Diretório onde estão os arquivos .proto
PROTO_DIR = 'protos'
COMPILED_DIR = 'compiled_protos'

# Função para compilar todos os arquivos .proto na pasta especificada
def compilar_protos(diretorio_origem,diretorio_destino):
    print(f"Compilando arquivos .proto de {diretorio_origem}...")
    for arquivo in os.listdir(diretorio_origem):
        if arquivo.endswith(".proto"):
            caminho_completo = os.path.join(diretorio_origem, arquivo)
            subprocess.run(['C:\\protobuf\\bin\\protoc', '--proto_path=' + diretorio_origem, '--python_out=' + diretorio_destino, caminho_completo])
            print(f"Compilação concluída para {arquivo}")

# Compila os protos
compilar_protos(PROTO_DIR,COMPILED_DIR)