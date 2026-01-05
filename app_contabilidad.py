import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Generador Siigo - Cartera", 
    layout="wide", 
    page_icon="🏢"
)

# ==========================================
# 2. BARRA LATERAL (LOGO Y CONFIGURACIÓN)
# ==========================================
with st.sidebar:
    # --- ZONA DEL LOGO ---
    # Si tienes el archivo logo.png, lo muestra. Si no, muestra texto.
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.header("🏢 UNICENTRO")
        st.caption("Cartera y Contabilidad")

    st.divider() 
    
    # --- CONFIGURACIÓN ---
    st.header("⚙️ Configuración")
    
    st.subheader("Numeración")
    CONSECUTIVO_INICIAL = st.number_input(
        "Consecutivo Inicial (Recibo):", 
        min_value=1, 
        value=19489, 
        step=1,
        help="Número con el que iniciará el primer recibo de caja generado."
    )

    st.subheader("Datos Siigo")
    CONST_TIPO = st.text_input("Tipo Comprobante", value="R")
    CONST_CODIGO = st.text_input("Código Comprobante", value="1")
    
    col_cc1, col_cc2 = st.columns(2)
    with col_cc1:
        CONST_CENTRO = st.text_input("C. Costo", value="1")
    with col_cc2:
        CONST_SUBCENTRO = st.text_input("Subcentro", value="2")

    st.info("ℹ️ Recuerda verificar que el mes contable esté abierto en SIIGO.")

# ==========================================
# 3. CABECERA PRINCIPAL
# ==========================================
st.title("📊 Generador de Plano Contable")
st.markdown("""
**Herramienta de Conciliación Automática - Cartera vs Bancos** Este sistema procesa el *Listado de Intereses* y los *Extractos Bancarios* para generar la importación masiva a **SIIGO**.
""")
st.divider()

# Cuentas Contables Internas
CUENTAS_BANCOS = {
    "9682": "111005682",
    "9526": "111005526",
    "0538": "111005538"
}
CUENTA_PENDIENTE = "130505999"

# ==========================================
# 4. FUNCIONES DE LÓGICA
# ==========================================

def safe_float_conversion(series):
    if pd.api.types.is_numeric_dtype(series): return series
    return series.astype(str).str.replace("$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)

def limpiar_listado_intereses(df_raw):
    # Buscar encabezado dinámicamente
    header_row = None
    tmp = df_raw.head(50)
    for i in range(len(tmp)):
        fila = tmp.iloc[i].astype(str).str.strip().str.lower().tolist()
        if ("fecha" in fila) and ("nit" in fila) and ("cuenta" in fila):
            header_row = i
            break
            
    if header_row is None:
        st.error("❌ No se encontró la fila de encabezados en INTERESES (debe tener Fecha, Nit, Cuenta).")
        return None

    new_header = df_raw.iloc[header_row]
    df = df_raw[header_row + 1:].copy()
    df.columns = new_header
    
    rename_map = {}
    for c in df.columns:
        c_norm = str(c).strip().lower()
        if c_norm.startswith("fecha"): rename_map[c] = "fecha"
        elif c_norm == "nit": rename_map[c] = "nit"
        elif "cuenta" in c_norm: rename_map[c] = "cuenta"
        elif "descrip" in c_norm: rename_map[c] = "descripcion"
        elif any(x in c_norm for x in ["crédito", "creditos", "credito"]): rename_map[c] = "creditos"
    
    df = df.rename(columns=rename_map)
    df_std = pd.DataFrame()
    df_std["fecha"] = pd.to_datetime(df["fecha"], errors='coerce').dt.normalize()
    df_std["nit"]   = df["nit"]
    df_std["cuenta_interes"] = df["cuenta"]
    df_std["desc_interes"]   = df["descripcion"]
    df_std["valor_interes"]  = safe_float_conversion(df["creditos"])
    
    return df_std.dropna(subset=["fecha", "valor_interes"])

def limpiar_detallado_banco(df_raw, origen):
    rename_map = {}
    for c in df_raw.columns:
        c_norm = str(c).strip().lower()
        if "fecha de sistema" in c_norm: rename_map[c] = "fecha_de_sistema"
        elif "valor total" in c_norm: rename_map[c] = "valor_total"
        elif "motivo" in c_norm: rename_map[c] = "descripcion_motivo"
    
    df = df_raw.rename(columns=rename_map)
    df_std = pd.DataFrame()
    df_std["fecha_banco"] = pd.to_datetime(df["fecha_de_sistema"], dayfirst=True, errors="coerce").dt.normalize()
    df_std["valor_banco"] = safe_float_conversion(df["valor_total"])
    df_std["desc_banco"]  = df["descripcion_motivo"]
    df_std["origen"]      = origen
    return df_std.dropna(subset=["fecha_banco", "valor_banco"])

# ==========================================
# 5. INTERFAZ DE CARGA DE ARCHIVOS
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📂 1. Cargar Intereses")
    file_int = st.file_uploader("Subir Excel de Intereses", type=["xlsx", "xls"])

with col2:
    st.subheader("🏦 2. Cargar Bancos")
    files_bancos = st.file_uploader("Subir Bancos (9682, 9526, 0538)", type=["xlsx", "xls"], accept_multiple_files=True)

# ==========================================
# 6. BOTÓN Y PROCESAMIENTO
# ==========================================
if st.button("🚀 Procesar y Generar Archivos", type="primary", use_container_width=True):
    if not file_int or not files_bancos:
        st.warning("⚠️ Por favor sube el archivo de Intereses y al menos un Banco.")
        st.stop()

    with st.spinner('⏳ Analizando datos, cruzando información y generando planos...'):
        try:
            # 1. Procesar Intereses
            df_int_raw = pd.read_excel(file_int, header=None)
            df_int = limpiar_listado_intereses(df_int_raw)
            if df_int is None: st.stop()

            # 2. Procesar Bancos
            lista_dfs_bancos = []
            for uploaded_file in files_bancos:
                nombre = uploaded_file.name
                origen = "DESC"
                if "9682" in nombre: origen = "9682"
                elif "9526" in nombre: origen = "9526"
                elif "0538" in nombre: origen = "0538"
                
                df_banco_raw = pd.read_excel(uploaded_file)
                df_clean = limpiar_detallado_banco(df_banco_raw, origen)
                lista_dfs_bancos.append(df_clean)
            
            df_bancos = pd.concat(lista_dfs_bancos, ignore_index=True)

            # 3. Cruce
            df_int['id_ocurrencia'] = df_int.groupby(['fecha', 'valor_interes']).cumcount()
            df_bancos['id_ocurrencia'] = df_bancos.groupby(['fecha_banco', 'valor_banco']).cumcount()

            df_cruce = pd.merge(
                df_int, df_bancos,
                left_on=["fecha", "valor_interes", "id_ocurrencia"],
                right_on=["fecha_banco", "valor_banco", "id_ocurrencia"],
                how="left", suffixes=("", "_bco")
            )
            
            # 4. Métricas
            total_int = df_cruce['valor_interes'].sum()
            cruzados = df_cruce[df_cruce["origen"].notna()]
            no_cruzados = df_cruce[df_cruce["origen"].isna()]
            
            total_cruzado = cruzados['valor_interes'].sum()
            total_pendiente = no_cruzados['valor_interes'].sum()

            st.divider()
            
            # Tarjetas
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Intereses Cargados", f"${total_int:,.0f}")
            m2.metric("Total Cruzado (Conciliado)", f"${total_cruzado:,.0f}", delta="Ok")
            m3.metric("Total Pendiente (Sin Banco)", f"${total_pendiente:,.0f}", delta_color="inverse")

            # Pestañas
            tab1, tab2 = st.tabs(["📋 Vista Previa del Plano", "⚠️ Reporte de Pendientes"])

            # 5. Generar Plano SIIGO
            TEMPLATE_COLUMNS = [
                "TIPO DE COMPROBANTE (OBLIGATORIO)", "CÓDIGO COMPROBANTE  (OBLIGATORIO)", "NÚMERO DE DOCUMENTO", 
                "CUENTA CONTABLE   (OBLIGATORIO)", "DÉBITO O CRÉDITO (OBLIGATORIO)", "VALOR DE LA SECUENCIA   (OBLIGATORIO)", 
                "AÑO DEL DOCUMENTO", "MES DEL DOCUMENTO", "DÍA DEL DOCUMENTO", 
                "CÓDIGO DEL VENDEDOR", "CÓDIGO DE LA CIUDAD", "CÓDIGO DE LA ZONA", "SECUENCIA", 
                "CENTRO DE COSTO", "SUBCENTRO DE COSTO", "NIT", "SUCURSAL", "DESCRIPCIÓN DE LA SECUENCIA", 
                "NÚMERO DE CHEQUE", "COMPROBANTE ANULADO", "CÓDIGO DEL MOTIVO DE DEVOLUCIÓN", "FORMA DE PAGO",
                "VALOR DEL CARGO 1 DE LA SECUENCIA", "VALOR DEL CARGO 2 DE LA SECUENCIA", "VALOR DEL DESCUENTO 1 DE LA SECUENCIA",
                "FACTURA ELECTRÓNICA A DEBITAR/ACREDITAR", "NÚMERO DE FACTURA ELECTRÓNICA A DEBITAR/ACREDITAR",
                "INGRESOS PARA TERCEROS", "BASE DE RETENCIÓN", "BASE PARA CUENTAS MARCADAS COMO RETEIVA",
                "SECUENCIA GRAVADA O EXCENTA", "VALOR TOTAL IMPOCONSUMO DE LA SECUENCIA", "CANTIDAD"
            ]
            
            filas_plano = []
            consecutivo_actual = CONSECUTIVO_INICIAL
            
            for _, row in df_cruce.iterrows():
                fecha_dt = row["fecha"]
                anio, mes, dia = fecha_dt.year, fecha_dt.month, fecha_dt.day
                nit = str(row["nit"]).replace(".0", "").strip() if pd.notna(row["nit"]) else ""
                cta_int = str(row["cuenta_interes"]).replace(".0", "").strip() if pd.notna(row["cuenta_interes"]) else ""
                valor = float(row["valor_interes"])
                desc_base = str(row["desc_interes"]).strip()[:50]
                origen = row["origen"] if pd.notna(row["origen"]) else ""

                if origen in CUENTAS_BANCOS:
                    cta_banco = CUENTAS_BANCOS[origen]
                    desc_banco = f"PAGO INT - {desc_base}"
                else:
                    cta_banco = CUENTA_PENDIENTE
                    desc_banco = f"PENDIENTE - {desc_base}"
                
                # Fila 1: Crédito
                fila_c = {col: "" for col in TEMPLATE_COLUMNS} 
                fila_c.update({
                    "TIPO DE COMPROBANTE (OBLIGATORIO)": CONST_TIPO, "CÓDIGO COMPROBANTE  (OBLIGATORIO)": CONST_CODIGO,
                    "NÚMERO DE DOCUMENTO": str(consecutivo_actual), "CUENTA CONTABLE   (OBLIGATORIO)": cta_int,
                    "DÉBITO O CRÉDITO (OBLIGATORIO)": "C", "VALOR DE LA SECUENCIA   (OBLIGATORIO)": valor,
                    "AÑO DEL DOCUMENTO": anio, "MES DEL DOCUMENTO": mes, "DÍA DEL DOCUMENTO": dia,
                    "SECUENCIA": 1, "CENTRO DE COSTO": CONST_CENTRO, "SUBCENTRO DE COSTO": CONST_SUBCENTRO,
                    "NIT": nit, "SUCURSAL": 0, "DESCRIPCIÓN DE LA SECUENCIA": desc_base,
                    "COMPROBANTE ANULADO": "N", "FORMA DE PAGO": 0, "CÓDIGO DEL VENDEDOR": 0, "CÓDIGO DE LA CIUDAD": 0, "CÓDIGO DE LA ZONA": 0,
                    "VALOR DEL CARGO 1 DE LA SECUENCIA": 0, "VALOR DEL CARGO 2 DE LA SECUENCIA": 0, "VALOR DEL DESCUENTO 1 DE LA SECUENCIA": 0, "BASE DE RETENCIÓN": 0, "CANTIDAD": 0
                })
                filas_plano.append(fila_c)

                # Fila 2: Débito
                fila_d = {col: "" for col in TEMPLATE_COLUMNS}
                fila_d.update({
                    "TIPO DE COMPROBANTE (OBLIGATORIO)": CONST_TIPO, "CÓDIGO COMPROBANTE  (OBLIGATORIO)": CONST_CODIGO,
                    "NÚMERO DE DOCUMENTO": str(consecutivo_actual), "CUENTA CONTABLE   (OBLIGATORIO)": cta_banco,
                    "DÉBITO O CRÉDITO (OBLIGATORIO)": "D", "VALOR DE LA SECUENCIA   (OBLIGATORIO)": valor,
                    "AÑO DEL DOCUMENTO": anio, "MES DEL DOCUMENTO": mes, "DÍA DEL DOCUMENTO": dia,
                    "SECUENCIA": 2, "CENTRO DE COSTO": CONST_CENTRO, "SUBCENTRO DE COSTO": CONST_SUBCENTRO,
                    "NIT": nit, "SUCURSAL": 0, "DESCRIPCIÓN DE LA SECUENCIA": desc_banco,
                    "COMPROBANTE ANULADO": "N", "FORMA DE PAGO": 0, "CÓDIGO DEL VENDEDOR": 0, "CÓDIGO DE LA CIUDAD": 0, "CÓDIGO DE LA ZONA": 0,
                    "VALOR DEL CARGO 1 DE LA SECUENCIA": 0, "VALOR DEL CARGO 2 DE LA SECUENCIA": 0, "VALOR DEL DESCUENTO 1 DE LA SECUENCIA": 0, "BASE DE RETENCIÓN": 0, "CANTIDAD": 0
                })
                filas_plano.append(fila_d)
                consecutivo_actual += 1

            df_plano = pd.DataFrame(filas_plano)[TEMPLATE_COLUMNS]

            # Mostrar Dataframe en Tab 1
            with tab1:
                st.dataframe(df_plano.head(20), use_container_width=True)
                st.caption(f"Mostrando primeros 20 registros de {len(df_plano)} totales.")

            # Mostrar Pendientes en Tab 2
            with tab2:
                if not no_cruzados.empty:
                    st.error(f"Se encontraron {len(no_cruzados)} registros que NO cruzaron con bancos.")
                    st.dataframe(no_cruzados[['fecha', 'nit', 'cuenta_interes', 'desc_interes', 'valor_interes']], use_container_width=True)
                else:
                    st.success("¡Perfecto! Todos los registros cruzaron correctamente.")

            # 6. Descargas
            st.subheader("📥 Descargar Archivos")
            
            c_down1, c_down2 = st.columns(2)
            
            buffer_siigo = io.BytesIO()
            with pd.ExcelWriter(buffer_siigo, engine='xlsxwriter') as writer:
                df_plano.to_excel(writer, index=False)
            
            with c_down1:
                st.download_button(
                    label="✅ Descargar Plano SIIGO (Oficial)",
                    data=buffer_siigo.getvalue(),
                    file_name=f"Plano_Siigo_Recibos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )

            if not no_cruzados.empty:
                buffer_errores = io.BytesIO()
                with pd.ExcelWriter(buffer_errores, engine='xlsxwriter') as writer:
                    no_cruzados.to_excel(writer, index=False, sheet_name="No Cruzados")
                
                with c_down2:
                    st.download_button(
                        label="⚠️ Descargar Reporte de Pendientes",
                        data=buffer_errores.getvalue(),
                        file_name=f"Reporte_Pendientes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.ms-excel",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")

# ==========================================
# 7. CRÉDITOS Y COPYRIGHT (PIE DE PÁGINA)
# ==========================================
# Esto se mostrará SIEMPRE al final de la página, sin importar nada.
st.divider()
st.markdown("---")
col_cred1, col_cred2 = st.columns([1, 3])
with col_cred1:
    st.caption(f"© {datetime.now().year} Unicentro")
with col_cred2:
    st.markdown("**Desarrollado por: Edgar Javier Díaz Rincón** | v1.2.0")  # <--- ¡AQUÍ ESTÁ TU CRÉDITO VISIBLE!