from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class LoadDimensionOperator(BaseOperator):

    """The operator is expected to take as input a SQL statement and target
    database on which to run the query against. You must also define a target
    table that will contain the results of the transformation.

    Parameters
    ----------
    table: str
        Target table in redshift
    select_stmt: str
        SQL statement as input for insert statement     
    redshift_conn_id: str
        redshift connection id
    delete_load=True: boolean
        switch between append-only and delete-load functionality
    """
    ui_color = '#80BD9E'

    @apply_defaults
    def __init__(self,
            table,
            select_stmt,
            redshift_conn_id,
            delete_load=True,
            *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.table = table
        self.select_stmt = select_stmt
        self.redshift_conn_id = redshift_conn_id
        self.delete_load = delete_load

    def execute(self, context):
        self.log.info("Get Redshift connection")
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)

        if self.delete_load:
            self.log.info("Remove data from dimension table %s", self.table)
            redshift.run(f"TRUNCATE TABLE {self.table};")

        self.log.info("Insert data into dimension table %s", self.table)
        insert_stmt = f"""
            INSERT INTO {self.table}
            {self.select_stmt}
        """

        redshift.run(insert_stmt)
