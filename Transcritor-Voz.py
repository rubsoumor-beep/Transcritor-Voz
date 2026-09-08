import threading
import time
import re
import queue
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext

import sounddevice as sd
import speech_recognition as sr
import numpy as np


# ============================================================
# CONFIGURAÇÕES
# ============================================================

FREQUENCIA = 16000

# Bloco interno de captura.
# Não limita a duração da fala.
BUFFER_FRAMES = 1024

# Tempo de silêncio para finalizar uma frase.
SILENCIO_FINAL = 0.8

# Tempo máximo de uma frase contínua.
DURACAO_MAXIMA = 60

# Trecho capturado antes da detecção da voz.
PRE_ROLL = 0.30

# Sensibilidade da detecção de voz.
LIMIAR_VOZ = 0.015


class AppTranscritorGrande:

    # ========================================================
    # VOCABULÁRIO NUMÉRICO
    # ========================================================

    UNIDADES = {
        "zero": 0,
        "um": 1,
        "uma": 1,
        "dois": 2,
        "duas": 2,
        "três": 3,
        "tres": 3,
        "quatro": 4,
        "cinco": 5,
        "seis": 6,
        "sete": 7,
        "oito": 8,
        "nove": 9,
        "dez": 10,
        "onze": 11,
        "doze": 12,
        "treze": 13,
        "quatorze": 14,
        "catorze": 14,
        "quinze": 15,
        "dezesseis": 16,
        "dezasseis": 16,
        "dezessete": 17,
        "dezassete": 17,
        "dezoito": 18,
        "dezenove": 19,
        "dezanove": 19,
    }

    DEZENAS = {
        "vinte": 20,
        "trinta": 30,
        "quarenta": 40,
        "cinquenta": 50,
        "sessenta": 60,
        "setenta": 70,
        "oitenta": 80,
        "noventa": 90,
    }

    CENTENAS = {
        "cem": 100,
        "cento": 100,
        "duzentos": 200,
        "duzentas": 200,
        "trezentos": 300,
        "trezentas": 300,
        "quatrocentos": 400,
        "quatrocentas": 400,
        "quinhentos": 500,
        "quinhentas": 500,
        "seiscentos": 600,
        "seiscentas": 600,
        "setecentos": 700,
        "setecentas": 700,
        "oitocentos": 800,
        "oitocentas": 800,
        "novecentos": 900,
        "novecentas": 900,
    }

    PALAVRAS_NUMERICAS = (
        set(UNIDADES.keys())
        | set(DEZENAS.keys())
        | set(CENTENAS.keys())
        | {
            "mil",
            "milhão",
            "milhoes",
            "milhões",
            "e"
        }
    )

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def __init__(self, janela_principal):

        self.janela = janela_principal

        self.janela.title(
            "Transcritor de Voz Dinâmico"
        )

        self.janela.geometry(
            "500x500"
        )

        self.janela.resizable(
            False,
            False
        )

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        self.rodando = False

        self.thread_captura = None

        # Evita várias transcrições simultâneas.
        self.fila_processamento = queue.Queue()

        self.thread_processamento = None

        # ----------------------------------------------------
        # RECONHECEDOR
        # ----------------------------------------------------

        self.reconhecedor = sr.Recognizer()

        self.reconhecedor.dynamic_energy_threshold = True

        self.reconhecedor.energy_threshold = 300

        self.reconhecedor.pause_threshold = 0.8

        self.reconhecedor.phrase_threshold = 0.2

        self.reconhecedor.non_speaking_duration = 0.3

        # ----------------------------------------------------
        # INTERFACE
        # ----------------------------------------------------

        self.btn_controle = tk.Button(
            self.janela,
            text="LIGAR TRANSCRIÇÃO",
            bg="#107C41",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            command=self.alternar_sistema
        )

        self.btn_controle.pack(
            fill="x",
            padx=20,
            pady=15
        )

        self.lbl_status = tk.Label(
            self.janela,
            text="Status: Parado",
            fg="red",
            font=("Arial", 10, "italic")
        )

        self.lbl_status.pack(
            pady=5
        )

        self.caixa_grande = scrolledtext.ScrolledText(
            self.janela,
            font=("Arial", 11),
            wrap=tk.WORD,
            height=17
        )

        self.caixa_grande.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        self.caixa_grande.config(
            state=tk.DISABLED
        )

        self.janela.protocol(
            "WM_DELETE_WINDOW",
            self.fechar_aplicativo
        )

    # ========================================================
    # INTERFACE
    # ========================================================

    def injetar_texto_na_caixa(self, texto_novo):

        self.caixa_grande.config(
            state=tk.NORMAL
        )

        self.caixa_grande.insert(
            tk.END,
            texto_novo + "\n"
        )

        self.caixa_grande.see(
            tk.END
        )

        self.caixa_grande.config(
            state=tk.DISABLED
        )

    def atualizar_status_interface(
        self,
        texto,
        cor
    ):

        self.lbl_status.config(
            text=texto,
            fg=cor
        )

    # ========================================================
    # ÁUDIO
    # ========================================================

    def calcular_nivel_audio(
        self,
        audio
    ):

        if len(audio) == 0:
            return 0.0

        audio_float = (
            audio.astype(
                np.float32
            ) / 32768.0
        )

        rms = np.sqrt(
            np.mean(
                audio_float * audio_float
            )
        )

        return float(rms)

    # ========================================================
    # INTERPRETADOR NUMÉRICO
    # ========================================================

    def interpretar_numero(
        self,
        palavras
    ):
        """
        Interpreta um número composto.

        Exemplos:

        vinte e três
        -> 23

        quarenta e dois
        -> 42

        cento e vinte e cinco
        -> 125

        mil duzentos e cinquenta
        -> 1250
        """

        total = 0
        atual = 0

        for palavra in palavras:

            if palavra == "e":
                continue

            # -----------------------------
            # UNIDADES
            # -----------------------------

            if palavra in self.UNIDADES:

                atual += self.UNIDADES[
                    palavra
                ]

            # -----------------------------
            # DEZENAS
            # -----------------------------

            elif palavra in self.DEZENAS:

                atual += self.DEZENAS[
                    palavra
                ]

            # -----------------------------
            # CENTENAS
            # -----------------------------

            elif palavra in self.CENTENAS:

                atual += self.CENTENAS[
                    palavra
                ]

            # -----------------------------
            # MIL
            # -----------------------------

            elif palavra == "mil":

                if atual == 0:
                    atual = 1

                total += (
                    atual * 1000
                )

                atual = 0

            # -----------------------------
            # MILHÃO
            # -----------------------------

            elif palavra in (
                "milhão",
                "milhoes",
                "milhões"
            ):

                if atual == 0:
                    atual = 1

                total += (
                    atual * 1_000_000
                )

                atual = 0

        return total + atual

    # ========================================================
    # DETECTAR SE É SEQUÊNCIA NUMÉRICA
    # ========================================================

    def eh_sequencia_numerica(
        self,
        texto
    ):

        texto_limpo = texto.lower()

        texto_limpo = re.sub(
            r"[^\w\s]",
            " ",
            texto_limpo,
            flags=re.UNICODE
        )

        palavras = (
            texto_limpo
            .split()
        )

        if not palavras:
            return False

        for palavra in palavras:

            if palavra not in self.PALAVRAS_NUMERICAS:
                return False

        return True

    # ========================================================
    # NORMALIZAÇÃO INTELIGENTE
    # ========================================================

    def normalizar_numeros(
        self,
        texto
    ):

        texto_original = texto.strip()

        if not texto_original:
            return texto_original

        # ----------------------------------------------------
        # Primeiro verificamos se a frase inteira é numérica.
        # ----------------------------------------------------

        if self.eh_sequencia_numerica(
            texto_original
        ):

            texto_lower = (
                texto_original.lower()
            )

            texto_limpo = re.sub(
                r"[^\w\s]",
                " ",
                texto_lower,
                flags=re.UNICODE
            )

            palavras = (
                texto_limpo
                .split()
            )

            # ------------------------------------------------
            # SEQUÊNCIA PURA
            #
            # dez vinte trinta quarenta
            #
            # vira
            #
            # 10 20 30 40
            # ------------------------------------------------

            if "e" not in palavras:

                numeros = []

                for palavra in palavras:

                    if palavra in self.UNIDADES:

                        numeros.append(
                            str(
                                self.UNIDADES[
                                    palavra
                                ]
                            )
                        )

                    elif palavra in self.DEZENAS:

                        numeros.append(
                            str(
                                self.DEZENAS[
                                    palavra
                                ]
                            )
                        )

                    elif palavra in self.CENTENAS:

                        numeros.append(
                            str(
                                self.CENTENAS[
                                    palavra
                                ]
                            )
                        )

                    elif palavra == "mil":

                        numeros.append(
                            "1000"
                        )

                    elif palavra in (
                        "milhão",
                        "milhoes",
                        "milhões"
                    ):

                        numeros.append(
                            "1000000"
                        )

                if numeros:

                    return " ".join(
                        numeros
                    )

            # ------------------------------------------------
            # NÚMERO COMPOSTO
            #
            # vinte e três
            #
            # vira
            #
            # 23
            # ------------------------------------------------

            numero = self.interpretar_numero(
                palavras
            )

            return str(
                numero
            )

        # ====================================================
        # FRASE NORMAL COM NÚMEROS
        # ====================================================

        return self.normalizar_numeros_dentro_frase(
            texto_original
        )

    # ========================================================
    # NÚMEROS DENTRO DE FRASES
    # ========================================================

    def normalizar_numeros_dentro_frase(
        self,
        texto
    ):

        palavras = texto.split()

        resultado = []

        i = 0

        while i < len(palavras):

            palavra_original = palavras[i]

            # Remove pontuação para análise.
            palavra = re.sub(
                r"[^\wÀ-ÿ]",
                "",
                palavra_original.lower()
            )

            # ------------------------------------------------
            # Palavra não numérica
            # ------------------------------------------------

            if palavra not in self.PALAVRAS_NUMERICAS:

                resultado.append(
                    palavra_original
                )

                i += 1

                continue

            # ------------------------------------------------
            # Tenta capturar sequência composta.
            #
            # Ex:
            #
            # vinte e três
            #
            # cento e vinte
            # ------------------------------------------------

            grupo = [
                palavra
            ]

            j = i + 1

            while j < len(palavras):

                proxima = re.sub(
                    r"[^\wÀ-ÿ]",
                    "",
                    palavras[j].lower()
                )

                if proxima in self.PALAVRAS_NUMERICAS:

                    grupo.append(
                        proxima
                    )

                    j += 1

                else:

                    break

            # ------------------------------------------------
            # Se tiver "e", provavelmente é número composto.
            # ------------------------------------------------

            if "e" in grupo:

                numero = self.interpretar_numero(
                    grupo
                )

                resultado.append(
                    str(numero)
                )

                i = j

                continue

            # ------------------------------------------------
            # Número isolado dentro da frase.
            #
            # Ex:
            #
            # tenho vinte anos
            #
            # permanece "tenho vinte anos"
            #
            # Não queremos alterar frases naturais.
            # ------------------------------------------------

            resultado.append(
                palavra_original
            )

            i += 1

        return " ".join(
            resultado
        )

    # ========================================================
    # PROCESSAMENTO DA FRASE
    # ========================================================

    def processar_audio(
        self,
        audio
    ):

        if not self.rodando:
            return

        if len(audio) == 0:
            return

        try:

            # ------------------------------------------------
            # MONO
            # ------------------------------------------------

            if audio.ndim > 1:

                audio = audio[:, 0]

            audio_bytes = (
                audio.astype(
                    np.int16
                ).tobytes()
            )

            audio_data = sr.AudioData(
                audio_bytes,
                FREQUENCIA,
                2
            )

            self.janela.after(
                0,
                self.atualizar_status_interface,
                "Processando voz...",
                "blue"
            )

            try:

                # ------------------------------------------------
                # GOOGLE SPEECH
                # ------------------------------------------------

                texto = (
                    self.reconhecedor
                    .recognize_google(
                        audio_data,
                        language="pt-BR"
                    )
                )

                texto = texto.strip()

                if texto:

                    # ============================================
                    # INTERPRETAÇÃO
                    # ============================================

                    texto_final = (
                        self.normalizar_numeros(
                            texto
                        )
                    )

                    self.janela.after(
                        0,
                        self.injetar_texto_na_caixa,
                        f"Você disse: {texto_final}"
                    )

            except sr.UnknownValueError:

                # Não foi possível entender.
                pass

            except sr.RequestError as e:

                self.janela.after(
                    0,
                    self.mostrar_erro_conexao,
                    str(e)
                )

            if self.rodando:

                self.janela.after(
                    0,
                    self.atualizar_status_interface,
                    "Ouvindo... Pode falar!",
                    "green"
                )

        except Exception as e:

            self.janela.after(
                0,
                self.mostrar_erro_hardware,
                str(e)
            )

    # ========================================================
    # FILA DE PROCESSAMENTO
    # ========================================================

    def trabalhador_processamento(
        self
    ):

        while self.rodando:

            try:

                audio = (
                    self.fila_processamento
                    .get(
                        timeout=0.5
                    )
                )

            except queue.Empty:

                continue

            try:

                self.processar_audio(
                    audio
                )

            finally:

                self.fila_processamento.task_done()

    # ========================================================
    # LOOP CONTÍNUO DE CAPTURA
    # ========================================================

    def seu_loop_original(
        self
    ):

        try:

            dispositivo = (
                sd.default.device
            )

            print(
                f"Dispositivo de áudio: {dispositivo}"
            )

            # ------------------------------------------------
            # STREAM CONTÍNUO
            # ------------------------------------------------

            with sd.InputStream(
                samplerate=FREQUENCIA,
                channels=1,
                dtype="int16",
                blocksize=BUFFER_FRAMES
            ) as stream:

                audio_frase = []

                pre_buffer = []

                falando = False

                tempo_inicio_fala = None

                ultimo_som = None

                # ------------------------------------------------
                # THREAD DE PROCESSAMENTO
                # ------------------------------------------------

                self.thread_processamento = (
                    threading.Thread(
                        target=self.trabalhador_processamento,
                        daemon=True
                    )
                )

                self.thread_processamento.start()

                self.janela.after(
                    0,
                    self.atualizar_status_interface,
                    "Ouvindo... Pode falar!",
                    "green"
                )

                # =================================================
                # LOOP
                # =================================================

                while self.rodando:

                    dados, overflow = (
                        stream.read(
                            BUFFER_FRAMES
                        )
                    )

                    audio = (
                        dados[:, 0]
                        .copy()
                    )

                    nivel = (
                        self.calcular_nivel_audio(
                            audio
                        )
                    )

                    agora = time.time()

                    # ------------------------------------------------
                    # PRÉ-BUFFER
                    # ------------------------------------------------

                    pre_buffer.append(
                        audio
                    )

                    max_pre_buffers = max(
                        1,
                        int(
                            PRE_ROLL
                            * FREQUENCIA
                            / BUFFER_FRAMES
                        )
                    )

                    if (
                        len(pre_buffer)
                        > max_pre_buffers
                    ):

                        pre_buffer.pop(0)

                    # ------------------------------------------------
                    # DETECTOU VOZ
                    # ------------------------------------------------

                    if nivel >= LIMIAR_VOZ:

                        if not falando:

                            falando = True

                            tempo_inicio_fala = (
                                agora
                            )

                            audio_frase = []

                            # Recupera o pré-buffer.
                            for bloco in pre_buffer:

                                audio_frase.append(
                                    bloco.copy()
                                )

                            self.janela.after(
                                0,
                                self.atualizar_status_interface,
                                "Ouvindo fala...",
                                "green"
                            )

                        audio_frase.append(
                            audio.copy()
                        )

                        ultimo_som = agora

                    # ------------------------------------------------
                    # SILÊNCIO DURANTE A FALA
                    # ------------------------------------------------

                    elif falando:

                        audio_frase.append(
                            audio.copy()
                        )

                        tempo_silencio = (
                            agora - ultimo_som
                            if ultimo_som
                            else 0
                        )

                        tempo_fala = (
                            agora - tempo_inicio_fala
                            if tempo_inicio_fala
                            else 0
                        )

                        terminou_por_silencio = (
                            tempo_silencio
                            >= SILENCIO_FINAL
                        )

                        terminou_por_tempo = (
                            tempo_fala
                            >= DURACAO_MAXIMA
                        )

                        # ------------------------------------------------
                        # FINALIZA FRASE
                        # ------------------------------------------------

                        if (
                            terminou_por_silencio
                            or terminou_por_tempo
                        ):

                            falando = False

                            if audio_frase:

                                audio_completo = (
                                    np.concatenate(
                                        audio_frase
                                    )
                                )

                                audio_frase = []

                                # ------------------------------------------------
                                # Envia para fila.
                                # ------------------------------------------------

                                self.fila_processamento.put(
                                    audio_completo
                                )

                            pre_buffer = []

                    # ------------------------------------------------
                    # Pequena pausa.
                    # ------------------------------------------------

                    time.sleep(
                        0.001
                    )

        except Exception as e:

            self.janela.after(
                0,
                self.mostrar_erro_hardware,
                str(e)
            )

        finally:

            self.rodando = False

            self.janela.after(
                0,
                self.desligar_recursos
            )

    # ========================================================
    # ERROS
    # ========================================================

    def mostrar_erro_conexao(
        self,
        erro
    ):

        messagebox.showerror(
            "Erro de Conexão",
            f"Erro de conexão com o serviço:\n\n{erro}"
        )

        self.desligar_recursos()

    def mostrar_erro_hardware(
        self,
        erro
    ):

        messagebox.showerror(
            "Erro de Hardware",
            f"Falha no microfone:\n\n{erro}"
        )

        self.desligar_recursos()

    # ========================================================
    # LIGAR / DESLIGAR
    # ========================================================

    def alternar_sistema(
        self
    ):

        if not self.rodando:

            self.rodando = True

            self.btn_controle.config(
                text="DESLIGAR TRANSCRIÇÃO",
                bg="#A80000"
            )

            self.caixa_grande.config(
                state=tk.NORMAL
            )

            self.caixa_grande.delete(
                1.0,
                tk.END
            )

            self.caixa_grande.config(
                state=tk.DISABLED
            )

            # ------------------------------------------------
            # Thread de captura
            # ------------------------------------------------

            self.thread_captura = (
                threading.Thread(
                    target=self.seu_loop_original,
                    daemon=True
                )
            )

            self.thread_captura.start()

            messagebox.showinfo(
                "Sucesso",
                "A transcrição contínua foi iniciada."
            )

        else:

            self.desligar_recursos()

            messagebox.showinfo(
                "Sistema",
                "Transcrição encerrada com segurança."
            )

    def desligar_recursos(
        self
    ):

        self.rodando = False

        self.btn_controle.config(
            text="LIGAR TRANSCRIÇÃO",
            bg="#107C41"
        )

        self.atualizar_status_interface(
            "Status: Parado",
            "red"
        )

    # ========================================================
    # FECHAR
    # ========================================================

    def fechar_aplicativo(
        self
    ):

        self.rodando = False

        self.janela.destroy()


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = AppTranscritorGrande(
        root
    )

    root.mainloop()
