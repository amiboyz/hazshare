import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

#Display Title and Description
#st.title("Contoh entry form")
st.markdown("Masukan informasi pengguna di bawah ini untuk menjalankan kalkulasi")

#Establishing a google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

#Fetch existing vendor data
existing_data = conn.read(worksheet="Data", usecols=list(range(4)), ttl=5)
existing_data = existing_data.dropna(how="all")

# st.dataframe(existing_data)
# List of profession
JENIS_PROFESI = [
    "Akademisi",
    "Government",
    "Profesional",
    "Mahasiswa",
    "Lainnya",
]

# Membuat Form baru
with st.form(key="User_Form"):
    nama_user = st.text_input(label="Nama User*")
    jenis_profesi = st.selectbox("Profesi*", options=JENIS_PROFESI, index=None)
    tanggal_akses = datetime.now()
    jam_akses = datetime.now().time()

    # Mark Mandatory field
    st.markdown("**required*")

    submit_button = st.form_submit_button(label="Kalkulasi Infiltrasi dan HSS")

    # if the submit button is press
    if submit_button:
        # Cek if all mandatory field are filled
        if not nama_user or not jenis_profesi:
            st.warning("Pastikan Nama dan Profesi anda terisi")
            st.stop()
        else:
            # Create a new row of user
            user_data = pd.DataFrame(
                [
                        {
                            "Nama_User": nama_user,
                            "Profesi": jenis_profesi,
                            "Tanggal_Akses": tanggal_akses,
                            "Jam_Akses": jam_akses
                        }
                ]
            )

            # Add the new user name to the existing data
            update_df = pd.concat([existing_data, user_data], ignore_index=True)

            # Update Google Sheets with the user data
            conn.update(worksheet="Data", data=update_df)
            st.success("Pengisian Berhasil")