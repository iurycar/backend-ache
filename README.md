# Backend Aché: Sistema de Cronogramas Modulares e Chatbot

## Introdução

Este projeto apresenta o backend desenvolvido para para otimizar a gestão de projetos e a organização de cronogramas. Criada para o **Challenge FIAP 2025, em colaboração com a Aché**. 

O objetivo do desafio foi desenvolver uma ferramenta para gestão de cronogramas modulares, que utilize tecnologias, como a Inteligência Artificial e o Processamento de Linguagem Natural, para maximizar a eficiência no desenvolvimento de projetos. Esse projeto é parte da nossa resposta a essa necessidade, oferecendo um sistema de tratamento de dados e um chatbot eficientes. O chatbot Melora possui um repositório dedicado [Melora](https://github.com/iurycar/Melora-chatbot).

## Como funciona

O backend foi projetado para ser o centro da aplicação web, gerenciando a lógica de negócio, a comunicação com a API de IA e o controle de arquivos. As principais funcionalidades incluem:
* **Chatbot Inteligente:** Um assistente virtual com dois modos de operação:

    * **Modo Padrão:** Para interações rápidas e comandos específicos (por exemplo, buscar tarefas, filtrar). A lógica é baseada em termos-chave definidos.

    * **Modo Avançado:** Para interações mais complexas e criativas. Utiliza o modelo de IA Google Gemini para gerar respostas dinâmicas e contextuais.

* **Autenticação de Usuário:** Um sistema de login simples, gerenciado por sessões do Flask, para autenticar usuários e garantir que apenas pessoas autorizadas possam interagir com a aplicação.

* **Gestão de Arquivos:** Um sistema seguro para upload e exclusão de arquivos de planilha (.xlsx, .csv), com controle de acesso para garantir que cada usuário só possa manipular seus próprios arquivos.

* **Persistência de Dados:** As informações dos arquivos importados são armazenadas de forma persistente em um arquivo JSON local, simulando um banco de dados, para que os dados não sejam perdidos ao reiniciar o servidor.

## Tecnologias principais
O projeto é construído com as seguintes tecnologias:
* **Python:** Linguagem de programação principal.
* **Flask:** Micro-framework web para a criação da API REST.
* **Flask-CORS:** Para lidar com as questões de segurança entre o frontend e o backend.
* **python-doenv:** Para gerenciar de forma segura as variáveis de ambiente.
* **google-generativeai:** SDK oficial do Google para interagir com a API do Gemini.
* **pandas:** Biblioteca de manipulação e análise de dados, ideal para trabalhar com arquivos de panilha.
* **UUID:** Para a criação de identificadores únicos para os arquivos e os usuários.

```
backend-aché/
├── backend/
│   ├── uploads/            # Diretório para arquivos de planilha
│   ├── __init__.py         # Inicializa o pacote
│   ├── app.py              # Ponto de entrada da aplicação
│   ├── auth.py             # Blueprint para rotas de autenticação (login/logout)
│   └── files.py            # Blueprint para rotas de arquivos (upload/download/delete)
│   └── db.py               # Lógica de comunicação com o banco de dados MySQL
│   └── from_to_mysql.py    # Converte os dados das planilhas para o MySQL e vice-versa
├── chatbotV8/
│   ├── __init__.py         # Inicializa o pacote
│   ├── chatbot.py          # Rota e lógica de interação do chatbot
│   ├── interpretador.py    # Lógica de interpretação da mensagem
│   ├── organizador.py      # Lógica de comunicação com o Gemini e tratamento de panilhas
│   └── treinar.py          # Dados para o modo padrão do chatbot
├── .env                    # Variáveis de ambiente (sua chave secreta, API Key Gemini e acesso ao MySQL)
└── requirements.txt        # Lista de dependências do Python
```

## Como colocar para funcionar
### 1. Pré-requisitos
Certifique-se de ter o `Python 3.8+` e o `pip` instalados em seu sistema.

### 2. Configurar o ambiente
Clone o repositório:
```
git clone https://github.com/iurycar/backend-ache
```

Instale todas as dependências listadas no `requirements.txt`:
```
pip install -r requirements.txt
```

### 3. Variáveis do ambiente
Crie um arquivo chamado `.env` na pasta principal do projeto (`backend-aché`), siga o exemplo `.env.example`. Adicione as seguintes chaves com seus respectivos valores:

```
FLASK_SECRET_KEY="SUA_CHAVE_SECRETA_AQUI"
GOOGLE_API_KEY="SUA_CHAVE_GEMINI_AQUI"
USER_DB="NOME_DE_USUARIO_DO_BANCO_DE_DADOS"
PASSWORD_DB="SENHA_DO_BANCO_DE_DADOS"
HOST_DB="HOST_DO_BANCO_DE_DADOS"
PORT_DB="0000"
DATABASE="NOME_DO_BANCO_DE_DADOS"
```

* **FLASK_SECRET_KEY:** Uma chave de sessão segura. Você pode adicionar qualquer valor aleatório.
* **GOOGLE_API_KEY:** A chave da API do Gemini, pode ser criada em [Google AI Studio](https://aistudio.google.com/app/apikey).
* **DEMAIS VARIÁVEIS:** É necessário fazer download e configurar o MySQL. Disponível em: [MySQL Download](https://www.mysql.com/downloads/).

### 4. Configurar o MySQL
Na pasta `database` está o arquivo `TABELAS_ACHÉ-MySQL.sql` com os comandos para criar um banco de dados `ache_db` que armazena as informações dos usuários e os dados das planilhas importadas.

![Diagrama](/assets/Database.jpg)

### 5. Executar o servidor
Navegue até o diretório do projeto
```
cd D:\...\backend-aché\
```

E execute o seguinte comando, para iniciar o servidor
```
D:\...\backend-aché> python -m backend.app
```

O servidor estará disponível em `http://127.0.0.1:5000` e pronto para receber requisições do frontend. Para fazer login, use as credenciais simuladas no arquivo `auth.py`:

* **Email:** `usuario@empresa.com.br`
* **Senha:** `123456`