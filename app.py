import streamlit as st
from openai import OpenAI
import pandas as pd
from io import BytesIO
from fastapi import FastAPI, UploadFile, Form, HTTPException, Header
import os

app = FastAPI()

# 🔐 Pega a chave secreta da variável de ambiente
EXPECTED_API_KEY = os.getenv("API_KEY_SECRETA")

# Configuração do Streamlit
st.set_page_config(page_title="Extractor Yalo Multilíngue", layout="wide")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("yalo_logo.jpg", width=120)

# Mapear nomes de idioma da interface para chaves internas
idiomas_suportados = {
    "Português": "portuguese",
    "Español": "spanish",
    "English": "english"
}

# Textos da interface
textos = {
    "pt": {
        "title": "🧠 Extrator de Insights - Português",
        "subtitle": "Faça upload dos arquivos e extraia insights do discovery técnico.",
        "idioma_analise": "📘 Idioma de geração do relatório",
        "client_name": "🧾 Nome do cliente",
        "upload_excel": "📤 Envie o arquivo Excel (.xlsx) do discovery técnico",
        "upload_txt": "📤 Envie arquivo .txt com transcrição (opcional)",
        "paste_transcript": "📋 Ou cole aqui a transcrição da call (opcional)",
        "consultant_notes": "📝 Observações do consultor (opcional)",
        "extract_button": "🚀 Extrair Insights",
        "fill_client": "Por favor, preencha o nome do cliente.",
        "provide_inputs": "Você deve fornecer ao menos um discovery ou transcrição.",
        "analyzing": "🔍 Analisando discovery...",
        "analyzing_call": "🎧 Processando transcrição...",
        "consolidating": "🧠 Consolidando insights...",
        "success": "✅ Insights extraídos com sucesso!",
        "download": "📥 Baixar Insights (.txt)"
    },
    "es": {
        "title": "🧠 Extractor de Insights - Español",
        "subtitle": "Sube los archivos y extrae insights del discovery técnico.",
        "idioma_analise": "📘 Idioma para generar el informe",
        "client_name": "🧾 Nombre del cliente",
        "upload_excel": "📤 Sube el archivo Excel (.xlsx) del discovery técnico",
        "upload_txt": "📤 Sube archivo .txt con transcripción (opcional)",
        "paste_transcript": "📋 O pega aquí la transcripción de la llamada (opcional)",
        "consultant_notes": "📝 Observaciones del consultor (opcional)",
        "extract_button": "🚀 Extraer Insights",
        "fill_client": "Por favor, introduce el nombre del cliente.",
        "provide_inputs": "Debes proporcionar al menos un discovery o transcripción.",
        "analyzing": "🔍 Analizando discovery...",
        "analyzing_call": "🎧 Procesando transcripción...",
        "consolidating": "🧠 Consolidando insights...",
        "success": "✅ ¡Insights extraídos con éxito!",
        "download": "📥 Descargar Insights (.txt)"
    },
    "en": {
        "title": "🧠 Insights Extractor - English",
        "subtitle": "Upload the files and extract insights from the technical discovery.",
        "idioma_analise": "📘 Report generation language",
        "client_name": "🧾 Client name",
        "upload_excel": "📤 Upload Excel (.xlsx) file from discovery",
        "upload_txt": "📤 Upload .txt transcript (optional)",
        "paste_transcript": "📋 Or paste the call transcript here (optional)",
        "consultant_notes": "📝 Consultant's notes (optional)",
        "extract_button": "🚀 Extract Insights",
        "fill_client": "Please enter the client name.",
        "provide_inputs": "You must provide at least a discovery or transcript.",
        "analyzing": "🔍 Analyzing discovery...",
        "analyzing_call": "🎧 Processing transcript...",
        "consolidating": "🧠 Consolidating insights...",
        "success": "✅ Insights successfully extracted!",
        "download": "📥 Download Insights (.txt)"
    }
}

idioma_interface = st.selectbox("🌐 Please select Language", list(idiomas_suportados.keys()))
idioma_key = idiomas_suportados[idioma_interface]  # ex: "portuguese"

mapa_curto = {"portuguese":"pt", "spanish":"es", "english":"en"}
t = textos[ mapa_curto[idioma_key] ]

st.title(t["title"])
st.markdown(t["subtitle"])

# Seletor de idioma de análise
idioma = st.selectbox(t["idioma_analise"], list(idiomas_suportados.keys()), index=list(idiomas_suportados.keys()).index(idioma_interface))
nome_cliente = st.text_input(t["client_name"])
arquivo = st.file_uploader(t["upload_excel"], type=["xlsx"])
arquivo_txt = st.file_uploader(t["upload_txt"], type=["txt"])
texto_call = st.text_area(t["paste_transcript"], height=250)
observacoes_consultor = st.text_area(t["consultant_notes"], height=150)

def extrair_discovery_texto(arquivo_excel_bytes):
    try:
        xls = pd.ExcelFile(BytesIO(arquivo_excel_bytes))
        abas = [s for s in xls.sheet_names if "SalesDesk" not in s]
        blocos = []
        for aba in abas:
            df = xls.parse(aba).dropna(how='all').dropna(axis=1, how='all')
            for _, row in df.iterrows():
                if len(row) >= 3 and pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
                    p = str(row.iloc[1]).strip()
                    r = str(row.iloc[2]).strip()
                    blocos.append(f"[{aba}] Pergunta: {p}\nResposta: {r}")
        return "\n\n".join(blocos)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar Excel: {e}")

if st.button(t["extract_button"]):
    if not nome_cliente.strip():
        st.warning(t["fill_client"])
    elif not arquivo and not texto_call and not arquivo_txt:
        st.warning(t["provide_inputs"])
    else:
        # 1) Puxar texto discovery
        with st.spinner(t["analyzing"]):
            discovery_texto = ""
            if arquivo:
                discovery_texto = extrair_discovery_texto(arquivo.read())
        # 2) Preparar insights da call
        with st.spinner(t["analyzing_call"]):
            insights_call = texto_call.strip() or ""
        # 3) Consolidar com blocos multilíngue
        with st.spinner(t["consolidating"]):
            idi_key = idiomas_suportados[idioma]
            # Escolher bloco completo conforme idioma
            if idi_key == "portuguese":
                bloco = f"""🛑 IMPORTANTE: Responda apenas em **português**. Não use outros idiomas.

Projeto com o cliente: **{nome_cliente}**

Abaixo estão os conteúdos de três fontes:

📂 Insights do discovery técnico:
\"\"\"{discovery_texto}\"\"\"

💬 Insights da transcrição da call:
\"\"\"{insights_call}\"\"\"

📌 Observações diretas do Solutions Consultant:
\"\"\"{observacoes_consultor}\"\"\"

Agora, una essas informações em um único relatório estruturado, evitando duplicações e organizando os tópicos com o máximo de clareza e objetividade.

1. 📌 **Contexto do projeto**  
   - Descreva de forma completa e detalhada o modelo de operação atual da empresa.  
   - Inclua informações como: modelo de negócios, número de centros de distribuição, número de vendedores, ticket médio, volume médio de pedidos, processos operacionais atuais, canais de venda (WhatsApp, loja online, televendas), formas de pagamento (boleto antecipado, boleto faturado, PIX, cartão), clusters de clientes, tabelas de preços, regras de promoções (combos, leve X pague Y, descontos progressivos, cupons), condições comerciais, controle de estoque (estoque por CD, disponibilidade restrita), regras de corte (dias/horários), sistemas envolvidos (Mercanet, Infracommerce, SAP, Salesforce, gateways de pagamento, APIs internas) e qualquer outro dado relevante.  
   - 🚫 **Não resuma de forma genérica**; mantenha todos os detalhes disponíveis.  
   - 📌 Dados quantitativos (nº de pedidos, clientes, SKUs, volumes, ticket médio) devem estar aqui.

2. 🌟 **Objetivos principais do projeto**  
   - Use bullets com verbos de ação fortes (Digitalizar, Automatizar, Viabilizar, Expandir, Aumentar, Implementar, Reduzir, Integrar).  
   - Relacione cada objetivo a resultados práticos (eficiência, engajamento, automação, expansão).  
   - Sempre que possível, conecte os objetivos às fases do projeto (fase 1 = autosserviço, fase 2 = commerce).  
   - Evite frases genéricas como “melhorar processos”.

3. ⚠️ **Riscos e gaps identificados** (em bullets)

4. 📦 **Casos de uso propostos ou discutidos** (em bullets)

5. 🔗 **Integrações mencionadas ou necessárias** (em bullets)  
   - Descreva todos os sistemas (Mercanet, Infracommerce, gateways, ERPs, APIs internas).  
   - Detalhe quais dados devem ser sincronizados ou expostos (catálogo, preços, estoque, status de pedidos, cadastro de clientes, dados de representantes).  
   - Informe métodos de integração (API/REST, CSV, Webhook).  
   - Se houver requisitos de teste, homologação, segurança ou autenticação, inclua-os.  
   - 🚫 **Não resuma**; preserve todos os detalhes das fontes.

6. ❓ **Dúvidas ou pontos pendentes levantados na call** (em bullets)

7. 🔒 **Restrições técnicas ou comerciais citadas** (em bullets)

8. 🧩 **Premissas acordadas entre as partes** (em bullets)

9. 🔄 **Próximos passos mencionados ou sugeridos** (em bullets)

10. 📝 **Observações gerais ou insights adicionais relevantes**

11. 📊 **Dados operacionais e regras comerciais identificadas**  
    - Consolide catálogo de produtos, SKUs, tipos de clientes, clusters, tabelas de preços, condições comerciais, regras de promoções, formas de pagamento, métodos de corte, controle de estoque, volumes e ticket médio.  
    - Descreva regras de checkout: limitações de pagamento, pré-requisitos de compra, políticas de crédito, exigências de faturamento ou pagamento antecipado.  
    - ✅ **Formato de “painel operacional”** (bullets ou tabela).  
    - 🔥 Transcreva fielmente; se faltar algo, exiba “Informação não fornecida nas fontes.”"""

            elif idi_key == "spanish":
                bloco = f"""🛑 IMPORTANTE: Responde solo en **español**. No utilices otros idiomas.

Proyecto con el cliente: **{nome_cliente}**

A continuación se presentan los contenidos de tres fuentes:

📂 Insights del discovery técnico:
\"\"\"{discovery_texto}\"\"\"

💬 Insights de la transcripción de la llamada:
\"\"\"{insights_call}\"\"\"

📌 Observaciones directas del Solutions Consultant:
\"\"\"{observacoes_consultor}\"\"\"

Ahora, une esta información en un informe estructurado, evitando duplicaciones y organizando los temas con la mayor claridad posible.

1. 📌 **Contexto del proyecto**  
   - Describe en detalle el modelo operativo actual de la empresa.  
   - Incluye: modelo de negocio, número de centros de distribución, número de vendedores, ticket promedio, volumen de pedidos, procesos vigentes, canales de venta (WhatsApp, tienda online, televentas), formas de pago (boleto anticipado, boleto facturado, PIX, tarjeta), grupos de clientes, tablas de precios, reglas de promociones (combos, lleva X paga Y, descuentos progresivos, cupones), condiciones comerciales, control de inventario (por CD, disponibilidad restringida), reglas de corte (días/horarios), sistemas involucrados (Mercanet, Infracommerce, SAP, Salesforce, pasarelas, APIs internas) y cualquier otro dato relevante.  
   - 🚫 **No resumas de forma genérica**; conserva todos los detalles.  
   - 📌 Si hay datos cuantitativos (n.º de pedidos, clientes, SKUs, volúmenes, ticket promedio), inclúyelos.

2. 🌟 **Objetivos principales del proyecto**  
   - Usa bullets con verbos de acción (Digitalizar, Automatizar, Viabilizar, Expandir, Aumentar, Implementar, Reducir, Integrar).  
   - Relaciona cada objetivo con resultados prácticos (eficiencia, engagement, automatización, expansión).  
   - Conecta con fases del proyecto (fase 1 = autoservicio, fase 2 = commerce).  
   - Evita frases genéricas como “mejorar procesos”.

3. ⚠️ **Riesgos y brechas identificadas** (en bullets)

4. 📦 **Casos de uso propuestos o discutidos** (en bullets)

5. 🔗 **Integraciones mencionadas o necesarias** (en bullets)  
   - Describe todos los sistemas, datos, métodos, requisitos de prueba/homologación/seguridad.  
   - 🚫 **No resumas**; conserva todos los detalles.

6. ❓ **Dudas o puntos pendientes planteados en la llamada** (en bullets)

7. 🔒 **Restricciones técnicas o comerciales mencionadas** (en bullets)

8. 🧩 **Supuestos acordados entre las partes** (en bullets)

9. 🔄 **Próximos pasos mencionados o sugeridos** (en bullets)

10. 📝 **Observaciones generales o insights adicionales**  

11. 📊 **Datos operativos y reglas comerciales identificadas**  
    - Consolida catálogo, SKUs, clusters, tablas de precios, condiciones comerciales, reglas de promociones, formas de pago, métodos de corte, control de inventario, volúmenes, ticket medio.  
    - Describe reglas de checkout: limitaciones de pago, prerrequisitos, políticas de crédito, requisitos de facturación o anticipación.  
    - ✅ **Panel operativo** (bullets ou tabla).  
    - 🔥 Transcribe fielmente; si falta algo, “Información no proporcionada en las fuentes.”"""

            else:  # english
                bloco = f"""🛑 IMPORTANT: Respond only in **English**. Do not use any other language.

Project with client: **{nome_cliente}**

Below are the contents from three sources:

📂 Insights from the technical discovery:
\"\"\"{discovery_texto}\"\"\"

💬 Insights from the call transcript:
\"\"\"{insights_call}\"\"\"

📌 Consultant’s direct notes:
\"\"\"{observacoes_consultor}\"\"\"

Now, merge this information into a single structured report, avoiding duplication and organizing the topics clearly and concisely.

1. 📌 **Project context**  
   - Describe in full detail the company’s current operating model: business model, number of distribution centers, number of sales reps, average ticket, order volume, current processes, sales channels (WhatsApp, online store, telesales), payment methods (boleto antecipado, boleto faturado, PIX, credit card), customer clusters, price tables, promotion rules (combos, buy X pay Y, tiered discounts, coupons), commercial conditions, inventory control (by DC, restricted availability), cut-off rules (days/hours), systems involved (Mercanet, Infracommerce, SAP, Salesforce, payment gateways, internal APIs) and any other relevant data.  
   - 🚫 **Do not summarize generically**; preserve all details.  
   - 📌 If quantitative data exists (order count, customers, SKUs, volumes, average ticket), include it.

2. 🌟 **Main objectives of the project**  
   - Use bullets with strong action verbs (Digitize, Automate, Enable, Expand, Increase, Implement, Reduce, Integrate).  
   - Link each objective to practical outcomes (efficiency, engagement, automation, expansion).  
   - When possible, tie objectives to project phases (phase 1 = self-service, phase 2 = commerce).  
   - Avoid generic phrases like “improve processes.”

3. ⚠️ **Identified risks and gaps** (in bullets)

4. 📦 **Proposed or discussed use cases** (in bullets)

5. 🔗 **Mentioned or required integrations** (in bullets)  
   - Describe all systems, data, methods, security requirements.  
   - 🚫 **Do not summarize.**

6. ❓ **Open questions or pending issues raised in the call** (in bullets)

7. 🔒 **Technical or commercial constraints mentioned** (in bullets)

8. 🧩 **Agreed assumptions between the parties** (in bullets)

9. 🔄 **Suggested or mentioned next steps** (in bullets)

10. 📝 **General observations or additional insights**

11. 📊 **Operational data and commercial rules identified**  
    - Consolidate catalog, SKUs, clusters, price tables, commercial conditions, promotion rules, payment methods, DC cut-off rules, inventory controls, volumes, ticket.  
    - Describe checkout rules: payment limitations, purchase prerequisites, credit policies, billing or advance payment requirements.  
    - ✅ **This must be an “operational panel”** (bullets or table).  
    - 🔥 Transcribe exactly as in the sources; if missing, “Information not provided in the sources.”"""

            # Chamada à OpenAI
            import os
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            r = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role":"user","content":bloco}],
                temperature=0.3,
                max_tokens=3000,
            )
            resultado = r.choices[0].message.content

            st.success(t["success"])
            st.markdown(resultado)
            st.download_button(t["download"], resultado, file_name="insights_yalo.txt")


# Rodapé
st.markdown("---")
st.markdown("🛠️ Desenvolvido por Solutions Team | Yalo · Powered by OpenAI · MVP interno")

import unicodedata

# Função para normalizar o idioma (remove acentos, caixa e espaços)
def normalizar_idioma(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto

# Dicionário com chaves sem acento
idiomas_suportados = {
    "portugues": "portuguese",
    "espanol": "spanish",
    "english": "english"
}

@app.post("/extract-insights")
async def extract_insights_api(
    nome_cliente: str = Form(...),
    idioma: str = Form(...),
    observacoes: str = Form(""),
    texto_transcricao: str = Form(""),
    arquivo_discovery: UploadFile = None,
    arquivo_transcricao: UploadFile = None,
    x_api_key: str = Header(None)
):
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    idioma_normalizado = idiomas_suportados.get(normalizar_idioma(idioma))
    if not idioma_normalizado:
        raise HTTPException(status_code=400, detail="Idioma inválido. Use: portugues, espanol ou english.")

    idioma = idioma_normalizado

    discovery_texto = ""
    if arquivo_discovery:
        discovery_texto = extrair_discovery_texto(await arquivo_discovery.read())

    if not discovery_texto and not texto_transcricao and not arquivo_transcricao:
        raise HTTPException(status_code=400, detail="É necessário fornecer discovery e/ou transcrição.")

    if arquivo_transcricao:
        texto_transcricao = (await arquivo_transcricao.read()).decode()

    insights = gerar_insights(discovery_texto, texto_transcricao, observacoes, nome_cliente, idioma)
    return {"insights": insights}

def gerar_insights(discovery, transcricao, observacoes, cliente, idioma):
    if idioma == "portuguese":
        prompt = f'''🛑 IMPORTANTE: Responda apenas em **português**. Não use outros idiomas.

Projeto com o cliente: **{cliente}**

Abaixo estão os conteúdos de três fontes:

📂 Insights do discovery técnico:
"""{discovery}"""

💬 Insights da transcrição da call:
"""{transcricao}"""

📌 Observações diretas do Solutions Consultant:
"""{observacoes}"""

Agora, una essas informações em um único relatório estruturado, evitando duplicações e organizando os tópicos com o máximo de clareza e objetividade.

1. 📌 **Contexto do projeto**
   - Descreva de forma completa e detalhada o modelo de operação atual da empresa.
   - Inclua: modelo de negócios, CDs, vendedores, ticket médio, volume médio de pedidos, canais de venda, formas de pagamento, clusters, tabelas, promoções, estoque, regras de corte, sistemas envolvidos etc.
   - 🚫 Não resuma; mantenha os detalhes. 📌 Inclua dados quantitativos.

2. 🌟 **Objetivos principais do projeto**
   - Use bullets com verbos de ação fortes.

3. ⚠️ **Riscos e gaps identificados**

4. 📦 **Casos de uso propostos ou discutidos**

5. 🔗 **Integrações mencionadas ou necessárias**

6. ❓ **Dúvidas ou pontos pendentes levantados na call**

7. 🔒 **Restrições técnicas ou comerciais citadas**

8. 🧩 **Premissas acordadas entre as partes**

9. 🔄 **Próximos passos mencionados ou sugeridos**

10. 📝 **Observações gerais ou insights adicionais relevantes**

11. 📊 **Dados operacionais e regras comerciais identificadas**
    - Consolide catálogo, SKUs, clusters, preços, condições comerciais, promoções, formas de pagamento, regras de corte, estoque, volumes, ticket médio.
    - ✅ Painel operacional (bullets ou tabela). 🔥 Transcreva fielmente ou escreva: “Informação não fornecida nas fontes.”'''
    elif idioma == "spanish":
        prompt = f'''🛑 IMPORTANTE: Responde solo en **español**. No utilices otros idiomas.

Proyecto con el cliente: **{cliente}**

📂 Insights del discovery técnico:
"""{discovery}"""

💬 Insights de la transcripción:
"""{transcricao}"""

📌 Observaciones del consultor:
"""{observacoes}"""

Ahora, une esta información en un informe con los siguientes bloques:

1. 📌 **Contexto del proyecto**  
2. 🌟 **Objetivos principales del proyecto**  
3. ⚠️ **Riesgos y brechas identificadas**  
4. 📦 **Casos de uso propuestos o discutidos**  
5. 🔗 **Integraciones mencionadas o necesarias**  
6. ❓ **Dudas o puntos pendientes planteados en la llamada**  
7. 🔒 **Restricciones técnicas o comerciales**  
8. 🧩 **Supuestos acordados entre las partes**  
9. 🔄 **Próximos pasos mencionados o sugeridos**  
10. 📝 **Observaciones generales o insights adicionales**  
11. 📊 **Datos operativos y reglas comerciales identificadas**  
    - Consolida catálogo, SKUs, clusters, precios, promociones, pagos, corte, inventario, volúmenes y ticket. 🔥 Transcribe fielmente.'''
    else:
        prompt = f'''🛑 IMPORTANT: Respond only in **English**. Do not use any other language.

Project with client: **{cliente}**

📂 Discovery insights:
"""{discovery}"""

💬 Call transcript:
"""{transcricao}"""

📌 Consultant notes:
"""{observacoes}"""

Please generate a structured report with these sections:

1. 📌 **Project context**
2. 🌟 **Main objectives of the project**
3. ⚠️ **Identified risks and gaps**
4. 📦 **Proposed or discussed use cases**
5. 🔗 **Mentioned or required integrations**
6. ❓ **Open questions or pending issues raised**
7. 🔒 **Technical or commercial constraints**
8. 🧩 **Agreed assumptions between the parties**
9. 🔄 **Suggested or mentioned next steps**
10. 📝 **General observations or additional insights**
11. 📊 **Operational data and commercial rules identified**
    - Consolidate catalog, SKUs, clusters, price tables, conditions, promotion rules, payment methods, cutoff rules, inventory, volumes, ticket.
    - ✅ Operational panel (bullets or table). 🔥 If missing: “Information not provided in the sources.”'''

    from openai import OpenAI
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    r = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3000,
    )
    return r.choices[0].message.content
