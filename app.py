import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import json
import io
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Reembolso Digital", page_icon="📲")

# Puxa a chave dos Secrets (Onde a mágica da segurança acontece)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("Erro de configuração: API Key não encontrada nos Secrets.")
    st.stop()

class RelatorioPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Relatorio de Reembolso Consolidado', 0, 1, 'C')
        self.ln(5)

# Inicializa a lista de gastos na memória
if 'lista_gastos' not in st.session_state:
    st.session_state['lista_gastos'] = []

# --- INTERFACE ---
st.title("📑 Solicitação de Reembolso")

# Cadastro (Fica fixo para o relatório)
with st.expander("👤 Seus Dados de Recebimento", expanded=True):
    nome = st.text_input("Nome Completo")
    forma_rec = st.selectbox("Forma de Recebimento", ["Chave PIX", "Conta Corrente"])
    dados_rec = st.text_input("Chave PIX ou Agência/Conta")

st.divider()

# Lançamento de Gastos
st.subheader("📸 Lançar Novo Gasto")
cat = st.selectbox("Tipo de Gasto", ["Almoço", "Café", "Jantar", "Estacionamento", "Pedágio", "Combustível", "Outros"])
foto = st.camera_input("Tirar foto da nota")

if foto:
    if st.button("Analisar e Salvar Gasto"):
        with st.spinner("IA processando nota..."):
            try:
                img = Image.open(foto)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = "Extraia Local, Data (DD/MM/AAAA), Valor (numero) e Horario (HH:MM). Responda apenas JSON: {'local': '...', 'data': '...', 'valor': 0.00, 'horario': '...'}"
                
                response = model.generate_content([prompt, img])
                dados = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                
                st.session_state['lista_gastos'].append({
                    "categoria": cat,
                    "local": dados['local'],
                    "valor": float(dados['valor']),
                    "horario": dados['horario'],
                    "foto": img
                })
                st.success("Gasto adicionado!")
            except:
                st.error("Erro na leitura. Tente novamente com mais luz.")

# --- GERAÇÃO DO PDF ---
if st.session_state['lista_gastos']:
    st.divider()
    st.write(f"### Total de Gastos: {len(st.session_state['lista_gastos'])}")
    
    if st.button("✨ GERAR PDF FINAL PARA ENVIO"):
        pdf = RelatorioPDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Solicitante: {nome}", 0, 1)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 10, f"RECEBER VIA: {forma_rec} - {dados_rec}", 0, 1)
        pdf.set_text_color(0, 0, 0)
        
        # Tabela e Fotos (Loop para incluir tudo no mesmo arquivo)
        for i, g in enumerate(st.session_state['lista_gastos']):
            pdf.ln(5)
            pdf.cell(0, 10, f"Item {i+1}: {g['categoria']} - {g['local']} - R$ {g['valor']:.2f}", 1, 1)
            
        pdf.add_page()
        for i, g in enumerate(st.session_state['lista_gastos']):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 10, f"Anexo {i+1}: {g['categoria']}", 0, 1)
            img_byte_arr = io.BytesIO()
            g['foto'].convert("RGB").save(img_byte_arr, format='JPEG')
            pdf.image(img_byte_arr, w=100)
            pdf.ln(10)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Baixar PDF Completo", data=pdf_bytes, file_name="reembolso.pdf")
