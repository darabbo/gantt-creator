import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import textwrap
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Gantt Builder Dinamico")

st.title("📊 Gantt Builder Dinamico")
st.write("Aggiungi i task dal menu laterale. Scegli nome, date e colore. Il grafico si aggiornerà automaticamente.")

# --- PALETTE COLORI PREDEFINITA ---
# Mappiamo dei nomi leggibili a dei codici colore HEX per Plotly
COLOR_PALETTE = {
    "Blu": "#1f77b4",
    "Rosso": "#d62728",
    "Verde": "#2ca02c",
    "Arancione": "#ff7f0e",
    "Viola": "#9467bd",
    "Azzurro": "#17becf",
    "Grigio": "#7f7f7f"
}

# --- INIZIALIZZAZIONE DELLO STATO (SESSION STATE) ---
# Se è la prima volta che apriamo l'app, creiamo la lista con un solo task
if 'tasks' not in st.session_state:
    st.session_state.tasks = [{
        'id': 0, # Identificativo univoco
        'name': 'Primo Task',
        'start': datetime.date.today(),
        'end': datetime.date.today() + datetime.timedelta(days=7),
        'color': 'Blu'
    }]
if 'task_counter' not in st.session_state:
    st.session_state.task_counter = 1 # Serve per assegnare ID sempre nuovi

# --- BARRA LATERALE: GESTIONE TASK ---
st.sidebar.header("🛠️ Gestione Task")

# Bottone per aggiungere un nuovo task
if st.sidebar.button("➕ Aggiungi Nuovo Task", use_container_width=True):
    nuovo_id = st.session_state.task_counter
    st.session_state.tasks.append({
        'id': nuovo_id,
        'name': f'Nuovo Task {nuovo_id + 1}',
        'start': datetime.date.today(),
        'end': datetime.date.today() + datetime.timedelta(days=7),
        'color': 'Blu'
    })
    st.session_state.task_counter += 1
    st.rerun() # Ricarica l'app per mostrare il nuovo blocco

st.sidebar.markdown("---")

# Cicliamo su tutti i task salvati nello stato per creare gli input
task_da_rimuovere = None

for i, task in enumerate(st.session_state.tasks):
    with st.sidebar.expander(f"Task: {task['name']}", expanded=(i == len(st.session_state.tasks)-1)):
        # Input dinamici che aggiornano direttamente i dizionari nello st.session_state
        task['name'] = st.text_input("Nome", value=task['name'], key=f"nome_{task['id']}")
        
        col1, col2 = st.columns(2)
        with col1:
            task['start'] = st.date_input("Inizio", value=task['start'], key=f"start_{task['id']}")
        with col2:
            task['end'] = st.date_input("Fine", value=task['end'], key=f"end_{task['id']}")
            
        task['color'] = st.selectbox("Colore", options=list(COLOR_PALETTE.keys()), 
                                     index=list(COLOR_PALETTE.keys()).index(task['color']), 
                                     key=f"color_{task['id']}")
        
        # Opzione per eliminare il task (utile per la UX)
        if len(st.session_state.tasks) > 1: # Permette l'eliminazione solo se c'è più di un task
            if st.button("🗑️ Elimina", key=f"del_{task['id']}", help="Elimina questo task"):
                task_da_rimuovere = i

# Gestione rimozione task
if task_da_rimuovere is not None:
    st.session_state.tasks.pop(task_da_rimuovere)
    st.rerun()

# # --- SALVATAGGIO E CARICAMENTO DATI ---
# st.sidebar.markdown("---")
# st.sidebar.header("💾 Salva / Carica Dati")

# col_save, col_load = st.sidebar.columns(2)

# # PULSANTE SALVA
# with col_save:
#     if st.button("💾 Salva", use_container_width=True):
#         # Prepariamo i dati convertendo le date in stringhe (formato ISO)
#         dati_da_salvare = []
#         for t in st.session_state.tasks:
#             task_copy = t.copy()
#             task_copy['start'] = task_copy['start'].isoformat()
#             task_copy['end'] = task_copy['end'].isoformat()
#             dati_da_salvare.append(task_copy)
            
#         # Salviamo su file
#         with open("gantt_data.json", "w") as f:
#             json.dump(dati_da_salvare, f, indent=4)
        
#         st.sidebar.success("Dati salvati!")

# # PULSANTE CARICA
# with col_load:
#     if st.button("📂 Carica", use_container_width=True):
#         try:
#             # Leggiamo dal file
#             with open("gantt_data.json", "r") as f:
#                 dati_caricati = json.load(f)
                
#             # Riconvertiamo le stringhe in oggetti datetime.date
#             for t in dati_caricati:
#                 t['start'] = datetime.datetime.fromisoformat(t['start']).date()
#                 t['end'] = datetime.datetime.fromisoformat(t['end']).date()
                
#             # Aggiorniamo lo stato
#             st.session_state.tasks = dati_caricati
            
#             # Aggiorniamo il contatore degli ID per i prossimi task
#             if dati_caricati:
#                 st.session_state.task_counter = max(t['id'] for t in dati_caricati) + 1
#             else:
#                 st.session_state.task_counter = 1
                
#             st.rerun() # Ricarichiamo l'app per mostrare i nuovi dati
            
#         except FileNotFoundError:
#             st.sidebar.error("Nessun file trovato!")

# --- CREAZIONE DEL DATAFRAME ---
# Convertiamo la lista di dizionari in un DataFrame Pandas
df = pd.DataFrame(st.session_state.tasks)

# Controllo date
df['Inizio_Valido'] = pd.to_datetime(df['start'])
df['Fine_Valida'] = pd.to_datetime(df['end'])
df['Fine_Valida'] = df[['Inizio_Valido', 'Fine_Valida']].max(axis=1)

df['Plot_Start'] = df['Inizio_Valido'].dt.strftime('%Y-%m-%d 00:00:00')
df['Plot_Finish'] = (df['Fine_Valida'] + pd.Timedelta(days=1)).dt.strftime('%Y-%m-%d 00:00:00')

# NUOVO: A capo automatico per i nomi dei task lunghi (es. ogni 35 caratteri)
# textwrap.wrap divide la stringa, poi uniamo i pezzi con "<br>" (il ritorno a capo di Plotly/HTML)
df['name_wrapped'] = df['name'].apply(lambda x: "<br>".join(textwrap.wrap(x, width=35)))

# --- CREAZIONE GRAFICO PLOTLY ---
fig = px.timeline(
    df, 
    x_start="Plot_Start", 
    x_end="Plot_Finish", 
    y="name_wrapped", # Usiamo la colonna con i ritorni a capo
    color="color", 
    color_discrete_map=COLOR_PALETTE, 
    hover_name="name",
    hover_data={
        "name_wrapped": False, # Nascondiamo questa dal tooltip perché ha i tag <br>
        "name": False,
        "color": False,
        "Plot_Start": False, 
        "Plot_Finish": False,
        "start": True,
        "end": True
    }
)

# Invertiamo l'asse Y e INGRANDIAMO il testo dei task
fig.update_yaxes(
    autorange="reversed",
    tickfont=dict(size=18, color="black"), # Aumenta questo valore per fare i nomi ancora più grandi
    title_text=""
) 

# Personalizzazione asse X e INGRANDIAMO il testo delle date
fig.update_xaxes(
    tickformat="%d %b\n%Y",  
    showgrid=True,
    gridcolor='lightgray',
    tickfont=dict(size=18, color="black") # Dimensione carattere delle date in basso
)

fig.update_layout(
    # Aumentiamo il moltiplicatore (da 60 a 90) per dare più spazio verticale 
    # a ogni barra, dato che ora il testo può andare su più righe ed è più grande
    height=max(400, len(df)*90), 
    showlegend=False, 
    margin=dict(l=20, r=20, t=20, b=20)
)

# Mostriamo il grafico
st.plotly_chart(fig, use_container_width=True)

# --- OUTPUT TABELLARE ---
st.markdown("---")
st.subheader("Tabella Dati")
st.dataframe(df[['name', 'start', 'end', 'color']].rename(columns={
    'name': 'Nome Task', 
    'start': 'Data Inizio', 
    'end': 'Data Fine', 
    'color': 'Colore Assegnato'
}), use_container_width=True, hide_index=True)