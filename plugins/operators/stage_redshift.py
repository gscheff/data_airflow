from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook


class StageToRedshiftOperator(BaseOperator):

    """The stage operator loads any JSON formatted files from S3 to Amazon
    Redshift. The operator creates and runs a SQL COPY statement based on the
    parameters provided. The parameters should specify where in S3 the file is
    loaded and what is the target table.

    Parameters
    ----------
    redshift_conn_id: airfow connection
        redshift connection id
    aws_conn_id: airfow connection
        aws connection id
    table: str
        Target table in redshift
    s3_bucket: str
        s3 bucket with json source data
    s3_key: str
        Path in s3 to json source files
    aws_region: str
        aws aws_region of s3 bucket
    json_option: str
        Map the data elements in the JSON source data to the columns in the
        target table. Valid values for json_option are as follows:
            - 'auto'
            - 's3://jsonpaths_file'

    """

    ui_color = '#358140'
    template_fields = ("s3_key",)
    copy_sql = """
        COPY {}
        FROM '{}'
        ACCESS_KEY_ID '{}'
        SECRET_ACCESS_KEY '{}'
        REGION AS '{}'
        FORMAT as json '{}'
    """

    @apply_defaults
    def __init__(self,
             redshift_conn_id,
             aws_conn_id,
             table,
             s3_bucket,
             s3_key,
             aws_region,
             json_option,
             *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.redshift_conn_id = redshift_conn_id
        self.aws_conn_id = aws_conn_id
        self.table = table
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.aws_region = aws_region
        self.json_option = json_option

    def execute(self, context):
        self.log.info("Get Redshift connection")
        aws_hook = AwsHook(aws_conn_id=self.aws_conn_id)
        credentials = aws_hook.get_credentials()
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)

        self.log.info("Clearing data from destination Redshift table")
        redshift.run("DELETE FROM {}".format(self.table))

        self.log.info("Copying data from S3 to Redshift")
        rendered_key = self.s3_key.format(**context)
        s3_path = "s3://{}/{}".format(self.s3_bucket, rendered_key)
        formatted_sql = self.copy_sql.format(
            self.table,
            s3_path,
            credentials.access_key,
            credentials.secret_key,
            self.aws_region,
            self.json_option
        )
        redshift.run(formatted_sql)
