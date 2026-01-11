import streamlit as st
import random
import re
import pandas as pd
import io
from supabase import create_client

# --------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------
st.set_page_config(
    page_title="Sorteo Instagram",
    page_icon="🎉",
    layout="centered"
)

# --------------------------------
# FONDO + TEMA PROFESIONAL
# --------------------------------
def set_background():
    st.markdown(
        """
        <style>
        /* Fondo general */
        .stApp {
            background: linear-gradient(135deg, #0f172a, #020617);
        }

        /* Contenedor principal */
        .block-container {
            background-color: #ffffff;
            padding: 3rem 3.5rem;
            border-radius: 22px;
            max-width: 720px;
            margin-top: 3rem;
            box-shadow: 0 25px 60px rgba(0,0,0,0.35);
        }

        /* Títulos */
        h1 {
            text-align: center;
            font-weight: 800;
            color: #0f172a;
        }

        h2, h3 {
            color: #1e293b;
        }

        /* Inputs */
        input, textarea, select {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            border-radius: 10px !important;
            border: 1px solid #cbd5e1 !important;
        }

        /* Labels */
        label {
            font-weight: 600;
            color: #334155;
        }

        /* Botones */
        .stButton > button {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            font-weight: 700;
            border-radius: 12px;
            padding: 0.7rem 1.4rem;
            border: none;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #1e40af, #1e3a8a);
        }

        /* Mensajes */
        .stAlert {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

set_background()

# --------------------------------
# CREDENCIALES
# --------------------------------
ADMIN_PASSWORD = st.secrets["admin"]["password"]

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if "sorteo_realizado" not in st.session_state:
    st.session_state.sorteo_realizado = False

# --------------------------------
# VALIDACIONES
# --------------------------------
def telefono_argentina_valido(telefono):
    return re.fullmatch(r"^549\d{10}$", telefono)

# --------------------------------
# TÍTULO
# --------------------------------
st.title("🎉 Sorteo Oficial de Instagram")
st.caption("Registro de participantes y sorteo transparente")

# --------------------------------
# FORMULARIO DE REGISTRO
# --------------------------------
st.subheader("📝 Registro de Participantes")

if st.session_state.sorteo_realizado:
    st.warning("⛔ El sorteo ya fue realizado. Registro cerrado.")
else:
    with st.form("registro"):
        nombres = st.text_input("Nombres *")
        apellidos = st.text_input("Apellidos *")
        telefono = st.text_input("Teléfono (549XXXXXXXXX) *")
        instagram = st.text_input("Instagram (sin @) *")
        provincia = st.selectbox(
            "Provincia *",
            [
                "Buenos Aires", "CABA", "Córdoba", "Santa Fe", "Mendoza",
                "Tucumán", "Salta", "Jujuy", "Chaco", "Corrientes", "Misiones",
                "Entre Ríos", "San Juan", "San Luis", "La Rioja", "Catamarca",
                "Santiago del Estero", "Formosa", "Neuquén", "Río Negro",
                "Chubut", "Santa Cruz", "Tierra del Fuego"
            ]
        )

        enviar = st.form_submit_button("Registrar")

        if enviar:
            if not all([nombres, apellidos, telefono, instagram, provincia]):
                st.error("⚠️ Todos los campos son obligatorios")
            elif not telefono_argentina_valido(telefono):
                st.error("❌ Teléfono inválido. Ejemplo: 5491123456789")
            else:
                try:
                    supabase.table("participantes").insert({
                        "nombres": nombres,
                        "apellidos": apellidos,
                        "telefono": telefono,
                        "instagram": instagram.lower(),
                        "provincia": provincia
                    }).execute()

                    mensaje = f"Hola {nombres}! Tu participación en el sorteo fue registrada correctamente 🎉"
                    wa_link = f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}"

                    st.success("✅ Registro exitoso")
                    st.markdown(f"📲 [Enviar confirmación por WhatsApp]({wa_link})")

                except Exception as e:
                    if "telefono" in str(e):
                        st.error("❌ Teléfono ya registrado")
                    elif "instagram" in str(e):
                        st.error("❌ Instagram ya registrado")
                    else:
                        st.error("❌ Error al registrar participante")

# --------------------------------
# PARTICIPANTES
# --------------------------------
st.subheader("📊 Participantes")

resp = supabase.table("participantes").select("*").execute()
participantes = resp.data

st.metric("Total registrados", len(participantes))

if participantes:
    df = pd.DataFrame(participantes)
    st.dataframe(df, use_container_width=True)

    st.subheader("📍 Participantes por provincia")
    st.bar_chart(df["provincia"].value_counts())

    # Exportar Excel (CORRECTO)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Participantes")

    st.download_button(
        "📥 Descargar Excel",
        data=output.getvalue(),
        file_name="participantes_sorteo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Aún no hay participantes")

# --------------------------------
# GANADOR GUARDADO
# --------------------------------
resp_ganador = supabase.table("ganadores").select("*").limit(1).execute()
ganador_guardado = resp_ganador.data[0] if resp_ganador.data else None

if ganador_guardado:
    st.subheader("🏆 Ganador del Sorteo")

    participante = (
        supabase
        .table("participantes")
        .select("*")
        .eq("id", ganador_guardado["participante_id"])
        .single()
        .execute()
        .data
    )

    st.success(
        f"""
👤 {participante['nombres']} {participante['apellidos']}  
📱 {participante['telefono']}  
📸 @{participante['instagram']}  
📍 {participante['provincia']}
"""
    )

    st.info("🔒 El sorteo ya fue realizado y no puede repetirse.")

# --------------------------------
# SORTEO
# --------------------------------
st.subheader("🎁 Realizar Sorteo")

clave_sorteo = st.text_input(
    "Contraseña para realizar el sorteo",
    type="password"
)

if clave_sorteo == ADMIN_PASSWORD and not ganador_guardado:
    if st.button("🎲 Ejecutar sorteo"):
        if len(participantes) < 2:
            st.warning("Se necesitan al menos 2 participantes")
        else:
            # Protección doble
            check = supabase.table("ganadores").select("id").execute()
            if check.data:
                st.warning("El sorteo ya fue realizado.")
                st.stop()

            ganador = random.choice(participantes)
            st.session_state.sorteo_realizado = True

            supabase.table("ganadores").insert({
                "participante_id": ganador["id"],
                "instagram": ganador["instagram"]
            }).execute()

            st.success(
                f"""
🏆 **GANADOR/A**

👤 {ganador['nombres']} {ganador['apellidos']}  
📱 {ganador['telefono']}  
📸 @{ganador['instagram']}  
📍 {ganador['provincia']}
"""
            )

elif clave_sorteo:
    st.error("❌ Contraseña incorrecta")

# --------------------------------
# ADMINISTRACIÓN
# --------------------------------
with st.expander("⚠️ Administración"):
    clave = st.text_input("Contraseña admin", type="password")

    if clave == ADMIN_PASSWORD:
        if st.button("🗑️ Reiniciar sorteo"):
            supabase.table("ganadores").delete().neq("id", 0).execute()
            supabase.table("participantes").delete().neq("id", 0).execute()
            st.session_state.sorteo_realizado = False
            st.success("✅ Base de datos reiniciada correctamente")
    elif clave:
        st.error("❌ Contraseña incorrecta")
