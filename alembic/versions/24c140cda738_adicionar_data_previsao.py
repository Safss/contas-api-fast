"""adicionar data previsao

Revision ID: 24c140cda738
Revises: baef43de7869
Create Date: 2024-07-30 13:28:05.981128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24c140cda738'
down_revision: Union[str, None] = 'baef43de7869'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contas_a_pagar_e_receber', sa.Column('data_previsao', sa.DateTime(), nullable=True))
    op.execute("UPDATE contas_a_pagar_e_receber set data_previsao = now()")
    op.alter_column('contas_a_pagar_e_receber', 'data_previsao', nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('contas_a_pagar_e_receber', 'data_previsao')
    # ### end Alembic commands ###
