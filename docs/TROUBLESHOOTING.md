# 🔧 Troubleshooting - Repo Health AI

## Problemas Comuns e Soluções

### 1. Erro: "ModuleNotFoundError: No module named 'streamlit'"

**Causa:** Dependências não instaladas.

**Solução:**
```bash
pip install -r requirements.txt
```

Se persistir:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

### 2. Erro: "Caminho inválido" ou "Not a git repository"

**Causa:** Caminho fornecido não é um repositório Git válido.

**Soluções:**

#### Windows:
```
Correto:   C:/Users/nome/meu-projeto
Correto:   C:\\Users\\nome\\meu-projeto
Incorreto: C:\Users\nome\meu-projeto  (barra simples não funciona em input)
```

#### Linux/Mac:
```
Correto:   /home/usuario/meu-projeto
Correto:   ~/projetos/meu-repo
Incorreto: home/usuario/meu-projeto  (falta barra inicial)
```

**Verificação:**
```bash
# Certifique-se de que existe a pasta .git
ls -la /caminho/do/repo  # Linux/Mac
dir C:\caminho\do\repo   # Windows
```

---

### 3. Dashboard Lento ou Travando

**Causas Possíveis:**
- Muitos commits sendo analisados
- Repositório muito grande
- Cache desabilitado

**Soluções:**

1. **Reduza o número de commits:**
   - Comece com 50-100 commits
   - Aumente gradualmente se necessário

2. **Não limpe o cache desnecessariamente:**
   - O cache acelera análises repetidas
   - Só use "Limpar Cache" ao mudar de repositório

3. **Feche outras abas/aplicativos:**
   - Análise de Git + IA pode ser intensiva

---

### 4. Erro: "Google API Error" ou "Invalid API Key"

**Causa:** Problemas com a API Key do Google Gemini.

**Soluções:**

1. **Verifique a chave:**
   - Acesse: https://aistudio.google.com/app/apikey
   - Copie a chave completa
   - Cole novamente no campo da sidebar

2. **Verifique créditos:**
   - Google AI Studio tem limite gratuito
   - Confirme que não excedeu a quota

3. **Teste a chave:**
   ```python
   import google.generativeai as genai
   
   genai.configure(api_key="sua-chave-aqui")
   model = genai.GenerativeModel("gemini-1.5-flash")
   response = model.generate_content("Olá")
   print(response.text)
   ```

4. **Use sem IA:**
   - O dashboard funciona sem a API Key
   - Apenas o "Consultor IA" ficará desabilitado
   - Todas as outras funcionalidades continuam ativas

---

### 5. Gráfico de Dispersão Vazio ou Sem Hotspots

**Causa:** Filtros muito restritivos ou poucos dados.

**Soluções:**

1. **Reduza o Risco Mínimo:**
   - Na aba "Matriz de Risco"
   - Mova o slider "Risco Mínimo" para 0

2. **Desmarque "Mostrar apenas Hotspots":**
   - Verá todos os arquivos, não só os críticos

3. **Aumente o número de commits:**
   - Mais commits = mais dados para análise

4. **Verifique se há arquivos Python:**
   - Complexidade ciclomática só funciona para .py
   - Outros arquivos terão complexity = 1

---

### 6. Acoplamento Não Aparece

**Causa:** Nenhum par de arquivos mudou junto ≥3 vezes.

**Soluções:**

1. **Aumente o número de commits:**
   - Mais commits = maior chance de detectar acoplamento

2. **Projeto muito modular:**
   - Isso é BOM! Significa baixo acoplamento lógico
   - Ausência de acoplamento forte é um sinal positivo

---

### 7. Bus Factor = 0

**Causa:** Nenhum arquivo tem >80% de autoria concentrada.

**Solução:**
- **Isso é ÓTIMO!**
- Indica boa distribuição de conhecimento
- Projeto tem baixo risco de silos

---

### 8. Erro: "PermissionError" ao Analisar Repositório

**Causa:** Falta de permissão para ler arquivos.

**Soluções:**

1. **Execute como administrador** (Windows):
   - Clique com direito em PowerShell
   - "Executar como administrador"

2. **Verifique permissões** (Linux/Mac):
   ```bash
   chmod -R 755 /caminho/do/repo
   ```

3. **Feche editores/IDEs:**
   - VSCode, PyCharm podem trancar arquivos
   - Feche antes de analisar

---

### 9. Importação Falha: "cannot import name 'GitCollector'"

**Causa:** Estrutura de diretórios incorreta.

**Solução:**

1. **Verifique a estrutura:**
   ```
   seu-projeto/
   ├── app.py          ← Arquivo principal
   └── src/
       ├── __init__.py  ← Deve existir (pode ser vazio)
       ├── collector.py
       ├── analyzer.py
       └── config.py
   ```

2. **Crie `__init__.py` se não existir:**
   ```bash
   # Linux/Mac
   touch src/__init__.py
   
   # Windows
   type nul > src\__init__.py
   ```

---

### 10. Dashboard Não Abre no Navegador

**Causa:** Porta 8501 já está em uso.

**Soluções:**

1. **Mate processos Streamlit antigos:**
   ```bash
   # Linux/Mac
   pkill -f streamlit
   
   # Windows
   taskkill /F /IM streamlit.exe
   ```

2. **Use outra porta:**
   ```bash
   streamlit run app.py --server.port 8502
   ```

3. **Abra manualmente:**
   - Vá para: http://localhost:8501

---

### 11. Erro: "UnicodeDecodeError" ao Ler Arquivos

**Causa:** Arquivos com encoding não-UTF8.

**Solução:**

- **Temporária:** Projeto está configurado para ignorar esses arquivos
- **Permanente:** Converta arquivos para UTF-8:
  ```python
  # converter.py
  with open('arquivo.txt', 'r', encoding='latin-1') as f:
      content = f.read()
  with open('arquivo.txt', 'w', encoding='utf-8') as f:
      f.write(content)
  ```

---

### 12. Métricas Parecem Erradas

**Verificações:**

1. **Churn:**
   - É cumulativo (soma de todas as mudanças)
   - Arquivos muito modificados terão churn alto
   - **Normal:** 50-200 para arquivos ativos
   - **Atenção:** >500 indica hotspot

2. **Complexidade:**
   - Só funciona para Python (.py)
   - Outros arquivos = 1 (fallback)
   - **Normal:** 5-20 para módulos simples
   - **Atenção:** >50 indica complexidade alta

3. **Risk Score:**
   - Multiplicação: Churn × Complexidade
   - **Normal:** <1000
   - **Atenção:** >5000 é hotspot crítico

---

### 13. IA Retorna Respostas Genéricas

**Causa:** Dados insuficientes ou muito homogêneos.

**Soluções:**

1. **Aumente arquivos analisados:**
   - Na aba "Consultor IA"
   - Aumente "Número de arquivos" para 10-15

2. **Inclua acoplamento:**
   - Marque "Incluir análise de acoplamento"
   - Fornece mais contexto para a IA

3. **Aumente commits:**
   - Mais dados históricos = análise mais rica

---

### 14. Erro: "StreamlitAPIException"

**Causa:** Versão incompatível do Streamlit.

**Solução:**
```bash
pip install --upgrade streamlit>=1.30.0
```

---

### 15. Cache Não Está Funcionando

**Sintomas:** Análise demora toda vez, mesmo sem mudar parâmetros.

**Soluções:**

1. **Não altere parâmetros:**
   - Cache quebra se mudar caminho, commits, etc.

2. **Limpe cache corrompido:**
   - Clique em "Limpar Cache e Recarregar"
   - Rode análise novamente

3. **Verifique espaço em disco:**
   - Cache usa espaço temporário
   - Certifique-se de ter ≥1GB livre

---

## 🆘 Suporte Adicional

### Logs de Debug

Para ver logs detalhados:
```bash
streamlit run app.py --logger.level=debug
```

### Reportar Bugs

Se nenhuma solução funcionou:

1. **Capture o erro completo:**
   - Screenshot ou copie a mensagem de erro

2. **Informe o ambiente:**
   - Sistema operacional
   - Versão do Python (`python --version`)
   - Versão do Streamlit (`pip show streamlit`)

3. **Passos para reproduzir:**
   - O que você fez antes do erro aparecer

---

## 📚 Recursos Úteis

- **Documentação Streamlit:** https://docs.streamlit.io
- **Google AI Studio:** https://aistudio.google.com
- **PyDriller Docs:** https://pydriller.readthedocs.io
- **Radon Docs:** https://radon.readthedocs.io

---

**Ainda com problemas?** Verifique o [README.md](README.md) e [QUICKSTART.md](QUICKSTART.md) para instruções básicas.
