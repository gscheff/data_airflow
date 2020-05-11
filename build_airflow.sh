docker build --rm --build-arg AIRFLOW_DEPS="s3,aws,dask" --build-arg PYTHON_DEPS="sqlalchemy<1.3.16 pymysql" -t my/docker-airflow:1.10.9 .
