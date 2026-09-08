import threading
import time
import re
import queue
import unicodedata
import difflib

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
BUFFER_FRAMES = 1024

SILENCIO_FINAL = 0.80
DURACAO_MAXIMA = 60.0
PRE_ROLL = 0.30

LIMIAR_VOZ_PADRAO = 0.015
CALIBRACAO_SEGUNDOS = 1.0
FATOR_LIMIAR_RUIDO = 3.0
LIMIAR_MINIMO_VOZ = 0.008
LIMIAR_MAXIMO_VOZ = 0.080

DURACAO_MINIMA_FALA = 0.25
ENERGIA_MINIMA_FALA = 0.004

MAX_ALTERNATIVAS = 10


# ============================================================
# INTERPRETADOR DE LINGUAGEM
# ============================================================

class InterpretadorLinguagem:

    # ========================================================
    # UNIDADES E NÚMEROS DE 0 A 19
    # ========================================================

    UNIDADES = {
        "zero": 0,

        "um": 1,
        "uma": 1,
        "uns": 1,
        "umas": 1,

        "dois": 2,
        "duas": 2,

        "tres": 3,
        "três": 3,

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
        "dezanove": 19,
        "dezenove": 19,
    }

    # ========================================================
    # DEZENAS
    # ========================================================

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

    # ========================================================
    # CENTENAS
    # ========================================================

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

    # ========================================================
    # MULTIPLICADORES
    # ========================================================

    MULTIPLICADORES = {
        "mil": 1000,

        "milhao": 1_000_000,
        "milhoes": 1_000_000,

        "bilhao": 1_000_000_000,
        "bilhoes": 1_000_000_000,
    }

    # ========================================================
    # CORREÇÕES FONÉTICAS
    # ========================================================

    CORRECOES_NUMERICAS = {
        "hum": "um",
        "humm": "um",

        "dous": "dois",
        "doiz": "dois",

        "treis": "tres",
        "treiz": "tres",

        "quato": "quatro",

        "cincoenta": "cinquenta",

        "secenta": "sessenta",
        "sesenta": "sessenta",

        "setanta": "setenta",

        "oitanta": "oitenta",

        "novanta": "noventa",
    }

    # ========================================================
    # LETRAS
    # ========================================================

    LETRAS = {
        "a": "A",

        "be": "B",
        "bê": "B",
        "beh": "B",

        "ce": "C",
        "cê": "C",
        "seh": "C",

        "de": "D",
        "dê": "D",

        "efe": "F",
        "effe": "F",

        "ge": "G",
        "gê": "G",

        "aga": "H",
        "agá": "H",
        "aha": "H",

        "i": "I",

        "jota": "J",

        "ka": "K",
        "cá": "K",

        "ele": "L",
        "lê": "L",

        "eme": "M",

        "ene": "N",

        "o": "O",

        "pe": "P",
        "pê": "P",

        "que": "Q",
        "quê": "Q",

        "erre": "R",
        "ere": "R",

        "esse": "S",
        "sê": "S",

        "te": "T",
        "tê": "T",

        "u": "U",

        "ve": "V",
        "vê": "V",

        "dablio": "W",
        "dáblio": "W",
        "duplo": "W",

        "xis": "X",
        "xiz": "X",

        "ipsilon": "Y",
        "ípsilon": "Y",
        "epsilon": "Y",

        "ze": "Z",
        "zê": "Z",
    }

    # ========================================================
    # PALAVRAS PROTEGIDAS
    # ========================================================

    PALAVRAS_PROTEGIDAS = {
        "de",
        "e",
        "o",
        "a",
        "os",
        "as",
        "que",
        "te",
        "ele",
        "me",
        "se",
        "u",
        "i",

        "ano",
        "anos",

        "depois",
        "antes",

        "para",
        "como",
        "quando",
        "onde",
        "porque",
        "por",
        "com",
        "sem",

        "tem",
        "tenho",
        "tinha",
        "ter",

        "ser",
        "sou",
        "era",

        "numero",
        "número",

        "palavra",
        "palavras",

        "casa",
        "teste",

        "voce",
        "você",

        "isso",
        "isto",

        "essa",
        "esse",

        "eles",
        "elas",

        "um",
        "uma",
        "dois",
        "duas",

        "meu",
        "minha",
        "meus",
        "minhas",

        "seu",
        "sua",
        "seus",
        "suas",

        "moro",
        "morar",
    }

    # ========================================================
    # SIGLAS
    # ========================================================

    SIGLAS_CONHECIDAS = {
        "CPU",
        "GPU",
        "RAM",
        "ROM",
        "SSD",
        "HDD",
        "USB",
        "HDMI",
        "API",
        "AI",
        "IA",
        "RAG",
        "STT",
        "TTS",
        "BCD",
        "ABC",
        "CD",
        "DVD",
        "PC",
        "PCs",
        "HTTP",
        "HTTPS",
        "URL",
        "JSON",
        "XML",
        "SQL",
        "CSS",
        "HTML",
        "JS",
        "C",
        "C#",
        "C++",
    }

    # ========================================================
    # UTILITÁRIOS
    # ========================================================

    @staticmethod
    def remover_acentos(texto):

        texto = unicodedata.normalize(
            "NFD",
            texto
        )

        return "".join(
            c
            for c in texto
            if unicodedata.category(c) != "Mn"
        )

    @staticmethod
    def tokenizar(texto):

        texto = texto.strip()

        texto = re.sub(
            r"[^\wÀ-ÿ+#\s]",
            " ",
            texto,
            flags=re.UNICODE
        )

        return texto.split()

    def normalizar_token(
        self,
        palavra
    ):

        return self.remover_acentos(
            palavra.lower().strip()
        )

    # ========================================================
    # OBTER VALOR NUMÉRICO
    # ========================================================

    def obter_valor_numero(
        self,
        palavra
    ):

        token = self.normalizar_token(
            palavra
        )

        if re.fullmatch(
            r"\d+",
            token
        ):

            return int(token)

        if token in self.CORRECOES_NUMERICAS:

            token = self.normalizar_token(
                self.CORRECOES_NUMERICAS[token]
            )

        for nome, valor in self.UNIDADES.items():

            if (
                self.normalizar_token(nome)
                == token
            ):

                return valor

        for nome, valor in self.DEZENAS.items():

            if (
                self.normalizar_token(nome)
                == token
            ):

                return valor

        for nome, valor in self.CENTENAS.items():

            if (
                self.normalizar_token(nome)
                == token
            ):

                return valor

        return None

    # ========================================================
    # TIPO DO NÚMERO
    # ========================================================

    def tipo_numero(
        self,
        palavra
    ):

        token = self.normalizar_token(
            palavra
        )

        if token in self.CORRECOES_NUMERICAS:

            token = self.normalizar_token(
                self.CORRECOES_NUMERICAS[token]
            )

        for nome, valor in self.UNIDADES.items():

            if (
                self.normalizar_token(nome)
                == token
            ):

                if 0 <= valor <= 9:

                    return "DIGITO"

                return "NUMERO"

        for nome in self.DEZENAS:

            if (
                self.normalizar_token(nome)
                == token
            ):

                return "DEZENA"

        for nome in self.CENTENAS:

            if (
                self.normalizar_token(nome)
                == token
            ):

                return "CENTENA"

        if token in self.MULTIPLICADORES:

            return "MULTIPLICADOR"

        return None

    # ========================================================
    # CORREÇÃO NUMÉRICA FUZZY
    # ========================================================

    def corrigir_numero_fonetico(
        self,
        palavra
    ):

        token = self.normalizar_token(
            palavra
        )

        candidatos = []

        candidatos.extend(
            self.UNIDADES.keys()
        )

        candidatos.extend(
            self.DEZENAS.keys()
        )

        candidatos.extend(
            self.CENTENAS.keys()
        )

        candidatos_normalizados = [
            self.normalizar_token(
                candidato
            )
            for candidato in candidatos
        ]

        semelhantes = difflib.get_close_matches(
            token,
            candidatos_normalizados,
            n=1,
            cutoff=0.90
        )

        if semelhantes:

            return semelhantes[0]

        return None

    # ========================================================
    # NÚMERO COMPOSTO
    # ========================================================

    def interpretar_numero_composto(
        self,
        palavras
    ):

        valores = []

        for palavra in palavras:

            token = self.normalizar_token(
                palavra
            )

            if token == "e":

                continue

            if token in self.CORRECOES_NUMERICAS:

                token = self.normalizar_token(
                    self.CORRECOES_NUMERICAS[token]
                )

            valor = self.obter_valor_numero(
                token
            )

            if valor is not None:

                valores.append(
                    (
                        "valor",
                        valor
                    )
                )

                continue

            if token in self.MULTIPLICADORES:

                valores.append(
                    (
                        "multiplicador",
                        self.MULTIPLICADORES[token]
                    )
                )

                continue

            corrigido = (
                self.corrigir_numero_fonetico(
                    token
                )
            )

            if corrigido:

                valor = (
                    self.obter_valor_numero(
                        corrigido
                    )
                )

                if valor is not None:

                    valores.append(
                        (
                            "valor",
                            valor
                        )
                    )

                    continue

            return None

        if not valores:

            return None

        total = 0
        atual = 0

        ultimo_valor = None

        for tipo, valor in valores:

            if tipo == "valor":

                # ------------------------------------------------
                # Impedir sequências absurdas como:
                #
                # dez onze
                #
                # que não representam naturalmente 21.
                # ------------------------------------------------

                if (
                    ultimo_valor is not None
                    and
                    ultimo_valor >= 10
                    and
                    valor >= 10
                    and
                    not (
                        ultimo_valor
                        >= 100
                    )
                ):

                    return None

                atual += valor

                ultimo_valor = valor

            elif tipo == "multiplicador":

                if atual == 0:

                    atual = 1

                total += (
                    atual
                    * valor
                )

                atual = 0

                ultimo_valor = None

        total += atual

        return str(total)

    # ========================================================
    # VALIDAR NÚMERO COMPOSTO
    # ========================================================

    def eh_numero_composto_real(
        self,
        palavras
    ):

        if len(palavras) < 2:

            return False

        tipos = []

        quantidade_conectores = 0

        for palavra in palavras:

            token = self.normalizar_token(
                palavra
            )

            if token == "e":

                quantidade_conectores += 1

                continue

            tipo = self.tipo_numero(
                palavra
            )

            if tipo is None:

                if token in self.MULTIPLICADORES:

                    tipo = "MULTIPLICADOR"

                else:

                    corrigido = (
                        self.corrigir_numero_fonetico(
                            palavra
                        )
                    )

                    if corrigido:

                        tipo = self.tipo_numero(
                            corrigido
                        )

            if tipo is None:

                return False

            tipos.append(
                tipo
            )

        if not tipos:

            return False

        # ----------------------------------------------------
        # Apenas dígitos falados
        # ----------------------------------------------------

        if all(
            tipo == "DIGITO"
            for tipo in tipos
        ):

            return False

        # ----------------------------------------------------
        # Dois números simples ligados por "e"
        # ----------------------------------------------------

        if (
            len(tipos) == 2
            and
            quantidade_conectores > 0
            and
            all(
                tipo in {
                    "DIGITO",
                    "NUMERO"
                }
                for tipo in tipos
            )
        ):

            return False

        possui_dezena = (
            "DEZENA" in tipos
        )

        possui_centena = (
            "CENTENA" in tipos
        )

        possui_multiplicador = (
            "MULTIPLICADOR" in tipos
        )

        if not (
            possui_dezena
            or
            possui_centena
            or
            possui_multiplicador
        ):

            return False

        # ----------------------------------------------------
        # Não aceitar:
        #
        # dez onze
        # vinte trinta
        #
        # como número composto.
        # ----------------------------------------------------

        for indice in range(
            len(tipos) - 1
        ):

            atual = tipos[indice]
            proximo = tipos[indice + 1]

            if (
                atual == "DEZENA"
                and
                proximo == "DEZENA"
            ):

                return False

            if (
                atual == "NUMERO"
                and
                proximo == "NUMERO"
            ):

                return False

        return True

    # ========================================================
    # ANÁLISE NUMÉRICA CONTEXTUAL
    # ========================================================

    def analisar_numero_contextual(
        self,
        palavras
    ):

        resultado = []

        i = 0

        while i < len(palavras):

            palavra = palavras[i]

            token = self.normalizar_token(
                palavra
            )

            # ------------------------------------------------
            # Números já reconhecidos pelo Google
            # ------------------------------------------------

            if re.fullmatch(
                r"\d+(?:[.,]\d+)?",
                token
            ):

                resultado.append(
                    palavra
                )

                i += 1

                continue

            # ------------------------------------------------
            # Sequência de dígitos falados
            # ------------------------------------------------

            if (
                self.tipo_numero(
                    palavra
                )
                == "DIGITO"
            ):

                bloco = []

                j = i

                while j < len(palavras):

                    atual = palavras[j]

                    if (
                        self.tipo_numero(
                            atual
                        )
                        == "DIGITO"
                    ):

                        valor = (
                            self.obter_valor_numero(
                                atual
                            )
                        )

                        bloco.append(
                            str(valor)
                        )

                        j += 1

                        continue

                    break

                resultado.extend(
                    bloco
                )

                i = j

                continue

            # ------------------------------------------------
            # Procurar número composto
            # ------------------------------------------------

            melhor_fim = None
            melhor_numero = None

            limite = min(
                len(palavras),
                i + 7
            )

            for fim in range(
                limite,
                i + 1,
                -1
            ):

                if (
                    fim - i
                    < 2
                ):

                    continue

                trecho = palavras[
                    i:fim
                ]

                if not self.eh_numero_composto_real(
                    trecho
                ):

                    continue

                numero = (
                    self.interpretar_numero_composto(
                        trecho
                    )
                )

                if numero is not None:

                    melhor_fim = fim
                    melhor_numero = numero

                    break

            if (
                melhor_fim is not None
                and
                melhor_numero is not None
            ):

                resultado.append(
                    melhor_numero
                )

                i = melhor_fim

                continue

            # ------------------------------------------------
            # Número isolado
            # ------------------------------------------------

            numero = self.obter_valor_numero(
                palavra
            )

            if numero is not None:

                resultado.append(
                    str(numero)
                )

                i += 1

                continue

            # ------------------------------------------------
            # Palavra normal
            # ------------------------------------------------

            resultado.append(
                palavra
            )

            i += 1

        return resultado

    # ========================================================
    # LETRAS
    # ========================================================

    def corrigir_letra(
        self,
        palavra,
        permitir_fuzzy=False
    ):

        token = self.normalizar_token(
            palavra
        )

        protegidas = {
            self.normalizar_token(
                palavra_protegida
            )
            for palavra_protegida
            in self.PALAVRAS_PROTEGIDAS
        }

        if token in protegidas:

            return None

        for nome, letra in self.LETRAS.items():

            if (
                self.normalizar_token(nome)
                == token
            ):

                return letra

        if not permitir_fuzzy:

            return None

        candidatos = []

        for nome in self.LETRAS:

            normalizado = (
                self.normalizar_token(
                    nome
                )
            )

            if (
                normalizado
                not in protegidas
            ):

                candidatos.append(
                    normalizado
                )

        semelhantes = difflib.get_close_matches(
            token,
            candidatos,
            n=1,
            cutoff=0.93
        )

        if semelhantes:

            encontrado = semelhantes[0]

            for nome, letra in self.LETRAS.items():

                if (
                    self.normalizar_token(nome)
                    == encontrado
                ):

                    return letra

        return None

    # ========================================================
    # SIGLAS
    # ========================================================

    def interpretar_sigla(
        self,
        palavra
    ):

        if palavra in self.SIGLAS_CONHECIDAS:

            return " ".join(
                list(palavra)
            )

        if (
            len(palavra) >= 2
            and
            len(palavra) <= 6
            and
            palavra.isupper()
            and
            re.fullmatch(
                r"[A-Z]+",
                palavra
            )
        ):

            return " ".join(
                list(palavra)
            )

        return None

    # ========================================================
    # INTERPRETAR
    # ========================================================

    def interpretar(
        self,
        texto
    ):

        if not texto:

            return ""

        texto = texto.strip()

        if not texto:

            return ""

        palavras = self.tokenizar(
            texto
        )

        if not palavras:

            return ""

        resultado = (
            self.analisar_numero_contextual(
                palavras
            )
        )

        final = []

        i = 0

        while i < len(resultado):

            palavra = resultado[i]

            # ------------------------------------------------
            # Siglas
            # ------------------------------------------------

            sigla = (
                self.interpretar_sigla(
                    palavra
                )
            )

            if sigla:

                final.append(
                    sigla
                )

                i += 1

                continue

            # ------------------------------------------------
            # Bloco explícito de letras
            # ------------------------------------------------

            bloco = []

            j = i

            while j < len(resultado):

                letra = (
                    self.corrigir_letra(
                        resultado[j],
                        permitir_fuzzy=False
                    )
                )

                if not letra:

                    break

                bloco.append(
                    letra
                )

                j += 1

            # ------------------------------------------------
            # Pelo menos duas letras consecutivas
            # ------------------------------------------------

            if len(bloco) >= 2:

                final.extend(
                    bloco
                )

                i = j

                continue

            # ------------------------------------------------
            # Palavra normal
            # ------------------------------------------------

            final.append(
                palavra
            )

            i += 1

        return " ".join(
            final
        )


# ============================================================
# ANALISADOR DE ALTERNATIVAS DO GOOGLE
# ============================================================

class AnalisadorAlternativas:

    PALAVRAS_COMUNS = {
        "o",
        "a",
        "os",
        "as",
        "um",
        "uma",
        "de",
        "do",
        "da",
        "e",
        "que",
        "para",
        "por",
        "com",
        "sem",
        "em",
        "no",
        "na",
        "eu",
        "ele",
        "ela",
        "isso",
        "tem",
        "tenho",
        "foi",
        "ser",
        "como",
        "não",
        "sim",
        "meu",
        "minha",
        "meus",
        "minhas",
        "ano",
        "anos",
    }

    # ========================================================
    # NORMALIZAR
    # ========================================================

    def normalizar(
        self,
        texto
    ):

        texto = texto.lower()

        texto = unicodedata.normalize(
            "NFD",
            texto
        )

        return "".join(
            c
            for c in texto
            if unicodedata.category(c) != "Mn"
        )

    # ========================================================
    # TOKENS
    # ========================================================

    def tokens_normalizados(
        self,
        texto
    ):

        return self.normalizar(
            texto
        ).split()

    # ========================================================
    # DETECTAR NÚMEROS SUSPEITOS
    # ========================================================

    def analisar_numeros_suspeitos(
        self,
        texto
    ):

        tokens = self.tokens_normalizados(
            texto
        )

        penalidade = 0.0

        numeros = []

        for token in tokens:

            if re.fullmatch(
                r"\d+",
                token
            ):

                numeros.append(
                    token
                )

        # ----------------------------------------------------
        # Números extremamente longos
        # ----------------------------------------------------

        for numero in numeros:

            if len(numero) >= 7:

                penalidade += 3.0

        # ----------------------------------------------------
        # Números contendo outros números
        # ----------------------------------------------------

        for i in range(
            len(numeros)
        ):

            numero_atual = numeros[i]

            for j in range(
                i + 1,
                len(numeros)
            ):

                numero_proximo = numeros[j]

                if (
                    numero_atual
                    in numero_proximo
                    and
                    numero_atual
                    != numero_proximo
                ):

                    penalidade += 4.0

                elif (
                    numero_proximo
                    in numero_atual
                    and
                    numero_atual
                    != numero_proximo
                ):

                    penalidade += 4.0

        return penalidade

    # ========================================================
    # DETECTAR FUSÃO NUMÉRICA
    # ========================================================

    def detectar_fusao_numerica(
        self,
        texto,
        interpretado
    ):

        bruto = self.tokens_normalizados(
            texto
        )

        if not bruto:

            return 0.0

        penalidade = 0.0

        palavras_digitais = {
            "zero",
            "um",
            "uma",
            "uns",
            "umas",
            "dois",
            "duas",
            "tres",
            "quatro",
            "cinco",
            "seis",
            "sete",
            "oito",
            "nove",
        }

        quantidade_digitais = sum(
            1
            for token in bruto
            if token in palavras_digitais
        )

        # ----------------------------------------------------
        # Se o Google preservou vários dígitos falados
        # como palavras, isso é uma informação importante.
        # ----------------------------------------------------

        if quantidade_digitais >= 3:

            numeros_grandes = [
                token
                for token in bruto
                if re.fullmatch(
                    r"\d{4,}",
                    token
                )
            ]

            if numeros_grandes:

                penalidade += (
                    quantidade_digitais
                    * 3.0
                )

        return penalidade

    # ========================================================
    # DETECTAR CONTEXTO CONTAMINADO
    # ========================================================

    def detectar_contexto_contaminado(
        self,
        texto_maior,
        texto_menor
    ):

        maior = self.tokens_normalizados(
            texto_maior
        )

        menor = self.tokens_normalizados(
            texto_menor
        )

        if not maior or not menor:

            return False

        if len(maior) <= len(menor):

            return False

        tamanho = len(
            menor
        )

        for inicio in range(
            len(maior)
            - tamanho
            + 1
        ):

            trecho = maior[
                inicio:
                inicio + tamanho
            ]

            if trecho == menor:

                return True

        return False

    # ========================================================
    # SIMILARIDADE
    # ========================================================

    def similaridade(
        self,
        texto_a,
        texto_b
    ):

        return difflib.SequenceMatcher(
            None,
            self.normalizar(
                texto_a
            ),
            self.normalizar(
                texto_b
            )
        ).ratio()

    # ========================================================
    # PENALIDADE DE TAMANHO
    # ========================================================

    def penalidade_tamanho(
        self,
        texto
    ):

        palavras = self.tokens_normalizados(
            texto
        )

        quantidade = len(
            palavras
        )

        if quantidade <= 12:

            return 0.0

        excesso = (
            quantidade - 12
        )

        return excesso * 1.2

    # ========================================================
    # SCORE
    # ========================================================

    def score(
        self,
        texto,
        confianca,
        confianca_disponivel,
        interpretado,
        interpretador
    ):

        if not texto:

            return -999999.0

        palavras = self.tokens_normalizados(
            texto
        )

        score = 0.0

        # ----------------------------------------------------
        # Confiança
        #
        # Não pode dominar todo o algoritmo.
        # ----------------------------------------------------

        if confianca_disponivel:

            score += (
                float(confianca)
                * 15.0
            )

        # ----------------------------------------------------
        # Tamanho
        # ----------------------------------------------------

        score -= (
            self.penalidade_tamanho(
                texto
            )
        )

        # ----------------------------------------------------
        # Números suspeitos
        # ----------------------------------------------------

        score -= (
            self.analisar_numeros_suspeitos(
                texto
            )
        )

        # ----------------------------------------------------
        # Fusão numérica
        # ----------------------------------------------------

        score -= (
            self.detectar_fusao_numerica(
                texto,
                interpretado
            )
        )

        # ----------------------------------------------------
        # Repetições
        # ----------------------------------------------------

        for i in range(
            1,
            len(palavras)
        ):

            atual = self.normalizar(
                palavras[i]
            )

            anterior = self.normalizar(
                palavras[i - 1]
            )

            if atual == anterior:

                score -= 5.0

        # ----------------------------------------------------
        # Palavras comuns
        # ----------------------------------------------------

        for palavra in palavras:

            if (
                self.normalizar(
                    palavra
                )
                in self.PALAVRAS_COMUNS
            ):

                score += 0.5

        # ----------------------------------------------------
        # Coerência entre bruto e interpretado
        # ----------------------------------------------------

        if interpretado:

            distancia = (
                self.similaridade(
                    texto,
                    interpretado
                )
            )

            score += (
                distancia
                * 2.0
            )

        return score

    # ========================================================
    # ESCOLHER MELHOR ALTERNATIVA
    # ========================================================

    def escolher(
        self,
        resposta,
        interpretador
    ):

        if not isinstance(
            resposta,
            dict
        ):

            return ""

        alternativas = (
            resposta.get(
                "alternative",
                []
            )
        )

        if not alternativas:

            return ""

        candidatos = []

        # ====================================================
        # CRIAR CANDIDATOS
        # ====================================================

        for indice, alternativa in enumerate(
            alternativas[
                :MAX_ALTERNATIVAS
            ]
        ):

            texto = str(
                alternativa.get(
                    "transcript",
                    ""
                )
            ).strip()

            if not texto:

                continue

            confidence_original = (
                alternativa.get(
                    "confidence",
                    None
                )
            )

            confianca_disponivel = (
                confidence_original
                is not None
            )

            try:

                confianca = float(
                    confidence_original
                )

            except (
                ValueError,
                TypeError
            ):

                confianca = 0.0

                confianca_disponivel = False

            interpretado = (
                interpretador.interpretar(
                    texto
                )
            )

            score = self.score(
                texto,
                confianca,
                confianca_disponivel,
                interpretado,
                interpretador
            )

            candidatos.append(
                {
                    "indice":
                        indice + 1,

                    "texto":
                        texto,

                    "interpretado":
                        interpretado,

                    "confianca":
                        confianca,

                    "confianca_disponivel":
                        confianca_disponivel,

                    "score":
                        score,
                }
            )

        if not candidatos:

            return ""

        # ====================================================
        # COMPARAR ALTERNATIVAS
        # ====================================================

        for candidato_a in candidatos:

            for candidato_b in candidatos:

                if (
                    candidato_a
                    is candidato_b
                ):

                    continue

                texto_a = (
                    candidato_a["texto"]
                )

                texto_b = (
                    candidato_b["texto"]
                )

                if self.detectar_contexto_contaminado(
                    texto_a,
                    texto_b
                ):

                    tokens_a = (
                        self.tokens_normalizados(
                            texto_a
                        )
                    )

                    tokens_b = (
                        self.tokens_normalizados(
                            texto_b
                        )
                    )

                    diferenca = (
                        len(tokens_a)
                        -
                        len(tokens_b)
                    )

                    if diferenca >= 2:

                        candidato_a["score"] -= (
                            8.0
                            +
                            diferenca * 1.5
                        )

                        candidato_b["score"] += 5.0

        # ====================================================
        # ORDENAR
        # ====================================================

        candidatos.sort(
            key=lambda candidato:
                candidato["score"],
            reverse=True
        )

        melhor = candidatos[0]

        # ====================================================
        # DEBUG
        # ====================================================

        print()
        print(
            "[ALTERNATIVAS GOOGLE]"
        )

        for candidato in candidatos:

            if candidato[
                "confianca_disponivel"
            ]:

                confianca_texto = (
                    f"{candidato['confianca']:.3f}"
                )

            else:

                confianca_texto = (
                    "não informada"
                )

            print(
                f"{candidato['indice']}. "
                f"{candidato['texto']} "
                f"| confiança="
                f"{confianca_texto} "
                f"| score="
                f"{candidato['score']:.2f}"
            )

            print(
                f"   -> entendido: "
                f"{candidato['interpretado']}"
            )

        print(
            f"[ESCOLHIDA] "
            f"{melhor['texto']}"
        )

        return melhor["texto"]


# ============================================================
# APLICAÇÃO
# ============================================================

class AppTranscritorGrande:

    def __init__(
        self,
        janela_principal
    ):

        self.janela = (
            janela_principal
        )

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

        # ====================================================
        # ESTADO
        # ====================================================

        self.rodando = False

        self.thread_captura = None

        self.thread_processamento = None

        self.fila_processamento = (
            queue.Queue()
        )

        self.limiar_voz_atual = (
            LIMIAR_VOZ_PADRAO
        )

        self.nivel_ruido = 0.0

        # ====================================================
        # INTERPRETAÇÃO
        # ====================================================

        self.interpretador = (
            InterpretadorLinguagem()
        )

        self.analisador_alternativas = (
            AnalisadorAlternativas()
        )

        # ====================================================
        # GOOGLE STT
        # ====================================================

        self.reconhecedor = (
            sr.Recognizer()
        )

        self.reconhecedor.dynamic_energy_threshold = True

        self.reconhecedor.energy_threshold = 300

        self.reconhecedor.pause_threshold = 0.8

        self.reconhecedor.phrase_threshold = 0.2

        self.reconhecedor.non_speaking_duration = 0.3

        # ====================================================
        # INTERFACE
        # ====================================================

        self.btn_controle = tk.Button(
            self.janela,
            text="LIGAR TRANSCRIÇÃO",
            bg="#107C41",
            fg="white",
            font=(
                "Arial",
                12,
                "bold"
            ),
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
            font=(
                "Arial",
                10,
                "italic"
            )
        )

        self.lbl_status.pack(
            pady=5
        )

        self.caixa_grande = (
            scrolledtext.ScrolledText(
                self.janela,
                font=(
                    "Arial",
                    11
                ),
                wrap=tk.WORD,
                height=17
            )
        )

        self.caixa_grande.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(
                0,
                20
            )
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

    def injetar_texto_na_caixa(
        self,
        texto
    ):

        self.caixa_grande.config(
            state=tk.NORMAL
        )

        self.caixa_grande.insert(
            tk.END,
            texto + "\n"
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
            )
            / 32768.0
        )

        rms = np.sqrt(
            np.mean(
                audio_float
                * audio_float
            )
        )

        return float(
            rms
        )

    def normalizar_audio(
        self,
        audio
    ):

        if len(audio) == 0:

            return audio

        audio_float = (
            audio.astype(
                np.float32
            )
        )

        pico = np.max(
            np.abs(
                audio_float
            )
        )

        if pico < 1:

            return audio.astype(
                np.int16
            )

        if pico < 7000:

            ganho = min(
                2.5,
                12000.0 / pico
            )

            audio_float *= ganho

        audio_float = np.clip(
            audio_float,
            -32768,
            32767
        )

        return audio_float.astype(
            np.int16
        )

    # ========================================================
    # CALIBRAÇÃO
    # ========================================================

    def calibrar_ruido(
        self,
        stream
    ):

        niveis = []

        quantidade = max(
            1,
            int(
                CALIBRACAO_SEGUNDOS
                * FREQUENCIA
                / BUFFER_FRAMES
            )
        )

        for _ in range(
            quantidade
        ):

            dados, _ = (
                stream.read(
                    BUFFER_FRAMES
                )
            )

            audio = (
                dados[:, 0]
                .copy()
            )

            niveis.append(
                self.calcular_nivel_audio(
                    audio
                )
            )

        if not niveis:

            self.nivel_ruido = 0.0

            self.limiar_voz_atual = (
                LIMIAR_VOZ_PADRAO
            )

            return (
                self.limiar_voz_atual
            )

        ruido = float(
            np.percentile(
                niveis,
                75
            )
        )

        limiar = (
            ruido
            * FATOR_LIMIAR_RUIDO
        )

        limiar = max(
            LIMIAR_MINIMO_VOZ,
            min(
                LIMIAR_MAXIMO_VOZ,
                limiar
            )
        )

        self.nivel_ruido = ruido

        self.limiar_voz_atual = (
            limiar
        )

        return limiar

    # ========================================================
    # PROCESSAR ÁUDIO
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

            if audio.ndim > 1:

                audio = audio[:, 0]

            duracao = (
                len(audio)
                / FREQUENCIA
            )

            energia = (
                self.calcular_nivel_audio(
                    audio
                )
            )

            if (
                duracao
                < DURACAO_MINIMA_FALA
            ):

                return

            if (
                energia
                < ENERGIA_MINIMA_FALA
            ):

                return

            audio = (
                self.normalizar_audio(
                    audio
                )
            )

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

                resposta = (
                    self.reconhecedor
                    .recognize_google(
                        audio_data,
                        language="pt-BR",
                        show_all=True
                    )
                )

                texto = (
                    self.analisador_alternativas
                    .escolher(
                        resposta,
                        self.interpretador
                    )
                )

                if (
                    not texto
                    and isinstance(
                        resposta,
                        str
                    )
                ):

                    texto = (
                        resposta.strip()
                    )

                if texto:

                    print()
                    print(
                        "=" * 60
                    )

                    print(
                        f"[STT] {texto}"
                    )

                    texto_final = (
                        self.interpretador
                        .interpretar(
                            texto
                        )
                    )

                    print(
                        f"[ENTENDIDO] "
                        f"{texto_final}"
                    )

                    print(
                        "=" * 60
                    )

                    self.janela.after(
                        0,
                        self.injetar_texto_na_caixa,
                        f"Você disse: {texto_final}"
                    )

            except sr.UnknownValueError:

                print(
                    "[STT] Não foi possível "
                    "entender a fala."
                )

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
    # THREAD DE PROCESSAMENTO
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
    # LOOP DO MICROFONE
    # ========================================================

    def seu_loop_original(
        self
    ):

        try:

            dispositivo = (
                sd.default.device
            )

            print(
                f"Dispositivo de áudio: "
                f"{dispositivo}"
            )

            with sd.InputStream(
                samplerate=FREQUENCIA,
                channels=1,
                dtype="int16",
                blocksize=BUFFER_FRAMES
            ) as stream:

                self.janela.after(
                    0,
                    self.atualizar_status_interface,
                    "Calibrando microfone...",
                    "orange"
                )

                limiar = (
                    self.calibrar_ruido(
                        stream
                    )
                )

                print(
                    f"Nível de ruído: "
                    f"{self.nivel_ruido:.6f}"
                )

                print(
                    f"Limiar de voz: "
                    f"{limiar:.6f}"
                )

                audio_frase = []

                pre_buffer = []

                falando = False

                tempo_inicio_fala = None

                ultimo_som = None

                self.thread_processamento = (
                    threading.Thread(
                        target=(
                            self.trabalhador_processamento
                        ),
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

                while self.rodando:

                    dados, overflow = (
                        stream.read(
                            BUFFER_FRAMES
                        )
                    )

                    if overflow:

                        print(
                            "Aviso: overflow "
                            "do áudio."
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
                    # Pré-buffer
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
                    # Início da fala
                    # ------------------------------------------------

                    if (
                        nivel
                        >= self.limiar_voz_atual
                    ):

                        if not falando:

                            falando = True

                            tempo_inicio_fala = (
                                agora
                            )

                            audio_frase = []

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
                    # Silêncio
                    # ------------------------------------------------

                    elif falando:

                        audio_frase.append(
                            audio.copy()
                        )

                        tempo_silencio = (
                            agora
                            - ultimo_som
                            if ultimo_som
                            else 0
                        )

                        tempo_fala = (
                            agora
                            - tempo_inicio_fala
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

                        if (
                            terminou_por_silencio
                            or
                            terminou_por_tempo
                        ):

                            falando = False

                            if audio_frase:

                                audio_completo = (
                                    np.concatenate(
                                        audio_frase
                                    )
                                )

                                audio_frase = []

                                self.fila_processamento.put(
                                    audio_completo
                                )

                            pre_buffer = []

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
    # ERRO DE CONEXÃO
    # ========================================================

    def mostrar_erro_conexao(
        self,
        erro
    ):

        messagebox.showerror(
            "Erro de Conexão",
            "Erro de conexão com o Google STT:\n\n"
            f"{erro}"
        )

        self.desligar_recursos()

    # ========================================================
    # ERRO DE HARDWARE
    # ========================================================

    def mostrar_erro_hardware(
        self,
        erro
    ):

        messagebox.showerror(
            "Erro de Hardware",
            "Falha no microfone:\n\n"
            f"{erro}"
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

            self.thread_captura = (
                threading.Thread(
                    target=self.seu_loop_original,
                    daemon=True
                )
            )

            self.thread_captura.start()

            messagebox.showinfo(
                "Sucesso",
                "A transcrição contínua "
                "foi iniciada."
            )

        else:

            self.desligar_recursos()

            messagebox.showinfo(
                "Sistema",
                "Transcrição encerrada "
                "com segurança."
            )

    # ========================================================
    # DESLIGAR
    # ========================================================

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
