# Liveping

Liveping es un script de monitoreo de red en Python que visualiza la latencia a un host específico con un **gráfico en vivo directamente en la consola**. Al finalizar, exporta automáticamente los datos a un archivo `.csv` y el gráfico final a una imagen `.png`.

## Cómo Usarlo

El script está diseñado para ser flexible y fácil de usar desde la línea de comandos.

#### Comportamiento por Defecto
Si se ejecuta sin argumentos, el script hará ping a `8.8.8.8` de forma **indefinida**. Para detenerlo y generar los reportes, presiona `Ctrl+C`.

```bash
python liveping.py
```

#### Opciones de Línea de Comandos
Puedes personalizar la ejecución con los siguientes flags:

-   `-t`, `--target`: Especifica el host (dominio o IP) al que deseas hacer ping.
    ```bash
    python liveping.py --target google.com
    ```

-   `-T`, `--time`: Define la duración de la prueba en segundos. El script se detendrá automáticamente después de este tiempo.
    ```bash
    # Ejecutar una prueba de 60 segundos
    python liveping.py -t 1.1.1.1 --time 60
    ```

## Archivos de Salida

Cuando el script finaliza (ya sea por tiempo o por interrupción manual), se generan dos archivos con un nombre único basado en el host y la hora de inicio:

1.  **Archivo de Datos (`.csv`)**
    -   **Nombre**: `ping_results_HOST_FECHA_HORA.csv`
    -   **Contenido**: Un registro detallado de cada ping con las columnas `timestamp`, `ping_number`, `latency_ms` y `status`. Perfecto para importar en hojas de cálculo o para análisis más profundos.

2.  **Imagen del Gráfico (`.png`)**
    -   **Nombre**: `ping_chart_HOST_FECHA_HORA.png`
    -   **Contenido**: Una imagen de alta calidad que muestra la evolución de la latencia a lo largo de la sesión, incluyendo marcadores para pings fallidos y un resumen de estadísticas.

## Ejemplo


![image](https://github.com/user-attachments/assets/76b43791-c9f2-44a2-af9a-45dd516f8d15)
