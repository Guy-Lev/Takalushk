from alembic.operations import Operations, MigrateOperation

from app.migrations.operators.operators import build_condition


@Operations.register_operation("model_delete")
class DeleteOP(MigrateOperation):

    def __init__(self, table_cls, data):
        self.tablecls=table_cls
        self.data=data

    @classmethod
    def model_delete(cls, operations, table, data):
        operator = DeleteOP(table, data)
        return operations.invoke(operator)

    def build_sql(self, data):
        condition = build_condition(data)
        return "Delete from {table} where {condition}".format(table=self.tablecls.__table__, condition=condition)


@Operations.implementation_for(DeleteOP)
def model_delete(operations, operation):
    for data in operation.data:
        operations.execute(operation.build_sql(data))
