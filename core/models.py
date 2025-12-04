# core/models.py

from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Produto(Base):
    __tablename__ = "produtos"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    nome = Column(String, index=True)
    preco = Column(Float)
    estoque = Column(Integer, default=0)

    # Representação Python do objeto para debug
    def __repr__(self):
        return f"<Produto(nome='{self.nome}', preco={self.preco:.2f})>"