from alembic.operations import Operations, MigrateOperation

from app.migrations.operators.operators import build_condition


@Operations.register_operation("model_update")
class UpdateOP(MigrateOperation):

    def __init__(self, table_cls, data):
        self.tablecls=table_cls
        self.data=data

    @classmethod
    def model_update(cls, operations, table, data):
        operator = UpdateOP(table, data)
        return operations.invoke(operator)

    def build_sql(self, data):
        update_cols = " , ".join("{col}='{value}'".format(col=col, value=value) for col,value in data["update_cols"].items())
        condition = build_condition(data["key"])
        return "Update {table} set {update_cols} where {condition}".format(table=self.tablecls.__table__, update_cols=update_cols, condition=condition)


@Operations.implementation_for(UpdateOP)
def model_update(operations, operation):
    for data in operation.data:
        operations.execute(operation.build_sql(data))
