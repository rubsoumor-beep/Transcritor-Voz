import socket
import threading
import time  # Adicionado para criar a pausa de alívio da CPU
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import sounddevice as sd
import speech_recognition as sr
import numpy as np

# CONFIGURAÇÕES DO SEU CÓDIGO ORIGINAL
frequencia = 16000
segundos = 7


class AppTranscritorGrande:
    def __init__(self, janela_principal):
        self.janela = janela_principal
        self.janela.title("Transcritor de Voz Dinâmico")
        self.janela.geometry("450x400")
        self.janela.resizable(False, False)

        self.rodando = False
        self.reconhecedor = sr.Recognizer()

        # --- INTERFACE VISUAL ---

        self.btn_controle = tk.Button(self.janela, text="LIGAR TRANSCRIÇÃO", bg="#107C41", fg="white",
                                      font=("Arial", 12, "bold"), height=2, command=self.alternar_sistema)
        self.btn_controle.pack(fill="x", padx=20, pady=15)

        self.lbl_status = tk.Label(self.janela, text="Status: Parado", fg="red", font=("Arial", 10, "italic"))
        self.lbl_status.pack(pady=5)

        self.caixa_grande = scrolledtext.ScrolledText(self.janela, font=("Arial", 11), wrap=tk.WORD, height=12)
        self.caixa_grande.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.caixa_grande.config(state=tk.DISABLED)

        self.janela.protocol("WM_DELETE_WINDOW", self.fechar_aplicativo)

    def injetar_texto_na_caixa(self, texto_novo):
        """Adiciona o texto traduzido e força a janela a redesenhar a tela imediatamente"""
        self.caixa_grande.config(state=tk.NORMAL)
        self.caixa_grande.insert(tk.END, texto_novo + "\n")
        self.caixa_grande.see(tk.END)
        self.caixa_grande.config(state=tk.DISABLED)
        self.janela.update_idletasks()  # DESTRAVA A TELA: Força o Windows a renderizar o texto na hora

    def atualizar_status_interface(self, texto, cor):
        """Muda o texto de status de forma segura sem congelar a janela"""
        self.lbl_status.config(text=texto, fg=cor)
        self.janela.update_idletasks()

    def seu_loop_original(self):
        """O seu loop original corrigido contra engasgos e lentidão"""
        sd.default.device = [0, None]

        while self.rodando:
            try:
                # Avisa que está gravando e força a tela a atualizar
                self.janela.after(0, self.atualizar_status_interface, "🎤 Ouvindo (Dispositivo 0)... Pode falar!",
                                  "green")

                # Captura o som (trava aqui por 7 segundos físicos)
                audio_bruto = sd.rec(int(segundos * frequencia), samplerate=frequencia, channels=1, dtype='int16')
                sd.wait()

                if not self.rodando:
                    break

                # Avisa que começou a enviar para a internet
                self.janela.after(0, self.atualizar_status_interface, "🧠 Processando voz na internet (Aguarde)...",
                                  "blue")

                audio_data = sr.AudioData(audio_bruto.tobytes(), frequencia, 2)

                try:
                    # Esta linha demora alguns segundos dependendo da sua velocidade de internet
                    texto = self.reconhecedor.recognize_google(audio_data, language="pt-BR")
                    self.janela.after(0, self.injetar_texto_na_caixa, f"🗣️ Você disse: {texto}")

                except sr.UnknownValueError:
                    self.janela.after(0, self.injetar_texto_na_caixa, "❌ O Google ainda não detectou voz.")
                except sr.RequestError as e:
                    messagebox.showerror("Erro de Conexão", f"Erro de conexão com o serviço: {e}")
                    self.janela.after(0, self.desligar_recursos)
                    break

                # ALÍVIO DE SINAL: Dá 1 segundo de folga para o Windows processar os cliques do mouse
                time.sleep(1)

            except Exception as e:
                messagebox.showerror("Erro de Hardware", f"Falha no microfone: {e}")
                self.janela.after(0, self.desligar_recursos)
                break

    def alternar_sistema(self):
        if not self.rodando:
            self.rodando = True
            self.btn_controle.config(text="DESLIGAR TRANSCRIÇÃO", bg="#A80000")

            self.caixa_grande.config(state=tk.NORMAL)
            self.caixa_grande.delete(1.0, tk.END)
            self.caixa_grande.config(state=tk.DISABLED)

            threading.Thread(target=self.seu_loop_original, daemon=True).start()
            messagebox.showinfo("Sucesso", "O loop de transcrição contânua foi iniciado!")
        else:
            self.desligar_recursos()
            messagebox.showinfo("Sistema", "Transcrição encerrada com segurança.")

    def desligar_recursos(self):
        self.rodando = False
        self.btn_controle.config(text="LIGAR SISTEMA", bg="#107C41")
        self.janela.after(0, self.atualizar_status_interface, "Status: Parado", "red")

    def fechar_aplicativo(self):
        self.rodando = False
        self.janela.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AppTranscritorGrande(root)
    root.mainloop()
