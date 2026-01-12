# 🔍 Repo Health AI - Dashboard Streamlit

Dashboard web interativo para análise de saúde de repositórios Git. Identifica Hotspots, Acoplamento Lógico e riscos de manutenção usando métricas de Churn e Complexidade Ciclomática.

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar o Dashboard

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente no navegador em `http://localhost:8501`

## 📋 Funcionalidades

### 📊 KPIs Principais
- **Total de Arquivos**: Quantidade de arquivos únicos analisados
- **Risco Médio**: Média do Risk Score (Churn × Complexidade)
- **Bus Factor**: Arquivos onde >80% das mudanças vêm de 1 pessoa (risco de silos de conhecimento)

### 📈 Visão Geral
- Resumo estatístico das métricas
- Top 10 arquivos com maior risco
- Tabela com barras de progresso para visualização de risco

### 🎯 Matriz de Risco
- **Gráfico de Dispersão Interativo**:
  - Eixo X: Complexidade Ciclomática
  - Eixo Y: Churn (Frequência de mudanças)
  - Tamanho da bolha: Risk Score
  - Cor: Hotspot (vermelho) vs Normal (azul)
  - Tooltip: Nome do arquivo e autores principais
- **Tabela Interativa** com filtros por Hotspots e Risco Mínimo

### 🔗 Acoplamento Lógico
- Identifica arquivos que mudam frequentemente juntos
- Gráfico de barras dos top 5 acoplamentos mais fortes
- Tabela detalhada com força do acoplamento

### 🤖 Consultor IA (Gemini)
- Análise avançada usando Google Gemini
- Relatório técnico em Markdown com:
  - Diagnóstico de saúde
  - Análise de risco dos top hotspots
  - Identificação de silos de conhecimento
  - Plano de ação imediato

## ⚙️ Configuração

### Sidebar (Barra Lateral)
1. **Caminho do Repositório**: Informe o caminho completo do repositório Git local
2. **API Key do Google**: (Opcional) Para usar o Consultor IA
   - Obtenha em: https://aistudio.google.com/app/apikey
3. **Número de Commits**: Slider de 10 a 500 commits
   - Mais commits = análise mais completa, mas mais lenta

### Cache e Performance
- O dashboard usa `@st.cache_data` para cachear resultados da mineração Git
- Use o botão **"Limpar Cache e Recarregar"** apenas quando:
  - Mudar para outro repositório
  - Quiser reanalisar após novos commits

## 💡 Dicas de Uso

1. **Primeira Análise**: Comece com 100 commits para ter uma visão geral rápida
2. **Análise Profunda**: Aumente para 300-500 commits se o repositório for grande
3. **Hotspots**: Arquivos em vermelho no scatter plot exigem atenção imediata
4. **Bus Factor Alto**: Indica dependência excessiva de poucos desenvolvedores
5. **Acoplamento Forte**: Pode indicar violação de responsabilidade única

## 🎨 Estilo e Layout

- **Layout Wide**: Aproveitamento máximo da tela
- **Tabs (Abas)**: Organização clara das diferentes análises
- **Plotly Express**: Gráficos interativos e responsivos
- **Código Modular**: Funções separadas para cada responsabilidade
- **Tratamento de Erros**: Validação de caminho e mensagens claras

## 📦 Estrutura do Projeto

```
saude-evolutiva-ia/
├── app.py                 # Dashboard Streamlit (NOVO)
├── requirements.txt       # Dependências (atualizado)
├── src/
│   ├── collector.py      # GitCollector (classe de mineração)
│   ├── analyzer.py       # AIAnalyzer (integração Gemini)
│   ├── cli.py            # CLI original
│   └── config.py         # Configurações
└── README_DASHBOARD.md   # Este arquivo
```

## 🔧 Tecnologias Utilizadas

- **Streamlit**: Framework web para dashboards em Python
- **Pandas**: Manipulação e análise de dados
- **Plotly Express**: Visualizações interativas
- **PyDriller**: Mineração de repositórios Git
- **Radon**: Cálculo de complexidade ciclomática
- **Google Gemini**: IA generativa para análise avançada

## 🐛 Solução de Problemas

### Erro: "Caminho inválido"
- Verifique se o caminho está correto e se é um repositório Git válido
- Use barras normais (/) ou duplas invertidas (\\\\) no Windows

### Erro ao consultar IA
- Verifique se a API Key está correta
- Confirme se tem créditos disponíveis no Google AI Studio
- Teste sua conexão com internet

### Dashboard lento
- Reduza o número de commits
- Use o cache (não clique em "Limpar Cache" desnecessariamente)
- Analise repositórios menores primeiro

## 📝 Exemplo de Uso

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar dashboard
streamlit run app.py

# 3. No navegador:
#    - Sidebar > Caminho: C:/Users/seu-nome/meu-projeto
#    - Sidebar > API Key: (opcional) sua-chave-gemini
#    - Sidebar > Commits: 100
#    - Aguardar análise
#    - Explorar as 4 abas (Visão Geral, Matriz de Risco, Acoplamento, Consultor IA)
```

---

Desenvolvido com ❤️ usando Streamlit + Google Gemini
