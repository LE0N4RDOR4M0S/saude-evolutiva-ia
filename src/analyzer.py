import google.generativeai as genai
from .config import Config
import json

class AIAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
            },
            system_instruction="Você é um Staff Software Engineer sênior focado em manutenibilidade, dívida técnica e arquitetura de software."
        )

    def analyze_health(self, metrics_data):
        context = json.dumps(metrics_data, indent=2)
        
        prompt = f"""
        Analise os seguintes dados métricos extraídos de um repositório Git.
        Estes são os arquivos com maior risco (Hotspots) baseados em Churn x Complexidade.

        [DADOS DO REPOSITÓRIO]
        {context}
        
        [SEUS CRITÉRIOS DE ANÁLISE]
        1. Hotspots: Arquivos com muita alteração (churn) e alta complexidade são candidatos a refatoração.
        2. Bus Factor: Se 'top_authors' mostrar apenas 1 pessoa com >80% das mudanças, é um risco.
        3. Acoplamento: Arquivos que mudam sempre juntos ou têm churn constante indicam violação de SRP (Single Responsibility Principle).

        [TAREFA]
        Gere um relatório técnico em Markdown com as seções:
        
        ## 🚨 Diagnóstico de Saúde
        Resumo executivo do estado atual.
        
        ## 🔥 Análise de Risco (Top Hotspots)
        Destaque 2 ou 3 arquivos mais críticos e explique o porquê baseado nos números.
        
        ## 👥 Risco Humano (Silos de Conhecimento)
        Identifique se há dependência excessiva de desenvolvedores específicos.
        
        ## 🛠 Plano de Ação Imediato
        3 tarefas técnicas práticas (ex: "Refatorar classe X", "Criar testes para Y", "Quebrar módulo Z").
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro ao consultar o Gemini: {str(e)}"