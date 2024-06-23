import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
from bokeh.plotting import figure
from bokeh.models import Span, Label, HoverTool
#from bokeh.io import output_notebook
from scipy.stats import norm, lognorm, pearson3, gumbel_r, kstest, genextreme


# Initialize Bokeh output in notebook
#output_notebook()

# Title
st.title("Rainfall Analysis and Design Storm Calculator")

# Input for Rainfall Data (R)
R_input = st.text_area("Enter rainfall data (mm/day), separated by commas", 
                       "17.7, 25.0, 34.2, 36.0, 37.0, 42.5, 43.6, 46.9, 53.0, 53.0, 54.0, 55.0, 57.0, 62.7, 68.6, 69.0, 72.0, 74.0, 78.0, 81.1, 115.0")

# Input for Years (T)
T_input = st.text_area("Enter years, separated by commas", 
                       "2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020")

if st.button('Calculate'):
    R = np.array([float(x) for x in R_input.split(',')])
    R_awal = R
    tahun_array = np.array([int(x) for x in T_input.split(',')])

    R = np.sort(R, kind='quicksort')[::-1]  # Sort rainfall data from highest to lowest
    n = len(R)  # Number of data points
    T = []  # Create empty array for return periods
    for i in range(len(R)): 
        P = (i + 1) / (n + 1)  # Calculate probability using Weibull plotting formula
        T.append(1 / P)  # Store the return period (1 / P) in array T

    # Create a DataFrame for rainfall probability according to Weibull
    st.write("Tabel Probabilitas Hujan Menurut Weibul")
    Tprob = {
        'Hujan Desain (mm/hari)': R,
        'Periode Ulang (Tr)': np.round(T, 2),
    }
    R_empirik = R
    dfTprob = pd.DataFrame(Tprob)

    # Display the DataFrame
    st.write(dfTprob)

    # Reverse the order of R and T (from smallest to largest)
    R = R[::-1]
    T = T[::-1]
    T = np.array(T)  # Define T as a numpy array
    tr = [2, 5, 10, 20]  # For return periods of 2, 5, 10, and 20 years

    Rdesain = np.round(np.interp(tr, T, R))
    for i in range(len(tr)):
        st.write(f'Hujan desain untuk kala ulang {tr[i]} = {np.round(Rdesain[i], 2)} mm/hari')

    # Intensity Duration Frequency Curve according to Mononobe
    I = []
    tjam = 24
    for t in range(1, tjam, 1):  # Create range of times from 1 minute to 24 hours
        a = np.round((Rdesain / 24) * (24 / t)**(2 / 3), 2)  # Mononobe formula
        I.append(a)
    I = np.array(I)
    t = np.arange(1, tjam, 1)

    # Create Bokeh plot for IDF curve
    p = figure(title="Intensity Duration Frequency Curve", x_axis_label='Durasi Hujan (jam)', y_axis_label='Intensitas Hujan (mm/jam)', width=800, height=600)

    # Add lines for each return period
    for i in range(len(tr)):
        p.line(t, I[:, i], legend_label=f"Kala ulang {tr[i]} tahun", line_width=2)

    # Add hover tool
    hover = HoverTool()
    hover.tooltips = [("Durasi", "@x jam"), ("Intensitas", "@y mm/jam")]
    p.add_tools(hover)

    # Customize the legend
    p.legend.title = 'Return Period'
    p.legend.label_text_font_size = "10pt"
    p.legend.location = "top_right"

    # Show plot in Streamlit
    st.bokeh_chart(p)

    st.write("-------------------------------------")
    st.write("Tabel Mononobe Berdasarkan Kala Ulang")

    # Create DataFrame for Mononobe table
    mononobe_data = {f"Kala Ulang {tr[i]} tahun": I[:, i] for i in range(len(tr))}
    df_mononobe = pd.DataFrame(mononobe_data, index=t)

    # Display Mononobe table
    st.write(df_mononobe)
    
    def grubbs_test(R):
        n = len(R)
        mean_R = np.mean(R)
        std_R = np.std(R)
        
        # Hitung nilai Grubbs
        G = np.max(np.abs(R - mean_R)) / std_R
        
        # Hitung nilai kritis dari distribusi t-student
        alpha = 0.05  # tingkat signifikansi
        t_critical = stats.t.ppf(1 - alpha / (2 * n), n - 2)
        
        # Hitung nilai kritis Grubbs
        critical_value = ((n - 1) / np.sqrt(n)) * np.sqrt(t_critical**2 / (n - 2 + t_critical**2))
        
        return G, critical_value

    R= R_awal
    # Uji outliner menggunakan Grubbs
    G, critical_value = grubbs_test(R)

    mean_R = np.mean(R)
    std_R = np.std(R)
    upper_outlier_threshold = mean_R + critical_value * std_R
    lower_outlier_threshold = mean_R - critical_value * std_R

    # Create a Bokeh plot for Grubbs' test
    p = figure(title='Grafik Data dengan Deteksi Outliers menggunakan Grubbs Test', x_axis_label='Tahun', y_axis_label='Curah Hujan (mm/hari)', plot_width=800, plot_height=400)
    p.line(tahun_array, R, line_width=2, legend_label='Data')
    p.circle(tahun_array, R, size=8, legend_label='Data')

    # Add upper and lower outlier lines
    upper_outlier_line = Span(location=upper_outlier_threshold, dimension='width', line_color='red', line_dash='dashed', line_width=2)
    lower_outlier_line = Span(location=lower_outlier_threshold, dimension='width', line_color='green', line_dash='dashed', line_width=2)

    p.add_layout(upper_outlier_line)
    p.add_layout(lower_outlier_line)

    # Add labels for the outlier lines
    upper_label = Label(x=tahun_array[-1], y=upper_outlier_threshold, text=f'Upper Outlier: {upper_outlier_threshold:.2f}', text_color='red')
    lower_label = Label(x=tahun_array[-1], y=lower_outlier_threshold, text=f'Lower Outlier: {lower_outlier_threshold:.2f}', text_color='green')

    p.add_layout(upper_label)
    p.add_layout(lower_label)

    p.legend.location = "top_left"

    # Streamlit app title for Grubbs' test
    st.write("Grafik Data dengan Deteksi Outliers menggunakan Grubbs Test")

    # Display the Bokeh plot using Streamlit
    st.bokeh_chart(p)

    st.write("Nilai Grubbs:", np.round(G, 2))
    st.write("Nilai kritis:", np.round(critical_value, 2))
    st.write('Batas atas:', np.round(upper_outlier_threshold, 2))
    st.write('Batas bawah:', np.round(lower_outlier_threshold, 2))

    tr = [2, 5, 10, 20, 25, 50, 100]

    # Create DataFrame to store results
    result = pd.DataFrame(index=tr, columns=['Normal', 'Log-Normal', 'Log Pearson Type III', 'Gumbel', 'Genextreme'])
    result.index.name = 'Kala Ulang'

    # Normal Distribution
    mean_normal, std_normal = np.mean(R), np.std(R)
    result['Normal'] = [norm.ppf(1 - 1/t) * std_normal + mean_normal for t in tr]

    # Log-Normal Distribution
    shape_ln, loc_ln, scale_ln = lognorm.fit(R)
    result['Log-Normal'] = [lognorm.ppf(1 - 1/t, shape_ln, loc=loc_ln, scale=scale_ln) for t in tr]

    # Log Pearson Type III Distribution
    shape_lp, loc_lp, scale_lp = pearson3.fit(R)
    result['Log Pearson Type III'] = [pearson3.ppf(1 - 1/t, shape_lp, loc=loc_lp, scale=scale_lp) for t in tr]

    # Gumbel Distribution
    loc_gumbel, scale_gumbel = gumbel_r.fit(R)
    result['Gumbel'] = [gumbel_r.ppf(1 - 1/t, loc_gumbel, scale_gumbel) for t in tr]
    
    # Generalized Extreme Value Distribution
    params_genex = genextreme.fit(R)
    result['Genextreme'] = [genextreme.ppf(1 - 1/t, *params_genex) for t in tr]

    st.write("Hasil:")
    st.write(result.round(2))

    # Kolmogorov-Smirnov Test
    ks_tests = {
        'Normal': kstest(R, 'norm', args=(mean_normal, std_normal)),
        'Log-Normal': kstest(R, 'lognorm', args=(shape_ln, loc_ln, scale_ln)),
        'Log Pearson Type III': kstest(R, 'pearson3', args=(shape_lp, loc_lp, scale_lp)),
        'Gumbel': kstest(R, 'gumbel_r', args=(loc_gumbel, scale_gumbel)),
        'Genextreme': kstest(R, 'genextreme', args=params_genex)
    }

    ks_results = pd.DataFrame(ks_tests, index=['KS Statistic', 'p-value']).T
    ks_results.index.name = 'Distribusi'
    st.write("Uji Kolmogorov-Smirnov:")
    st.write(ks_results)

    # Plotting with Bokeh
    prb = 1 / np.array(tr)
    p = figure(title="Return Period Analysis", x_axis_label='Probability', y_axis_label='Curah Hujan (mm)', plot_width=800, plot_height=600)

    # Plot lines for each distribution
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    distributions = ['Normal', 'Log-Normal', 'Log Pearson Type III', 'Gumbel', 'Genextreme']
    lines = []

    for i, dist in enumerate(distributions):
        line = p.line(prb, result[dist], line_width=2, color=colors[i], legend_label=dist)
        lines.append(line)

    # Add hover tool
    hover = HoverTool()
    hover.tooltips = [("Probability", "@x"), ("Curah Hujan", "@y mm")]
    p.add_tools(hover)

    # Customize the legend
    p.legend.title = 'Distributions'
    p.legend.label_text_font_size = "10pt"
    p.legend.location = "top_left"

    # Show plot in Streamlit
    st.bokeh_chart(p)

        # Create DataFrame to store results
    result = pd.DataFrame(index=T, columns=['Probability', 'Normal', 'Log-Normal', 'Log Pearson Type III', 'Gumbel', 'Weibull', 'Genextreme'])
    result.index.name = 'Kala Ulang'

    # Normal Distribution
    mean_normal, std_normal = np.mean(R), np.std(R)
    result['Normal'] = [norm.ppf(1 - 1/t) * std_normal + mean_normal for t in T]

    # Log-Normal Distribution
    shape_ln, loc_ln, scale_ln = lognorm.fit(R)
    result['Log-Normal'] = [lognorm.ppf(1 - 1/t, shape_ln, loc=loc_ln, scale=scale_ln) for t in T]

    # Log Pearson Type III Distribution
    shape_lp, loc_lp, scale_lp = pearson3.fit(R)
    result['Log Pearson Type III'] = [pearson3.ppf(1 - 1/t, shape_lp, loc=loc_lp, scale=scale_lp) for t in T]

    # Gumbel Distribution
    loc_gumbel, scale_gumbel = gumbel_r.fit(R)
    result['Gumbel'] = [gumbel_r.ppf(1 - 1/t, loc_gumbel, scale_gumbel) for t in T]

    # Weibull Distribution (Empirical Data)
    R_empirik_sort = np.sort(R)[::1]
    result['Weibull'] = R_empirik_sort[:len(T)]

    # Generalized Extreme Value (GEV) Distribution
    params_gev = genextreme.fit(R)
    result['Genextreme'] = [genextreme.ppf(1 - 1/t, *params_gev) for t in T]

    result['Probability'] = 1 / T

    st.write("Hasil:")
    st.write(result.round(2))

    # Kolmogorov-Smirnov Test
    ks_tests = {
        'Normal': kstest(R, 'norm', args=(mean_normal, std_normal)),
        'Log-Normal': kstest(R, 'lognorm', args=(shape_ln, loc_ln, scale_ln)),
        'Log Pearson Type III': kstest(R, 'pearson3', args=(shape_lp, loc_lp, scale_lp)),
        'Gumbel': kstest(R, 'gumbel_r', args=(loc_gumbel, scale_gumbel)),
        'Genextreme': kstest(R, 'genextreme', args=params_gev)
    }

    ks_results = pd.DataFrame(ks_tests, index=['KS Statistic', 'p-value']).T
    st.write("Uji Kolmogorov-Smirnov:")
    st.write(ks_results)

    # Bokeh Plotting
    p = figure(title="Return Period Analysis", x_axis_label='Probability', y_axis_label='Curah Hujan (mm)', plot_width=800, plot_height=600)

    # Plot lines for each distribution
    colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown']
    distributions = ['Normal', 'Log-Normal', 'Log Pearson Type III', 'Gumbel', 'Weibull', 'Genextreme']
    
    for i, dist in enumerate(distributions):
        if dist == 'Weibull':
            p.circle(result['Probability'], result[dist], size=8, color='red', legend_label=dist)
        else:
            p.line(result['Probability'], result[dist], line_width=2, color=colors[i], legend_label=dist)

        # Add hover tool
    hover = HoverTool()
    hover.tooltips = [("Probability", "@x"), ("Curah Hujan", "@y mm")]
    p.add_tools(hover)

    # Customize the legend
    p.legend.title = 'Distributions'
    p.legend.label_text_font_size = "10pt"
    p.legend.location = "top_left"

    # Show plot in Streamlit
    st.bokeh_chart(p)

    # RSME and NSE Calculation Functions
    def calculate_rsme(weibull, other):
        return np.sqrt(np.mean((weibull - other)**2))

    def calculate_nse(weibull, other):
        return 1 - np.sum((weibull - other)**2) / np.sum((other - np.mean(other))**2)

    # Calculate RSME and NSE
    rsme_tests = {
        'Normal': calculate_rsme(np.array(result['Weibull']), np.array(result['Normal'])),
        'Log-Normal': calculate_rsme(np.array(result['Weibull']), np.array(result['Log-Normal'])),
        'Log Pearson Type III': calculate_rsme(np.array(result['Weibull']), np.array(result['Log Pearson Type III'])),
        'Gumbel': calculate_rsme(np.array(result['Weibull']), np.array(result['Gumbel'])),
        'GEV': calculate_rsme(np.array(result['Weibull']), np.array(result['Genextreme']))
    }
    nse_tests = {
        'Normal': calculate_nse(np.array(result['Weibull']), np.array(result['Normal'])),
        'Log-Normal': calculate_nse(np.array(result['Weibull']), np.array(result['Log-Normal'])),
        'Log Pearson Type III': calculate_nse(np.array(result['Weibull']), np.array(result['Log Pearson Type III'])),
        'Gumbel': calculate_nse(np.array(result['Weibull']), np.array(result['Gumbel'])),
        'GEV': calculate_nse(np.array(result['Weibull']), np.array(result['Genextreme']))
    }

    # Create DataFrame for RSME and NSE results
    results_df = pd.DataFrame({'RMSE': rsme_tests, 'NSE': nse_tests})
    results_df.index.name = 'Distribution'

    #st.write("Hasil RSME dan NSE:")
    #st.write(results_df.round(3))

    # Urutkan berdasarkan RMSE atau NSE
    sorted_results_rmse = results_df.sort_values(by='RMSE')
    sorted_results_nse = results_df.sort_values(by='NSE')

    # Ambil distribusi dengan nilai RMSE dan NSE terkecil
    best_rmse_distribution = sorted_results_rmse.index[0]
    best_nse_distribution = sorted_results_nse.index[0]

    # Tampilkan hasil menggunakan Streamlit
    st.write("Hasil RMSE dan NSE:")
    st.write(results_df.round(3))

    st.write("\nDistribusi dengan RMSE terkecil:")
    st.write(f"{best_rmse_distribution}: {sorted_results_rmse.loc[best_rmse_distribution, 'RMSE']:.3f}")

    st.write("\nDistribusi dengan NSE terkecil:")
    st.write(f"{best_nse_distribution}: {sorted_results_nse.loc[best_nse_distribution, 'NSE']:.3f}")




