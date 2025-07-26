from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# Inicializa a sessão Spark
spark = SparkSession.builder \
    .appName("WriteDeltaTable") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Dados de exemplo
data = [
    ("Alice", 1, "New York"),
    ("Bob", 2, "London"),
    ("Charlie", 3, "Paris")
]
columns = ["name", "id", "city"]
df = spark.createDataFrame(data, columns)

# Caminho para a tabela Delta no S3
delta_table_path = "s3a://datalake-bucket-for-airflow-and-delta/delta_tables/users"

# Escreve o DataFrame como uma tabela Delta
df.write.format("delta").mode("overwrite").save(delta_table_path)

print(f"Tabela Delta escrita com sucesso em: {delta_table_path}")

# Para verificar a tabela (opcional)
# df_delta = spark.read.format("delta").load(delta_table_path)
# df_delta.show()

spark.stop()


