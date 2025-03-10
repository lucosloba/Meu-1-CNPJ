import os
import time
import random
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import google.generativeai as genai

# --- Initial Configuration ---
app = Flask(__name__)
load_dotenv()

# Validate API key
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("Google API key (GOOGLE_API_KEY) not configured in .env file")

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Gemini model
MODEL_NAME = 'models/gemini-2.0-pro-exp-02-05'  # Can be replaced with other AI models
try:
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    print(f"Error initializing model: {e}")
    raise ValueError(f"Could not initialize model '{MODEL_NAME}'. Check if the name is correct and if you have access.") from e

# --- Course Content Structure ---
MODULES = {
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

# --- Conversation Prompts ---
PROMPTS = {
    # Greeting and form prompts
    "saudacao": [
        "Olá! Sou o assistente do curso de empreendedorismo da UVV, com mais de 50 anos de experiência em negócios, finanças, contabilidade e, claro, startups! 😉 Estou aqui para te guiar nessa jornada. Para começarmos, que tal me contar um pouco sobre você?",
        "Oi! Pronto para mergulhar no mundo do empreendedorismo? 😊 Sou um especialista em negócios, contabilidade, startups e finanças, com décadas de experiência. Antes de mais nada, gostaria de te conhecer melhor.",
        "Olá! Bem-vindo(a) ao curso de empreendedorismo da UVV! Sou o seu assistente, um especialista em ajudar jovens empreendedores como você a terem sucesso. Para personalizarmos o curso, preciso de algumas informações suas. 😉",
    ],
    "pergunta": [
        "Para continuarmos, poderia me dizer {pergunta}?",
        "Agora, me diga: {pergunta}?",
        "E sobre {pergunta}, o que você me conta?",
        "Continuando, {pergunta}?",
        "{pergunta} (Estou curioso! 😊)",
    ],
    "agradecimento": [
        "Ótimo! Obrigado pela informação.",
        "Perfeito! Anotado.",
        "Excelente! 👍",
        "Muito bom! 😊",
        "Informação valiosa! Obrigado.",
    ],
    
    # Content presentation prompts
    "introducao_modulo": [
        "Vamos começar com uma introdução a {submodulo}. O que você acha?",
        "Que tal começarmos pelo começo? 😉 Vamos falar sobre {submodulo}.",
        "Preparado para o primeiro passo? Vamos abordar {submodulo}.",
    ],
    "apresentacao_conteudo": [
        "Aqui está um resumo sobre {submodulo}, adaptado para o seu perfil:\n\n{conteudo}",
        "Vamos explorar {submodulo}. Aqui está o que você precisa saber, considerando seus interesses:\n\n{conteudo}",
        "Mergulhando em {submodulo}... Preste atenção, pois isso é importante para você:\n\n{conteudo}",
    ],
    "pergunta_reflexao": [
        "E aí, o que você achou de {submodulo}? Alguma dúvida ou insight?",
        "Pensando sobre {submodulo}, qual a sua opinião sobre isso?",
        "Com base no que vimos sobre {submodulo}, você consegue pensar em algum exemplo prático?",
        "Que insights você teve ao aprender sobre {submodulo}?",
        "Como você poderia aplicar o que aprendeu sobre {submodulo} no seu contexto na UVV?"
    ],
    
    # Quiz prompts
    "resposta_correta": [
        "Correto! 🎉 Você ganhou 10 pontos!",
        "Excelente! ✅ +10 pontos para você!",
        "Perfeito! 👍 10 pontos adicionados.",
    ],
    "resposta_incorreta": [
        "Não é bem isso... A resposta correta é: {resposta}",
        "Quase lá! Na verdade, a resposta correta é: {resposta}",
        "Vamos revisar isso. A resposta correta é: {resposta}",
    ],
    
    # Error messages
    "erro": [
        "Desculpe, ocorreu um erro. Vamos tentar novamente?",
        "Ops! Algo deu errado. Pode repetir, por favor?",
        "Tive um pequeno problema. Vamos recomeçar?",
    ]
}

# --- Student State Management ---
students = {}

def get_student_state(phone_number):
    """Initialize or retrieve student state"""
    if phone_number not in students:
        students[phone_number] = {
            "form_completed": False,
            "profile": {
                "nome": None,
                "curso": None,
                "periodo": None,
                "experiencia": None,
                "objetivos": None,
                "conhecimento": None,
                "interesses": None,
            },
            "conversation_history": [],
            "current_module": "introducao",
            "current_submodule": 0,
            "context": "form",
            "waiting_response": None,
            "points": 0,
            "quiz_active": False,
            "quiz_answers": [],
            "current_quiz": None,
        }
    return students[phone_number]

# --- Helper Functions ---

def generate_master_prompt():
    """Generate the master prompt that defines the assistant's persona"""
    return """
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
    Divida o conteúdo em blocos menores, adequados para mensagens do WhatsApp (máximo 1000 caracteres).

    LEMBRE-SE: Você tem acesso ao histórico completo da conversa e ao perfil do aluno.
    Use essas informações para personalizar suas respostas e manter o contexto.

    Varie suas respostas. NÃO repita as mesmas frases e perguntas. Seja PROATIVO.
    Faça perguntas, ofereça exemplos, sugira recursos e incentive o aluno.

    Você está aqui para ajudar o aluno a ter SUCESSO!
    """

def extract_profile_info(conversation_history):
    """Extract student profile information from conversation using Gemini"""
    prompt = f"""
    Da conversa a seguir, extraia as seguintes informações:
    1. Nome do aluno
    2. Curso na universidade
    3. Período/Semestre
    4. Experiência prévia com empreendedorismo
    5. Objetivos com o curso
    6. Nível de conhecimento em empreendedorismo (1-5)
    7. Áreas de interesse

    Conversa:
    {conversation_history}

    Forneça as informações no formato: 
    nome: [nome]
    curso: [curso] 
    periodo: [periodo]
    experiencia: [experiencia]
    objetivos: [objetivos]
    conhecimento: [conhecimento]
    interesses: [interesses]
    
    Se uma informação não estiver disponível, use "None" como valor.
    """
    
    try:
        response = model.generate_content(prompt)
        # Parse the response into a dictionary
        info = {}
        for line in response.text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value.lower() in ["none", "n/a", ""]:
                    value = None
                info[key] = value
        return info
    except Exception as e:
        print(f"Error extracting profile info: {e}")
        return {}

def collect_initial_info(message, state):
    """Collect student information in a flexible way"""
    
    # Add message to conversation history
    conversation_history = state["conversation_history"]
    conversation_history.append(f"Aluno: {message}")
    
    # Extract profile info from conversation
    profile_info = extract_profile_info("\n".join(conversation_history))
    for key, value in profile_info.items():
        if value is not None:
            state["profile"][key] = value
    
    # Determine which information is still missing
    missing_info = []
    if not state["profile"]["nome"]:
        missing_info.append("qual é o seu nome completo")
    elif not state["profile"]["curso"]:
        missing_info.append("qual curso você está fazendo na UVV")
    elif not state["profile"]["periodo"]:
        missing_info.append("em qual período/semestre você está")
    elif not state["profile"]["experiencia"]:
        missing_info.append("se você já teve alguma experiência empreendedora (mesmo que informal)")
    elif not state["profile"]["objetivos"]:
        missing_info.append("quais são seus principais objetivos com este curso")
    elif not state["profile"]["conhecimento"]:
        missing_info.append("em uma escala de 1 a 5, como você avalia seu conhecimento sobre empreendedorismo")
    elif not state["profile"]["interesses"]:
        missing_info.append("quais áreas do empreendedorismo te interessam mais")
    
    # If all information is collected, move to content presentation
    if not missing_info:
        state["form_completed"] = True
        state["context"] = "presenting_content"
        
        # Generate AI response for form completion
        prompt = f"""
        {generate_master_prompt()}
        
        O aluno completou o formulário inicial. Gere uma mensagem entusiasmada e personlizada 
        para informar ao aluno que vamos iniciar o curso. A mensagem deve ser curta (máximo 3 frases)
        e deve mencionar algum detalhe do perfil do aluno, como o curso, interesses ou objetivos.
        
        Perfil do aluno:
        {state["profile"]}
        
        Não mencione que o formulário foi completado ou que estamos iniciando qualquer módulo específico.
        """
        
        try:
            completion_message = model.generate_content(prompt).text
            conversation_history.append(f"Assistente: {completion_message}")
            
            # Get first content after form completion
            content_messages = present_content(state)
            return [completion_message] + content_messages
        except Exception as e:
            print(f"Error generating form completion message: {e}")
            return ["Ótimo! Agora que conheço você melhor, vamos começar o curso!"] + present_content(state)
    
    # If still collecting information, ask the next question
    next_question = missing_info[0]
    prompt_template = random.choice(PROMPTS["pergunta"])
    prompt = prompt_template.format(pergunta=next_question)
    
    conversation_history.append(f"Assistente: {prompt}")
    return [prompt]

def generate_module_content(module_name, submodule_index, student_profile):
    """Generate content for a specific submodule using Gemini"""
    
    # Get module and submodule info
    module = MODULES[module_name]
    module_title = module["titulo"]
    
    # Check if submodule exists
    if submodule_index >= len(module["submodulos"]):
        return None
    
    submodule = module["submodulos"][submodule_index]
    
    prompt = f"""
    {generate_master_prompt()}
    
    Gere conteúdo educativo para o tópico "{submodule}" que faz parte do módulo "{module_title}".
    
    Perfil do aluno:
    {student_profile}
    
    O conteúdo deve:
    1. Ser conciso (máximo 1000 caracteres)
    2. Ser didático e envolvente
    3. Incluir exemplos práticos relevantes para estudantes da UVV
    4. Ser personalizado para o perfil do aluno
    5. Usar emojis ocasionalmente para tornar o texto mais expressivo
    6. Incluir 1-2 perguntas reflexivas ao final
    
    NÃO use listas longas ou muitos tópicos. Foque em explicar de forma fluida e conversacional.
    """
    
    try:
        content = model.generate_content(prompt).text
        return content
    except Exception as e:
        print(f"Error generating module content: {e}")
        return f"Desculpe, tive um problema ao gerar o conteúdo sobre {submodule}. Vamos tentar novamente?"

def present_content(state):
    """Present current module content to the student"""
    module_name = state["current_module"]
    submodule_index = state["current_submodule"]
    
    # Check if we've reached the end of the module
    if module_name == "fim":
        state["context"] = "course_completed"
        return ["🎓 Parabéns! Você completou o curso de empreendedorismo! Agora você está preparado para iniciar sua jornada empreendedora. Se tiver dúvidas ou quiser discutir suas ideias, digite 'mentoria' para solicitar uma sessão."]
    
    module = MODULES[module_name]
    
    # Check if we've reached the end of submodules in this module
    if submodule_index >= len(module["submodulos"]):
        # Move to the next module
        module_order = ["introducao", "modulo1", "modulo2", "modulo3", "mentoria", "fim"]
        current_index = module_order.index(module_name)
        
        if current_index + 1 < len(module_order):
            # Move to next module
            next_module = module_order[current_index + 1]
            state["current_module"] = next_module
            state["current_submodule"] = 0
            
            # Generate transition message
            prompt = f"""
            {generate_master_prompt()}
            
            Gere uma mensagem curta (máximo 2 frases) de transição para informar ao aluno que completou o 
            módulo "{module["titulo"]}" e agora vai iniciar o módulo "{MODULES[next_module]["titulo"]}".
            
            A mensagem deve ser motivadora e entusiasmada.
            """
            
            try:
                transition_message = model.generate_content(prompt).text
                return [transition_message] + present_content(state)
            except Exception as e:
                print(f"Error generating transition message: {e}")
                transition_message = f"Parabéns! Você completou o módulo \"{module['titulo']}\"! Agora vamos para \"{MODULES[next_module]['titulo']}\"."
                return [transition_message] + present_content(state)
        else:
            # End of course
            state["context"] = "course_completed"
            return ["🎓 Parabéns! Você completou o curso de empreendedorismo! Se precisar de mais orientações, estou à disposição."]
    
    # Generate content for the current submodule
    submodule = module["submodulos"][submodule_index]
    content = generate_module_content(module_name, submodule_index, state["profile"])
    
    # Format the message
    presentation_template = random.choice(PROMPTS["apresentacao_conteudo"])
    presentation = presentation_template.format(submodulo=submodule, conteudo=content)
    
    # Add reflection question
    reflection_template = random.choice(PROMPTS["pergunta_reflexao"])
    reflection = reflection_template.format(submodulo=submodule)
    
    # Format the message with bold title
    message = f"*{module['titulo']} - {submodule}*\n\n{presentation}\n\n{reflection}\n\nDigite 'continuar' quando quiser avançar para o próximo conteúdo. Fique a vontade para realizar qualquer pergunta se ainda não estiver pronto para avançar"
    
    # Update state
    state["waiting_response"] = None
    state["conversation_history"].append(f"Assistente: {message}")
    
    # Return formatted message
    return [message]

def generate_quiz(module_name):
    """Generate a quiz for the specified module"""
    module = MODULES[module_name]
    
    prompt = f"""
    Crie um quiz de 5 perguntas de múltipla escolha sobre o módulo "{module['titulo']}" para um curso de empreendedorismo.
    
    Cada pergunta deve ter 4 opções de resposta (a, b, c, d).
    
    Forneça as perguntas, todas as opções para cada pergunta, e a letra da resposta correta.
    
    Use o seguinte formato:
    
    Pergunta 1: [texto da pergunta]
    a) [opção a]
    b) [opção b]
    c) [opção c]
    d) [opção d]
    Resposta: [letra da resposta correta]
    
    Pergunta 2: [texto da pergunta]
    ...
    
    Pergunta 3: [texto da pergunta]
    ...
    """
    
    try:
        response = model.generate_content(prompt).text
        
        # Parse quiz data
        quiz = []
        current_question = None
        current_options = []
        
        for line in response.splitlines():
            line = line.strip()
            
            if line.startswith("Pergunta"):
                if current_question:
                    quiz.append({
                        "question": current_question,
                        "options": current_options,
                        "correct_answer": current_answer
                    })
                
                # Start new question
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_question = parts[1].strip()
                    current_options = []
            
            elif line.startswith("a)") or line.startswith("b)") or line.startswith("c)") or line.startswith("d)"):
                option = line[2:].strip()
                current_options.append(line)
            
            elif line.startswith("Resposta:"):
                current_answer = line.split(":", 1)[1].strip().lower()
        
        # Add the last question
        if current_question and current_options:
            quiz.append({
                "question": current_question,
                "options": current_options,
                "correct_answer": current_answer
            })
        
        return quiz
    
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return None

def handle_quiz_response(message, state):
    """Process a student's response to a quiz question"""
    quiz = state["current_quiz"]
    question_index = len(state["quiz_answers"])
    
    # Check if response is valid (a, b, c, or d)
    student_answer = message.lower().strip()
    if student_answer not in ['a', 'b', 'c', 'd']:
        return ["Por favor, responda com a letra da alternativa (a, b, c ou d)."]
    
    current_question = quiz[question_index]
    correct_answer = current_question["correct_answer"]
    
    # Add answer to state
    state["quiz_answers"].append(student_answer)
    
    # Check if correct
    if student_answer == correct_answer:
        state["points"] += 10
        feedback = random.choice(PROMPTS["resposta_correta"])
    else:
        feedback = random.choice(PROMPTS["resposta_incorreta"]).format(resposta=correct_answer)
    
    # Check if quiz is complete
    if len(state["quiz_answers"]) >= len(quiz):
        # Quiz completed
        state["quiz_active"] = False
        state["quiz_answers"] = []
        state["current_quiz"] = None
        
        # Move to next module
        current_submodule = state["current_submodule"]
        state["current_submodule"] = current_submodule + 1
        state["context"] = "presenting_content"
        
        completion_message = f"{feedback}\n\n🎯 Quiz concluído! Você tem agora {state['points']} pontos."
        
        # Continue to next content
        return [completion_message] + present_content(state)
    
    # Present next question
    next_question_index = len(state["quiz_answers"])
    next_question = quiz[next_question_index]
    
    question_text = next_question["question"]
    options_text = "\n".join(next_question["options"])
    
    return [f"{feedback}\n\n*Próxima pergunta:*\n\n{question_text}\n{options_text}"]

def process_free_interaction(message, state):
    """Handle free interaction with the AI assistant"""
    conversation_history = "\n".join(state["conversation_history"])
    
    prompt = f"""
    {generate_master_prompt()}
    
    Responda à mensagem do aluno abaixo com base no contexto da conversa e no perfil do aluno.
    
    Perfil do aluno:
    {state["profile"]}
    
    Módulo atual: {state["current_module"]}
    Submódulo atual: {state["current_submodule"]}
    
    Pontos do aluno: {state["points"]}
    
    Contexto da conversa:
    {conversation_history}
    
    Mensagem do aluno: {message}
    
    Sua resposta deve ser:
    1. Concisa (máximo 1000 caracteres)
    2. Personalizada ao perfil e ao contexto da conversa
    3. Útil e informativa
    4. Alinhada com o módulo atual do curso
    """
    
    try:
        response = model.generate_content(prompt).text
        state["conversation_history"].append(f"Aluno: {message}")
        state["conversation_history"].append(f"Assistente: {response}")
        return [response]
    except Exception as e:
        print(f"Error in free interaction: {e}")
        return [random.choice(PROMPTS["erro"])]

# --- Main Message Processing Logic ---

def process_message(student_message, student_number):
    """Process an incoming message from a student"""
    state = get_student_state(student_number)
    
    # Handle special commands
    if student_message.lower() == "quiz":
        # Generate quiz for current module
        quiz = generate_quiz(state["current_module"])
        if not quiz:
            return ["Desculpe, não consegui gerar um quiz neste momento. Tente novamente mais tarde."]
        
        state["quiz_active"] = True
        state["current_quiz"] = quiz
        state["quiz_answers"] = []
        state["context"] = "quiz"
        
        # Present first question
        first_question = quiz[0]
        question_text = first_question["question"]
        options_text = "\n".join(first_question["options"])
        
        return [f"*Quiz do módulo {MODULES[state['current_module']]['titulo']}*\n\n{question_text}\n{options_text}"]
    
    elif student_message.lower() == "continuar":
        # Move to next submodule
        state["current_submodule"] += 1
        state["context"] = "presenting_content"
        return present_content(state)
    
    elif student_message.lower() == "pontos":
        return [f"Você tem {state['points']} pontos. 🏆\n\nContinue respondendo quizzes para ganhar mais pontos!"]
    
    elif student_message.lower() == "mentoria":
        if state["current_module"] in ["mentoria", "fim"]:
            if state["points"] >= 50:
                state["points"] -= 50
                return [f"Parabéns! 🎉 Você resgatou uma mentoria. Entraremos em contato para agendar. Seus pontos restantes: {state['points']}"]
            else:
                return [f"Você precisa de 50 pontos para solicitar uma mentoria, mas só tem {state['points']} pontos. Continue respondendo aos quizzes para ganhar mais pontos!"]
        else:
            return ["Você só pode solicitar mentoria quando chegar ao módulo de Mentoria. Continue avançando no curso!"]
    
    # Process message based on current context
    if state["context"] == "form":
        return collect_initial_info(student_message, state)
    
    elif state["context"] == "presenting_content":
        if student_message.lower() in ["próximo", "proximo", "continuar", "avançar", "avancar", "seguir"]:
                state["current_submodule"] += 1
                return present_content(state)
        else:
            state["context"] = "free_interaction"
            return process_free_interaction(student_message, state)
    
    elif state["context"] == "quiz":
        return handle_quiz_response(student_message, state)
    
    elif student_message.lower() in ["ajuda", "help", "comandos"]:
        return ["""📚 *Comandos disponíveis*
                - *continuar* ou *próximo*: Avançar para o próximo conteúdo
                - *quiz*: Testar seus conhecimentos com um quiz
                - *pontos*: Verificar sua pontuação atual
                - *mentoria*: Solicitar uma mentoria (disponível no final do curso)
                - *módulo*: Ver em qual módulo você está
                - *reiniciar*: Reiniciar o módulo atual
                Você também pode fazer qualquer pergunta relacionada ao empreendedorismo a qualquer momento!"""]
    
    elif state["context"] == "free_interaction" or state["context"] == "course_completed":
        return process_free_interaction(student_message, state)
    
   # Default fallback
    return ["Desculpe, não entendi. Você pode tentar novamente ou digitar 'continuar' para prosseguir com o curso."]

# --- Twilio webhook and Flask routes ---
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages via Twilio webhook"""
    # Get message content and sender info
    incoming_msg = request.values.get('Body', '').strip()
    sender_number = request.values.get('From', '')
    
    # Process the message and get responses
    responses = process_message(incoming_msg, sender_number)
    
    # Create Twilio response
    resp = MessagingResponse()
    
    # Add each message to the response
    for message in responses:
        # Ensure message is not too long for WhatsApp
        if len(message) > 1600:
            chunks = [message[i:i+1600] for i in range(0, len(message), 1600)]
            for chunk in chunks:
                resp.message(chunk)
        else:
            resp.message(message)
    
    return str(resp)

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "timestamp": time.time()}

@app.route("/reset", methods=["GET"])
def reset_students():
    """Reset all student data (for development/testing)"""
    global students
    students = {}
    return {"status": "ok", "message": "All student data reset"}

@app.route("/", methods=["GET"])
def home():
    """Basic home page"""
    return """
    <html>
        <head><title>Curso de Empreendedorismo UVV - Chatbot</title></head>
        <body>
            <h1>Curso de Empreendedorismo UVV</h1>
            <p>Chatbot para WhatsApp em funcionamento.</p>
            <p>Envie uma mensagem via WhatsApp para iniciar.</p>
        </body>
    </html>
    """

# --- Rate Limiting and Message Queue ---
# Simple in-memory rate limiting to prevent API abuse
last_message_time = {}
def rate_limit(sender_number):
    """Implement basic rate limiting"""
    current_time = time.time()
    if sender_number in last_message_time:
        time_since_last = current_time - last_message_time[sender_number]
        if time_since_last < 1.0:  # 1 second minimum between messages
            return False
    last_message_time[sender_number] = current_time
    return True

# --- Error Handling ---
@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler"""
    print(f"Error in application: {str(e)}")
    resp = MessagingResponse()
    resp.message("Desculpe, ocorreu um erro no sistema. Por favor, tente novamente mais tarde.")
    return str(resp)

# --- Main Application Entry Point ---
if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask application
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DEBUG", "False").lower() == "true")