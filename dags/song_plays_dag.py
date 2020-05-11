from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.udacity_plugin import (
    StageToRedshiftOperator,
    LoadFactOperator,
    LoadDimensionOperator,
    DataQualityOperator,
    )
from helpers import SqlQueries


s3_bucket = 'udacity-dend'
aws_region = 'us-west-2'
# s3_bucket='udacity-569126059190-eu-central-1'
# aws_region = 'eu-central-1'


default_args = {
    'owner': 'udacity',
    'depends_on_past': False,
    'start_date': datetime(2019, 1, 12),
    'end_date': datetime(2019, 1, 12, 3),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_retry': False,
    'catchup': False,
}


dag = DAG('song_plays_dag',
          default_args=default_args,
          description='Load and transform data in Redshift with Airflow',
          schedule_interval='0 * * * *'
        )


start_operator = DummyOperator(task_id='begin_execution',  dag=dag)


stage_events_to_redshift = StageToRedshiftOperator(
    task_id='stage_events',
    table='staging_events',
    redshift_conn_id='redshift',
    aws_conn_id='aws_credentials',
    s3_bucket=s3_bucket,
    s3_key='log_data',
    aws_region=aws_region,
    json_option=f"s3://{s3_bucket}/log_json_path.json",
    dag=dag
)


stage_songs_to_redshift = StageToRedshiftOperator(
    task_id='stage_songs',
    table='staging_songs',
    redshift_conn_id='redshift',
    aws_conn_id='aws_credentials',
    s3_bucket=s3_bucket,
    s3_key='song_data',
    aws_region=aws_region,
    json_option='auto',
    dag=dag,
)


load_songplays_table = LoadFactOperator(
    task_id='load_songplays_fact_table',
    table='songplays',
    select_stmt=SqlQueries.songplay_table_insert,
    redshift_conn_id='redshift',
    dag=dag
)


load_user_dimension_table = LoadDimensionOperator(
    task_id='load_user_dim_table',
    table='users',
    select_stmt=SqlQueries.user_table_insert,
    delete_load=True,
    redshift_conn_id='redshift',
    dag=dag,
)


load_song_dimension_table = LoadDimensionOperator(
    task_id='load_song_dim_table',
    table='songs',
    select_stmt=SqlQueries.song_table_insert,
    delete_load=True,
    redshift_conn_id='redshift',
    dag=dag
)


load_artist_dimension_table = LoadDimensionOperator(
    task_id='load_artist_dim_table',
    table='artists',
    select_stmt=SqlQueries.artist_table_insert,
    delete_load=True,
    redshift_conn_id='redshift',
    dag=dag
)


load_time_dimension_table = LoadDimensionOperator(
    task_id='load_time_dim_table',
    table='time',
    select_stmt=SqlQueries.time_table_insert,
    delete_load=True,
    redshift_conn_id='redshift',
    dag=dag
)


run_quality_checks = DataQualityOperator(
    task_id='run_data_quality_checks',
    test_stmt='select count(*) from songplays where songid is null or artistid is null',
    expected=0,
    redshift_conn_id='redshift',
    dag=dag
)


end_operator = DummyOperator(task_id='stop_execution',  dag=dag)


start_operator >> [
    stage_songs_to_redshift,
    stage_events_to_redshift,
    ] >> load_songplays_table

load_songplays_table >> [
    load_user_dimension_table,
    load_song_dimension_table,
    load_artist_dimension_table,
    load_user_dimension_table,
    load_time_dimension_table,
    ] >> run_quality_checks

run_quality_checks >> end_operator
