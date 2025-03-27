# TP0 ~ Sistemas Distribuidos

Este es el tp0 de nivelación para la materia Sistemas Distribuidos 1. Consta de un cliente-servidor sencillo, con el cliente en go y el servidor en python. La cosigna puede encontrarse en el archivo [cosigna.md](./cosigna.md).

## Ejecución

Para ejecutar el cliente y el servidor:

1. Instalar [docker](https://docs.docker.com/engine/install/).
2. Hacer `git checkout` a la rama del ejercicio correspondiente (ejN).
3. De ser necesario, generar un `docker-compose` con la cantidad de clientes deseada usando el script [generar-compose.sh](./generar-compose.sh) (uso: `./generar-compose.sh <nombre_de_salida> <num_de_clientes>`)
4. Ejectuar ambos containers con `docker compose -f <nombre_de_salida>.yml up -d`, o uno sólo con `docker compose -f <nombre_de_salida>.yml up -d <servidor/cliente>`.
5. Para correr los tests, clonar el [repositorio con los mismos](https://github.com/7574-sistemas-distribuidos/tp0-tests) y seguir las instrucciones.
6. Para correr los servicios en local, se requiere python 3.9 para el servidor (recomendablemente con un entorno virtual de `venv` o `pyenv`) y golang 1.24 para el cliente.

## Detalles de la solución

### 1. Docker

El script generador de docker compose tiene 2 partes. La primera es un script sencillo de bash que chequea la cantidad de argumentos e invoca a la segunda parte. La segunda es un script de python que realiza el procesamiento real. Es un script que parsea el archivo yaml, y lo copia con los cambios necesarios (i.e. distinto número de clientes con sus respectivas variables) al archivo recibido como parámetro. Con el correr de los ejercicios se le fueron agregando funcionalidades para soportar los requerimientos de los compose más avanzados. La versión final copia todas las variables de entorno tanto de cliente como de servidor, salvo las variables `CLI_ID` para clientes (que es setada de forma secuencial) y `N_AGENCIES` para el servidor (que es setada al número de clientes presentes en el compose).

Los clientes tienen montados 2 volúmenes: uno para la config y uno para los datos de entrada (ej6 en adelante). El servidor tiene montado únicamente el volumen de la config

### 2. Comunicaciones

La comunacición cliente-servidor para la lotería nacional utiliza un protocolo binario de tamaño de paquete variable y con paquetes terminados en `\0`, que consta de los siguientes mensajes cliente -> servidor:

1. Enviar apuesta: El cliente envía los datos de una única apuesta. El formato es:
```
<msg_id> <len_nombre> <nombre> <len_apellido> <apellido> <documento> <fecha_nacimiento> <nro_de_apuesta>
```
Donde:
- `msg_id` es un `uint8` que representa el tipo de mensaje enviado (`1` en este caso)
- `len_nombre` y `len_apellido` son `uint16` que representan la longitud de los campos correspondientes
- `nombre` y `apellido` son cadenas de caracteres de longitud variable
- `documento` y `nro_de_apuesta` son `uint32` que representan los números de documento y de apuesta respectivamente
- `fecha_nacimiento` son 4 bytes, donde los primeros dos representan el año (en `uint16`), el tercero el mes y el cuarto el día

2. Enviar bloque de apuestas: El cliente envía los datos de varias apuestas a la vez. El formato es:
```
<msg_id> <nro_agencia> <cant_apuestas> <apuestas>
```
Donde:
- `msg_id` es un `uint8` que representa el tipo de mensaje enviado (`2` en este caso)
- `nro_agencia` es un `uint16` que representa la id de la agencia que envía las apuestas
- `cant_apuestas` es la cantidad de apuestas que van a ser enviadas en el bloque
- `apuestas` son todas las apuestas del bloque seguidas, en el mismo formato que el mensaje de enviar apuestas

3. Finalizar envío: El cliente informa al servidor que ya terminó de enviar apuestas. Este mensaje consta de un único byte que es la id del mismo (`3`)

Además, existe un único mensaje servidor -> cliente: Enviar ganadores, que consta de 1 byte para la id del mensaje (`1`), y un `uint16` que representa la cantidad de ganadores asociados a esa agencia

### 3. Concurrencia

El servidor maneja las conexiones con los clientes de forma concurrente. Cada cliente es manejado en un único thread, y además existe un thread principal en el servidor. El thread del cliente se encarga de recibir las apuestas, guardarlas, y enviar los resultados a los clientes. Para estos efectos, existen 2 mecanismos de sincronización:

1. Monitor de apuestas: un monitor que protege el acceso al archivo de apuestas para que los distintos threads puedan almacenar lo que recibieron de forma segura.
2. Canales: existen 2 canales entre los threads de los clientes y el thread principal del servidor. El primero se utiliza para que los threads de clientes notifiquen al servidor que ya han recibido y almacenado todas sus apuesta, y que puede entonces proceder con el sorteo, enviando por el channel la id de la agencia que les corresponde. El segundo se utiliza para que el servidor notifique a los thread de clientes la cantidad de ganadores que deben reportar a su respectiva agencia
