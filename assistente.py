mport speech_recognition as sr
import pyttsx3
import asyncio
from datetime import datetime
import sqlite3

# Variável global para armazenar o nome do usuário
nomeUser = ''

# Conecta ao banco de dados (ou cria se não existir)
conn = sqlite3.connect('meubanco.db')

# Cria um cursor para interagir com o banco de dados
cursor = conn.cursor()

# Cria a tabela se ela não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
)
''')

# Cria a tabela lembretes se ela não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS lembretes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Confirma a criação das tabelas
conn.commit()

# Inicializa o reconhecedor
recognizer = sr.Recognizer()

# Inicializa o engine de TTS
engine = pyttsx3.init()

# Configura o volume e a taxa de fala
engine.setProperty('rate', 220)
engine.setProperty('volume', 1.0)

async def speak(text):
    engine.say(text)
    engine.runAndWait()

async def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        
        # Verificar se é a primeira vez usando o assistente, se for não haverá dados cadastrados no database
        cursor.execute('SELECT * FROM usuarios')
        todos_usuarios = cursor.fetchall()
        
        if len(todos_usuarios) == 0:
            await speak("Olá, eu sou a Beatriz, serei sua assistente. Para começarmos, diga-me seu nome para que possa salvá-lo na minha base de dados!")
            print('Ouvindo...')
            audio = recognizer.listen(source)
            try:
                # Usa o Google Web Speech API para transcrever o áudio
                text_nome = recognizer.recognize_google(audio, language='pt-BR').lower()
                
                # Salvar o nome do usuário no database
                cursor.execute('INSERT INTO usuarios (nome) VALUES (?)', (text_nome,))
                conn.commit()
                await speak(f'Nome {text_nome} salvo com sucesso!')
                return text_nome
            except sr.UnknownValueError:
                await speak("Desculpe, não consegui entender. Pode repetir seu nome?")
                return None
            except sr.RequestError as e:
                print(f"Erro ao solicitar resultados do serviço de reconhecimento de fala; {e}")
                return None
        else:
            global nomeUser
            id_usuario, nomeUser = todos_usuarios[0]
            print("Ouvindo...")
            audio = recognizer.listen(source)
            return audio

async def process_command():
    
    while True:
        try:
            chamado = await listen()
            if chamado is not None:
                # Verifica se chamado é uma instância de AudioData
                if isinstance(chamado, sr.AudioData):
                    # Usa o Google Web Speech API para transcrever o áudio
                    text = recognizer.recognize_google(chamado, language='pt-BR').lower()
                    if "beatriz" in text:
                        print(nomeUser, "Como posso te ajudar?")
                        await speak(f"olá {nomeUser}, como posso ajudar?")
                        comando = await listen()
                        if comando is not None and isinstance(comando, sr.AudioData):
                            try:
                                txt_comando = recognizer.recognize_google(comando, language='pt-BR').lower()
                                print("Comando recebido: " + txt_comando)
                                
                                if 'como você está' in txt_comando:
                                    await speak(f'Estou bem {nomeUser}, obrigada por perguntar!')
                                elif 'que horas são' in txt_comando:
                                    current_time = datetime.now().strftime("%H:%M")
                                    await speak(f'Agora são {current_time}')
                                elif 'qual é a data de hoje' in txt_comando:
                                    current_date = datetime.now().strftime("%d/%m/%Y")
                                    await speak(f'Hoje é {current_date}')
                                elif 'definir lembrete' in txt_comando:
                                    await speak("Qual será o título do lembrete?")
                                    with sr.Microphone() as source:
                                        recognizer.adjust_for_ambient_noise(source)
                                        titulo_audio = recognizer.listen(source)
                                        try:
                                            titulo_lembrete = recognizer.recognize_google(titulo_audio, language='pt-BR').lower()
                                            await speak(f'O título do lembrete foi definido como {titulo_lembrete}')
                                            # Salvar o lembrete no banco de dados
                                            cursor.execute('INSERT INTO lembretes (titulo) VALUES (?)', (titulo_lembrete,))
                                            conn.commit()
                                        except sr.UnknownValueError:
                                            await speak("Desculpe, não consegui entender o título do lembrete.")
                                    # await speak('Lembrete definido.')
                                else:
                                    await speak('Desculpe, não entendi o comando.')
                            except sr.UnknownValueError:
                                await speak("Desculpe, não consegui entender o comando.")
                        else:
                            await speak("Desculpe, não consegui captar o áudio.")
                else:
                    await speak("Desculpe, não consegui captar o áudio.")
        except sr.UnknownValueError:
            print("Não consegui entender o áudio.")
        except sr.RequestError as e:
            print(f"Erro ao solicitar resultados do serviço de reconhecimento de fala; {e}")
            break

async def main():
    await process_command()

if _name_ == "_main_":
    asyncio.run(main())