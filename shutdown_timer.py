import tkinter as tk
from tkinter import messagebox
import os
import threading
import time
from datetime import datetime, timedelta

app_data_path = os.getenv('APPDATA')
app_folder = os.path.join(app_data_path, 'AgendadorDesligamento')
os.makedirs(app_folder, exist_ok=True)
ARQUIVO_ESTADO = os.path.join(app_folder, 'shutdown_info.txt')

tempo_restante = 0
timer_rodando = False
thread_timer = None

def executar_comando_em_background(comando, callback):
    def run_command():
        os.system(comando)
        janela.after(0, callback)
    
    threading.Thread(target=run_command, daemon=True).start()

def agendar_desligamento():
    try:
        horas = int(entry_horas.get() or 0)
        minutos = int(entry_minutos.get() or 0)
        segundos_totais = (horas * 3600) + (minutos * 60)

        if segundos_totais <= 0:
            messagebox.showwarning("Aviso", "O tempo total deve ser maior que zero.")
            return

        set_ui_state(loading=True, message="Agendando...")

        comando = f'shutdown -s -t {segundos_totais}'
        executar_comando_em_background(comando, lambda: on_agendamento_completo(segundos_totais))

    except ValueError:
        messagebox.showerror("Erro de Entrada", "Por favor, insira apenas números válidos.")

def on_agendamento_completo(segundos_totais):
    horario_desligamento = datetime.now() + timedelta(seconds=segundos_totais)
    with open(ARQUIVO_ESTADO, "w") as f:
        f.write(str(horario_desligamento.timestamp()))

    iniciar_contagem_regressiva(segundos_totais)
    
    set_ui_state(loading=False, message=f"Agendado para as {horario_desligamento.strftime('%H:%M:%S')}.", color="green")

def cancelar_desligamento():
    set_ui_state(loading=True, message="Cancelando...")
    
    global timer_rodando
    timer_rodando = False
    timer_label.config(text="00:00:00")
    
    comando = 'shutdown -a'
    executar_comando_em_background(comando, on_cancelamento_completo)

def on_cancelamento_completo():
    if os.path.exists(ARQUIVO_ESTADO):
        os.remove(ARQUIVO_ESTADO)
    
    set_ui_state(loading=False, message="Agendamento cancelado.", color="blue")

def set_ui_state(loading, message="", color="black"):
    if loading:
        botao_agendar.config(state=tk.DISABLED)
        botao_cancelar.config(state=tk.DISABLED)
        status_label.config(text=message, fg="orange")
    else:
        botao_agendar.config(state=tk.NORMAL)
        botao_cancelar.config(state=tk.NORMAL)
        status_label.config(text=message, fg=color)

def iniciar_contagem_regressiva(segundos):
    global tempo_restante, timer_rodando, thread_timer
    tempo_restante = segundos
    if not timer_rodando:
        timer_rodando = True
        thread_timer = threading.Thread(target=atualizar_timer, daemon=True)
        thread_timer.start()

def atualizar_timer():
    global tempo_restante, timer_rodando
    while tempo_restante > 0 and timer_rodando:
        horas, rem = divmod(tempo_restante, 3600)
        minutos, segundos = divmod(rem, 60)
        timer_label.config(text=f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}")
        time.sleep(1)
        tempo_restante -= 1
    if timer_rodando:
        status_label.config(text="Desligando...", fg="blue")
    timer_rodando = False

def verificar_estado_ao_iniciar():
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, "r") as f:
                timestamp_desligamento = float(f.read())
            horario_desligamento = datetime.fromtimestamp(timestamp_desligamento)
            if horario_desligamento > datetime.now():
                segundos_restantes = (horario_desligamento - datetime.now()).total_seconds()
                iniciar_contagem_regressiva(int(segundos_restantes))
                set_ui_state(loading=False, message=f"Agendado para as {horario_desligamento.strftime('%H:%M:%S')}.", color="green")
            else:
                os.remove(ARQUIVO_ESTADO)
        except (ValueError, FileNotFoundError):
            if os.path.exists(ARQUIVO_ESTADO):
                os.remove(ARQUIVO_ESTADO)

janela = tk.Tk()
janela.title("Agendador de Desligamento")
janela.geometry("450x350") 
janela.resizable(False, False)
frame_principal = tk.Frame(janela, padx=20, pady=20)
frame_principal.pack(expand=True)
titulo_label = tk.Label(frame_principal, text="Programar Desligamento", font=("Arial", 16, "bold"))
titulo_label.pack(pady=(0, 20))
frame_tempo = tk.Frame(frame_principal)
frame_tempo.pack(pady=10)
label_horas = tk.Label(frame_tempo, text="Horas:", font=("Arial", 12))
label_horas.pack(side=tk.LEFT, padx=5)
entry_horas = tk.Entry(frame_tempo, width=5, font=("Arial", 12))
entry_horas.pack(side=tk.LEFT)
entry_horas.insert(0, "0")
label_minutos = tk.Label(frame_tempo, text="Minutos:", font=("Arial", 12))
label_minutos.pack(side=tk.LEFT, padx=5)
entry_minutos = tk.Entry(frame_tempo, width=5, font=("Arial", 12))
entry_minutos.pack(side=tk.LEFT)
entry_minutos.insert(0, "0")
frame_botoes = tk.Frame(frame_principal)
frame_botoes.pack(pady=20)
botao_agendar = tk.Button(frame_botoes, text="Agendar Desligamento", command=agendar_desligamento, font=("Arial", 12), bg="#4CAF50", fg="white")
botao_agendar.pack(side=tk.LEFT, padx=10)
botao_cancelar = tk.Button(frame_botoes, text="Cancelar Agendamento", command=cancelar_desligamento, font=("Arial", 12), bg="#f44336", fg="white")
botao_cancelar.pack(side=tk.LEFT, padx=10)
status_label = tk.Label(frame_principal, text="Nenhum desligamento agendado.", font=("Arial", 10, "italic"), fg="red")
status_label.pack(pady=10)
timer_label = tk.Label(frame_principal, text="00:00:00", font=("Arial", 24, "bold"))
timer_label.pack()

set_ui_state(loading=False, message="Nenhum desligamento agendado.", color="red")
janela.after(100, verificar_estado_ao_iniciar)

janela.mainloop()