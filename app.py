import streamlit as st
import random
import re
import pandas as pd
from supabase import create_client

# --------------------------------
# CONFIGURACIÓN
# --------------------------------
st.set_page_config(
    page_title="Sorteo Instagram",
    page_icon="🎉",
    layout="centered"
)

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
st.title("🎉 Registro y Sorteo de Instagram")

# --------------------------------
# FORMULARIO DE REGISTRO
# --------------------------------
st.subheader("📝 Registro")

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
                # Insertar en Supabase
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

    # Gráfico por provincia
    st.subheader("📍 Participantes por provincia")
    st.bar_chart(df["provincia"].value_counts())

    # Exportar Excel
    st.download_button(
        "📥 Descargar Excel",
        data=df.to_excel(index=False),
        file_name="participantes_sorteo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Aún no hay participantes")
    
# --------------------------------
# MOSTRAR GANADOR
# --------------------------------
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
st.subheader("🎁 Sorteo")

clave_sorteo = st.text_input(
    "Contraseña para realizar el sorteo",
    type="password",
    key="clave_sorteo"
)

if clave_sorteo == ADMIN_PASSWORD:
    if st.button("🎲 Realizar sorteo"):
        if len(participantes) < 2:
            st.warning("Se necesitan al menos 2 participantes")
        else:
            # 1️⃣ Elegir ganador
            ganador = random.choice(participantes)
            st.session_state.sorteo_realizado = True

            # 2️⃣ Guardar ganador en Supabase
            supabase.table("ganadores").insert({
                "participante_id": ganador["id"],
                "instagram": ganador["instagram"]
            }).execute()

            # 3️⃣ Mostrar ganador
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
# ADMIN
# --------------------------------
with st.expander("⚠️ Administración"):
    clave = st.text_input("Contraseña admin", type="password")

    if clave == ADMIN_PASSWORD:
        if st.button("🗑️ Eliminar todos los registros"):
            supabase.table("participantes").delete().neq("id", 0).execute()
            st.session_state.sorteo_realizado = False
            st.success("Base de datos reiniciada")
    elif clave:
        st.error("❌ Contraseña incorrecta")
