from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class DataQualityOperator(BaseOperator):

    """The operator is expected to take as input a SQL statement and target
    database on which to run the query against. You must also define a target
    table that will contain the results of the transformation.

    Parameters
    ----------
    test_stmt: str
        SQL statement to run in redshift
    expected: int
        Expected result that matches the return value of test_stmt
    redshift_conn_id: str
        redshift connection id
    """
    ui_color = '#89DA59'

    @apply_defaults
    def __init__(self,
            test_stmt,
            expected,
            redshift_conn_id,
            *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.test_stmt = test_stmt
        self.expected = expected
        self.redshift_conn_id = redshift_conn_id

    def execute(self, context):
        self.log.info("Get Redshift connection")
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)

        self.log.info("Running test statement")
        records = redshift.get_records(self.test_stmt)
        if len(records) < 1 or len(records[0]) < 1:
            raise ValueError(f"Data quality check failed. Test query returned no results")

        num_records = records[0][0]
        if num_records != self.expected:
            msg = f"Check failed. Expected {self.expected} rows, but got {num_records}."
            raise ValueError(msg)

        self.log.info("Data quality check passed")
