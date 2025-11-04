# mogno_app/compiled_protos/__init__.py

"""
Stubs para os protos compilados.
Se os protos reais não estiverem disponíveis, estas classes vazias evitam erros.
"""

class Evento:
    """Stub para evento_pb2.Evento"""
    def __init__(self):
        self.data_hora_evento = None
        self.rastreador = type('obj', (object,), {'versao_hardware': None})()
    
    def ParseFromString(self, data):
        pass

class ReportStatus:
    """Stub para maxpb_report_pb2.ReportStatus"""
    def __init__(self):
        pass
    
    def ParseFromString(self, data):
        pass

# Criar módulos fake
class evento_pb2:
    Evento = Evento

class maxpb_report_pb2:
    ReportStatus = ReportStatus
