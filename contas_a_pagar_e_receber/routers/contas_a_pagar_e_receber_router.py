from datetime import date
from typing import List, OrderedDict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import extract
from sqlalchemy.orm import Session

from contas_a_pagar_e_receber.models.conta_a_pagar_receber_model import ContaPagarReceber
from contas_a_pagar_e_receber.models.fornecedor_cliente_model import FornecedorCliente
from contas_a_pagar_e_receber.routers.fornecedor_cliente_router import FornecedorClienteResponse
from shared.dependencies import get_db
from enum import Enum

from shared.exceptions import NotFound

router = APIRouter(prefix="/contas-a-pagar-e-receber")

class ContaPagarReceberTipoEnum(str, Enum):
    PAGAR = 'PAGAR'
    RECEBER = 'RECEBER'


class ContaPagarReceberResponse(BaseModel):
    id: int
    descricao: str
    valor: int
    tipo: str
    data_previsao: date
    fornecedor: FornecedorClienteResponse | None = None
    data_baixa: date | None = None
    valor_baixa: int | None = None
    esta_baixada: bool | None = None

    class Config:
        orm_mode = True

class ContaPagarReceberRequest(BaseModel):
    descricao: str = Field(min_length=3, max_length=30)
    valor: int = Field(gt=0)
    tipo: ContaPagarReceberTipoEnum
    fornecedor_cliente_id: int | None = None
    data_previsao: date

class PrevisaoPorMes(BaseModel):
    mes: int
    valor_total: int


@router.get("", response_model=List[ContaPagarReceberResponse])
def listar_contas(db: Session = Depends(get_db)) -> List[ContaPagarReceberResponse]:
    return db.query(ContaPagarReceber).all()


@router.get("/previsao-gastos-do-mes", response_model=List[PrevisaoPorMes])
def previsao_de_gastos_por_mes(db: Session = Depends(get_db), ano = date.today().year) -> List[PrevisaoPorMes]:
    return relatorio_gastos_previstos_por_mes_de_um_ano(db, ano)


@router.get("/{id_da_conta_a_pagar_e_receber}", response_model=ContaPagarReceberResponse)
def listar_contas_por_id(id_da_conta_a_pagar_e_receber: int ,db: Session = Depends(get_db)) -> ContaPagarReceberResponse:
    conta_a_pagar_e_receber: ContaPagarReceber = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)
    return conta_a_pagar_e_receber

@router.post("", response_model=ContaPagarReceberResponse, status_code=201)
def criar_conta(conta: ContaPagarReceberRequest, db: Session = Depends(get_db)) -> ContaPagarReceberResponse:

    _valida_fornecedor(conta.fornecedor_cliente_id, db)

    lanca_excecao_ultrapassa_registros(conta, db)

    contas_a_pagar_receber = ContaPagarReceber(
        **conta.dict()
    )


    db.add(contas_a_pagar_receber)
    db.commit()
    db.refresh(contas_a_pagar_receber)

    return contas_a_pagar_receber

def _valida_fornecedor(fornecedor_cliente_id, db):
    if fornecedor_cliente_id is not None:
        fornecedor = db.query(FornecedorCliente).get(fornecedor_cliente_id)
        if fornecedor is None:
            raise HTTPException(status_code=422, detail="Esse fornecedor não existe")

@router.put("/{id_da_conta_a_pagar_e_receber}", response_model=ContaPagarReceberResponse, status_code=200)
def atualizar_conta(id_da_conta_a_pagar_e_receber: int , conta: ContaPagarReceberRequest, db: Session = Depends(get_db)) -> ContaPagarReceberResponse:
    
    _valida_fornecedor(conta.fornecedor_cliente_id, db)
    conta_a_pagar_e_receber: ContaPagarReceber = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)
    conta_a_pagar_e_receber.tipo = conta.tipo
    conta_a_pagar_e_receber.descricao = conta.descricao
    conta_a_pagar_e_receber.valor = conta.valor
    conta_a_pagar_e_receber.fornecedor_cliente_id = conta.fornecedor_cliente_id

    db.add(conta_a_pagar_e_receber)
    db.commit()
    db.refresh(conta_a_pagar_e_receber)
    return conta_a_pagar_e_receber

@router.delete("/{id_da_conta_a_pagar_e_receber}", status_code=204)
def deletar_conta(id_da_conta_a_pagar_e_receber: int , db: Session = Depends(get_db)) -> None:
    
    conta = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)
    db.delete(conta)
    db.commit()


@router.post("/{id_da_conta_a_pagar_e_receber}/baixar", response_model=ContaPagarReceberResponse, status_code=200)
def baixar_conta(id_da_conta_a_pagar_e_receber: int , db: Session = Depends(get_db)) -> ContaPagarReceberResponse:
    
    conta_a_pagar_e_receber: ContaPagarReceber = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)

    if conta_a_pagar_e_receber.esta_baixada and conta_a_pagar_e_receber.valor == conta_a_pagar_e_receber.valor_baixa:
        return
    
    conta_a_pagar_e_receber.data_baixa = date.today()
    conta_a_pagar_e_receber.esta_baixada = True
    conta_a_pagar_e_receber.valor_baixa = conta_a_pagar_e_receber.valor

    db.add(conta_a_pagar_e_receber)
    db.commit()
    db.refresh(conta_a_pagar_e_receber)
    return conta_a_pagar_e_receber

def busca_conta_por_id(id_da_conta_a_pagar_e_receber: int, db: Session) -> ContaPagarReceber:
    conta_a_pagar_e_receber = db.query(ContaPagarReceber).get(id_da_conta_a_pagar_e_receber)
    if conta_a_pagar_e_receber is None:
        raise NotFound("conta a pagar e receber")
    
    return conta_a_pagar_e_receber


def lanca_excecao_ultrapassa_registros(conta: ContaPagarReceberRequest, db: Session) -> None:
    if (valida_se_pode_registrar_novas_contas(db, conta.data_previsao.year, conta.data_previsao.month)):
        raise HTTPException(status_code=422, detail="Voce nao pode mais cadastrar contas")


def valida_se_pode_registrar_novas_contas(db, year, month) -> bool:
    if recupera_numero_registros(db, year, month) >= 100:
        return True
    
    return False


def recupera_numero_registros(db, year, month) -> int:
    quantidade_registro = db.query(ContaPagarReceber).filter(extract('year', ContaPagarReceber.data_previsao) == year).filter(extract('month', ContaPagarReceber.data_previsao) == month).count()
    return quantidade_registro



def relatorio_gastos_previstos_por_mes_de_um_ano(db, year) -> List[PrevisaoPorMes]:
    contas_do_ano = db.query(ContaPagarReceber).filter(extract('year', ContaPagarReceber.data_previsao) == year).filter(ContaPagarReceber.tipo == ContaPagarReceberTipoEnum.PAGAR).order_by(ContaPagarReceber.data_previsao).all()

    valor_por_mes = OrderedDict()

    for conta_do_ano in contas_do_ano:
        mes = conta_do_ano.data_previsao.month
        valor = conta_do_ano.valor

        if valor_por_mes.get(mes) is None:
            valor_por_mes[mes] = valor

        valor_por_mes[mes] +=valor

    return [PrevisaoPorMes(mes=k, valor_total=v) for k, v in valor_por_mes.items()]