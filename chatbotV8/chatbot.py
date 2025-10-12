from flask import Blueprint, request, jsonify, session
from .interpreter import get_intention

"""
    Esse arquivo é responsável por lidar com as requisições de mensagens para a Melora
"""

chatbot_bp = Blueprint('chatbot_bp', __name__)

# Rota da API para o chatbot
@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    try:
        # Recebe a mensagem do JSON enviado pelo React
        dado = request.json

        if not dado or 'mensagem' not in dado:
            return jsonify({'resposta': 'Por favor, forneça uma mensagem na requisição'})

        mensagem = dado.get('mensagem', '')
        usuario = session.get('user_name', 'Convidado')
        modo_chat = session.get('modo_chat', 'standard')

        #print(f"--- ANTES DE INTERPRETAR ---")
        #print(f"Mensagem recebida: '{mensagem}'")
        #print(f"Modo da sessão ATUAL: '{modo_chat}'")

        # Envia a mensagem e o modo do chat para o interpretador
        resposta_chatbot, proximo_modo_chat = get_intention(mensagem, usuario, modo_chat)

        #print(f"--- DEPOIS DE INTERPRETAR ---")
        #print(f"Resposta gerada: '{resposta_chatbot}'")
        #print(f"Próximo modo retornado: '{proximo_modo_chat}'")

        # O modo de chat da sessão é atualizado para a próxima interação
        session['modo_chat'] = proximo_modo_chat
        session.modified = True
        #print(f"Modo da sessão SALVO: '{session['modo_chat']}'\n")

        return jsonify({'resposta': resposta_chatbot, 'modo_chat': proximo_modo_chat})

    except Exception as error:
        print(f"Erro na requisição: {error}")
        return jsonify({'resposta': 'Ocorreu um erro no servidor. Tente novamente mais tarde.'})
    
    # Configurar a resposta em formato json para devolver para o site
    #dados = {'user':'Iury', 'resposta':'resposta_chatbot', 'demanda':'realizar_tal_tarefa'}
