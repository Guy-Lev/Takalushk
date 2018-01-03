from alembic import op
from alembic.operations import Operations, MigrateOperation
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import table
from sqlalchemy.sql.schema import Column


@Operations.register_operation("model_insert")
class InsertOP(MigrateOperation):

    def __init__(self, table_cls, data):
        self.tablecls=table_cls
        self.data=data

    @classmethod
    def model_insert(cls, operations, table, data):
        operator = InsertOP(table, data)
        return operations.invoke(operator)

    def fill_data(self,data):
        item = self.tablecls()
        item.__dict__.update(data)
        return item

    def get_table(self):
        cols = [col for col in vars(self.tablecls).values() if isinstance(col, InstrumentedAttribute)]
        return table(self.tablecls.__tablename__, *cols)


@Operations.implementation_for(InsertOP)
def model_insert(operations, operation):
    op.bulk_insert(operation.get_table(), operation.data)
