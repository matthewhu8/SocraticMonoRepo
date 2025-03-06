"""Add name column to Test model

Revision ID: 02c5130f72dc
Revises: 
Create Date: 2025-03-05 08:33:41.518692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02c5130f72dc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('test_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_code', sa.String(), nullable=True),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('total_questions', sa.Integer(), nullable=True),
    sa.Column('correct_questions', sa.Integer(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_results_id'), 'test_results', ['id'], unique=False)
    op.create_index(op.f('ix_test_results_test_code'), 'test_results', ['test_code'], unique=False)
    op.create_index(op.f('ix_test_results_username'), 'test_results', ['username'], unique=False)
    op.create_table('tests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('questions', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tests_code'), 'tests', ['code'], unique=True)
    op.create_index(op.f('ix_tests_id'), 'tests', ['id'], unique=False)
    op.create_index(op.f('ix_tests_name'), 'tests', ['name'], unique=False)
    op.create_table('question_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('test_result_id', sa.Integer(), nullable=True),
    sa.Column('question_index', sa.Integer(), nullable=True),
    sa.Column('student_answer', sa.String(), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=True),
    sa.Column('time_spent', sa.Integer(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['test_result_id'], ['test_results.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_results_id'), 'question_results', ['id'], unique=False)
    op.create_table('chat_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_result_id', sa.Integer(), nullable=True),
    sa.Column('sender', sa.String(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['question_result_id'], ['question_results.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index(op.f('ix_question_results_id'), table_name='question_results')
    op.drop_table('question_results')
    op.drop_index(op.f('ix_tests_name'), table_name='tests')
    op.drop_index(op.f('ix_tests_id'), table_name='tests')
    op.drop_index(op.f('ix_tests_code'), table_name='tests')
    op.drop_table('tests')
    op.drop_index(op.f('ix_test_results_username'), table_name='test_results')
    op.drop_index(op.f('ix_test_results_test_code'), table_name='test_results')
    op.drop_index(op.f('ix_test_results_id'), table_name='test_results')
    op.drop_table('test_results')
    # ### end Alembic commands ###
