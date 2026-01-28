import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import json
import io
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Reembolso Inteligente", page_icon="💰")

# Classe para o PDF (Mantendo a estrutura que funcionou)
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Solicitacao de Reembolso de Despesas', 0, 1, 'C')
        self.ln(5)

# Interface Lateral
with st.sidebar:
    st.title("Configurações")
    api_key = st.text_input("Gemini API Key", type="password", help="Pegue sua chave no AI Studio")
    nome_usuario = st.text_input("Seu Nome Completo")
    forma_recebimento = st.selectbox(
        "Forma de Recebimento",
        ["PIX (Chave CPF)", "PIX (Chave Celular)", "Conta Corrente", "Cartão Corporativo"]
    )
    detalhe_recebimento = st.text_input("Dados da Chave/Conta (Ex: seu CPF ou Ag/Conta)")

# Interface Principal
st.title("📑 Solicitação de Reembolso")
st.info("Selecione a categoria, suba a foto e gere seu PDF com assinatura.")

categoria = st.selectbox("Categoria do Gasto", 
                        ["Café da manhã", "Almoço", "Café da tarde", "Jantar", "Extras", "Estacionamento", "Pedágio"])

arquivo_foto = st.file_uploader("Carregar Nota Fiscal", type=["jpg", "jpeg", "png"])

if arquivo_foto and api_key:
    img = Image.open(arquivo_foto)
    st.image(img, caption="Recibo carregado", width=300)
    
    if st.button("Analisar Nota Fiscal 🔍"):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.spinner("IA extraindo dados..."):
            try:
                prompt = "Extraia Local, Data (DD/MM/AAAA), Valor (numero) e Horario (HH:MM). Responda apenas JSON: {'local': '...', 'data': '...', 'valor': 0.00, 'horario': '...'}"
                response = model.generate_content([prompt, img])
                dados = json.loads(response.text.replace('```json', '').replace('```', '').strip())
                st.session_state['dados_extraidos'] = dados
                st.success("Dados lidos com sucesso!")
            except Exception as e:
                st.error("Erro ao ler nota. Verifique se a foto está legível ou se sua API Key é válida.")

# Se os dados foram extraídos, mostra para confirmação e gera o PDF
if 'dados_extraidos' in st.session_state:
    d = st.session_state['dados_extraidos']
    st.divider()
    st.subheader("Confirmação de Dados")
    
    col1, col2 = st.columns(2)
    with col1:
        res_local = st.text_input("Local", d['local'])
        res_valor = st.number_input("Valor", value=float(d['valor']))
    with col2:
        res_data = st.text_input("Data", d['data'])
        res_horario = st.text_input("Horário", d['horario'])

    if st.button("Gerar Relatório PDF Final 📄"):
        # Geração do PDF em memória (buffer) para download
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Solicitante: {nome_usuario}", 0, 1)
        
        # Destaque para a forma de recebimento
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 10, f"FORMA DE RECEBIMENTO: {forma_recebimento} - {detalhe_recebimento}", 0, 1)
        pdf.set_text_color(0, 0, 0)
        
        pdf.cell(0, 10, f"Data da Solicitação: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
        pdf.ln(5)
        
        # Tabela
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(35, 10, 'Categoria', 1, 0, 'C', True)
        pdf.cell(85, 10, 'Local', 1, 0, 'C', True)
        pdf.cell(30, 10, 'Horario', 1, 0, 'C', True)
        pdf.cell(40, 10, 'Valor', 1, 1, 'C', True)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(35, 10, categoria, 1)
        pdf.cell(85, 10, res_local[:40], 1)
        pdf.cell(30, 10, res_horario, 1, 0, 'C')
        pdf.cell(40, 10, f"R$ {res_valor:.2f}", 1, 1, 'R')
        
        # Assinaturas
        pdf.ln(20)
        y = pdf.get_y()
        pdf.line(20, y, 90, y); pdf.line(120, y, 190, y)
        pdf.set_y(y+2)
        pdf.cell(90, 10, 'Assinatura Solicitante', 0, 0, 'C')
        pdf.cell(90, 10, 'Financeiro', 0, 1, 'C')
        
        # Anexo
        pdf.add_page()
        pdf.image(img, x=15, y=30, w=120)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button(label="📥 Baixar Relatório PDF", data=pdf_output, file_name="reembolso.pdf", mime="application/pdf")
        st.balloons()
