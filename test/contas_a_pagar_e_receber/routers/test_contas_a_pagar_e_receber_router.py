from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.database import Base
from shared.dependencies import get_db

client = TestClient(app)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autoflush=False, bind=engine, autocommit=False)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_deve_listar_contas_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    client.post("/contas-a-pagar-e-receber", json={'descricao': 'aluguel', 'tipo': 'PAGAR', 'valor': 1000.0, 'data_previsao': '2024-07-30'})

    response = client.get('/contas-a-pagar-e-receber')
    assert response.status_code == 200

    assert response.json() == [
         {'descricao': 'aluguel', 'id': 1, 'tipo': 'PAGAR', 'valor': 1000.0, 'fornecedor': None, 'data_previsao': '2024-07-30', 'data_baixa': None, 'valor_baixa': None, 'esta_baixada': False}
    ]


def test_deve_criar_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    nova_conta = {
        "descricao": "Curso Python",
        "valor": 11,
        "tipo": "PAGAR",
        "fornecedor": None,
        "data_baixa": None,
        "valor_baixa": None,
        "esta_baixada": False,
        'data_previsao': '2024-07-30'
    }

    nova_conta_copy = nova_conta.copy()
    nova_conta_copy['id'] = 1

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 201
    assert response.json() == nova_conta_copy


def test_deve_retornar_erro_quando_exceder_descricao():
    response = client.post("/contas-a-pagar-e-receber", json={'descricao': '123456789123456789123456789123456789123456789', 'tipo': 'PAGAR', 'valor': 1000})
    assert response.json()['detail'][0]['loc'] == ["body", "descricao"]
    assert response.status_code == 422


def test_deve_retornar_erro_quando_for_menor_descricao():
    response = client.post("/contas-a-pagar-e-receber", json={'descricao': '12', 'tipo': 'PAGAR', 'valor': 1000})
    assert response.json()['detail'][0]['loc'] == ["body", "descricao"]
    assert response.status_code == 422


def test_deve_retornar_erro_quando_o_valor_for_zero_ou_menor():
    response = client.post("/contas-a-pagar-e-receber", json={'descricao': '123', 'tipo': 'PAGAR', 'valor': 0})
    assert response.json()['detail'][0]['loc'] == ["body", "valor"]
    assert response.status_code == 422

    response = client.post("/contas-a-pagar-e-receber", json={'descricao': '123', 'tipo': 'PAGAR', 'valor': -1})
    assert response.json()['detail'][0]['loc'] == ["body", "valor"]
    assert response.status_code == 422

def test_deve_retornar_erro_quando_tipo_for_invalido():
    response = client.post("/contas-a-pagar-e-receber", json={'descricao': '123', 'tipo': 'INVALIDO', 'valor': 1000})
    assert response.json()['detail'][0]['loc'] == ["body", "tipo"]
    assert response.status_code == 422


def test_deve_atualizar_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso Python",
        "valor": 11,
        "tipo": "PAGAR",
        'data_previsao': '2024-07-30'
    })

    id_da_conta = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta}", json={
        "descricao": "Curso Python",
        "valor": 12,
        "tipo": "PAGAR",
        'data_previsao': '2024-07-30'
    })


    assert response_put.json()['valor'] == 12
    assert response_put.status_code == 200

def test_deve_remover_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso Python",
        "valor": 11,
        "tipo": "PAGAR",
        'data_previsao': '2024-07-30'
    })

    id_da_conta = response.json()['id']

    response_put = client.delete(f"/contas-a-pagar-e-receber/{id_da_conta}")

    assert response_put.status_code == 204

def test_deve_retornar_nao_encontrado_para_id_nao_existente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.get("/contas-a-pagar-e-receber/100")

    assert response.status_code == 404


def test_deve_criar_conta_a_pagar_e_receber_com_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    novo_fornecedor_cliente = {
        "nome": "Casa de musica"
    }

    client.post("/fornecedor-cliente", json=novo_fornecedor_cliente)

    nova_conta = {
        "descricao": "Curso de guitarra",
        "valor": 999,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1,
        "data_baixa": None,
        "valor_baixa": None,
        "esta_baixada": False,
        'data_previsao': '2024-07-30'
    }

    nova_conta_copy = nova_conta.copy()
    nova_conta_copy['id'] = 1
    nova_conta_copy['fornecedor'] = {
        "id": 1,
        "nome": "Casa de musica"
    }
    del nova_conta_copy['fornecedor_cliente_id']

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 201
    assert response.json() == nova_conta_copy


def test_deve_retornar_erro_ao_inserir_conta_com_fornecedor_invalido():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    nova_conta = {
        "descricao": "Curso de guitarra",
        "valor": 999,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1001,
        'data_previsao': '2024-07-30'
    }

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 422
    assert response.json()['detail'] == 'Esse fornecedor não existe'