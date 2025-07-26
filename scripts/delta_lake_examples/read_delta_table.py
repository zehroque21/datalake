from pyspark.sql import SparkSession

# Inicializa a sessão Spark
spark = SparkSession.builder \
    .appName("ReadDeltaTable") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Caminho para a tabela Delta no S3
delta_table_path = "s3a://datalake-bucket-for-airflow-and-delta/delta_tables/users"

# Lê a tabela Delta
try:
    df_delta = spark.read.format("delta").load(delta_table_path)
    print(f"Tabela Delta lida com sucesso de: {delta_table_path}")
    df_delta.show()
except Exception as e:
    print(f"Erro ao ler a tabela Delta: {e}")

spark.stop()


