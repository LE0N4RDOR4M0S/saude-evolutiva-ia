# 🚀 Guia de Início Rápido - Repo Health AI

## Passo 1: Instalar Dependências

```bash
pip install -r requirements.txt
```

## Passo 2: Executar o Dashboard

### Opção A: Script Automatizado (Windows)
```bash
run_dashboard.bat
```

### Opção B: Script Automatizado (Linux/Mac)
```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

### Opção C: Comando Direto
```bash
streamlit run app.py
```

## Passo 3: Configurar no Navegador

O dashboard abrirá automaticamente em `http://localhost:8501`

### Na Barra Lateral (Sidebar):

1. **📂 Caminho do Repositório**
   - Cole o caminho completo do seu repositório Git
   - Exemplo: `C:/Users/seu-nome/meu-projeto`

2. **🔑 API Key do Google** (Opcional)
   - Necessária apenas para usar o Consultor IA
   - Obtenha em: https://aistudio.google.com/app/apikey
   - Cole a chave no campo

3. **📊 Número de Commits**
   - Use o slider para escolher quantos commits analisar
   - Recomendado: 100 para início

4. **Clique em qualquer lugar fora dos campos** ou pressione Enter
   - A análise começará automaticamente

## Passo 4: Explorar as Abas

### 📈 Visão Geral
- Veja estatísticas resumidas
- Identifique os top 10 arquivos com maior risco

### 🎯 Matriz de Risco
- Gráfico de dispersão interativo
- Passe o mouse sobre as bolhas para ver detalhes
- Use filtros para focar em Hotspots

### 🔗 Acoplamento
- Descubra arquivos que mudam juntos
- Identifique possíveis violações de responsabilidade única

### 🤖 Consultor IA
- Análise avançada com Google Gemini
- Relatório técnico com plano de ação
- **Requer API Key configurada**

## 💡 Dicas

- ✅ O cache acelera análises repetidas do mesmo repositório
- ✅ Use "Limpar Cache" apenas ao mudar de repositório
- ✅ Comece com menos commits (50-100) para testar
- ✅ Hotspots vermelhos = prioridade máxima de refatoração

## 🐛 Problemas Comuns

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "Caminho inválido"
- Verifique se o caminho existe
- Use barras `/` ou duplas `\\` no Windows
- Certifique-se de que é um repositório Git (contém pasta `.git`)

### IA não funciona
- Verifique se configurou a API Key
- Teste a chave em: https://aistudio.google.com/
- Confirme que tem créditos disponíveis

---

**Pronto para começar! 🎉**

Execute `streamlit run app.py` e comece a analisar seus repositórios!
