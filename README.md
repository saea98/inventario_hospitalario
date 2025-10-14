después del git clone
crear archivo .env con el siguiente contenido
DEBUG=False
SECRET_KEY=super_clave_segura_aqui
ALLOWED_HOSTS=*

POSTGRES_DB=inventario_bd
POSTGRES_USER=postgres
POSTGRES_PASSWORD=XXXXXX
POSTGRES_HOST=xxx.xxx.xxx.xxx

PORT=8700



posterior ejecutar 

docker-compose up -d --build 

finalmente sustituir las tablas de la base de datos por el respaldo que envió por separado

