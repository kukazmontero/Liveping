import subprocess
import re
import time
import os
import sys
import platform
import csv
from datetime import datetime
import signal
import argparse

try:
    import matplotlib.pyplot as plt
    import plotext
except ImportError:
    print("Error: Faltan dependencias. Por favor, instálalas en tu entorno virtual ejecutando:")
    print("pip install matplotlib plotext")
    sys.exit(1)

# --- Configuración por defecto ---
DEFAULT_TARGET_HOST = "8.8.8.8"
PING_INTERVAL_S = 1
TIMEOUT_S = 10             # Timeout de 10 segundos por defecto

# --- Variables Globales ---
ping_results = []
start_time = datetime.now()
exit_flag = False

def handle_exit(sig, frame):
    global exit_flag
    print("\n\n! Interrupción detectada. Finalizando y generando reportes...")
    exit_flag = True

signal.signal(signal.SIGINT, handle_exit)

def clear_console():
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    os.system(command)

def parse_ping_output(ping_output):
    match = re.search(r"time=([\d.]+)\s*ms", ping_output)
    if match:
        return float(match.group(1))
    match = re.search(r"Tiempo=([\d.]+)\s*ms", ping_output)
    if match:
        return float(match.group(1))
    return None

def perform_ping(host, timeout):
    system = platform.system().lower()
    if system == "windows":
        command = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
    else:
        command = ["ping", "-c", "1", "-W", str(timeout), host]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 1)
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "Timeout", ""
    except Exception as e:
        return f"Error al ejecutar ping: {e}", ""

def update_live_plot(results, target_host):
    clear_console()
    timestamps = list(range(1, len(results) + 1))
    latencies = [r['latency'] for r in results]
    
    successful_pings = [r['latency'] for r in results if r['status'] == 'success']
    packets_sent = len(results)
    packets_lost = packets_sent - len(successful_pings)
    loss_percentage = (packets_lost / packets_sent * 100) if packets_sent > 0 else 0
    
    avg_latency = sum(successful_pings) / len(successful_pings) if successful_pings else 0
    min_latency = min(successful_pings) if successful_pings else 0
    max_latency = max(successful_pings) if successful_pings else 0
    
    print(f"--- PING EN VIVO A {target_host} ---")
    print(f"Presiona Ctrl+C para detener y generar los reportes.\n")
    
    plotext.clt()
    plotext.title("Latencia de Ping (ms) en el Tiempo")
    plotext.xlabel("Número de Ping")
    plotext.ylabel("Latencia (ms)")
    plotext.plot_size(100, 20)
    
    plotext.canvas_color('default') 
    plotext.axes_color('default')   
    plotext.ticks_color('cyan')     
    
    plotext.xlim(1, len(results) + 1)
    if successful_pings:
        y_upper_limit = max(max_latency, 5) * 1.1 
    else:
        y_upper_limit = 50
    plotext.ylim(0, y_upper_limit)

    plotext.scatter(timestamps, latencies, marker="braille")
    plotext.show()
    
    print("\n--- Estadísticas ---")
    print(f"Enviados: {packets_sent} | Perdidos: {packets_lost} ({loss_percentage:.1f}% perdidos)")
    if successful_pings:
        print(f"Latencia (ms) -> Mín: {min_latency:.2f} | Máx: {max_latency:.2f} | Prom: {avg_latency:.2f}")
    if results:
        last_result = results[-1]
        status_color = "\033[92m" if last_result['status'] == 'success' else "\033[91m"
        status_end_color = "\033[0m"
        latency_str = f"{last_result['latency']:.2f} ms" if last_result['latency'] is not None else "FALLIDO"
        print(f"Último ping: {status_color}{latency_str}{status_end_color}")
        if last_result['status'] == 'failed':
            print(f"  \033[93m[DEBUG] Salida del comando:\n{last_result['debug_info']}\033[0m")

def save_results_to_csv(results, filename):
    if not results: return
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'ping_number', 'latency_ms', 'status'])
            for i, r in enumerate(results):
                writer.writerow([r['timestamp'], i + 1, r['latency'] or '', r['status']])
        print(f"\n✔ Datos guardados correctamente en: {filename}")
    except Exception as e:
        print(f"\n❌ Error al guardar el archivo CSV: {e}")

def generate_final_plot_image(results, filename, target_host):
    if not any(r['status'] == 'success' for r in results):
        print("No hay pings exitosos para graficar.")
        return

    successful_pings_x = [i+1 for i, r in enumerate(results) if r['status'] == 'success']
    successful_pings_y = [r['latency'] for r in results if r['status'] == 'success']
    failed_pings_x = [i+1 for i, r in enumerate(results) if r['status'] != 'success']
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(successful_pings_x, successful_pings_y, marker='o', linestyle='-', color='dodgerblue', label='Ping Exitoso')
    if failed_pings_x:
        ax.scatter(failed_pings_x, [0] * len(failed_pings_x), marker='x', color='red', s=100, label='Ping Fallido', zorder=5)

    ax.set_title(f'Análisis de Ping a {target_host}', fontsize=16)
    ax.set_xlabel('Número de Ping', fontsize=12)
    ax.set_ylabel('Latencia (ms)', fontsize=12)
    ax.legend()
    ax.grid(True)
    
    if successful_pings_y:
        stats_text = f'Promedio: {sum(successful_pings_y)/len(successful_pings_y):.2f} ms\nMín: {min(successful_pings_y):.2f} ms\nMáx: {max(successful_pings_y):.2f} ms'
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))

    try:
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        print(f"✔ Gráfico guardado correctamente en: {filename}")
    except Exception as e:
        print(f"\n❌ Error al guardar la imagen del gráfico: {e}")
    finally:
        plt.close()

def main():
    global exit_flag
    
    parser = argparse.ArgumentParser(
        description="Realiza pings a un host, muestra un gráfico en vivo y genera reportes.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-t', '--target',
        default=DEFAULT_TARGET_HOST,
        help=f"La dirección IP o dominio al que hacer ping.\n(Por defecto: {DEFAULT_TARGET_HOST})"
    )
    # CAMBIO: Se reemplaza -c/--count por -T/--time
    parser.add_argument(
        '-T', '--time',
        type=int,
        default=None, # Por defecto no hay límite de tiempo
        help="Duración en segundos para ejecutar el ping.\n(Por defecto: infinito, detener con Ctrl+C)"
    )
    args = parser.parse_args()
    target_host = args.target
    time_limit_s = args.time # Guardamos el límite de tiempo

    # CAMBIO: Iniciamos un cronómetro para el script
    script_start_time = time.monotonic()

    while not exit_flag:
        # CAMBIO: Se añade la lógica para comprobar el límite de tiempo
        if time_limit_s is not None:
            elapsed_time = time.monotonic() - script_start_time
            if elapsed_time >= time_limit_s:
                print(f"\n! Límite de tiempo de {time_limit_s} segundos alcanzado.")
                break # Sale del bucle para generar los reportes

        stdout, stderr = perform_ping(target_host, TIMEOUT_S)
        latency = parse_ping_output(stdout)
        
        debug_info = ""
        if latency is None:
            debug_info = f"STDOUT: '{stdout.strip()}' | STDERR: '{stderr.strip()}'"

        ping_results.append({
            "timestamp": datetime.now().isoformat(),
            "latency": latency,
            "status": "success" if latency is not None else "failed",
            "debug_info": debug_info
        })
        
        update_live_plot(ping_results, target_host)
        
        if not exit_flag:
            time.sleep(PING_INTERVAL_S)

    print("\n--- Proceso de ping finalizado. Generando reportes... ---")
    timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
    safe_host = re.sub(r'[^a-zA-Z0-9.-]', '_', target_host)
    csv_filename = f"ping_results_{safe_host}_{timestamp_str}.csv"
    img_filename = f"ping_chart_{safe_host}_{timestamp_str}.png"
    
    save_results_to_csv(ping_results, csv_filename)
    generate_final_plot_image(ping_results, img_filename, target_host)

    print("\n¡Análisis completado!")

if __name__ == "__main__":
    main()
