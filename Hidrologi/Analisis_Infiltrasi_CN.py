import numpy as np
import pandas as pd
import streamlit as st
from bokeh.plotting import figure, show
from bokeh.models import Legend

# Fungsi untuk menghitung limpasan berdasarkan metode CN
def calculate_limpasan(P, ARF, CN, Im):
    PSA007kum = [0.05, 0.15, 0.75, 0.91, 0.97, 1]
    PSA007 = np.diff(PSA007kum, prepend=0)
    Pjam = PSA007 * P
    Pjam_cum = np.cumsum(Pjam)
    # Tanpa Area Reduction F
    Pjam_ARF = Pjam * ARF  # Hujan Jam Jaman dikali dengan area reduction factor
    Pjam_ARF_cum = np.cumsum(Pjam_ARF)
    absis = np.arange(1, len(Pjam_ARF) + 1)  # Membuat array sumbu x (jumlah jam)

    P = np.array(Pjam_ARF)
    Pkum = np.array(Pjam_ARF_cum)

    def limpCN(CN, P):  # membuat fungsi dengan nilai CN dan Hujan
        '''P dalam mm, limp dalam mm'''
        S = 1000 / CN - 10  # persamaan hubungan storage dengan nilai CN
        k = 0.2  # where K is varied between 0-0.26 (springer et al.), K=0.2 is recommended by SCS
        Pkum = []  # membuat array hujan kumulatif
        Ptot = 0  # mendefinisikan hujan total =0
        for i in range(len(P)):  # membuat nilai i sejumlah hujan jam-jaman yang diberikan
            Ptot += P[i] / 25.4  # Hujan total baru adalah hujan total sebelumnya di tambah hujan pada jam i (diubah dari mm ke inch)
            Pkum.append(Ptot)  # Menyimpan hujan kumulatif ke dalam array Pkum
        reff = []  # membua t array hujan efektif
        infil = []  # membuat array infiltrasi
        Iab = []  # membuat array Inital Abstraction
        reffkumseb = 0  # memberikan nilai hujan efektif sebelumnya
        Faseb = 0  # memberikan nilai infiltrasi sebelumnya
        for i in range(len(Pkum)):  # membuat nilai i sejumlah Hujan kumulatif
            Ia = k * S  # initial abtraction koefisien x dengan storage
            if (Pkum[i] > Ia):  # Cek apakah nilai hujan kumulatif pada jam tersebut lebih besar dari initial abtraction
                Ia = Ia  # jika hujan kumulatif > Ia maka berikan nilai Ia adalah Ia
                Iab.append(Ia)
            else:
                Ia = Pkum[i]  # jika hujan kumulatif < atau = Ia maka berikan nilai Ia adalah hujan kumulatif pada jam tersebut
                Iab.append(Ia)
            Fa = (S * (Pkum[i] - Ia) / (Pkum[i] - Ia + S)) # continuing abstraction (Fa) = storage x (hujan kumulatif - initial abstraction) / (hujan kumulatif - initial abstraction + storage)
            infil.append(Fa - Faseb)  # memasukan nilai infiltrasi yaitu continuing abstraction (Fa) - continuing abstraction sebelumnya (Fa)
            Faseb = Fa  # update nilai continuing abstraction (Fa) sebelumnya
            reffkum = Pkum[i] - Ia - Fa  # hujan efektif kumulatif = Hujan kumulatif - Ia -Fa
            reff.append(reffkum - reffkumseb)  # memasukan nilai hujan efektif = hujan efektif kumulatif - hujan efektif kumulatif sebelumnya
            reffkumseb = reffkum  # update nilai hujan kumulatif
        infil = np.array(infil) * 25.4  # membuat array infiltrasi dan mnejadikan dari inch ke mm
        reff = np.array(reff) * 25.4  # membuat array hujan dan menjadikan dari inch ke mm
        Iab = np.array(Iab) * 25.4 # membuat array intial abstraction dan menjadikan dari inch ke mm
        return (reff, infil, Iab)  # Menyimpan fungsi hujan efektif dan infiltrasi

    reff, infil, Iab = (limpCN(CN, P))  # Memanggil fungsi limpasan CN

    #Hujan Efektif Jam-jaman 
    
    ##########################
    Iab_jam = np.zeros(len(Iab))
    Iab_jam[0]=Iab[0]
    Iab_jam[1:] = np.diff(Iab)
    #Hujan Efektif Jam-jaman 
    
    infiltrasi_jam = (Iab_jam+infil)
    reff_jam = Pjam_ARF - infiltrasi_jam
    infiltrasi_jam = infiltrasi_jam-(infiltrasi_jam*Im/100)
    infiltrasi_kum = np.cumsum(infiltrasi_jam)  
    reff_kum = np.cumsum(reff_jam)

    reffkumtab = {
        'Jam ke-': absis,
        'Hujan Rencana ': Pjam_cum,
        'Hujan Rencana (ARF)': Pkum,
        'Infiltrasi': infiltrasi_kum,
        'Hujan Efektif': reff_kum,
    #    'Iab': Iab,
        #'Nilai CN': CN,s
        #'Nilai Impervious (%)': Im,
    }
    dfreffkum = pd.DataFrame(reffkumtab)  

        # Menyimpan hasil perhitungan dalam DataFrame
    refftab = {
        'Jam ke-': absis,
        'Hujan Rencana ': Pjam,
        'Hujan Rencana (ARF)': Pjam_ARF,
        'Infiltrasi': infiltrasi_jam,
        'Hujan Efektif': reff_jam,
    #    'Iab': Iab_jam,
        #'Nilai CN': CN,
        #'Nilai Impervious (%)': Im,
    }
    dfreff = pd.DataFrame(refftab)
    
    # First plot
    fig = figure(width=600, height=400, title="Grafik Hujan Jam-Jaman Kumulatif dengan P = {} mm/hari (Metode SCS-CN)".format(np.round(np.sum(P) / ARF, 3)))

    # Plotting bars on the first plot
    #fig.vbar(x=absis - 0.25, top=Pkum, width=0.2, color="powderblue", legend_label="Hujan Rencana (ARF) [mm]")
    fig.vbar(x=absis + 0.25, top=reff_kum, width=0.2, color="orange", legend_label="Hujan efektif [mm]")  # Slightly shift bars to the right
    fig.vbar(x=absis, top=infiltrasi_kum, width=0.2, color="greenyellow", legend_label="Infiltrasi [mm]")  # Slightly shift bars to the right

    # Adding text annotations
    #for i in range(len(reff_kum)):
    #    fig.text(x=absis[i] - 0.25, y=Pkum[i], text=[str(round(Pkum[i], 1))], text_align='center', text_baseline='bottom',text_font_size="8pt")
    #    fig.text(x=absis[i] + 0.25, y=reff_kum[i], text=[str(round(reff_kum[i], 1))], text_align='center', text_baseline='bottom',text_font_size="8pt")
    #    fig.text(x=absis[i], y=infiltrasi_kum[i], text=[str(round(infiltrasi_kum[i], 1))], text_align='center', text_baseline='bottom',text_font_size="8pt")

    # Set axis labels and title
    fig.xaxis.axis_label = 'Jam Ke-'
    fig.yaxis.axis_label = 'Curah Hujan (mm)'

    # Second plot
    fig2 = figure(width=600, height=400, title="Grafik Hujan Jam-Jaman dengan P = {} mm/hari (Metode SCS-CN)".format(np.round(np.sum(P) / ARF, 3)))
    #fig2.vbar(x=absis - 0.25, top=Pjam_ARF, width=0.2, color="powderblue", legend_label="Hujan Rencana (ARF) [mm]")
    fig2.vbar(x=absis + 0.25, top=reff, width=0.2, color="orange", legend_label="Hujan efektif [mm]")  # Slightly shift bars to the right
    fig2.vbar(x=absis, top=infiltrasi_jam, width=0.2, color="greenyellow", legend_label="Infiltrasi [mm]")  # Slightly shift bars to the right

    # Adding text annotations
    #for i in range(len(reff_kum)):
    #    fig2.text(x=absis[i] - 0.25, y=P[i], text=[str(round(Pkum[i], 1))], text_align='center', text_baseline='bottom',text_font_size="8pt")
    #    fig2.text(x=absis[i] + 0.25, y=reff[i], text=[str(round(reff[i], 1))], text_align='center', text_baseline='bottom',text_font_size="8pt")
    #    fig2.text(x=absis[i], y=infiltrasi_jam[i], text=[str(round(infiltrasi_jam[i], 1))], text_align='center', text_baseline='bottom',text_font_size="8pt")

    # Set axis labels and title
    fig2.xaxis.axis_label = 'Jam ke-'
    fig2.yaxis.axis_label = 'Curah Hujan (mm)'

    # Adding legends
    fig.legend.location = "top_left"
    fig.legend.click_policy = "hide"
    fig2.legend.location = "top_left"
    fig2.legend.click_policy = "hide"   
  
    # Tampilkan tabel dan graph reffkumtab
    st.subheader("Tabel Hujan Efektif Kumulatif (Metode SCS-CN)")
    st.write(dfreffkum)
    st.bokeh_chart(fig)
    # Tampilkan tabel dan graph reff
    st.subheader("Tabel Hujan Efektif Jam-jaman (Metode SCS-CN)")
    st.write(dfreff)
    st.bokeh_chart(fig2)


# Streamlit UI
def main():
    st.header('Calculator Hujan Efektif dengan Metode Infiltrasi SCS-CN', divider='blue')
    st.caption('created by :blue[HAZ] :sunglasses:')
    #st.title("created by HAZ")

    # Masukkan data pengguna
    P = st.number_input("Masukkan Hujan Rencana (mm):", value=132.9)
    ARF = st.number_input("Masukkan Area Reduction Factor (ARF):", value=0.97)
    CN = st.number_input("Masukkan nilai CN:", value=77.11)
    Im = st.number_input("Masukkan nilai Impervious dalam %:", value=5.0419)
 
    # Hitung dan tampilkan hasil
    if st.button("Hitung"):
        calculate_limpasan(P, ARF, CN, Im)  

if __name__ == "__main__":
    main()
