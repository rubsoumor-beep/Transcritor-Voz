# Transcritor de Voz Dinâmico

Aplicativo desktop desenvolvido em **Python** para captura de áudio pelo microfone e **transcrição automática de voz em português do Brasil**.

O sistema realiza a captura de áudio em blocos de 7 segundos e utiliza o serviço de reconhecimento de voz do Google para converter a fala em texto.

## Funcionalidades

* Captura de áudio pelo microfone
* Transcrição automática de voz
* Reconhecimento configurado para português do Brasil (`pt-BR`)
* Interface gráfica utilizando Tkinter
* Transcrição contínua enquanto o sistema estiver ligado
* Histórico das transcrições exibido na própria aplicação
* Processamento da captura de áudio em uma thread separada para evitar o congelamento da interface
* Captura de áudio em **16 kHz**
* Blocos de gravação de **7 segundos**
* Utilização do Google Speech Recognition para conversão de voz em texto

## Tecnologias utilizadas

* **Python**
* **Tkinter** — interface gráfica
* **SoundDevice** — captura de áudio
* **SpeechRecognition** — reconhecimento e processamento da fala
* **NumPy** — manipulação dos dados de áudio
* **Google Speech Recognition** — transcrição da voz

## Estrutura do projeto

```text
Transcritor-Voz/
├── transcritor.py
├── Transcritor.exe
├── README.md
└── .gitignore
```

### Arquivos

| Arquivo           | Descrição                            |
| ----------------- | ------------------------------------ |
| `transcritor.py`  | Código-fonte principal da aplicação  |
| `Transcritor.exe` | Versão executável para Windows       |
| `README.md`       | Documentação do projeto              |
| `.gitignore`      | Arquivos e pastas ignorados pelo Git |

## Como executar

### Pré-requisitos

É necessário ter o **Python 3** instalado no computador.

Instale as dependências:

```bash
pip install sounddevice SpeechRecognition numpy
```

Depois execute:

```bash
python transcritor.py
```

## Como utilizar

1. Execute o programa.
2. Clique em **LIGAR TRANSCRIÇÃO**.
3. O aplicativo começará a capturar o áudio do microfone.
4. Fale normalmente.
5. O áudio será enviado para o serviço de reconhecimento de voz.
6. A transcrição aparecerá na área de texto.
7. Para interromper o sistema, clique no botão de desligamento.

## Configurações

As principais configurações do sistema estão definidas no código:

```python
frequencia = 16000
segundos = 7
```

### Frequência de áudio

O sistema utiliza uma frequência de amostragem de:

```text
16000 Hz
```

### Duração da captura

Cada ciclo de captura possui:

```text
7 segundos
```

Após a captura, o áudio é enviado para reconhecimento e o processo continua enquanto a transcrição estiver ativada.

## Reconhecimento de voz

O projeto utiliza o mecanismo de reconhecimento do Google através da biblioteca `SpeechRecognition`.

O idioma está configurado para:

```text
pt-BR
```

Portanto, o sistema foi desenvolvido principalmente para transcrição de **português brasileiro**.

> O reconhecimento de voz depende de uma conexão com a internet para acessar o serviço utilizado pela aplicação.

## Versão executável

O projeto também disponibiliza uma versão `.exe` para Windows, permitindo executar o aplicativo sem precisar iniciar diretamente o arquivo Python.

```text
Transcritor.exe
```

## Observações

O aplicativo precisa ter acesso ao microfone do computador.

A qualidade da transcrição pode variar de acordo com:

* qualidade do microfone;
* nível de ruído do ambiente;
* clareza da fala;
* conexão com a internet;
* disponibilidade do serviço de reconhecimento de voz.

## Segurança

O projeto não deve conter chaves de API, senhas, tokens ou outras credenciais privadas.

Arquivos de configuração e informações sensíveis devem permanecer fora do repositório público.

## Status

**Versão:** 1.0

**Plataforma:** Windows

**Interface:** Tkinter

**Idioma principal:** Português (Brasil)

## Autor

Desenvolvido por **Rubens Morais**.

Projeto desenvolvido como parte dos experimentos e aplicações de software relacionados ao ecossistema de ferramentas de voz e inteligência artificial.
