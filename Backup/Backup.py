import os
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import random
import textwrap
import time  # Para simular atrasos

# --- Configuração Inicial ---
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("A chave da API do Gemini (GOOGLE_API_KEY) não está configurada no arquivo .env")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = 'models/gemini-2.0-pro-exp-02-05'  # Posso Substituir por outras IA's

try:
    model = genai.GenerativeModel(MODEL_NAME)  # Inicializa o modelo
except Exception as e:
    print(f"Erro ao inicializar o modelo: {e}")
    raise ValueError(f"Não foi possível inicializar o modelo '{MODEL_NAME}'. Verifique se o nome está correto e se você tem acesso a ele.") from e


app = Flask(__name__)

# --- Constantes ---

MODULOS = {  # Estrutura dos módulos (exemplo - personalize!)
    "introducao": {
        "titulo": "Introdução ao Empreendedorismo",
        "submodulos": [
            "O que é Empreendedorismo?",
            "Por que Empreender na Universidade?",
            "Mitos e Verdades sobre Empreender",
        ],
        "objetivos": [
            "Entender o conceito de empreendedorismo.",
            "Identificar oportunidades de empreender na universidade.",
            "Desmistificar o empreendedorismo.",
        ]
    },
     "modulo1": {
        "titulo": "Identificando Oportunidades",
        "submodulos": [
            "O que é uma oportunidade de negócio?",
            "Como identificar problemas e necessidades.",
            "Análise de mercado e tendências (para a UVV).",
            "Ferramentas para identificar oportunidades (ex: Canvas).",
        ],
        "objetivos": [
            "Definir o que constitui uma oportunidade de negócio.",
            "Aprender a identificar problemas que podem ser transformados em negócios.",
            "Analisar o mercado e identificar tendências relevantes.",
            "Utilizar ferramentas como o Canvas para modelar oportunidades.",
        ]
    },
    "modulo2": {
        "titulo": "Desenvolvimento do Modelo de Negócio",
        "submodulos":[
            "O que é um modelo de negócio?",
            "Canvas: Uma ferramenta poderosa.",
            "Proposta de valor.",
            "Segmentos de clientes (na UVV).",
            "Canais de distribuição e comunicação.",
            "Relacionamento com clientes.",
            "Fontes de receita.",
            "Recursos-chave.",
            "Atividades-chave.",
            "Parcerias-chave.",
            "Estrutura de custos.",
        ],
        "objetivos": [
            "Compreender o conceito de modelo de negócio e sua importância.",
            "Dominar a ferramenta Canvas.",
            "Definir a proposta de valor do negócio.",
            "Identificar e segmentar os clientes.",
            "Escolher os canais de distribuição e comunicação adequados.",
            "Estabelecer um bom relacionamento com os clientes.",
            "Definir as fontes de receita do negócio.",
            "Identificar os recursos, atividades e parcerias chave.",
            "Analisar a estrutura de custos do negócio.",
        ]
    },
    "modulo3": {
        "titulo": "Validação e Testes",
        "submodulos": [
            "Por que validar é crucial?",
            "MVP (Minimum Viable Product): O que é e como criar.",
            "Testando com potenciais clientes (na UVV).",
            "Coleta e análise de feedback.",
            "Iteração e ajustes no modelo de negócio.",
        ],
        "objetivos": [
            "Entender a importância da validação do modelo de negócio.",
            "Aprender a criar um MVP.",
            "Realizar testes com potenciais clientes.",
            "Coletar e analisar feedback de forma eficaz.",
            "Iterar e ajustar o modelo de negócio com base nos resultados.",
        ]
    },
    "mentoria": {
        "titulo": "Mentoria",
        "submodulos": [
            "Como funciona a mentoria",
            "Preparando para mentoria",
        ],
        "objetivos":[
            "Preparar o aluno para a mentoria.",
            "Explicar sobre a mentoria."
        ]
    },
     "fim":{
        "titulo": "Fim",
        "submodulos": [
            "Fim do curso"
        ],
         "objetivos":[
            "Finalizar curso."
         ]
     }

}

# --- Prompts (Extensa lista de exemplos - personalize!) ---

# Prompts para o formulário inicial
FORMULARIO_PROMPTS = {
    "saudacao": [
        "Olá! Sou o assistente do curso de empreendedorismo da UVV, com mais de 50 anos de experiência em negócios, finanças, contabilidade e, claro, startups! 😉 Estou aqui para te guiar nessa jornada. Para começarmos, que tal me contar um pouco sobre você?",
        "Oi! Pronto para mergulhar no mundo do empreendedorismo? 😊 Sou um especialista em negócios, contabilidade, startups e finanças, com décadas de experiência.  Antes de mais nada, gostaria de te conhecer melhor.",
        "Olá! Bem-vindo(a) ao curso de empreendedorismo da UVV! Sou o seu assistente, um especialista em ajudar jovens empreendedores como você a terem sucesso. Para personalizarmos o curso, preciso de algumas informações suas. 😉",
        "Olá! Sou um especialista em negócios, startups, finanças e contabilidade, com vasta experiência no mercado. Estou aqui para te ajudar a trilhar o seu caminho no empreendedorismo. Para começarmos, que tal me contar um pouco sobre você?",
        "Oi! Preparado para transformar suas ideias em realidade? 😊 Sou um especialista em ajudar jovens empreendedores a terem sucesso. Antes de mais nada, gostaria de te conhecer melhor.",
        "Olá! Bem-vindo(a) ao curso de empreendedorismo! Sou o seu assistente, um especialista com mais de 50 anos de experiência em diversas áreas do mundo dos negócios. Para personalizarmos o curso, preciso de algumas informações suas. 😉",
    ],
    "pergunta": [
        "Para continuarmos, poderia me dizer {pergunta}?",
        "Agora, me diga: {pergunta}?",
        "E sobre {pergunta}, o que você me conta?",
        "Continuando, {pergunta}?",
        "{pergunta} (Estou curioso! 😊)",
        "Para te ajudar da melhor forma, preciso saber: {pergunta}?",
        "Vamos lá, me conte um pouco mais. {pergunta}?",
        "E então, {pergunta}?",
    ],
    "agradecimento": [
        "Ótimo! Obrigado pela informação.",
        "Perfeito! Anotado.",
        "Excelente! 👍",
        "Muito bom! 😊",
        "Informação valiosa! Obrigado.",
        "Agradeço por compartilhar!",
        "Isso me ajuda a personalizar o curso para você. Obrigado!",
    ],
      "prompt_geral": """
        Você é um assistente especialista em empreendedorismo, com foco em universitários da UVV.
        Você tem mais de 50 anos de experiência em diversas áreas, incluindo:

        * Finanças: investimentos, gestão financeira, análise de viabilidade, etc.
        * Startups: criação, desenvolvimento, aceleração, captação de recursos, etc.
        * Negócios (em geral): gestão, estratégia, marketing, vendas, operações, etc.
        * Contabilidade: princípios contábeis, legislação, impostos, etc.
        * Abertura de empresas: todos os passos e requisitos legais.
        * Conhecimentos *atuais*: você está sempre atualizado com as últimas tendências, tecnologias e regulamentações.

        Seu objetivo é guiar o aluno no curso de empreendedorismo, coletando informações,
        apresentando conteúdo, respondendo perguntas e oferecendo suporte personalizado.

        Seja SEMPRE amigável, didático e use uma linguagem acessível para universitários.
        Use emojis e formatação (negrito, itálico) para tornar a conversa mais expressiva.
        Divida o conteúdo em blocos menores, adequados para mensagens do WhatsApp.

        *LEMBRE-SE SEMPRE*: Você tem acesso ao histórico completo da conversa e ao perfil do aluno.
        Use essas informações para personalizar suas respostas e manter o contexto.

        *NÃO* repita as mesmas frases e perguntas. Varie suas respostas. Seja PROATIVO.
        Faça perguntas, ofereça exemplos, sugira recursos e incentive o aluno.

        Use os seguintes princípios ao interagir:
        1. Clareza: Seja claro e objetivo em suas explicações.
        2. Relevância: Forneça informações relevantes para o contexto do aluno.
        3. Personalização: Adapte suas respostas ao perfil e histórico do aluno.
        4. Engajamento: Incentive a participação e o aprendizado ativo do aluno.
        5. Empatia: Demonstre compreensão e apoio ao aluno.
        6. Proatividade:  Antecipe as necessidades do aluno e ofereça ajuda antes que ele peça.
        7. Precisão:  Garanta que suas respostas estejam corretas e atualizadas.
        8. Concisão:  Seja breve e direto ao ponto, mas sem comprometer a informação.
        9. Contextualização:  Sempre leve em consideração o histórico da conversa.
        10. Variedade: Use diferentes tipos de respostas, perguntas, exemplos, etc.

        Você está aqui para ajudar o aluno a ter SUCESSO!
        """
}

CONTEUDO_PROMPTS = {
    "introducao": [
        "Vamos começar com uma introdução a {submodulo}. O que você acha?",
        "Que tal começarmos pelo começo? 😉 Vamos falar sobre {submodulo}.",
        "Preparado para o primeiro passo? Vamos abordar {submodulo}.",
        "Dando o pontapé inicial, vamos explorar o tema: {submodulo}.",
        "Para aquecer os motores, vamos discutir sobre {submodulo}.",
    ],
    "apresentacao": [
        "Aqui está um resumo sobre {submodulo}, adaptado para o seu perfil:\n\n{conteudo}",
        "Vamos explorar {submodulo}. Aqui está o que você precisa saber, considerando seus interesses:\n\n{conteudo}",
        "Mergulhando em {submodulo}... Preste atenção, pois isso é importante para você:\n\n{conteudo}",
        "Com base no seu perfil, preparei este material sobre {submodulo}:\n\n{conteudo}",
        "Considerando seus objetivos, vamos aprofundar em {submodulo}:\n\n{conteudo}",
    ],
    "pergunta_reflexao": [
        "E aí, o que você achou de {submodulo}? Alguma dúvida ou insight?",
        "Pensando sobre {submodulo}, qual a sua opinião sobre isso?",
        "Com base no que vimos sobre {submodulo}, você consegue pensar em algum exemplo prático?",
        "Refletindo sobre {submodulo}... Isso te lembra alguma experiência sua?",
        "Qual a sua principal conclusão sobre {submodulo}?",
        "Você se identificou com algum ponto específico de {submodulo}?",
        "Como você aplicaria o que aprendeu sobre {submodulo} na sua realidade?",
    ],
    "exemplo_adicional": [
        "A propósito, aqui vai um exemplo prático relacionado a {submodulo}, pensando no contexto da UVV:\n\n{exemplo}",
        "Para ilustrar melhor {submodulo}, veja este exemplo de um negócio que poderia surgir na UVV:\n\n{exemplo}",
        "Pensando em {submodulo}, lembrei de um caso interessante que aconteceu aqui na UVV:\n\n{exemplo}",
        "Olha só que legal este exemplo relacionado a {submodulo}, que tem tudo a ver com a UVV:\n\n{exemplo}",
        "Para você que é da UVV, este exemplo sobre {submodulo} pode ser inspirador:\n\n{exemplo}",
    ],
    "estudo_de_caso": [
        "Que tal analisarmos um estudo de caso sobre {submodulo}? Veja só:\n\n{estudo_de_caso}",
        "Tenho um estudo de caso interessante sobre {submodulo} que pode te interessar:\n\n{estudo_de_caso}",
        "Para aprofundar em {submodulo}, vamos ver este estudo de caso:\n\n{estudo_de_caso}",
    ],
    "link_externo": [
        "Se você quiser saber mais sobre {submodulo}, recomendo este link:\n\n{link}",
        "Este artigo sobre {submodulo} pode te interessar:\n\n{link}",
        "Dê uma olhada neste vídeo sobre {submodulo}:\n\n{link}",
        "Para complementar seus estudos sobre {submodulo}, sugiro este recurso:\n\n{link}",
    ],
}

RESPOSTA_PROMPTS = {
    "resposta_curta": [
        "Entendi. {resposta_curta}",
        "Certo. {resposta_curta}",
        "Ok. {resposta_curta}",
        "Registrado. {resposta_curta}",
        "Beleza. {resposta_curta}",
    ],
    "resposta_longa": [
        "Interessante! {resposta_longa}",
        "Muito bom! Você está no caminho certo. {resposta_longa}",
        "Excelente ponto de vista! {resposta_longa}",
        "Ótima análise! {resposta_longa}",
        "Perfeito!  Isso mostra que você está aprendendo. {resposta_longa}",
    ],
    "pergunta_aberta": [
        "Me fale mais sobre {pergunta_aberta}.",
        "Gostaria de saber mais sobre {pergunta_aberta}. O que você pensa?",
        "E sobre {pergunta_aberta}, qual a sua experiência?",
        "Aprofundando um pouco... {pergunta_aberta}?",
        "Compartilhe comigo seus pensamentos sobre {pergunta_aberta}.",
    ],
    "resposta_duvida": [
        "{resposta_duvida}",
        "Respondendo à sua pergunta: {resposta_duvida}",
        "Esclarecendo sua dúvida: {resposta_duvida}",
        "Vamos lá, vou te explicar. {resposta_duvida}",
        "Em relação à sua pergunta, {resposta_duvida}",
    ],
    "resposta_positiva": [
        "Sim, exatamente! {resposta_positiva}",
        "Com certeza! {resposta_positiva}",
        "Isso mesmo! {resposta_positiva}",
        "Você acertou em cheio! {resposta_positiva}",
        "Perfeito! {resposta_positiva}",
    ],
    "resposta_negativa": [
        "Não exatamente. {resposta_negativa}",
        "Na verdade, não é bem assim. {resposta_negativa}",
        "Hum... Não é isso. {resposta_negativa}",
        "Preciso corrigir um ponto. {resposta_negativa}",
        "Vamos esclarecer isso. {resposta_negativa}",
    ],
    "elogio": [
        "Muito bem!",
        "Excelente!",
        "Parabéns!",
        "Ótimo trabalho!",
        "Continue assim!",
        "Estou gostando de ver!",
        "Você está indo muito bem!",
    ],
     "incentivo": [
        "Não desista!",
        "Você consegue!",
        "Continue se esforçando!",
        "Acredite em você!",
        "O sucesso está próximo!",
        "Mantenha o foco!",
        "Você tem potencial!",
    ],
    "feedback_positivo": [
        "Gostei da sua resposta! {feedback_positivo}",
        "Sua pergunta foi muito pertinente. {feedback_positivo}",
        "Você demonstrou um bom entendimento do assunto. {feedback_positivo}",
        "Excelente progresso! {feedback_positivo}",
        "Fico feliz em ver seu empenho. {feedback_positivo}",
    ],
    "feedback_construtivo": [
        "Que tal pensarmos um pouco mais sobre isso? {feedback_construtivo}",
        "Talvez você possa reformular sua resposta. {feedback_construtivo}",
        "Vamos explorar esse ponto com mais detalhes. {feedback_construtivo}",
        "Considere este outro aspecto da questão. {feedback_construtivo}",
        "Ainda há espaço para melhorias, mas você está no caminho certo. {feedback_construtivo}",
    ],
    "humor": [  # Adicionando um toque de humor (opcional)
        "Essa foi por pouco! 😉 {humor}",
        "Quase lá! 😄 {humor}",
        "Você é um empreendedor em construção! 🚧 {humor}",
        "Não se preocupe, até os maiores empreendedores já erraram. 😉 {humor}",
    ],
}

# --- Estado do Aluno ---
# --- Estado do Aluno ---
alunos = {}

def get_estado_aluno(numero):
    if numero not in alunos:
        alunos[numero] = {
            "formulario_completo": False,
            "perfil": {
                "nome": "N/A",
                "universidade": "UVV",  # Pré-preenchido
                "curso": "N/A",
                "periodo": "N/A",
                "experiencia": "N/A",
                "objetivos": "N/A",
                "conhecimento": "N/A",
                "interesses": "N/A",
                "conversa": []  # CORRIGIDO: Lista vazia
            },
            "modulo_atual": "introducao",
            "submodulo_atual": None,
            "aguardando_resposta": None,
            "contexto": "formulario",
            "pontos": 0,
            "quiz_pendente": False,
            "respostas_quiz": [],
            "quiz_atual": None,
        }
    return alunos[numero]

# --- Funções Auxiliares ---

def gerar_prompt_mestre():
    """Cria o prompt mestre que define a persona do assistente."""
    return textwrap.dedent("""
    Você é um assistente virtual especialista em empreendedorismo, com mais de 50 anos de experiência em:
    * Finanças: investimentos, gestão financeira, análise de viabilidade.
    * Startups: criação, desenvolvimento, aceleração, captação de recursos.
    * Negócios: gestão, estratégia, marketing, vendas, operações.
    * Contabilidade: princípios contábeis, legislação, impostos.
    * Abertura de empresas: todos os passos e requisitos legais.
    * Conhecimentos atuais: você está SEMPRE atualizado com as últimas tendências.

    Você está EXCLUSIVAMENTE focado em ajudar universitários da UVV a desenvolverem seus primeiros negócios.

    Seu objetivo é guiar o aluno no curso de empreendedorismo, respondendo perguntas,
    apresentando conteúdo e oferecendo suporte personalizado.

    Use uma linguagem ACESSÍVEL para universitários.
    Seja SEMPRE amigável, didático, paciente e motivador.
    Use emojis e formatação (negrito, itálico) para tornar a conversa mais expressiva no WhatsApp.
    Divida o conteúdo em blocos menores, adequados para mensagens do WhatsApp.

    LEMBRE-SE: Você tem acesso ao histórico completo da conversa e ao perfil do aluno.
    Use essas informações para personalizar suas respostas e manter o contexto.

    Varie suas respostas. NÃO repita as mesmas frases e perguntas. Seja PROATIVO.
    Faça perguntas, ofereça exemplos, sugira recursos e incentive o aluno.

    Você está aqui para ajudar o aluno a ter SUCESSO!
    """)

def extrair_informacoes(conversa):
    """Extrai informações do perfil do aluno da conversa usando o Gemini."""
    prompt = f"""
    Da conversa a seguir, extraia as seguintes informações:
    1. Nome completo:
    2. Curso:
    3. Período/Semestre:
    4. Experiência empreendedora:
    5. Objetivos com o curso:
    6. Nível de conhecimento em empreendedorismo (1-5):
    7. Áreas de interesse:

    Conversa:
    {conversa}

    Preencha cada item com a informação correspondente. Se alguma informação
    não estiver disponível, escreva "N/A".
    """
    try:
        resposta = model.generate_content(prompt).text
        info = {}
        for linha in resposta.splitlines():
            if ":" in linha:
                chave, valor = linha.split(":", 1)
                info[chave.strip()] = valor.strip()
        return info
    except Exception as e:
        print(f"Erro ao extrair informações: {e}")
        return {}

def coletar_informacoes_iniciais(mensagem, estado):
    """Coleta informações do aluno de forma flexível."""
    #Adiciona a conversa
    estado["conversa"].append(f"Aluno: {mensagem}") #CORRETO

     # Escolhe aleatoriamente um prompt de saudação ou pergunta
    if not estado["perfil"]["nome"] != "N/A":
        prompt_tipo = "saudacao"
    else:
        prompt_tipo = "pergunta"

    prompt_escolhido = random.choice(FORMULARIO_PROMPTS[prompt_tipo])

     # Se for uma pergunta, formata com a pergunta apropriada
    if prompt_tipo == "pergunta":
        perguntas_pendentes = []
        if estado["perfil"]["nome"] == "N/A":
            perguntas_pendentes.append("Qual é o seu nome completo?")
        if estado["perfil"]["curso"] == "N/A":
            perguntas_pendentes.append("Qual curso você está fazendo?")
        if estado["perfil"]["periodo"] == "N/A":
            perguntas_pendentes.append("Em qual período/semestre você está?")
        if estado["perfil"]["experiencia"] == "N/A":
            perguntas_pendentes.append("Você já teve alguma experiência empreendedora (mesmo que informal)?")
        if estado["perfil"]["objetivos"] == "N/A":
            perguntas_pendentes.append("Quais são seus principais objetivos com este curso?")
        if estado["perfil"]["conhecimento"] == "N/A":
            perguntas_pendentes.append("Em uma escala de 1 a 5, como você avalia seu conhecimento sobre empreendedorismo?")
        if estado["perfil"]["interesses"] == "N/A":
            perguntas_pendentes.append("Quais áreas do empreendedorismo te interessam mais?")

        if not perguntas_pendentes:  # Se não houver mais perguntas
            estado["formulario_completo"] = True
            estado["contexto"] = "apresentando_conteudo"
            estado["submodulo_atual"] = 0
            return [
                "Formulário completo! Suas informações foram registradas.",
                "Vamos começar com o módulo de introdução.",
                *apresentar_conteudo(estado)
            ]

        pergunta = random.choice(perguntas_pendentes)
        prompt_escolhido = prompt_escolhido.format(pergunta=pergunta)
    prompt = f"""
    {gerar_prompt_mestre()}
    
    {prompt_escolhido}

    Histórico da conversa:
    {' '.join(estado["conversa"])}

    Responda de forma concisa.
    """
    try:
        resposta = model.generate_content(prompt).text
        estado["conversa"].append(f"Assistente: {resposta}") #CORRETO
        #Extrai informações a cada interação
        estado["perfil"].update(extrair_informacoes(' '.join(estado["conversa"])))

        # Verifica se TODAS as informações foram coletadas
        todas_info_coletadas = all(
            estado["perfil"][campo] != "N/A"
            for campo in ["nome", "curso", "periodo", "experiencia", "objetivos", "conhecimento", "interesses"]
        )
        if todas_info_coletadas:
            estado["formulario_completo"] = True
            estado["contexto"] = "apresentando_conteudo"
            estado["submodulo_atual"] = 0
            #Junta as mensagens e as envia
            return [
                "Formulário completo! Suas informações foram registradas.",
                "Vamos começar com o módulo de introdução.",
                *apresentar_conteudo(estado) #Desempacota a lista
            ]
        return [resposta]  # Retorna uma lista com a resposta

    except Exception as e:
        print(f"Erro ao coletar informações: {e}")
        return ["Desculpe, tive um problema. Tente novamente."]

def gerar_indice_modulo(modulo, perfil_aluno):
    """Gera um índice (tópicos/subtópicos) para um módulo."""
    prompt = f"""
    Crie um índice detalhado para o módulo '{modulo}' do curso.
    Considere o perfil do aluno: {perfil_aluno}

    Use, no máximo, 3 níveis de indentação (tópico, subtópico, sub-subtópico).
    Formato:
    Tópico 1: ...
        Subtópico 1.1: ...
    """
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        print(f"Erro ao gerar índice: {e}")
        return None

def gerar_conteudo_submodulo(modulo, submodulo_indice, perfil_aluno, historico):
    """Gera o conteúdo de um submódulo específico."""
    indice = gerar_indice_modulo(modulo, perfil_aluno)
    if indice is None:
        return "Erro ao gerar o índice do módulo."

    linhas_indice = indice.splitlines()
    try:
        submodulo_nome = linhas_indice[submodulo_indice].strip()
    except IndexError:
        return None  # Fim do módulo

    prompt = f"""
    {gerar_prompt_mestre()}

    Apresente o conteúdo do seguinte tópico/subtópico do módulo '{MODULOS[modulo]["titulo"]}':

    {submodulo_nome}

    Considere o perfil do aluno:
    {perfil_aluno}

    Histórico da conversa:
    {' '.join(historico)}

    Seja didático, use exemplos práticos e adapte a linguagem ao perfil do aluno.
    Divida o conteúdo em blocos menores, adequados para mensagens do WhatsApp.
    """
    try:
        conteudo = model.generate_content(prompt).text
        return conteudo
    except Exception as e:
        print(f"Erro ao gerar conteúdo do submódulo: {e}")
        return f"Erro ao carregar o conteúdo do submódulo {submodulo_indice}"

def apresentar_conteudo(estado):
    """Apresenta o conteúdo do módulo atual, em blocos."""
    modulo = estado["modulo_atual"]
    submodulo_indice = estado["submodulo_atual"]

    if submodulo_indice is None: #Primeira vez
        submodulo_indice = 0
        estado["submodulo_atual"] = 0

    conteudo = gerar_conteudo_submodulo(modulo, submodulo_indice, estado["perfil"], estado["conversa"])
    if conteudo is None:  # Fim do módulo
        if avancar_modulo(estado):
            estado["submodulo_atual"] = 0
            return apresentar_conteudo(estado)  # Inicia o próximo módulo
        else:
            estado["contexto"] = "fim"
            return ["Parabéns! Você concluiu todos os módulos do curso."]

    estado["submodulo_atual"] += 1
    estado["aguardando_resposta"] = "sim/nao"
    estado["contexto"] = "apresentando_conteudo"

    # Escolhe aleatoriamente prompts para apresentação e perguntas
    prompt_apresentacao = random.choice(CONTEUDO_PROMPTS["apresentacao"]).format(submodulo=MODULOS[modulo]["submodulos"][submodulo_indice], conteudo=conteudo)
    prompt_pergunta = random.choice(CONTEUDO_PROMPTS["pergunta_reflexao"]).format(submodulo=MODULOS[modulo]["submodulos"][submodulo_indice])

    # Formata a mensagem com negrito e quebras de linha
    mensagem = f"*{MODULOS[modulo]['titulo']}*\n\n"  # Título em negrito
    mensagem += prompt_apresentacao + "\n\n"
    mensagem += prompt_pergunta + " (sim/não)"

    return [mensagem]
def gerar_quiz(modulo):
    """Gera um quiz para o módulo usando a API do Gemini."""
    prompt = f"Crie um quiz de 3 perguntas (múltipla escolha) sobre o módulo '{modulo}' do curso para universitários sobre como abrir o primeiro negócio.  Forneça as perguntas, opções de resposta e a resposta correta."
    try:
        quiz_data = model.generate_content(prompt).text
        # Processamento do quiz (extrair perguntas, opções e respostas)
        quiz = []
        blocos = quiz_data.split("Pergunta ")
        for bloco in blocos[1:]:
            partes = bloco.split("\n")
            pergunta = partes[0].strip().split(":", 1)[1].strip()
            opcoes = [op.strip() for op in partes[1:5] if op.strip()]
            resposta_correta = partes[5].split(":")[1].strip()

            quiz.append({
                "pergunta": pergunta,
                "opcoes": opcoes,
                "resposta_correta": resposta_correta
            })
        return quiz
    except Exception as e:
         print(f"Erro ao gerar quiz com Gemini: {e}")
         return None

def verificar_resposta_quiz(resposta_aluno, estado):
        """Verifica se a resposta do aluno ao quiz está correta."""
        num_pergunta = len(estado["respostas_quiz"])
        quiz_atual = estado["quiz_atual"]
        resposta_correta = quiz_atual[num_pergunta]["resposta_correta"]

        if resposta_aluno.lower().startswith(resposta_correta.lower()):
            estado["pontos"] += 10
            estado["respostas_quiz"].append(resposta_aluno)
            return "Resposta correta! +10 pontos"
        else:
            estado["respostas_quiz"].append(resposta_aluno)
            return f"Resposta incorreta. A resposta correta era: {resposta_correta}"

def avancar_modulo(estado):
        """Avança para o próximo módulo/tópico do curso."""
        modulos = ["introducao", "modulo1", "modulo2", "modulo3", "mentoria", "fim"]  # Adicione mais módulos conforme necessário
        indice_atual = modulos.index(estado["modulo_atual"])

        if indice_atual < len(modulos) - 1:
            estado["modulo_atual"] = modulos[indice_atual + 1]
            return True
        else:
            return False  # Chegou ao fim do curso.

# --- Lógica Principal ---

def processar_mensagem(mensagem_aluno, numero_aluno):
    estado = get_estado_aluno(numero_aluno)
    # Adiciona a mensagem do usuário ao histórico da conversa, *sempre*
    estado["conversa"].append(f"Aluno: {mensagem_aluno}")

    # --- Formulário ---
    if estado["contexto"] == "formulario":
        return coletar_informacoes_iniciais(mensagem_aluno, estado)

    # --- Apresentando Conteúdo ---
    if estado["contexto"] == "apresentando_conteudo":
        if estado["aguardando_resposta"] == "sim/nao":
            if mensagem_aluno.lower() == "sim":
                estado["aguardando_resposta"] = None
                return apresentar_conteudo(estado)
            elif mensagem_aluno.lower() == "não":
                estado["aguardando_resposta"] = None
                estado["contexto"] = "interacao_livre"
                return ["Ok. O que você gostaria de fazer agora?"]
            else:
                return ["Por favor, responda 'sim' ou 'não'."]
        else:
            # Se não estava esperando sim/não, vai para interação livre
            estado["contexto"] = "interacao_livre"

    # --- Quiz ---
    if estado["contexto"] == "quiz":
        if estado["quiz_pendente"]:
                feedback_resposta = verificar_resposta_quiz(mensagem_aluno, estado)
                num_pergunta = len(estado["respostas_quiz"])

                if num_pergunta == len(estado["quiz_atual"]):
                    estado["quiz_pendente"] = False
                    estado["respostas_quiz"] = []
                    if avancar_modulo(estado):
                        estado["submodulo_atual"] = 0
                        estado["contexto"] = "apresentando_conteudo"
                        return [f"{feedback_resposta}\n\nQuiz finalizado!.\n\nPróximo módulo: {estado['modulo_atual']}", *apresentar_conteudo(estado)] #Desempacota
                    else:
                        return [f"{feedback_resposta}\n\nQuiz finalizado!  Você concluiu o curso!"]
                else:
                    proxima_pergunta = estado["quiz_atual"][num_pergunta]
                    return [f"{feedback_resposta}\n\nPróxima pergunta:\n\n{proxima_pergunta['pergunta']}\n{chr(10).join(proxima_pergunta['opcoes'])}"]
    # --- Comandos ---
    if mensagem_aluno.lower() == "quiz":
        estado["quiz_atual"] = gerar_quiz(estado["modulo_atual"])
        if estado["quiz_atual"] is None:  return ["Desculpe, não consegui gerar o quiz agora."]
        estado["quiz_pendente"] = True
        estado["contexto"] = "quiz"
        primeira_pergunta = estado["quiz_atual"][0]
        return [f"Quiz do módulo {estado['modulo_atual']}:\n\n{primeira_pergunta['pergunta']}\n{chr(10).join(primeira_pergunta['opcoes'])}"]

    elif mensagem_aluno.lower() == "continuar":
        if estado["modulo_atual"] == "fim": return ["Você já concluiu todos os módulos."]

        if avancar_modulo(estado):
            estado["submodulo_atual"] = 0
            estado["contexto"] = "apresentando_conteudo"
            return apresentar_conteudo(estado)  # Apresenta o novo módulo
        else:
            return ["Você já concluiu todos os módulos."]

    elif mensagem_aluno.lower() == "pontos":
        return [f"Você tem {estado['pontos']} pontos."]

    elif mensagem_aluno.lower() == "mentoria":
        if estado['modulo_atual'] == 'mentoria':
            if estado['pontos'] >= 50:
                estado['pontos'] -= 50
                return ["Parabéns! Você resgatou uma mentoria. Entraremos em contato para agendar. Seus pontos restantes: {}".format(estado['pontos'])]
            else:
                return ["Você não tem pontos suficientes para resgatar uma mentoria. Você precisa de 50 pontos, e tem {}".format(estado['pontos'])]
        else:
            return ["Você só pode pedir mentoria quando chegar no módulo 'mentoria'. Continue o curso!"]

    # --- Interação Livre ---
    estado["contexto"] = "interacao_livre"  # Por padrão, se não for um comando, é interação livre
    prompt = f"""
    {gerar_prompt_mestre()}

    Responda à pergunta ou comentário do aluno.

    Perfil do Aluno:
    {estado["perfil"]}

    Histórico da Conversa:
    {' '.join(estado['conversa'])}

    Módulo Atual: {estado["modulo_atual"]}

    Mensagem do Aluno: {mensagem_aluno}
    """
    try:
        resposta = model.generate_content(prompt).text
        estado["conversa"].append(f"Assistente: {resposta}")
        return [resposta]  # Retorna uma lista com a resposta
    except Exception as e:
        print(f"Erro ao responder com Gemini: {e}")
        return ["Desculpe, tive um problema ao responder. Tente novamente."]

# --- Rota do WhatsApp ---
@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    mensagem_aluno = request.values.get('Body', '').lower()
    numero_aluno = request.values.get('From', '')

    try:
        respostas = processar_mensagem(mensagem_aluno, numero_aluno)
    except Exception as e:
        print(f"Erro geral em processar_mensagem: {e}")  # Log de erro genérico
        respostas = ["Houve um erro ao processar sua mensagem."]

    resp = MessagingResponse()
    for mensagem in respostas:
        resp.message(mensagem)  # Envia *várias* mensagens, se houver
    return str(resp)

@app.route("/")
def hello_world():
    return "<p>Olá, Mundo!</p>"

if __name__ == "__main__":
    app.run(debug=True)