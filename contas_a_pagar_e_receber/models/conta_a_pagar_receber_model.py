from shared.database import Base

from sqlalchemy import Boolean, Column, Date, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship

class ContaPagarReceber(Base):
    __tablename__ = "contas_a_pagar_e_receber"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(30))
    valor = Column(Numeric)
    tipo = Column(String(30))
    data_previsao = Column(Date(), nullable = False)
    data_baixa = Column(Date())
    valor_baixa = Column(Numeric)
    esta_baixada = Column(Boolean, default=False)
    fornecedor_cliente_id = Column(Integer, ForeignKey("fornecedor_cliente.id"))
    fornecedor = relationship("FornecedorCliente")