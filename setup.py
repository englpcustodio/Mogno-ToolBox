from setuptools import setup, find_packages

# Arquivo para rodar meu projeto como um módulo instalável dentro do meu ambiente virtual (venv)

# instalar com o comando: 
# pip install -e .
# -e para atualizar todas as edições futuras, sem a necessidade de rodar o comando novamente
# Para visualizar o projeto como módulo:
# pip list
# verificar o nome do pacote: "Mogno_ToolBox 0.0.0" e o caminho do projeto 

setup(
    name = "Mogno_ToolBox",
    packages = find_packages(),
)