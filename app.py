import streamlit as st
import pandas as pd
import plotly.express as px
from src.collector import GitCollector
from src.analyzer import AIAnalyzer
import google.generativeai as genai
import os

st.set_page_config(
    page_title="Repo Health AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(show_spinner=False)
def analyze_repository(repo_path: str, num_commits: int):
    """
    Minera o repositório Git e retorna métricas.
    Cache é essencial pois o processo pode ser demorado.
    """
    try:
        collector = GitCollector(repo_path, limit_commits=num_commits)
        metrics = collector.collect_metrics()
        coupling = collector.get_coupling_analysis(min_shared_commits=3)
        return metrics, coupling, None
    except Exception as e:
        return None, None, str(e)


def format_authors(authors_dict):
    """Formata dicionário de autores para exibição."""
    if not authors_dict:
        return "N/A"
    return ", ".join([f"{name} ({count})" for name, count in authors_dict.items()])


def calculate_kpis(df):
    """Calcula KPIs principais do dashboard."""
    total_files = len(df)
    avg_risk = df["risk_score"].mean() if not df.empty else 0
    
    bus_factor = 0
    for _, row in df.iterrows():
        authors = row["top_authors"]
        if authors:
            total_changes = sum(authors.values())
            top_author_changes = max(authors.values())
            if (top_author_changes / total_changes) > 0.8:
                bus_factor += 1
    
    return total_files, avg_risk, bus_factor


st.sidebar.title("Configurações")
st.sidebar.markdown("---")

repo_path = st.sidebar.text_input(
    "Caminho do Repositório (Local)",
    value="",
    placeholder="C:/Users/seu-nome/seu-repo",
    help="Digite o caminho completo do repositório Git local"
)

api_key = st.sidebar.text_input(
    "API Key do Google (Gemini)",
    type="password",
    placeholder="Cole sua chave aqui",
    help="Obtenha em: https://aistudio.google.com/app/apikey"
)

num_commits = st.sidebar.slider(
    "Número de Commits a Analisar",
    min_value=10,
    max_value=500,
    value=100,
    step=10,
    help="Mais commits = análise mais completa, mas mais lenta"
)

st.sidebar.markdown("---")

if st.sidebar.button("Limpar Cache e Recarregar"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(
    "**Dica:** O cache acelera análises repetidas. "
    "Use 'Limpar Cache' apenas se mudar o repositório."
)

st.title("Repo Health AI")
st.markdown(
    "**Dashboard de Análise de Saúde de Repositórios Git** | "
    "Identifique Hotspots, Acoplamento e Riscos de Manutenção"
)
st.markdown("---")

if not repo_path:
    st.warning("Configure o caminho do repositório na barra lateral para começar.")
    st.stop()

if not os.path.exists(repo_path):
    st.error(f"Caminho inválido: `{repo_path}`. Verifique se o diretório existe.")
    st.stop()

if api_key:
    genai.configure(api_key=api_key)

with st.spinner(f"Analisando os últimos {num_commits} commits... (pode levar alguns minutos)"):
    metrics, coupling, error = analyze_repository(repo_path, num_commits)

if error:
    st.error(f"Erro ao analisar o repositório: {error}")
    st.stop()

if not metrics:
    st.warning("Nenhuma métrica foi coletada. Verifique se o repositório possui commits.")
    st.stop()

df = pd.DataFrame(metrics)

threshold = df["risk_score"].quantile(0.7)
df["is_hotspot"] = df["risk_score"] > threshold

df["authors_display"] = df["top_authors"].apply(format_authors)

total_files, avg_risk, bus_factor = calculate_kpis(df)

st.markdown("### Indicadores Principais")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total de Arquivos Analisados",
        value=f"{total_files}",
        help="Quantidade de arquivos únicos com mudanças"
    )

with col2:
    st.metric(
        label="Risco Médio",
        value=f"{avg_risk:,.0f}",
        help="Média do Risk Score (Churn × Complexidade)"
    )

with col3:
    st.metric(
        label="Bus Factor",
        value=f"{bus_factor}",
        delta="Arquivos em risco de autoria",
        delta_color="inverse",
        help="Arquivos onde >80% das mudanças vêm de 1 pessoa"
    )

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "Visão Geral",
    "Matriz de Risco",
    "Acoplamento",
    "Consultor IA"
])

with tab1:
    st.markdown("### Resumo Estatístico")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Distribuição de Risco:**")
        st.dataframe(
            df[["risk_score"]].describe().T,
            use_container_width=True
        )
    
    with col2:
        st.markdown("**Distribuição de Complexidade:**")
        st.dataframe(
            df[["complexity"]].describe().T,
            use_container_width=True
        )
    
    st.markdown("---")
    st.markdown("### Top 10 Arquivos com Maior Risco")
    
    top_10 = df.nlargest(10, "risk_score")[["file", "churn", "complexity", "risk_score", "authors_display"]]
    
    st.dataframe(
        top_10,
        column_config={
            "file": st.column_config.TextColumn("Arquivo", width="medium"),
            "churn": st.column_config.NumberColumn("Churn", format="%d"),
            "complexity": st.column_config.NumberColumn("Complexidade", format="%d"),
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score",
                format="%d",
                min_value=0,
                max_value=int(df["risk_score"].max())
            ),
            "authors_display": st.column_config.TextColumn("Principais Autores", width="medium")
        },
        hide_index=True,
        use_container_width=True
    )

with tab2:
    st.markdown("### Matriz de Risco: Churn vs Complexidade")
    st.markdown(
        "**Interpretação:** Quanto maior a bolha e mais à direita/acima, maior o risco. "
        "Hotspots (vermelho) exigem atenção imediata."
    )
    
    fig = px.scatter(
        df,
        x="complexity",
        y="churn",
        size="risk_score",
        color="is_hotspot",
        hover_data={
            "file": True,
            "churn": True,
            "complexity": True,
            "risk_score": True,
            "authors_display": True,
            "is_hotspot": False
        },
        labels={
            "complexity": "Complexidade Ciclomática",
            "churn": "Churn (Frequência de Mudanças)",
            "risk_score": "Risk Score",
            "is_hotspot": "Hotspot",
            "authors_display": "Autores Principais"
        },
        color_discrete_map={True: "#FF4B4B", False: "#4B8BFF"},
        title="",
        height=600
    )
    
    fig.update_layout(
        xaxis_title="Complexidade Ciclomática",
        yaxis_title="Churn (Frequência de Mudanças)",
        showlegend=True,
        legend_title_text="Hotspot?",
        hovermode="closest"
    )
    
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='white'),
            opacity=0.8
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### Tabela Interativa com Filtros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        show_only_hotspots = st.checkbox("Mostrar apenas Hotspots", value=False)
    
    with col2:
        min_risk = st.slider(
            "Risco Mínimo",
            min_value=0,
            max_value=int(df["risk_score"].max()),
            value=0
        )
    
    filtered_df = df.copy()
    
    if show_only_hotspots:
        filtered_df = filtered_df[filtered_df["is_hotspot"]]
    
    filtered_df = filtered_df[filtered_df["risk_score"] >= min_risk]
    
    st.dataframe(
        filtered_df[["file", "churn", "complexity", "risk_score", "authors_display", "is_hotspot"]],
        column_config={
            "file": st.column_config.TextColumn("Arquivo", width="large"),
            "churn": st.column_config.NumberColumn("Churn", format="%d"),
            "complexity": st.column_config.NumberColumn("Complexidade", format="%d"),
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score",
                format="%d",
                min_value=0,
                max_value=int(df["risk_score"].max())
            ),
            "authors_display": st.column_config.TextColumn("Principais Autores"),
            "is_hotspot": st.column_config.CheckboxColumn("Hotspot")
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

with tab3:
    st.markdown("### Análise de Acoplamento Lógico")
    st.markdown(
        "**Acoplamento Lógico:** Arquivos que mudam frequentemente juntos podem indicar "
        "violação do princípio de responsabilidade única (SRP) ou dependências ocultas."
    )
    
    if coupling:
        coupling_df = pd.DataFrame(coupling)
        
        st.dataframe(
            coupling_df,
            column_config={
                "file_a": st.column_config.TextColumn("Arquivo A", width="medium"),
                "file_b": st.column_config.TextColumn("Arquivo B", width="medium"),
                "shared_commits": st.column_config.NumberColumn(
                    "Commits Compartilhados",
                    format="%d"
                ),
                "strength": st.column_config.TextColumn("Força do Acoplamento")
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("### Top 5 Acoplamentos Mais Fortes")
        
        top_5_coupling = coupling_df.nlargest(5, "shared_commits")
        
        fig_coupling = px.bar(
            top_5_coupling,
            x="shared_commits",
            y=[f"{row['file_a']} ↔ {row['file_b']}" for _, row in top_5_coupling.iterrows()],
            orientation="h",
            labels={
                "x": "Número de Commits Compartilhados",
                "y": "Par de Arquivos"
            },
            title="",
            color="shared_commits",
            color_continuous_scale="Reds"
        )
        
        fig_coupling.update_layout(
            showlegend=False,
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_coupling, use_container_width=True)
        
    else:
        st.info("ℹNenhum acoplamento significativo detectado (mínimo: 3 commits compartilhados).")

with tab4:
    st.markdown("### Consultor IA Gemini")
    st.markdown(
        "Use a IA para obter insights avançados sobre a saúde do repositório. "
        "A análise considera Hotspots, Bus Factor e Acoplamento Lógico."
    )
    
    if not api_key:
        st.warning("Configure a API Key do Google Gemini na barra lateral para usar esta funcionalidade.")
    else:
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            top_n = st.number_input(
                "Número de arquivos top para análise:",
                min_value=3,
                max_value=20,
                value=5,
                step=1
            )
        
        with col2:
            include_coupling = st.checkbox(
                "Incluir análise de acoplamento",
                value=True
            )
        
        if st.button("Analisar com IA", type="primary"):
            top_files = df.nlargest(top_n, "risk_score").to_dict(orient="records")
            
            data_for_ai = {
                "repository_path": repo_path,
                "total_commits_analyzed": num_commits,
                "total_files": total_files,
                "bus_factor": bus_factor,
                "avg_risk_score": float(avg_risk),
                "top_hotspots": top_files
            }
            
            if include_coupling and coupling:
                data_for_ai["logical_coupling"] = coupling[:5]
            
            with st.spinner("Consultando Gemini... (pode levar alguns segundos)"):
                try:
                    analyzer = AIAnalyzer()
                    analysis = analyzer.analyze_health(data_for_ai)
                    
                    st.markdown("---")
                    st.markdown("### Relatório de Análise")
                    st.markdown(analysis)
                    
                except Exception as e:
                    st.error(f"Erro ao consultar a IA: {str(e)}")
                    st.info(
                        "Verifique se:\n"
                        "- A API Key está correta\n"
                        "- Você tem créditos disponíveis no Google AI Studio\n"
                        "- Sua conexão com a internet está ativa"
                    )

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Repo Health AI v1.0"
    "</div>",
    unsafe_allow_html=True
)
