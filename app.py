import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import google.generativeai as genai
import io
import datetime
import os

# ==========================================
# 1. Configuration & Styling
# ==========================================
st.set_page_config(
    page_title="Hyundai Global SEM Maturity Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Hyundai-style aesthetics
st.markdown("""
    <style>
        /* Main background and font */
        .stApp {
            background-color: #f8fafc;
            font-family: 'Inter', sans-serif;
        }
        /* Metrics Cards */
        div[data-testid="stMetric"] {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #64748b;
            font-weight: 600;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #0f172a;
            font-weight: 700;
        }
        /* Header styling */
        h1, h2, h3 {
            color: #002c5f; /* Hyundai Blue */
        }
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #fff;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #002c5f;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Mock Data Injection (Hardcoded)
# ==========================================
RAW_CSV_DATA = """Date,Year,Month,Region,Region_Code,Country,NSC,Framework,Framework_Score,Monthly_Total_Budget,Allocated_Cost
1/1/24,2024,1,North America,NA,USA,HMA,Performance & Coverage,74.5,10684046.22,922226.75
1/1/24,2024,1,North America,NA,USA,HMA,Quality Excellence,73.6,10684046.22,8980885.84
1/1/24,2024,1,North America,NA,USA,HMA,Data Infrastructure,74.9,10684046.22,96981.05
1/1/24,2024,1,North America,NA,USA,HMA,AI Adoption,77.1,10684046.22,683952.58
1/1/24,2024,1,North America,NA,Canada,HAC,Performance & Coverage,65.2,1745409.82,414405.29
1/1/24,2024,1,North America,NA,Canada,HAC,Quality Excellence,69.5,1745409.82,32481.07
1/1/24,2024,1,North America,NA,Canada,HAC,Data Infrastructure,68.8,1745409.82,705064.25
1/1/24,2024,1,North America,NA,Canada,HAC,AI Adoption,69.3,1745409.82,593459.22
1/1/24,2024,1,North America,NA,Mexico,HMM,Performance & Coverage,62,757881.89,135192.41
1/1/24,2024,1,North America,NA,Mexico,HMM,Quality Excellence,55.9,757881.89,353181.21
1/1/24,2024,1,North America,NA,Mexico,HMM,Data Infrastructure,42.2,757881.89,111443.69
1/1/24,2024,1,North America,NA,Mexico,HMM,AI Adoption,58.6,757881.89,158064.59
1/1/24,2024,1,Europe,EU,Germany,HMD,Performance & Coverage,72.7,4414774.76,802686.44
1/1/24,2024,1,Europe,EU,Germany,HMD,Quality Excellence,74.3,4414774.76,1955418.98
1/1/24,2024,1,Europe,EU,Germany,HMD,Data Infrastructure,73.7,4414774.76,1189770.42
1/1/24,2024,1,Europe,EU,Germany,HMD,AI Adoption,75,4414774.76,466898.92
1/1/24,2024,1,Europe,EU,United Kingdom,HMUK,Performance & Coverage,68.8,3698415.35,1611729.71
1/1/24,2024,1,Europe,EU,United Kingdom,HMUK,Quality Excellence,73.1,3698415.35,12695.52
1/1/24,2024,1,Europe,EU,United Kingdom,HMUK,Data Infrastructure,71.8,3698415.35,959206.05
1/1/24,2024,1,Europe,EU,United Kingdom,HMUK,AI Adoption,73.3,3698415.35,1114784.05
1/1/24,2024,1,Europe,EU,France,HMF,Performance & Coverage,63.8,2671658.77,253066.97
1/1/24,2024,1,Europe,EU,France,HMF,Quality Excellence,69.1,2671658.77,347303.54
1/1/24,2024,1,Europe,EU,France,HMF,Data Infrastructure,67.5,2671658.77,1822088.98
1/1/24,2024,1,Europe,EU,France,HMF,AI Adoption,64.9,2671658.77,249199.27
1/1/24,2024,1,Europe,EU,Spain,HMS,Performance & Coverage,62.4,2195149.37,713782.88
1/1/24,2024,1,Europe,EU,Spain,HMS,Quality Excellence,67.4,2195149.37,94777.97
1/1/24,2024,1,Europe,EU,Spain,HMS,Data Infrastructure,64.1,2195149.37,449742.02
1/1/24,2024,1,Europe,EU,Spain,HMS,AI Adoption,61.3,2195149.37,936846.51
1/1/24,2024,1,Europe,EU,Italy,HMI,Performance & Coverage,65.5,2756560.47,13843.51
1/1/24,2024,1,Europe,EU,Italy,HMI,Quality Excellence,66.4,2756560.47,1450025.56
1/1/24,2024,1,Europe,EU,Italy,HMI,Data Infrastructure,63.4,2756560.47,997190.21
1/1/24,2024,1,Europe,EU,Italy,HMI,AI Adoption,63.5,2756560.47,295501.19
1/1/24,2024,1,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,60.1,1000651.38,466035.91
1/1/24,2024,1,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,73.3,1000651.38,34051.8
1/1/24,2024,1,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,70.7,1000651.38,148618.56
1/1/24,2024,1,Asia Pacific,APAC,Australia,HMCA,AI Adoption,69.5,1000651.38,351945.11
1/1/24,2024,1,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,52.9,435210.77,294657.74
1/1/24,2024,1,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,53.1,435210.77,87342.83
1/1/24,2024,1,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,51.6,435210.77,48206.87
1/1/24,2024,1,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,52.4,435210.77,5003.32
1/1/24,2024,1,Asia Pacific,APAC,India,HMIL,Performance & Coverage,66.5,1386214.93,997945.89
1/1/24,2024,1,Asia Pacific,APAC,India,HMIL,Quality Excellence,61.7,1386214.93,38030.74
1/1/24,2024,1,Asia Pacific,APAC,India,HMIL,Data Infrastructure,60.5,1386214.93,283117.92
1/1/24,2024,1,Asia Pacific,APAC,India,HMIL,AI Adoption,66.6,1386214.93,67120.38
1/1/24,2024,1,Central & South America,CS,Brazil,HMB,Performance & Coverage,48.9,1110637.61,523512.63
1/1/24,2024,1,Central & South America,CS,Brazil,HMB,Quality Excellence,58.8,1110637.61,278607.16
1/1/24,2024,1,Central & South America,CS,Brazil,HMB,Data Infrastructure,63,1110637.61,246200.15
1/1/24,2024,1,Central & South America,CS,Brazil,HMB,AI Adoption,57.8,1110637.61,62317.68
2/1/24,2024,2,North America,NA,USA,HMA,Performance & Coverage,76.9,12032164.91,2162214.33
2/1/24,2024,2,North America,NA,USA,HMA,Quality Excellence,71.3,12032164.91,964898.37
2/1/24,2024,2,North America,NA,USA,HMA,Data Infrastructure,72.7,12032164.91,1721848.25
2/1/24,2024,2,North America,NA,USA,HMA,AI Adoption,80.4,12032164.91,7183203.96
2/1/24,2024,2,North America,NA,Canada,HAC,Performance & Coverage,72.1,1896044.36,310375.98
2/1/24,2024,2,North America,NA,Canada,HAC,Quality Excellence,76.6,1896044.36,54130.55
2/1/24,2024,2,North America,NA,Canada,HAC,Data Infrastructure,52.7,1896044.36,24692.01
2/1/24,2024,2,North America,NA,Canada,HAC,AI Adoption,71,1896044.36,1506845.82
2/1/24,2024,2,North America,NA,Mexico,HMM,Performance & Coverage,56.9,954309.8,350438.78
2/1/24,2024,2,North America,NA,Mexico,HMM,Quality Excellence,56.1,954309.8,460593.71
2/1/24,2024,2,North America,NA,Mexico,HMM,Data Infrastructure,58.3,954309.8,32163
2/1/24,2024,2,North America,NA,Mexico,HMM,AI Adoption,59.5,954309.8,111114.3
2/1/24,2024,2,Europe,EU,Germany,HMD,Performance & Coverage,75.9,4988435.67,70664.65
2/1/24,2024,2,Europe,EU,Germany,HMD,Quality Excellence,77,4988435.67,1441129.32
2/1/24,2024,2,Europe,EU,Germany,HMD,Data Infrastructure,73.9,4988435.67,1398364.83
2/1/24,2024,2,Europe,EU,Germany,HMD,AI Adoption,73.8,4988435.67,2078276.87
2/1/24,2024,2,Europe,EU,United Kingdom,HMUK,Performance & Coverage,75.7,3380887.41,1376336.38
2/1/24,2024,2,Europe,EU,United Kingdom,HMUK,Quality Excellence,73.9,3380887.41,1315084.38
2/1/24,2024,2,Europe,EU,United Kingdom,HMUK,Data Infrastructure,68.3,3380887.41,257687.28
2/1/24,2024,2,Europe,EU,United Kingdom,HMUK,AI Adoption,71.4,3380887.41,431779.37
2/1/24,2024,2,Europe,EU,France,HMF,Performance & Coverage,62.2,2428297.24,661426.64
2/1/24,2024,2,Europe,EU,France,HMF,Quality Excellence,66.7,2428297.24,603216.09
2/1/24,2024,2,Europe,EU,France,HMF,Data Infrastructure,67.6,2428297.24,317835.5
2/1/24,2024,2,Europe,EU,France,HMF,AI Adoption,63.1,2428297.24,845819
2/1/24,2024,2,Europe,EU,Spain,HMS,Performance & Coverage,65.3,2504573.36,139393.19
2/1/24,2024,2,Europe,EU,Spain,HMS,Quality Excellence,62.7,2504573.36,806177.57
2/1/24,2024,2,Europe,EU,Spain,HMS,Data Infrastructure,70.1,2504573.36,1466484.15
2/1/24,2024,2,Europe,EU,Spain,HMS,AI Adoption,66,2504573.36,92518.45
2/1/24,2024,2,Europe,EU,Italy,HMI,Performance & Coverage,64.2,2298926.22,865311.98
2/1/24,2024,2,Europe,EU,Italy,HMI,Quality Excellence,63.9,2298926.22,237157.41
2/1/24,2024,2,Europe,EU,Italy,HMI,Data Infrastructure,62,2298926.22,55530.34
2/1/24,2024,2,Europe,EU,Italy,HMI,AI Adoption,60,2298926.22,1140926.49
2/1/24,2024,2,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,77.9,1047700.2,69520.06
2/1/24,2024,2,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,53.4,1047700.2,365173.82
2/1/24,2024,2,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,72.3,1047700.2,77052.76
2/1/24,2024,2,Asia Pacific,APAC,Australia,HMCA,AI Adoption,72.4,1047700.2,535953.55
2/1/24,2024,2,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,53.2,482988.1,129125.61
2/1/24,2024,2,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,59.4,482988.1,24081.09
2/1/24,2024,2,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,62.3,482988.1,292739.75
2/1/24,2024,2,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,52,482988.1,37041.66
2/1/24,2024,2,Asia Pacific,APAC,India,HMIL,Performance & Coverage,65.5,1408221.9,701209.36
2/1/24,2024,2,Asia Pacific,APAC,India,HMIL,Quality Excellence,57.4,1408221.9,100994.08
2/1/24,2024,2,Asia Pacific,APAC,India,HMIL,Data Infrastructure,61.6,1408221.9,355716.1
2/1/24,2024,2,Asia Pacific,APAC,India,HMIL,AI Adoption,61.8,1408221.9,250302.36
2/1/24,2024,2,Central & South America,CS,Brazil,HMB,Performance & Coverage,60.3,1187015.48,53816.27
2/1/24,2024,2,Central & South America,CS,Brazil,HMB,Quality Excellence,63.4,1187015.48,157146.28
2/1/24,2024,2,Central & South America,CS,Brazil,HMB,Data Infrastructure,59.7,1187015.48,128341.5
2/1/24,2024,2,Central & South America,CS,Brazil,HMB,AI Adoption,60.1,1187015.48,847711.44
3/1/24,2024,3,North America,NA,USA,HMA,Performance & Coverage,75.5,12995677.34,803298.22
3/1/24,2024,3,North America,NA,USA,HMA,Quality Excellence,73.9,12995677.34,8864428.68
3/1/24,2024,3,North America,NA,USA,HMA,Data Infrastructure,71.1,12995677.34,1535409.55
3/1/24,2024,3,North America,NA,USA,HMA,AI Adoption,74.3,12995677.34,1792540.88
3/1/24,2024,3,North America,NA,Canada,HAC,Performance & Coverage,71.9,1658251.22,749852.59
3/1/24,2024,3,North America,NA,Canada,HAC,Quality Excellence,69.3,1658251.22,233279
3/1/24,2024,3,North America,NA,Canada,HAC,Data Infrastructure,74.7,1658251.22,166654.56
3/1/24,2024,3,North America,NA,Canada,HAC,AI Adoption,72.2,1658251.22,508465.06
3/1/24,2024,3,North America,NA,Mexico,HMM,Performance & Coverage,58.7,875679.81,28989.47
3/1/24,2024,3,North America,NA,Mexico,HMM,Quality Excellence,59.7,875679.81,87393.71
3/1/24,2024,3,North America,NA,Mexico,HMM,Data Infrastructure,60,875679.81,171310.28
3/1/24,2024,3,North America,NA,Mexico,HMM,AI Adoption,60.3,875679.81,587986.35
3/1/24,2024,3,Europe,EU,Germany,HMD,Performance & Coverage,77.8,3782842.95,2322053.24
3/1/24,2024,3,Europe,EU,Germany,HMD,Quality Excellence,72.6,3782842.95,209847.02
3/1/24,2024,3,Europe,EU,Germany,HMD,Data Infrastructure,73.9,3782842.95,554617.3
3/1/24,2024,3,Europe,EU,Germany,HMD,AI Adoption,72.4,3782842.95,696325.39
3/1/24,2024,3,Europe,EU,United Kingdom,HMUK,Performance & Coverage,70,3228881.46,485236.5
3/1/24,2024,3,Europe,EU,United Kingdom,HMUK,Quality Excellence,74.6,3228881.46,1140951.88
3/1/24,2024,3,Europe,EU,United Kingdom,HMUK,Data Infrastructure,73.1,3228881.46,140868.66
3/1/24,2024,3,Europe,EU,United Kingdom,HMUK,AI Adoption,73.8,3228881.46,1461824.42
3/1/24,2024,3,Europe,EU,France,HMF,Performance & Coverage,60.5,3511641.65,682224.31
3/1/24,2024,3,Europe,EU,France,HMF,Quality Excellence,71.6,3511641.65,623473.94
3/1/24,2024,3,Europe,EU,France,HMF,Data Infrastructure,65.3,3511641.65,1607026.29
3/1/24,2024,3,Europe,EU,France,HMF,AI Adoption,69.7,3511641.65,598917.11
3/1/24,2024,3,Europe,EU,Spain,HMS,Performance & Coverage,66.9,2579475.63,303078.76
3/1/24,2024,3,Europe,EU,Spain,HMS,Quality Excellence,64,2579475.63,1331619.03
3/1/24,2024,3,Europe,EU,Spain,HMS,Data Infrastructure,66.2,2579475.63,476978.4
3/1/24,2024,3,Europe,EU,Spain,HMS,AI Adoption,63.9,2579475.63,467799.44
3/1/24,2024,3,Europe,EU,Italy,HMI,Performance & Coverage,55.7,2317524.25,199302.5
3/1/24,2024,3,Europe,EU,Italy,HMI,Quality Excellence,63.4,2317524.25,6736.99
3/1/24,2024,3,Europe,EU,Italy,HMI,Data Infrastructure,71.6,2317524.25,529180
3/1/24,2024,3,Europe,EU,Italy,HMI,AI Adoption,68.4,2317524.25,1582304.75
3/1/24,2024,3,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,69.7,1205577.59,68686.29
3/1/24,2024,3,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,73.7,1205577.59,252459.85
3/1/24,2024,3,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,71.8,1205577.59,838649.22
3/1/24,2024,3,Asia Pacific,APAC,Australia,HMCA,AI Adoption,67.8,1205577.59,45782.23
3/1/24,2024,3,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,53.3,473624.86,35130.95
3/1/24,2024,3,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,52.9,473624.86,213936.76
3/1/24,2024,3,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,52.5,473624.86,210445.68
3/1/24,2024,3,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,55.4,473624.86,14111.48
3/1/24,2024,3,Asia Pacific,APAC,India,HMIL,Performance & Coverage,64.3,1360196.17,452952.12
3/1/24,2024,3,Asia Pacific,APAC,India,HMIL,Quality Excellence,49.7,1360196.17,174048.13
3/1/24,2024,3,Asia Pacific,APAC,India,HMIL,Data Infrastructure,65.9,1360196.17,479324.65
3/1/24,2024,3,Asia Pacific,APAC,India,HMIL,AI Adoption,60.9,1360196.17,253871.27
3/1/24,2024,3,Central & South America,CS,Brazil,HMB,Performance & Coverage,48,1346922.45,22753.99
3/1/24,2024,3,Central & South America,CS,Brazil,HMB,Quality Excellence,61.4,1346922.45,586097.85
3/1/24,2024,3,Central & South America,CS,Brazil,HMB,Data Infrastructure,59.7,1346922.45,410982.07
3/1/24,2024,3,Central & South America,CS,Brazil,HMB,AI Adoption,57.8,1346922.45,327088.54
4/1/24,2024,4,North America,NA,USA,HMA,Performance & Coverage,76.3,11318326.83,919773.34
4/1/24,2024,4,North America,NA,USA,HMA,Quality Excellence,75,11318326.83,944681.96
4/1/24,2024,4,North America,NA,USA,HMA,Data Infrastructure,74.8,11318326.83,1793382.91
4/1/24,2024,4,North America,NA,USA,HMA,AI Adoption,74.4,11318326.83,7660488.62
4/1/24,2024,4,North America,NA,Canada,HAC,Performance & Coverage,71.1,1641920.71,797705.2
4/1/24,2024,4,North America,NA,Canada,HAC,Quality Excellence,71.7,1641920.71,295025.08
4/1/24,2024,4,North America,NA,Canada,HAC,Data Infrastructure,69.5,1641920.71,142569.54
4/1/24,2024,4,North America,NA,Canada,HAC,AI Adoption,66.5,1641920.71,406620.89
4/1/24,2024,4,North America,NA,Mexico,HMM,Performance & Coverage,61.9,769618.46,315096.49
4/1/24,2024,4,North America,NA,Mexico,HMM,Quality Excellence,61,769618.46,88997.72
4/1/24,2024,4,North America,NA,Mexico,HMM,Data Infrastructure,65,769618.46,56260.41
4/1/24,2024,4,North America,NA,Mexico,HMM,AI Adoption,58.1,769618.46,309263.85
4/1/24,2024,4,Europe,EU,Germany,HMD,Performance & Coverage,72.3,4106395.9,589854.81
4/1/24,2024,4,Europe,EU,Germany,HMD,Quality Excellence,76.9,4106395.9,168088.1
4/1/24,2024,4,Europe,EU,Germany,HMD,Data Infrastructure,70,4106395.9,716596.52
4/1/24,2024,4,Europe,EU,Germany,HMD,AI Adoption,77.3,4106395.9,2631856.47
4/1/24,2024,4,Europe,EU,United Kingdom,HMUK,Performance & Coverage,75.1,3273234.53,574670.86
4/1/24,2024,4,Europe,EU,United Kingdom,HMUK,Quality Excellence,71.3,3273234.53,1238147.75
4/1/24,2024,4,Europe,EU,United Kingdom,HMUK,Data Infrastructure,70.7,3273234.53,731639.2
4/1/24,2024,4,Europe,EU,United Kingdom,HMUK,AI Adoption,74,3273234.53,728776.73
4/1/24,2024,4,Europe,EU,France,HMF,Performance & Coverage,67.7,3182765.95,526816.76
4/1/24,2024,4,Europe,EU,France,HMF,Quality Excellence,65.5,3182765.95,81419.43
4/1/24,2024,4,Europe,EU,France,HMF,Data Infrastructure,64.4,3182765.95,1894043.62
4/1/24,2024,4,Europe,EU,France,HMF,AI Adoption,64.9,3182765.95,680486.15
4/1/24,2024,4,Europe,EU,Spain,HMS,Performance & Coverage,63.4,2263549.74,305437.18
4/1/24,2024,4,Europe,EU,Spain,HMS,Quality Excellence,70.4,2263549.74,951991.01
4/1/24,2024,4,Europe,EU,Spain,HMS,Data Infrastructure,62,2263549.74,335462.59
4/1/24,2024,4,Europe,EU,Spain,HMS,AI Adoption,63.9,2263549.74,670658.95
4/1/24,2024,4,Europe,EU,Italy,HMI,Performance & Coverage,66.6,2673054.97,262288.4
4/1/24,2024,4,Europe,EU,Italy,HMI,Quality Excellence,67.6,2673054.97,786929.13
4/1/24,2024,4,Europe,EU,Italy,HMI,Data Infrastructure,63.5,2673054.97,893834.35
4/1/24,2024,4,Europe,EU,Italy,HMI,AI Adoption,64,2673054.97,730003.09
4/1/24,2024,4,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,71.3,1064979.37,206468.72
4/1/24,2024,4,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,75.5,1064979.37,738.09
4/1/24,2024,4,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,68.9,1064979.37,209561.06
4/1/24,2024,4,Asia Pacific,APAC,Australia,HMCA,AI Adoption,73.1,1064979.37,648211.5
4/1/24,2024,4,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,60.3,450209.84,190675.92
4/1/24,2024,4,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,59.3,450209.84,7932.1
4/1/24,2024,4,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,55.9,450209.84,97298.56
4/1/24,2024,4,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,61.4,450209.84,154303.26
4/1/24,2024,4,Asia Pacific,APAC,India,HMIL,Performance & Coverage,63.5,1433087.04,332124.37
4/1/24,2024,4,Asia Pacific,APAC,India,HMIL,Quality Excellence,63.4,1433087.04,728830.24
4/1/24,2024,4,Asia Pacific,APAC,India,HMIL,Data Infrastructure,64.8,1433087.04,242666.09
4/1/24,2024,4,Asia Pacific,APAC,India,HMIL,AI Adoption,61.3,1433087.04,129466.33
4/1/24,2024,4,Central & South America,CS,Brazil,HMB,Performance & Coverage,46.1,1315556.24,388165.12
4/1/24,2024,4,Central & South America,CS,Brazil,HMB,Quality Excellence,58.8,1315556.24,402607.2
4/1/24,2024,4,Central & South America,CS,Brazil,HMB,Data Infrastructure,67.6,1315556.24,190913.91
4/1/24,2024,4,Central & South America,CS,Brazil,HMB,AI Adoption,63.6,1315556.24,333870.02
5/1/24,2024,5,North America,NA,USA,HMA,Performance & Coverage,71.9,10281628.33,2854147.57
5/1/24,2024,5,North America,NA,USA,HMA,Quality Excellence,77.7,10281628.33,3027703.42
5/1/24,2024,5,North America,NA,USA,HMA,Data Infrastructure,77.7,10281628.33,2230539.45
5/1/24,2024,5,North America,NA,USA,HMA,AI Adoption,78.6,10281628.33,2169237.89
5/1/24,2024,5,North America,NA,Canada,HAC,Performance & Coverage,68.4,1621773.58,1135414.81
5/1/24,2024,5,North America,NA,Canada,HAC,Quality Excellence,74.3,1621773.58,331927.56
5/1/24,2024,5,North America,NA,Canada,HAC,Data Infrastructure,69.4,1621773.58,6389.33
5/1/24,2024,5,North America,NA,Canada,HAC,AI Adoption,72.3,1621773.58,148041.88
5/1/24,2024,5,North America,NA,Mexico,HMM,Performance & Coverage,54.8,849537.14,26276.1
5/1/24,2024,5,North America,NA,Mexico,HMM,Quality Excellence,63.7,849537.14,573834.02
5/1/24,2024,5,North America,NA,Mexico,HMM,Data Infrastructure,62.3,849537.14,227104.69
5/1/24,2024,5,North America,NA,Mexico,HMM,AI Adoption,64.1,849537.14,22322.34
5/1/24,2024,5,Europe,EU,Germany,HMD,Performance & Coverage,71.4,3644061.83,342570.69
5/1/24,2024,5,Europe,EU,Germany,HMD,Quality Excellence,70.9,3644061.83,94477.5
5/1/24,2024,5,Europe,EU,Germany,HMD,Data Infrastructure,69.7,3644061.83,2633332.53
5/1/24,2024,5,Europe,EU,Germany,HMD,AI Adoption,71.1,3644061.83,573681.11
5/1/24,2024,5,Europe,EU,United Kingdom,HMUK,Performance & Coverage,68.9,3322406.74,1200783.05
5/1/24,2024,5,Europe,EU,United Kingdom,HMUK,Quality Excellence,70.4,3322406.74,171253.54
5/1/24,2024,5,Europe,EU,United Kingdom,HMUK,Data Infrastructure,76.2,3322406.74,1127159.03
5/1/24,2024,5,Europe,EU,United Kingdom,HMUK,AI Adoption,75.8,3322406.74,823211.12
5/1/24,2024,5,Europe,EU,France,HMF,Performance & Coverage,64.6,2664774.42,114134.57
5/1/24,2024,5,Europe,EU,France,HMF,Quality Excellence,66.9,2664774.42,564846.25
5/1/24,2024,5,Europe,EU,France,HMF,Data Infrastructure,66.6,2664774.42,1063760.23
5/1/24,2024,5,Europe,EU,France,HMF,AI Adoption,66.6,2664774.42,922033.38
5/1/24,2024,5,Europe,EU,Spain,HMS,Performance & Coverage,72.3,1688731.09,226756.45
5/1/24,2024,5,Europe,EU,Spain,HMS,Quality Excellence,70.3,1688731.09,703893.27
5/1/24,2024,5,Europe,EU,Spain,HMS,Data Infrastructure,71.1,1688731.09,520685.51
5/1/24,2024,5,Europe,EU,Spain,HMS,AI Adoption,66,1688731.09,237395.86
5/1/24,2024,5,Europe,EU,Italy,HMI,Performance & Coverage,66,1463385.17,179270.35
5/1/24,2024,5,Europe,EU,Italy,HMI,Quality Excellence,65.9,1463385.17,868247.65
5/1/24,2024,5,Europe,EU,Italy,HMI,Data Infrastructure,65.6,1463385.17,378304.19
5/1/24,2024,5,Europe,EU,Italy,HMI,AI Adoption,68.6,1463385.17,37562.97
5/1/24,2024,5,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,75.6,1002392.2,93226.68
5/1/24,2024,5,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,69.8,1002392.2,326860.74
5/1/24,2024,5,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,72,1002392.2,120707.83
5/1/24,2024,5,Asia Pacific,APAC,Australia,HMCA,AI Adoption,74.9,1002392.2,461596.96
5/1/24,2024,5,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,55.1,457425.17,12049.71
5/1/24,2024,5,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,51.7,457425.17,210473.85
5/1/24,2024,5,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,58,457425.17,191456.53
5/1/24,2024,5,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,52.3,457425.17,43445.08
5/1/24,2024,5,Asia Pacific,APAC,India,HMIL,Performance & Coverage,66.1,1324480.81,241399.64
5/1/24,2024,5,Asia Pacific,APAC,India,HMIL,Quality Excellence,63.8,1324480.81,71227.47
5/1/24,2024,5,Asia Pacific,APAC,India,HMIL,Data Infrastructure,68.9,1324480.81,812919.25
5/1/24,2024,5,Asia Pacific,APAC,India,HMIL,AI Adoption,62.3,1324480.81,198934.45
5/1/24,2024,5,Central & South America,CS,Brazil,HMB,Performance & Coverage,60.1,1017666.14,20478.08
5/1/24,2024,5,Central & South America,CS,Brazil,HMB,Quality Excellence,60.7,1017666.14,663162.25
5/1/24,2024,5,Central & South America,CS,Brazil,HMB,Data Infrastructure,61,1017666.14,87445.77
5/1/24,2024,5,Central & South America,CS,Brazil,HMB,AI Adoption,47.3,1017666.14,246580.04
6/1/24,2024,6,North America,NA,USA,HMA,Performance & Coverage,74.8,9475930.57,1486068.16
6/1/24,2024,6,North America,NA,USA,HMA,Quality Excellence,77.4,9475930.57,121015.12
6/1/24,2024,6,North America,NA,USA,HMA,Data Infrastructure,74.1,9475930.57,4821882.45
6/1/24,2024,6,North America,NA,USA,HMA,AI Adoption,79.4,9475930.57,3046964.84
6/1/24,2024,6,North America,NA,Canada,HAC,Performance & Coverage,58.6,1551588.63,421925.87
6/1/24,2024,6,North America,NA,Canada,HAC,Quality Excellence,72.8,1551588.63,374337.66
6/1/24,2024,6,North America,NA,Canada,HAC,Data Infrastructure,76.3,1551588.63,31391.49
6/1/24,2024,6,North America,NA,Canada,HAC,AI Adoption,65.1,1551588.63,723933.62
6/1/24,2024,6,North America,NA,Mexico,HMM,Performance & Coverage,46.8,851912.77,5393.44
6/1/24,2024,6,North America,NA,Mexico,HMM,Quality Excellence,58.5,851912.77,343050.96
6/1/24,2024,6,North America,NA,Mexico,HMM,Data Infrastructure,65.3,851912.77,358737.71
6/1/24,2024,6,North America,NA,Mexico,HMM,AI Adoption,61.9,851912.77,144730.66
6/1/24,2024,6,Europe,EU,Germany,HMD,Performance & Coverage,68.7,4030913.54,2332517.11
6/1/24,2024,6,Europe,EU,Germany,HMD,Quality Excellence,74.8,4030913.54,317100.15
6/1/24,2024,6,Europe,EU,Germany,HMD,Data Infrastructure,71.4,4030913.54,369003.91
6/1/24,2024,6,Europe,EU,Germany,HMD,AI Adoption,73.7,4030913.54,1012292.36
6/1/24,2024,6,Europe,EU,United Kingdom,HMUK,Performance & Coverage,74.9,2976669.38,461365.69
6/1/24,2024,6,Europe,EU,United Kingdom,HMUK,Quality Excellence,73.3,2976669.38,1600049.31
6/1/24,2024,6,Europe,EU,United Kingdom,HMUK,Data Infrastructure,73.5,2976669.38,801921.67
6/1/24,2024,6,Europe,EU,United Kingdom,HMUK,AI Adoption,72,2976669.38,113332.71
6/1/24,2024,6,Europe,EU,France,HMF,Performance & Coverage,73.6,2644737.42,1442269.35
6/1/24,2024,6,Europe,EU,France,HMF,Quality Excellence,64.8,2644737.42,33358.47
6/1/24,2024,6,Europe,EU,France,HMF,Data Infrastructure,67.6,2644737.42,659106.92
6/1/24,2024,6,Europe,EU,France,HMF,AI Adoption,60.3,2644737.42,510002.68
6/1/24,2024,6,Europe,EU,Spain,HMS,Performance & Coverage,68.5,2125162.78,132307.47
6/1/24,2024,6,Europe,EU,Spain,HMS,Quality Excellence,70.5,2125162.78,1011363.64
6/1/24,2024,6,Europe,EU,Spain,HMS,Data Infrastructure,62.3,2125162.78,16195.85
6/1/24,2024,6,Europe,EU,Spain,HMS,AI Adoption,63.5,2125162.78,965295.83
6/1/24,2024,6,Europe,EU,Italy,HMI,Performance & Coverage,69.6,2243279.89,90195.53
6/1/24,2024,6,Europe,EU,Italy,HMI,Quality Excellence,69.6,2243279.89,1099128.37
6/1/24,2024,6,Europe,EU,Italy,HMI,Data Infrastructure,71.2,2243279.89,26833.54
6/1/24,2024,6,Europe,EU,Italy,HMI,AI Adoption,65.2,2243279.89,1027122.46
6/1/24,2024,6,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,71.3,744316.9,255425.12
6/1/24,2024,6,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,70,744316.9,140484.24
6/1/24,2024,6,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,70.9,744316.9,260273.04
6/1/24,2024,6,Asia Pacific,APAC,Australia,HMCA,AI Adoption,74.8,744316.9,88134.51
6/1/24,2024,6,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,58.5,355368.72,131772.37
6/1/24,2024,6,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,56.8,355368.72,101333.4
6/1/24,2024,6,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,58.8,355368.72,51091.23
6/1/24,2024,6,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,56.6,355368.72,71171.72
6/1/24,2024,6,Asia Pacific,APAC,India,HMIL,Performance & Coverage,66,1241904.91,359646.59
6/1/24,2024,6,Asia Pacific,APAC,India,HMIL,Quality Excellence,67.7,1241904.91,849186.04
6/1/24,2024,6,Asia Pacific,APAC,India,HMIL,Data Infrastructure,64.9,1241904.91,6082.06
6/1/24,2024,6,Asia Pacific,APAC,India,HMIL,AI Adoption,63.1,1241904.91,26990.22
6/1/24,2024,6,Central & South America,CS,Brazil,HMB,Performance & Coverage,61.9,1107247.7,35249.25
6/1/24,2024,6,Central & South America,CS,Brazil,HMB,Quality Excellence,65,1107247.7,498078.38
6/1/24,2024,6,Central & South America,CS,Brazil,HMB,Data Infrastructure,59.9,1107247.7,570193.86
6/1/24,2024,6,Central & South America,CS,Brazil,HMB,AI Adoption,66.1,1107247.7,3726.21
7/1/24,2024,7,North America,NA,USA,HMA,Performance & Coverage,76.4,9118165.11,3180439.25
7/1/24,2024,7,North America,NA,USA,HMA,Quality Excellence,78.4,9118165.11,1631105.93
7/1/24,2024,7,North America,NA,USA,HMA,Data Infrastructure,77.2,9118165.11,2450385.46
7/1/24,2024,7,North America,NA,USA,HMA,AI Adoption,80.2,9118165.11,1856234.47
7/1/24,2024,7,North America,NA,Canada,HAC,Performance & Coverage,71.9,1213967.06,475262.26
7/1/24,2024,7,North America,NA,Canada,HAC,Quality Excellence,73,1213967.06,446175.13
7/1/24,2024,7,North America,NA,Canada,HAC,Data Infrastructure,75.9,1213967.06,49657.37
7/1/24,2024,7,North America,NA,Canada,HAC,AI Adoption,73,1213967.06,242872.3
7/1/24,2024,7,North America,NA,Mexico,HMM,Performance & Coverage,66.5,637954.6,293630.24
7/1/24,2024,7,North America,NA,Mexico,HMM,Quality Excellence,62.6,637954.6,20654.56
7/1/24,2024,7,North America,NA,Mexico,HMM,Data Infrastructure,64.1,637954.6,182427.71
7/1/24,2024,7,North America,NA,Mexico,HMM,AI Adoption,67.9,637954.6,141242.09
7/1/24,2024,7,Europe,EU,Germany,HMD,Performance & Coverage,70.7,2790772.56,460663.81
7/1/24,2024,7,Europe,EU,Germany,HMD,Quality Excellence,72.7,2790772.56,37120.92
7/1/24,2024,7,Europe,EU,Germany,HMD,Data Infrastructure,76.2,2790772.56,2199183.46
7/1/24,2024,7,Europe,EU,Germany,HMD,AI Adoption,71.5,2790772.56,93804.36
7/1/24,2024,7,Europe,EU,United Kingdom,HMUK,Performance & Coverage,76,2657848.46,1783678.93
7/1/24,2024,7,Europe,EU,United Kingdom,HMUK,Quality Excellence,78,2657848.46,357461.34
7/1/24,2024,7,Europe,EU,United Kingdom,HMUK,Data Infrastructure,78.2,2657848.46,75789.99
7/1/24,2024,7,Europe,EU,United Kingdom,HMUK,AI Adoption,73.5,2657848.46,440918.19
7/1/24,2024,7,Europe,EU,France,HMF,Performance & Coverage,69.5,1791620.14,617918.78
7/1/24,2024,7,Europe,EU,France,HMF,Quality Excellence,67.5,1791620.14,153468.48
7/1/24,2024,7,Europe,EU,France,HMF,Data Infrastructure,71.8,1791620.14,376670.18
7/1/24,2024,7,Europe,EU,France,HMF,AI Adoption,63.7,1791620.14,643562.7
7/1/24,2024,7,Europe,EU,Spain,HMS,Performance & Coverage,66.5,1679488.44,139176.24
7/1/24,2024,7,Europe,EU,Spain,HMS,Quality Excellence,67.2,1679488.44,542261.5
7/1/24,2024,7,Europe,EU,Spain,HMS,Data Infrastructure,63.7,1679488.44,450348.46
7/1/24,2024,7,Europe,EU,Spain,HMS,AI Adoption,68.4,1679488.44,547702.24
7/1/24,2024,7,Europe,EU,Italy,HMI,Performance & Coverage,64.6,2140903.43,902640.04
7/1/24,2024,7,Europe,EU,Italy,HMI,Quality Excellence,68.1,2140903.43,615682.89
7/1/24,2024,7,Europe,EU,Italy,HMI,Data Infrastructure,66.8,2140903.43,554627.85
7/1/24,2024,7,Europe,EU,Italy,HMI,AI Adoption,71.9,2140903.43,67952.64
7/1/24,2024,7,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,72.7,882855.41,27288.27
7/1/24,2024,7,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,79.3,882855.41,37121.61
7/1/24,2024,7,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,75,882855.41,80892.75
7/1/24,2024,7,Asia Pacific,APAC,Australia,HMCA,AI Adoption,72,882855.41,737552.78
7/1/24,2024,7,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,59.3,352236.35,216624.78
7/1/24,2024,7,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,55.9,352236.35,45884.63
7/1/24,2024,7,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,60.1,352236.35,73454.07
7/1/24,2024,7,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,60.1,352236.35,16272.88
7/1/24,2024,7,Asia Pacific,APAC,India,HMIL,Performance & Coverage,66.2,1105602.53,116711.44
7/1/24,2024,7,Asia Pacific,APAC,India,HMIL,Quality Excellence,61.7,1105602.53,554108.96
7/1/24,2024,7,Asia Pacific,APAC,India,HMIL,Data Infrastructure,65.2,1105602.53,138151.34
7/1/24,2024,7,Asia Pacific,APAC,India,HMIL,AI Adoption,68.6,1105602.53,296630.8
7/1/24,2024,7,Central & South America,CS,Brazil,HMB,Performance & Coverage,65.2,934965.67,239744.79
7/1/24,2024,7,Central & South America,CS,Brazil,HMB,Quality Excellence,62.1,934965.67,25679.6
7/1/24,2024,7,Central & South America,CS,Brazil,HMB,Data Infrastructure,62.2,934965.67,616351.41
7/1/24,2024,7,Central & South America,CS,Brazil,HMB,AI Adoption,59.7,934965.67,53189.87
8/1/24,2024,8,North America,NA,USA,HMA,Performance & Coverage,83.4,8991325.57,4775148.83
8/1/24,2024,8,North America,NA,USA,HMA,Quality Excellence,80.8,8991325.57,3251807.34
8/1/24,2024,8,North America,NA,USA,HMA,Data Infrastructure,78.7,8991325.57,431181.49
8/1/24,2024,8,North America,NA,USA,HMA,AI Adoption,83.6,8991325.57,533187.91
8/1/24,2024,8,North America,NA,Canada,HAC,Performance & Coverage,74.1,1358900.61,529606.86
8/1/24,2024,8,North America,NA,Canada,HAC,Quality Excellence,76.7,1358900.61,74195.9
8/1/24,2024,8,North America,NA,Canada,HAC,Data Infrastructure,76.8,1358900.61,350823.3
8/1/24,2024,8,North America,NA,Canada,HAC,AI Adoption,62.5,1358900.61,404274.54
8/1/24,2024,8,North America,NA,Mexico,HMM,Performance & Coverage,68.7,635730.54,188884.42
8/1/24,2024,8,North America,NA,Mexico,HMM,Quality Excellence,72.8,635730.54,141343.46
8/1/24,2024,8,North America,NA,Mexico,HMM,Data Infrastructure,66.7,635730.54,174596.08
8/1/24,2024,8,North America,NA,Mexico,HMM,AI Adoption,68.8,635730.54,130906.58
8/1/24,2024,8,Europe,EU,Germany,HMD,Performance & Coverage,77,3317781.22,702926.41
8/1/24,2024,8,Europe,EU,Germany,HMD,Quality Excellence,79.6,3317781.22,555609.25
8/1/24,2024,8,Europe,EU,Germany,HMD,Data Infrastructure,85.4,3317781.22,1435739.19
8/1/24,2024,8,Europe,EU,Germany,HMD,AI Adoption,81.3,3317781.22,785945.35
8/1/24,2024,8,Europe,EU,United Kingdom,HMUK,Performance & Coverage,78.5,2387781.72,433663.72
8/1/24,2024,8,Europe,EU,United Kingdom,HMUK,Quality Excellence,81,2387781.72,287174.04
8/1/24,2024,8,Europe,EU,United Kingdom,HMUK,Data Infrastructure,84.4,2387781.72,976369.47
8/1/24,2024,8,Europe,EU,United Kingdom,HMUK,AI Adoption,77.6,2387781.72,690574.49
8/1/24,2024,8,Europe,EU,France,HMF,Performance & Coverage,72.3,2084135.87,366440.82
8/1/24,2024,8,Europe,EU,France,HMF,Quality Excellence,72.3,2084135.87,294115.35
8/1/24,2024,8,Europe,EU,France,HMF,Data Infrastructure,58.5,2084135.87,1181166.45
8/1/24,2024,8,Europe,EU,France,HMF,AI Adoption,74.9,2084135.87,242413.25
8/1/24,2024,8,Europe,EU,Spain,HMS,Performance & Coverage,70.4,1706959.04,294140.07
8/1/24,2024,8,Europe,EU,Spain,HMS,Quality Excellence,64.2,1706959.04,869587.77
8/1/24,2024,8,Europe,EU,Spain,HMS,Data Infrastructure,73.9,1706959.04,129279.95
8/1/24,2024,8,Europe,EU,Spain,HMS,AI Adoption,76.1,1706959.04,413951.26
8/1/24,2024,8,Europe,EU,Italy,HMI,Performance & Coverage,70.2,1628151.08,542330.94
8/1/24,2024,8,Europe,EU,Italy,HMI,Quality Excellence,72.7,1628151.08,407121.78
8/1/24,2024,8,Europe,EU,Italy,HMI,Data Infrastructure,71.8,1628151.08,136088.78
8/1/24,2024,8,Europe,EU,Italy,HMI,AI Adoption,68.3,1628151.08,542609.57
8/1/24,2024,8,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,76.8,771228.31,317497.26
8/1/24,2024,8,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,78.2,771228.31,253281.73
8/1/24,2024,8,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,73.5,771228.31,174864.5
8/1/24,2024,8,Asia Pacific,APAC,Australia,HMCA,AI Adoption,76.2,771228.31,25584.81
8/1/24,2024,8,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,62,309517.33,50317.77
8/1/24,2024,8,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,60.8,309517.33,202.16
8/1/24,2024,8,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,56.9,309517.33,108169.71
8/1/24,2024,8,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,62.8,309517.33,150827.7
8/1/24,2024,8,Asia Pacific,APAC,India,HMIL,Performance & Coverage,63.3,875846.05,110463.04
8/1/24,2024,8,Asia Pacific,APAC,India,HMIL,Quality Excellence,65.8,875846.05,207474.15
8/1/24,2024,8,Asia Pacific,APAC,India,HMIL,Data Infrastructure,64,875846.05,209260.31
8/1/24,2024,8,Asia Pacific,APAC,India,HMIL,AI Adoption,66.1,875846.05,348648.56
8/1/24,2024,8,Central & South America,CS,Brazil,HMB,Performance & Coverage,63.6,798853.37,549681.62
8/1/24,2024,8,Central & South America,CS,Brazil,HMB,Quality Excellence,60.9,798853.37,76528.58
8/1/24,2024,8,Central & South America,CS,Brazil,HMB,Data Infrastructure,69.4,798853.37,101428.12
8/1/24,2024,8,Central & South America,CS,Brazil,HMB,AI Adoption,66.9,798853.37,71215.06
9/1/24,2024,9,North America,NA,USA,HMA,Performance & Coverage,74.6,7012353.08,2830548.42
9/1/24,2024,9,North America,NA,USA,HMA,Quality Excellence,70.5,7012353.08,1099135.86
9/1/24,2024,9,North America,NA,USA,HMA,Data Infrastructure,78.4,7012353.08,2651286.64
9/1/24,2024,9,North America,NA,USA,HMA,AI Adoption,79.9,7012353.08,431382.16
9/1/24,2024,9,North America,NA,Canada,HAC,Performance & Coverage,73.5,1122514.02,476649.27
9/1/24,2024,9,North America,NA,Canada,HAC,Quality Excellence,70.9,1122514.02,63670.31
9/1/24,2024,9,North America,NA,Canada,HAC,Data Infrastructure,77.2,1122514.02,276499.22
9/1/24,2024,9,North America,NA,Canada,HAC,AI Adoption,73.6,1122514.02,305695.22
9/1/24,2024,9,North America,NA,Mexico,HMM,Performance & Coverage,61.2,542233.76,36802.86
9/1/24,2024,9,North America,NA,Mexico,HMM,Quality Excellence,65.8,542233.76,168302.76
9/1/24,2024,9,North America,NA,Mexico,HMM,Data Infrastructure,64.1,542233.76,267388.95
9/1/24,2024,9,North America,NA,Mexico,HMM,AI Adoption,64.8,542233.76,69739.19
9/1/24,2024,9,Europe,EU,Germany,HMD,Performance & Coverage,78.1,2503841.25,475590.32
9/1/24,2024,9,Europe,EU,Germany,HMD,Quality Excellence,78.7,2503841.25,1547416.72
9/1/24,2024,9,Europe,EU,Germany,HMD,Data Infrastructure,76.9,2503841.25,352468.13
9/1/24,2024,9,Europe,EU,Germany,HMD,AI Adoption,79.7,2503841.25,128366.07
9/1/24,2024,9,Europe,EU,United Kingdom,HMUK,Performance & Coverage,72.8,2223449.34,130091.18
9/1/24,2024,9,Europe,EU,United Kingdom,HMUK,Quality Excellence,77.5,2223449.34,486139.8
9/1/24,2024,9,Europe,EU,United Kingdom,HMUK,Data Infrastructure,75.5,2223449.34,410897.68
9/1/24,2024,9,Europe,EU,United Kingdom,HMUK,AI Adoption,81.1,2223449.34,1196320.67
9/1/24,2024,9,Europe,EU,France,HMF,Performance & Coverage,70.1,2200529.1,244403.62
9/1/24,2024,9,Europe,EU,France,HMF,Quality Excellence,74.8,2200529.1,697266.43
9/1/24,2024,9,Europe,EU,France,HMF,Data Infrastructure,70.9,2200529.1,371264.06
9/1/24,2024,9,Europe,EU,France,HMF,AI Adoption,71.3,2200529.1,887595
9/1/24,2024,9,Europe,EU,Spain,HMS,Performance & Coverage,66.5,1550350.3,55500.22
9/1/24,2024,9,Europe,EU,Spain,HMS,Quality Excellence,65.8,1550350.3,508920.79
9/1/24,2024,9,Europe,EU,Spain,HMS,Data Infrastructure,69.1,1550350.3,291469.16
9/1/24,2024,9,Europe,EU,Spain,HMS,AI Adoption,73.5,1550350.3,694460.14
9/1/24,2024,9,Europe,EU,Italy,HMI,Performance & Coverage,65.4,1608653.41,180880.82
9/1/24,2024,9,Europe,EU,Italy,HMI,Quality Excellence,73.6,1608653.41,1183105.42
9/1/24,2024,9,Europe,EU,Italy,HMI,Data Infrastructure,53.1,1608653.41,212008.42
9/1/24,2024,9,Europe,EU,Italy,HMI,AI Adoption,68.5,1608653.41,32658.74
9/1/24,2024,9,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,72.3,702738.99,433973.35
9/1/24,2024,9,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,75.4,702738.99,78144.52
9/1/24,2024,9,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,71.7,702738.99,95971.68
9/1/24,2024,9,Asia Pacific,APAC,Australia,HMCA,AI Adoption,72.1,702738.99,94649.43
9/1/24,2024,9,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,62.2,310030.21,106685.38
9/1/24,2024,9,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,57.6,310030.21,15882.09
9/1/24,2024,9,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,44.5,310030.21,56616.4
9/1/24,2024,9,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,51.4,310030.21,130846.33
9/1/24,2024,9,Asia Pacific,APAC,India,HMIL,Performance & Coverage,64.2,1092848.88,914661.56
9/1/24,2024,9,Asia Pacific,APAC,India,HMIL,Quality Excellence,68.4,1092848.88,30342.11
9/1/24,2024,9,Asia Pacific,APAC,India,HMIL,Data Infrastructure,51.4,1092848.88,50664.66
9/1/24,2024,9,Asia Pacific,APAC,India,HMIL,AI Adoption,70.4,1092848.88,97180.55
9/1/24,2024,9,Central & South America,CS,Brazil,HMB,Performance & Coverage,58.3,967703.27,229942.96
9/1/24,2024,9,Central & South America,CS,Brazil,HMB,Quality Excellence,59.7,967703.27,129047.46
9/1/24,2024,9,Central & South America,CS,Brazil,HMB,Data Infrastructure,59.2,967703.27,144377.75
9/1/24,2024,9,Central & South America,CS,Brazil,HMB,AI Adoption,51.6,967703.27,464335.1
10/1/24,2024,10,North America,NA,USA,HMA,Performance & Coverage,78.9,8602734.74,1770964.2
10/1/24,2024,10,North America,NA,USA,HMA,Quality Excellence,79.2,8602734.74,436678.14
10/1/24,2024,10,North America,NA,USA,HMA,Data Infrastructure,76.6,8602734.74,3893370.71
10/1/24,2024,10,North America,NA,USA,HMA,AI Adoption,79.8,8602734.74,2501721.69
10/1/24,2024,10,North America,NA,Canada,HAC,Performance & Coverage,73.4,1337458.93,251898.84
10/1/24,2024,10,North America,NA,Canada,HAC,Quality Excellence,75,1337458.93,117644.83
10/1/24,2024,10,North America,NA,Canada,HAC,Data Infrastructure,72.3,1337458.93,169910.11
10/1/24,2024,10,North America,NA,Canada,HAC,AI Adoption,73.7,1337458.93,798005.14
10/1/24,2024,10,North America,NA,Mexico,HMM,Performance & Coverage,60.2,731689.1,238730.76
10/1/24,2024,10,North America,NA,Mexico,HMM,Quality Excellence,65.7,731689.1,211850.93
10/1/24,2024,10,North America,NA,Mexico,HMM,Data Infrastructure,70.5,731689.1,87463.42
10/1/24,2024,10,North America,NA,Mexico,HMM,AI Adoption,70.4,731689.1,193644
10/1/24,2024,10,Europe,EU,Germany,HMD,Performance & Coverage,81,3080319.57,816727.74
10/1/24,2024,10,Europe,EU,Germany,HMD,Quality Excellence,73.5,3080319.57,1419036.68
10/1/24,2024,10,Europe,EU,Germany,HMD,Data Infrastructure,77.5,3080319.57,218372.09
10/1/24,2024,10,Europe,EU,Germany,HMD,AI Adoption,60.3,3080319.57,626183.06
10/1/24,2024,10,Europe,EU,United Kingdom,HMUK,Performance & Coverage,78.1,1982069.75,10289.78
10/1/24,2024,10,Europe,EU,United Kingdom,HMUK,Quality Excellence,77.6,1982069.75,893205.36
10/1/24,2024,10,Europe,EU,United Kingdom,HMUK,Data Infrastructure,71.9,1982069.75,950032.65
10/1/24,2024,10,Europe,EU,United Kingdom,HMUK,AI Adoption,76.6,1982069.75,128541.96
10/1/24,2024,10,Europe,EU,France,HMF,Performance & Coverage,57.9,1923292.26,116625.71
10/1/24,2024,10,Europe,EU,France,HMF,Quality Excellence,73,1923292.26,294404.28
10/1/24,2024,10,Europe,EU,France,HMF,Data Infrastructure,73.3,1923292.26,787966.76
10/1/24,2024,10,Europe,EU,France,HMF,AI Adoption,71.2,1923292.26,724295.51
10/1/24,2024,10,Europe,EU,Spain,HMS,Performance & Coverage,53.4,1456259.26,765755.14
10/1/24,2024,10,Europe,EU,Spain,HMS,Quality Excellence,71,1456259.26,565471.17
10/1/24,2024,10,Europe,EU,Spain,HMS,Data Infrastructure,66,1456259.26,38023.7
10/1/24,2024,10,Europe,EU,Spain,HMS,AI Adoption,66.1,1456259.26,87009.24
10/1/24,2024,10,Europe,EU,Italy,HMI,Performance & Coverage,72,1943388.76,135510.29
10/1/24,2024,10,Europe,EU,Italy,HMI,Quality Excellence,67.7,1943388.76,1019617.22
10/1/24,2024,10,Europe,EU,Italy,HMI,Data Infrastructure,71.4,1943388.76,29921.07
10/1/24,2024,10,Europe,EU,Italy,HMI,AI Adoption,67,1943388.76,758340.17
10/1/24,2024,10,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,72.3,727818.27,24681.76
10/1/24,2024,10,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,70.4,727818.27,208573.79
10/1/24,2024,10,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,78.7,727818.27,251038.05
10/1/24,2024,10,Asia Pacific,APAC,Australia,HMCA,AI Adoption,70.9,727818.27,243524.66
10/1/24,2024,10,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,62,343331.28,161979.6
10/1/24,2024,10,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,58.4,343331.28,28040.66
10/1/24,2024,10,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,57.2,343331.28,75370.1
10/1/24,2024,10,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,59.3,343331.28,77940.92
10/1/24,2024,10,Asia Pacific,APAC,India,HMIL,Performance & Coverage,67.7,1144405.48,339634.17
10/1/24,2024,10,Asia Pacific,APAC,India,HMIL,Quality Excellence,64.5,1144405.48,675268.15
10/1/24,2024,10,Asia Pacific,APAC,India,HMIL,Data Infrastructure,64.5,1144405.48,5608.64
10/1/24,2024,10,Asia Pacific,APAC,India,HMIL,AI Adoption,65.5,1144405.48,123894.51
10/1/24,2024,10,Central & South America,CS,Brazil,HMB,Performance & Coverage,62,919333.14,113655.21
10/1/24,2024,10,Central & South America,CS,Brazil,HMB,Quality Excellence,61,919333.14,604337.02
10/1/24,2024,10,Central & South America,CS,Brazil,HMB,Data Infrastructure,58.2,919333.14,20024.47
10/1/24,2024,10,Central & South America,CS,Brazil,HMB,AI Adoption,66.6,919333.14,181316.45
11/1/24,2024,11,North America,NA,USA,HMA,Performance & Coverage,79.3,9029015.41,1996943.54
11/1/24,2024,11,North America,NA,USA,HMA,Quality Excellence,64.5,9029015.41,1345791.37
11/1/24,2024,11,North America,NA,USA,HMA,Data Infrastructure,77.4,9029015.41,445478.68
11/1/24,2024,11,North America,NA,USA,HMA,AI Adoption,83,9029015.41,5240801.82
11/1/24,2024,11,North America,NA,Canada,HAC,Performance & Coverage,73.3,1432866.13,55626.63
11/1/24,2024,11,North America,NA,Canada,HAC,Quality Excellence,68.4,1432866.13,107646.34
11/1/24,2024,11,North America,NA,Canada,HAC,Data Infrastructure,74.8,1432866.13,702882.43
11/1/24,2024,11,North America,NA,Canada,HAC,AI Adoption,75,1432866.13,566710.72
11/1/24,2024,11,North America,NA,Mexico,HMM,Performance & Coverage,60.5,595122.62,23267.6
11/1/24,2024,11,North America,NA,Mexico,HMM,Quality Excellence,63.4,296921.69,296921.69
11/1/24,2024,11,North America,NA,Mexico,HMM,Data Infrastructure,59.9,173110.35,173110.35
11/1/24,2024,11,North America,NA,Mexico,HMM,AI Adoption,63.3,101822.98,101822.98
11/1/24,2024,11,Europe,EU,Germany,HMD,Performance & Coverage,73.7,3726987.78,1276664.7
11/1/24,2024,11,Europe,EU,Germany,HMD,Quality Excellence,60.9,3726987.78,440635.33
11/1/24,2024,11,Europe,EU,Germany,HMD,Data Infrastructure,76.9,3726987.78,783296.23
11/1/24,2024,11,Europe,EU,Germany,HMD,AI Adoption,78.4,3726987.78,1226391.52
11/1/24,2024,11,Europe,EU,United Kingdom,HMUK,Performance & Coverage,77,2519247.64,105891.16
11/1/24,2024,11,Europe,EU,United Kingdom,HMUK,Quality Excellence,72.9,2519247.64,116123.67
11/1/24,2024,11,Europe,EU,United Kingdom,HMUK,Data Infrastructure,76.7,2519247.64,1439840.93
11/1/24,2024,11,Europe,EU,United Kingdom,HMUK,AI Adoption,75.8,2519247.64,857391.89
11/1/24,2024,11,Europe,EU,France,HMF,Performance & Coverage,70.3,2155473.32,101286.56
11/1/24,2024,11,Europe,EU,France,HMF,Quality Excellence,71.9,2155473.32,249632.33
11/1/24,2024,11,Europe,EU,France,HMF,Data Infrastructure,72.1,2155473.32,1467320.33
11/1/24,2024,11,Europe,EU,France,HMF,AI Adoption,68.7,2155473.32,337234.1
11/1/24,2024,11,Europe,EU,Spain,HMS,Performance & Coverage,67,1945658,239555.14
11/1/24,2024,11,Europe,EU,Spain,HMS,Quality Excellence,71.7,1945658,227726.16
11/1/24,2024,11,Europe,EU,Spain,HMS,Data Infrastructure,72.2,1945658,647992.38
11/1/24,2024,11,Europe,EU,Spain,HMS,AI Adoption,68.7,1945658,830384.33
11/1/24,2024,11,Europe,EU,Italy,HMI,Performance & Coverage,68.9,2152173.5,2080051.22
11/1/24,2024,11,Europe,EU,Italy,HMI,Quality Excellence,68.5,2152173.5,9163.11
11/1/24,2024,11,Europe,EU,Italy,HMI,Data Infrastructure,67.9,2152173.5,48506.86
11/1/24,2024,11,Europe,EU,Italy,HMI,AI Adoption,70.5,2152173.5,14452.32
11/1/24,2024,11,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,73.2,826275.22,229436.73
11/1/24,2024,11,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,69.8,826275.22,126657.92
11/1/24,2024,11,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,69.8,826275.22,260892.76
11/1/24,2024,11,Asia Pacific,APAC,Australia,HMCA,AI Adoption,71,826275.22,209287.8
11/1/24,2024,11,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,53.2,346609.83,69724.42
11/1/24,2024,11,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,38.7,346609.83,188316.99
11/1/24,2024,11,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,60.6,346609.83,3849.87
11/1/24,2024,11,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,54.9,346609.83,84718.56
11/1/24,2024,11,Asia Pacific,APAC,India,HMIL,Performance & Coverage,68.5,1049201.08,763768.15
11/1/24,2024,11,Asia Pacific,APAC,India,HMIL,Quality Excellence,60.9,1049201.08,2805.32
11/1/24,2024,11,Asia Pacific,APAC,India,HMIL,Data Infrastructure,70.8,1049201.08,270062.97
11/1/24,2024,11,Asia Pacific,APAC,India,HMIL,AI Adoption,67.2,1049201.08,12564.64
11/1/24,2024,11,Central & South America,CS,Brazil,HMB,Performance & Coverage,66.5,868537.03,182874.16
11/1/24,2024,11,Central & South America,CS,Brazil,HMB,Quality Excellence,61.2,868537.03,66045.29
11/1/24,2024,11,Central & South America,CS,Brazil,HMB,Data Infrastructure,59,868537.03,241892.21
11/1/24,2024,11,Central & South America,CS,Brazil,HMB,AI Adoption,62,868537.03,377725.37
12/1/24,2024,12,North America,NA,USA,HMA,Performance & Coverage,81.6,10700546.51,3051567.36
12/1/24,2024,12,North America,NA,USA,HMA,Quality Excellence,83.6,10700546.51,1166749.74
12/1/24,2024,12,North America,NA,USA,HMA,Data Infrastructure,82.2,10700546.51,941130.83
12/1/24,2024,12,North America,NA,USA,HMA,AI Adoption,75.2,10700546.51,5541098.58
12/1/24,2024,12,North America,NA,Canada,HAC,Performance & Coverage,67.5,1297439.79,773307.6
12/1/24,2024,12,North America,NA,Canada,HAC,Quality Excellence,75.2,1297439.79,12229.4
12/1/24,2024,12,North America,NA,Canada,HAC,Data Infrastructure,74.1,1297439.79,157347.24
12/1/24,2024,12,North America,NA,Canada,HAC,AI Adoption,71.8,1297439.79,354555.55
12/1/24,2024,12,North America,NA,Mexico,HMM,Performance & Coverage,61.7,805115.1,253126.63
12/1/24,2024,12,North America,NA,Mexico,HMM,Quality Excellence,68.6,805115.1,430565.69
12/1/24,2024,12,North America,NA,Mexico,HMM,Data Infrastructure,64.6,805115.1,82886.71
12/1/24,2024,12,North America,NA,Mexico,HMM,AI Adoption,67.9,805115.1,38536.07
12/1/24,2024,12,Europe,EU,Germany,HMD,Performance & Coverage,81.5,3383807.29,1489441.36
12/1/24,2024,12,Europe,EU,Germany,HMD,Quality Excellence,83,3383807.29,273062.43
12/1/24,2024,12,Europe,EU,Germany,HMD,Data Infrastructure,82.1,3383807.29,901777.68
12/1/24,2024,12,Europe,EU,Germany,HMD,AI Adoption,80.2,3383807.29,719525.81
12/1/24,2024,12,Europe,EU,United Kingdom,HMUK,Performance & Coverage,59,3026718.41,149760.1
12/1/24,2024,12,Europe,EU,United Kingdom,HMUK,Quality Excellence,75.3,3026718.41,881905.23
12/1/24,2024,12,Europe,EU,United Kingdom,HMUK,Data Infrastructure,75.9,3026718.41,1677226.16
12/1/24,2024,12,Europe,EU,United Kingdom,HMUK,AI Adoption,74.2,3026718.41,317826.92
12/1/24,2024,12,Europe,EU,France,HMF,Performance & Coverage,67.3,2981447.66,365729.61
12/1/24,2024,12,Europe,EU,France,HMF,Quality Excellence,55.4,2981447.66,96668.26
12/1/24,2024,12,Europe,EU,France,HMF,Data Infrastructure,67.7,2981447.66,1428569.7
12/1/24,2024,12,Europe,EU,France,HMF,AI Adoption,54.3,2981447.66,1090480.09
12/1/24,2024,12,Europe,EU,Spain,HMS,Performance & Coverage,70.4,1869744.13,359771.34
12/1/24,2024,12,Europe,EU,Spain,HMS,Quality Excellence,69.6,1869744.13,480551.5
12/1/24,2024,12,Europe,EU,Spain,HMS,Data Infrastructure,67.1,1869744.13,120121.81
12/1/24,2024,12,Europe,EU,Spain,HMS,AI Adoption,74.9,1869744.13,909299.47
12/1/24,2024,12,Europe,EU,Italy,HMI,Performance & Coverage,64.6,2398118.08,12264.22
12/1/24,2024,12,Europe,EU,Italy,HMI,Quality Excellence,69.2,2398118.08,369283.82
12/1/24,2024,12,Europe,EU,Italy,HMI,Data Infrastructure,78.1,2398118.08,144326.7
12/1/24,2024,12,Europe,EU,Italy,HMI,AI Adoption,68,2398118.08,1872243.35
12/1/24,2024,12,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,74,850215.89,46027.51
12/1/24,2024,12,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,74.5,850215.89,79338.6
12/1/24,2024,12,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,71.8,850215.89,19677.65
12/1/24,2024,12,Asia Pacific,APAC,Australia,HMCA,AI Adoption,70.5,850215.89,705172.13
12/1/24,2024,12,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,60.2,413432.75,215246.11
12/1/24,2024,12,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,57.2,413432.75,61368.05
12/1/24,2024,12,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,55.5,413432.75,50737.61
12/1/24,2024,12,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,60.8,413432.75,86080.98
12/1/24,2024,12,Asia Pacific,APAC,India,HMIL,Performance & Coverage,53.3,1080606.24,153239.65
12/1/24,2024,12,Asia Pacific,APAC,India,HMIL,Quality Excellence,60.5,1080606.24,608712.88
12/1/24,2024,12,Asia Pacific,APAC,India,HMIL,Data Infrastructure,66,1080606.24,308079.38
12/1/24,2024,12,Asia Pacific,APAC,India,HMIL,AI Adoption,63.1,1080606.24,10574.33
12/1/24,2024,12,Central & South America,CS,Brazil,HMB,Performance & Coverage,62.8,1307979.22,727471.6
12/1/24,2024,12,Central & South America,CS,Brazil,HMB,Quality Excellence,65.4,1307979.22,339571.11
12/1/24,2024,12,Central & South America,CS,Brazil,HMB,Data Infrastructure,64.1,1307979.22,53458.13
12/1/24,2024,12,Central & South America,CS,Brazil,HMB,AI Adoption,64.7,1307979.22,187478.39
1/1/25,2025,1,North America,NA,USA,HMA,Performance & Coverage,81,10843304.98,251006.54
1/1/25,2025,1,North America,NA,USA,HMA,Quality Excellence,81.3,10843304.98,6884475.51
1/1/25,2025,1,North America,NA,USA,HMA,Data Infrastructure,76.5,10843304.98,516682.33
1/1/25,2025,1,North America,NA,USA,HMA,AI Adoption,78.9,10843304.98,3191140.59
1/1/25,2025,1,North America,NA,Canada,HAC,Performance & Coverage,59.9,1553385.64,515749.28
1/1/25,2025,1,North America,NA,Canada,HAC,Quality Excellence,68.2,1553385.64,291299.44
1/1/25,2025,1,North America,NA,Canada,HAC,Data Infrastructure,69.2,1553385.64,261357.22
1/1/25,2025,1,North America,NA,Canada,HAC,AI Adoption,75.2,1553385.64,484979.7
1/1/25,2025,1,North America,NA,Mexico,HMM,Performance & Coverage,64.9,845218.22,295833.61
1/1/25,2025,1,North America,NA,Mexico,HMM,Quality Excellence,64.9,845218.22,199340.97
1/1/25,2025,1,North America,NA,Mexico,HMM,Data Infrastructure,63,845218.22,240208.63
1/1/25,2025,1,North America,NA,Mexico,HMM,AI Adoption,51.3,845218.22,109835.01
1/1/25,2025,1,Europe,EU,Germany,HMD,Performance & Coverage,63.5,4819702.7,382611.05
1/1/25,2025,1,Europe,EU,Germany,HMD,Quality Excellence,84.9,4819702.7,3047906.23
1/1/25,2025,1,Europe,EU,Germany,HMD,Data Infrastructure,77.6,4819702.7,1354865.91
1/1/25,2025,1,Europe,EU,Germany,HMD,AI Adoption,68.7,4819702.7,34319.52
1/1/25,2025,1,Europe,EU,United Kingdom,HMUK,Performance & Coverage,78.1,3398180.81,2665740.75
1/1/25,2025,1,Europe,EU,United Kingdom,HMUK,Quality Excellence,75.6,3398180.81,46301.61
1/1/25,2025,1,Europe,EU,United Kingdom,HMUK,Data Infrastructure,77.1,3398180.81,87540.48
1/1/25,2025,1,Europe,EU,United Kingdom,HMUK,AI Adoption,80.9,3398180.81,598597.95
1/1/25,2025,1,Europe,EU,France,HMF,Performance & Coverage,69.9,3180538.82,1409236.32
1/1/25,2025,1,Europe,EU,France,HMF,Quality Excellence,73.7,3180538.82,232865.85
1/1/25,2025,1,Europe,EU,France,HMF,Data Infrastructure,74.1,3180538.82,1341075.65
1/1/25,2025,1,Europe,EU,France,HMF,AI Adoption,74.8,3180538.82,197360.99
1/1/25,2025,1,Europe,EU,Spain,HMS,Performance & Coverage,69.4,2458273.65,1585961.91
1/1/25,2025,1,Europe,EU,Spain,HMS,Quality Excellence,75.8,2458273.65,322675.16
1/1/25,2025,1,Europe,EU,Spain,HMS,Data Infrastructure,71.2,2458273.65,378686.45
1/1/25,2025,1,Europe,EU,Spain,HMS,AI Adoption,68.1,2458273.65,170950.13
1/1/25,2025,1,Europe,EU,Italy,HMI,Performance & Coverage,72.1,2271958.66,560967.71
1/1/25,2025,1,Europe,EU,Italy,HMI,Quality Excellence,70.1,2271958.66,1422543.79
1/1/25,2025,1,Europe,EU,Italy,HMI,Data Infrastructure,58.3,2271958.66,4326.72
1/1/25,2025,1,Europe,EU,Italy,HMI,AI Adoption,68.9,2271958.66,284120.44
1/1/25,2025,1,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,68.1,1029013.79,587796.27
1/1/25,2025,1,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,61.8,1029013.79,22526.84
1/1/25,2025,1,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,72,1029013.79,59618.31
1/1/25,2025,1,Asia Pacific,APAC,Australia,HMCA,AI Adoption,77.1,1029013.79,359072.36
1/1/25,2025,1,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,59.7,410955.54,59944
1/1/25,2025,1,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,56.8,410955.54,241106.36
1/1/25,2025,1,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,56,410955.54,22767.18
1/1/25,2025,1,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,64.2,410955.54,87138
1/1/25,2025,1,Asia Pacific,APAC,India,HMIL,Performance & Coverage,68.9,1040883.34,586156.36
1/1/25,2025,1,Asia Pacific,APAC,India,HMIL,Quality Excellence,67.9,1040883.34,66764
1/1/25,2025,1,Asia Pacific,APAC,India,HMIL,Data Infrastructure,71.7,1040883.34,188221.96
1/1/25,2025,1,Asia Pacific,APAC,India,HMIL,AI Adoption,72.6,1040883.34,199741.01
1/1/25,2025,1,Central & South America,CS,Brazil,HMB,Performance & Coverage,65.8,1522697.15,1040009.49
1/1/25,2025,1,Central & South America,CS,Brazil,HMB,Quality Excellence,68.5,1522697.15,225641.64
1/1/25,2025,1,Central & South America,CS,Brazil,HMB,Data Infrastructure,51.5,1522697.15,69391.98
1/1/25,2025,1,Central & South America,CS,Brazil,HMB,AI Adoption,65.4,1522697.15,187654.05
2/1/25,2025,2,North America,NA,USA,HMA,Performance & Coverage,84.3,10782008.27,5690864.23
2/1/25,2025,2,North America,NA,USA,HMA,Quality Excellence,69,10782008.27,1525380.49
2/1/25,2025,2,North America,NA,USA,HMA,Data Infrastructure,70.8,10782008.27,1855949.07
2/1/25,2025,2,North America,NA,USA,HMA,AI Adoption,81.5,10782008.27,1709814.47
2/1/25,2025,2,North America,NA,Canada,HAC,Performance & Coverage,76.9,1675318.46,155347.65
2/1/25,2025,2,North America,NA,Canada,HAC,Quality Excellence,75.3,1675318.46,130210.18
2/1/25,2025,2,North America,NA,Canada,HAC,Data Infrastructure,76.9,1675318.46,1319796.78
2/1/25,2025,2,North America,NA,Canada,HAC,AI Adoption,74.8,1675318.46,69963.85
2/1/25,2025,2,North America,NA,Mexico,HMM,Performance & Coverage,65.5,911026.42,86844.14
2/1/25,2025,2,North America,NA,Mexico,HMM,Quality Excellence,67.5,911026.42,90512.57
2/1/25,2025,2,North America,NA,Mexico,HMM,Data Infrastructure,66.5,911026.42,278119.33
2/1/25,2025,2,North America,NA,Mexico,HMM,AI Adoption,62.9,911026.42,455550.39
2/1/25,2025,2,Europe,EU,Germany,HMD,Performance & Coverage,76.3,4437755,1695793.54
2/1/25,2025,2,Europe,EU,Germany,HMD,Quality Excellence,74.9,4437755,438676.21
2/1/25,2025,2,Europe,EU,Germany,HMD,Data Infrastructure,82.5,4437755,1559711.37
2/1/25,2025,2,Europe,EU,Germany,HMD,AI Adoption,75.5,4437755,743573.88
2/1/25,2025,2,Europe,EU,United Kingdom,HMUK,Performance & Coverage,78.8,3475887.62,70121.04
2/1/25,2025,2,Europe,EU,United Kingdom,HMUK,Quality Excellence,71.2,3475887.62,2856051.96
2/1/25,2025,2,Europe,EU,United Kingdom,HMUK,Data Infrastructure,80.8,3475887.62,476465.51
2/1/25,2025,2,Europe,EU,United Kingdom,HMUK,AI Adoption,70.5,3475887.62,73249.11
2/1/25,2025,2,Europe,EU,France,HMF,Performance & Coverage,70.3,2597084.07,123423.55
2/1/25,2025,2,Europe,EU,France,HMF,Quality Excellence,70.7,2597084.07,1930018.26
2/1/25,2025,2,Europe,EU,France,HMF,Data Infrastructure,69.8,2597084.07,490536.17
2/1/25,2025,2,Europe,EU,France,HMF,AI Adoption,71.1,2597084.07,53106.09
2/1/25,2025,2,Europe,EU,Spain,HMS,Performance & Coverage,69,2516222.33,383024.14
2/1/25,2025,2,Europe,EU,Spain,HMS,Quality Excellence,67.4,2516222.33,268117.08
2/1/25,2025,2,Europe,EU,Spain,HMS,Data Infrastructure,68.7,2516222.33,1725896.1
2/1/25,2025,2,Europe,EU,Spain,HMS,AI Adoption,71.5,2516222.33,139185.02
2/1/25,2025,2,Europe,EU,Italy,HMI,Performance & Coverage,69.7,2906974.84,426235.7
2/1/25,2025,2,Europe,EU,Italy,HMI,Quality Excellence,72.9,2906974.84,526147.47
2/1/25,2025,2,Europe,EU,Italy,HMI,Data Infrastructure,67.1,2906974.84,479602.71
2/1/25,2025,2,Europe,EU,Italy,HMI,AI Adoption,64.7,2906974.84,1474988.97
2/1/25,2025,2,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,77.5,956387.58,521026.47
2/1/25,2025,2,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,77.3,956387.58,8576.73
2/1/25,2025,2,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,81.9,956387.58,61245.33
2/1/25,2025,2,Asia Pacific,APAC,Australia,HMCA,AI Adoption,72.5,956387.58,365539.05
2/1/25,2025,2,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,56,503671.58,66073.92
2/1/25,2025,2,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,56,503671.58,376321.18
2/1/25,2025,2,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,68,503671.58,43325.4
2/1/25,2025,2,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,61.6,503671.58,17951.08
2/1/25,2025,2,Asia Pacific,APAC,India,HMIL,Performance & Coverage,67.3,1315300.07,189869.06
2/1/25,2025,2,Asia Pacific,APAC,India,HMIL,Quality Excellence,53.5,1315300.07,214674.51
2/1/25,2025,2,Asia Pacific,APAC,India,HMIL,Data Infrastructure,70.3,1315300.07,666413.06
2/1/25,2025,2,Asia Pacific,APAC,India,HMIL,AI Adoption,69.9,1315300.07,244343.44
2/1/25,2025,2,Central & South America,CS,Brazil,HMB,Performance & Coverage,67.5,1549586.62,8465.6
2/1/25,2025,2,Central & South America,CS,Brazil,HMB,Quality Excellence,65.3,1549586.62,319905.32
2/1/25,2025,2,Central & South America,CS,Brazil,HMB,Data Infrastructure,62.4,1549586.62,585714.38
2/1/25,2025,2,Central & South America,CS,Brazil,HMB,AI Adoption,65.9,1549586.62,635501.32
3/1/25,2025,3,North America,NA,USA,HMA,Performance & Coverage,77.1,11034457.83,1083642.77
3/1/25,2025,3,North America,NA,USA,HMA,Quality Excellence,77.9,11034457.83,1381822.65
3/1/25,2025,3,North America,NA,USA,HMA,Data Infrastructure,78.6,11034457.83,6752250.19
3/1/25,2025,3,North America,NA,USA,HMA,AI Adoption,84.7,11034457.83,1816742.21
3/1/25,2025,3,North America,NA,Canada,HAC,Performance & Coverage,76.9,1910705.38,150588.22
3/1/25,2025,3,North America,NA,Canada,HAC,Quality Excellence,76.3,1910705.38,91725.07
3/1/25,2025,3,North America,NA,Canada,HAC,Data Infrastructure,78.7,1910705.38,356709.73
3/1/25,2025,3,North America,NA,Canada,HAC,AI Adoption,78.6,1910705.38,1311682.36
3/1/25,2025,3,North America,NA,Mexico,HMM,Performance & Coverage,65.1,996837.66,65461.6
3/1/25,2025,3,North America,NA,Mexico,HMM,Quality Excellence,63.1,996837.66,89386.47
3/1/25,2025,3,North America,NA,Mexico,HMM,Data Infrastructure,66.7,996837.66,584427.48
3/1/25,2025,3,North America,NA,Mexico,HMM,AI Adoption,60.1,996837.66,257562.1
3/1/25,2025,3,Europe,EU,Germany,HMD,Performance & Coverage,86.1,4214532.16,163628.38
3/1/25,2025,3,Europe,EU,Germany,HMD,Quality Excellence,80.2,4214532.16,408873.03
3/1/25,2025,3,Europe,EU,Germany,HMD,Data Infrastructure,79.8,4214532.16,814269.33
3/1/25,2025,3,Europe,EU,Germany,HMD,AI Adoption,76.9,4214532.16,2827761.42
3/1/25,2025,3,Europe,EU,United Kingdom,HMUK,Performance & Coverage,77.7,3757603.21,1251407.34
3/1/25,2025,3,Europe,EU,United Kingdom,HMUK,Quality Excellence,77.7,3757603.21,1104436.14
3/1/25,2025,3,Europe,EU,United Kingdom,HMUK,Data Infrastructure,81.3,3757603.21,995476.16
3/1/25,2025,3,Europe,EU,United Kingdom,HMUK,AI Adoption,76.7,3757603.21,406283.56
3/1/25,2025,3,Europe,EU,France,HMF,Performance & Coverage,75.7,3326025.04,529618.96
3/1/25,2025,3,Europe,EU,France,HMF,Quality Excellence,67.4,3326025.04,1965026.15
3/1/25,2025,3,Europe,EU,France,HMF,Data Infrastructure,74.5,3326025.04,414435.76
3/1/25,2025,3,Europe,EU,France,HMF,AI Adoption,78.4,3326025.04,416944.17
3/1/25,2025,3,Europe,EU,Spain,HMS,Performance & Coverage,69.3,2262450.54,1470048.12
3/1/25,2025,3,Europe,EU,Spain,HMS,Quality Excellence,67.8,2262450.54,1778.3
3/1/25,2025,3,Europe,EU,Spain,HMS,Data Infrastructure,66.6,2262450.54,484131.63
3/1/25,2025,3,Europe,EU,Spain,HMS,AI Adoption,67.7,2262450.54,306492.49
3/1/25,2025,3,Europe,EU,Italy,HMI,Performance & Coverage,71.4,2966349.61,262276.03
3/1/25,2025,3,Europe,EU,Italy,HMI,Quality Excellence,71.8,2966349.61,324547.12
3/1/25,2025,3,Europe,EU,Italy,HMI,Data Infrastructure,68.6,2966349.61,1357090.27
3/1/25,2025,3,Europe,EU,Italy,HMI,AI Adoption,67.5,2966349.61,1022436.19
3/1/25,2025,3,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,75.5,1158241.05,274809.64
3/1/25,2025,3,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,68.8,1158241.05,6852.22
3/1/25,2025,3,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,75.9,1158241.05,513460.48
3/1/25,2025,3,Asia Pacific,APAC,Australia,HMCA,AI Adoption,69.6,1158241.05,363118.71
3/1/25,2025,3,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,56.5,513495.86,76628.43
3/1/25,2025,3,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,55.1,513495.86,354474.14
3/1/25,2025,3,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,65.1,513495.86,47758.48
3/1/25,2025,3,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,56,513495.86,34634.82
3/1/25,2025,3,Asia Pacific,APAC,India,HMIL,Performance & Coverage,68.8,1466407.51,63984.07
3/1/25,2025,3,Asia Pacific,APAC,India,HMIL,Quality Excellence,66,1466407.51,551542.71
3/1/25,2025,3,Asia Pacific,APAC,India,HMIL,Data Infrastructure,67.4,1466407.51,385750.8
3/1/25,2025,3,Asia Pacific,APAC,India,HMIL,AI Adoption,69.3,1466407.51,465129.94
3/1/25,2025,3,Central & South America,CS,Brazil,HMB,Performance & Coverage,61.6,1208755.22,327253.53
3/1/25,2025,3,Central & South America,CS,Brazil,HMB,Quality Excellence,69,1208755.22,507109.37
3/1/25,2025,3,Central & South America,CS,Brazil,HMB,Data Infrastructure,65.9,1208755.22,348422.35
3/1/25,2025,3,Central & South America,CS,Brazil,HMB,AI Adoption,68,1208755.22,25969.97
4/1/25,2025,4,North America,NA,USA,HMA,Performance & Coverage,73.7,11605340.16,5889840.09
4/1/25,2025,4,North America,NA,USA,HMA,Quality Excellence,83.2,11605340.16,2107536.85
4/1/25,2025,4,North America,NA,USA,HMA,Data Infrastructure,80.8,11605340.16,1082795.42
4/1/25,2025,4,North America,NA,USA,HMA,AI Adoption,80.1,11605340.16,2525167.8
4/1/25,2025,4,North America,NA,Canada,HAC,Performance & Coverage,68.9,1802118.34,520570.5
4/1/25,2025,4,North America,NA,Canada,HAC,Quality Excellence,76.6,1802118.34,129812.74
4/1/25,2025,4,North America,NA,Canada,HAC,Data Infrastructure,77.1,1802118.34,882409.78
4/1/25,2025,4,North America,NA,Canada,HAC,AI Adoption,78,1802118.34,269325.33
4/1/25,2025,4,North America,NA,Mexico,HMM,Performance & Coverage,67.6,816422.24,51699.55
4/1/25,2025,4,North America,NA,Mexico,HMM,Quality Excellence,63.4,816422.24,404617.06
4/1/25,2025,4,North America,NA,Mexico,HMM,Data Infrastructure,64.8,816422.24,82029.17
4/1/25,2025,4,North America,NA,Mexico,HMM,AI Adoption,66,816422.24,278076.46
4/1/25,2025,4,Europe,EU,Germany,HMD,Performance & Coverage,73.6,4000101.49,530587.66
4/1/25,2025,4,Europe,EU,Germany,HMD,Quality Excellence,79.7,4000101.49,1368379.29
4/1/25,2025,4,Europe,EU,Germany,HMD,Data Infrastructure,79,4000101.49,438686.63
4/1/25,2025,4,Europe,EU,Germany,HMD,AI Adoption,79.2,4000101.49,1662447.92
4/1/25,2025,4,Europe,EU,United Kingdom,HMUK,Performance & Coverage,84.3,3542703.64,1692375.69
4/1/25,2025,4,Europe,EU,United Kingdom,HMUK,Quality Excellence,63.6,3542703.64,1412262.58
4/1/25,2025,4,Europe,EU,United Kingdom,HMUK,Data Infrastructure,77.7,3542703.64,169921.31
4/1/25,2025,4,Europe,EU,United Kingdom,HMUK,AI Adoption,78.8,3542703.64,268144.06
4/1/25,2025,4,Europe,EU,France,HMF,Performance & Coverage,72.4,2952762.3,169323.56
4/1/25,2025,4,Europe,EU,France,HMF,Quality Excellence,73.6,2952762.3,134112.61
4/1/25,2025,4,Europe,EU,France,HMF,Data Infrastructure,74.5,2952762.3,1073940.69
4/1/25,2025,4,Europe,EU,France,HMF,AI Adoption,69.8,2952762.3,1575385.45
4/1/25,2025,4,Europe,EU,Spain,HMS,Performance & Coverage,58,2529034.89,160890.69
4/1/25,2025,4,Europe,EU,Spain,HMS,Quality Excellence,69.1,2529034.89,261095.66
4/1/25,2025,4,Europe,EU,Spain,HMS,Data Infrastructure,71.4,2529034.89,730505.74
4/1/25,2025,4,Europe,EU,Spain,HMS,AI Adoption,66.7,2529034.89,1376542.79
4/1/25,2025,4,Europe,EU,Italy,HMI,Performance & Coverage,66.3,2711164.2,864232.21
4/1/25,2025,4,Europe,EU,Italy,HMI,Quality Excellence,63.8,2711164.2,411798.88
4/1/25,2025,4,Europe,EU,Italy,HMI,Data Infrastructure,72.4,2711164.2,146959.95
4/1/25,2025,4,Europe,EU,Italy,HMI,AI Adoption,70,2711164.2,1288173.16
4/1/25,2025,4,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,73.2,819965.93,576980.75
4/1/25,2025,4,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,72.6,819965.93,175024.1
4/1/25,2025,4,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,78.5,819965.93,33248.47
4/1/25,2025,4,Asia Pacific,APAC,Australia,HMCA,AI Adoption,75.4,819965.93,34712.6
4/1/25,2025,4,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,59.8,476371.65,219812.65
4/1/25,2025,4,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,48.3,476371.65,62014.8
4/1/25,2025,4,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,58.2,476371.65,28891.82
4/1/25,2025,4,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,59,476371.65,165652.38
4/1/25,2025,4,Asia Pacific,APAC,India,HMIL,Performance & Coverage,72.9,1276961.53,176159.67
4/1/25,2025,4,Asia Pacific,APAC,India,HMIL,Quality Excellence,74.7,1276961.53,394200.53
4/1/25,2025,4,Asia Pacific,APAC,India,HMIL,Data Infrastructure,69.1,1276961.53,561021.06
4/1/25,2025,4,Asia Pacific,APAC,India,HMIL,AI Adoption,68.7,1276961.53,145580.27
4/1/25,2025,4,Central & South America,CS,Brazil,HMB,Performance & Coverage,65.1,1457506.14,112781.4
4/1/25,2025,4,Central & South America,CS,Brazil,HMB,Quality Excellence,64.7,1457506.14,181976.65
4/1/25,2025,4,Central & South America,CS,Brazil,HMB,Data Infrastructure,65,1457506.14,1029564.23
4/1/25,2025,4,Central & South America,CS,Brazil,HMB,AI Adoption,65.1,1457506.14,133183.86
5/1/25,2025,5,North America,NA,USA,HMA,Performance & Coverage,81.2,11259435.8,5862170.45
5/1/25,2025,5,North America,NA,USA,HMA,Quality Excellence,82.5,11259435.8,2457446.65
5/1/25,2025,5,North America,NA,USA,HMA,Data Infrastructure,80,11259435.8,2893859.79
5/1/25,2025,5,North America,NA,USA,HMA,AI Adoption,78.6,11259435.8,45958.9
5/1/25,2025,5,North America,NA,Canada,HAC,Performance & Coverage,76.9,1181510.28,373700.82
5/1/25,2025,5,North America,NA,Canada,HAC,Quality Excellence,72.6,1181510.28,410817.88
5/1/25,2025,5,North America,NA,Canada,HAC,Data Infrastructure,70.5,1181510.28,326156.22
5/1/25,2025,5,North America,NA,Canada,HAC,AI Adoption,78.5,1181510.28,70835.36
5/1/25,2025,5,North America,NA,Mexico,HMM,Performance & Coverage,60.7,890910.77,430943.18
5/1/25,2025,5,North America,NA,Mexico,HMM,Quality Excellence,66.6,890910.77,50806.9
5/1/25,2025,5,North America,NA,Mexico,HMM,Data Infrastructure,68.7,890910.77,320418
5/1/25,2025,5,North America,NA,Mexico,HMM,AI Adoption,62.6,890910.77,88742.69
5/1/25,2025,5,Europe,EU,Germany,HMD,Performance & Coverage,81.6,4019178.78,1137242.95
5/1/25,2025,5,Europe,EU,Germany,HMD,Quality Excellence,78.4,4019178.78,1275640.48
5/1/25,2025,5,Europe,EU,Germany,HMD,Data Infrastructure,76,4019178.78,1502849.28
5/1/25,2025,5,Europe,EU,Germany,HMD,AI Adoption,78.7,4019178.78,103446.07
5/1/25,2025,5,Europe,EU,United Kingdom,HMUK,Performance & Coverage,79.3,3384769.92,68878.51
5/1/25,2025,5,Europe,EU,United Kingdom,HMUK,Quality Excellence,65.3,3384769.92,2041982.24
5/1/25,2025,5,Europe,EU,United Kingdom,HMUK,Data Infrastructure,81.4,3384769.92,641525.53
5/1/25,2025,5,Europe,EU,United Kingdom,HMUK,AI Adoption,80.8,3384769.92,632383.64
5/1/25,2025,5,Europe,EU,France,HMF,Performance & Coverage,71.1,2994664.14,535136.2
5/1/25,2025,5,Europe,EU,France,HMF,Quality Excellence,69.2,2994664.14,1528610.02
5/1/25,2025,5,Europe,EU,France,HMF,Data Infrastructure,71.7,2994664.14,92110.26
5/1/25,2025,5,Europe,EU,France,HMF,AI Adoption,74.2,2994664.14,838807.65
5/1/25,2025,5,Europe,EU,Spain,HMS,Performance & Coverage,74.1,2165945.14,653400.4
5/1/25,2025,5,Europe,EU,Spain,HMS,Quality Excellence,63.7,2165945.14,658252.71
5/1/25,2025,5,Europe,EU,Spain,HMS,Data Infrastructure,75.5,2165945.14,278210.37
5/1/25,2025,5,Europe,EU,Spain,HMS,AI Adoption,68.4,2165945.14,576081.66
5/1/25,2025,5,Europe,EU,Italy,HMI,Performance & Coverage,61.8,2619930.37,363227
5/1/25,2025,5,Europe,EU,Italy,HMI,Quality Excellence,71.9,2619930.37,910869.06
5/1/25,2025,5,Europe,EU,Italy,HMI,Data Infrastructure,78.1,2619930.37,980966.99
5/1/25,2025,5,Europe,EU,Italy,HMI,AI Adoption,76.7,2619930.37,364867.33
5/1/25,2025,5,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,76.7,1101628.44,18170.52
5/1/25,2025,5,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,74.1,1101628.44,115668.41
5/1/25,2025,5,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,73,1101628.44,252472.41
5/1/25,2025,5,Asia Pacific,APAC,Australia,HMCA,AI Adoption,77,1101628.44,715317.1
5/1/25,2025,5,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,60.8,474611.54,178529.95
5/1/25,2025,5,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,62.2,474611.54,121672.34
5/1/25,2025,5,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,63.2,474611.54,75868.32
5/1/25,2025,5,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,63.8,474611.54,98540.94
5/1/25,2025,5,Asia Pacific,APAC,India,HMIL,Performance & Coverage,69.9,1230392.25,534891.49
5/1/25,2025,5,Asia Pacific,APAC,India,HMIL,Quality Excellence,64.7,1230392.25,464273.74
5/1/25,2025,5,Asia Pacific,APAC,India,HMIL,Data Infrastructure,71.1,1230392.25,23348.38
5/1/25,2025,5,Asia Pacific,APAC,India,HMIL,AI Adoption,67.6,1230392.25,207878.63
5/1/25,2025,5,Central & South America,CS,Brazil,HMB,Performance & Coverage,63.4,1086335.19,452153.74
5/1/25,2025,5,Central & South America,CS,Brazil,HMB,Quality Excellence,60.9,1086335.19,278684.28
5/1/25,2025,5,Central & South America,CS,Brazil,HMB,Data Infrastructure,69.1,1086335.19,61954.82
5/1/25,2025,5,Central & South America,CS,Brazil,HMB,AI Adoption,52.5,1086335.19,293542.34
6/1/25,2025,6,North America,NA,USA,HMA,Performance & Coverage,81.7,10305053.32,4484611.79
6/1/25,2025,6,North America,NA,USA,HMA,Quality Excellence,80.6,10305053.32,193470.66
6/1/25,2025,6,North America,NA,USA,HMA,Data Infrastructure,81.9,10305053.32,295953.58
6/1/25,2025,6,North America,NA,USA,HMA,AI Adoption,73.4,10305053.32,5331017.29
6/1/25,2025,6,North America,NA,Canada,HAC,Performance & Coverage,81.1,1521874.71,742030.22
6/1/25,2025,6,North America,NA,Canada,HAC,Quality Excellence,73.6,1521874.71,169893.52
6/1/25,2025,6,North America,NA,Canada,HAC,Data Infrastructure,78.6,1521874.71,402093.28
6/1/25,2025,6,North America,NA,Canada,HAC,AI Adoption,80.6,1521874.71,207857.69
6/1/25,2025,6,North America,NA,Mexico,HMM,Performance & Coverage,64.9,766078.58,197323.12
6/1/25,2025,6,North America,NA,Mexico,HMM,Quality Excellence,66.8,766078.58,554711.66
6/1/25,2025,6,North America,NA,Mexico,HMM,Data Infrastructure,69.2,766078.58,13695.13
6/1/25,2025,6,North America,NA,Mexico,HMM,AI Adoption,66.3,766078.58,348.66
6/1/25,2025,6,Europe,EU,Germany,HMD,Performance & Coverage,75.1,3764818.67,201388.95
6/1/25,2025,6,Europe,EU,Germany,HMD,Quality Excellence,78.2,3764818.67,990114.93
6/1/25,2025,6,Europe,EU,Germany,HMD,Data Infrastructure,84.3,3764818.67,2354802.65
6/1/25,2025,6,Europe,EU,Germany,HMD,AI Adoption,77.1,3764818.67,218512.14
6/1/25,2025,6,Europe,EU,United Kingdom,HMUK,Performance & Coverage,81.3,3101797.59,1538491.78
6/1/25,2025,6,Europe,EU,United Kingdom,HMUK,Quality Excellence,83.2,3101797.59,522268.69
6/1/25,2025,6,Europe,EU,United Kingdom,HMUK,Data Infrastructure,75.4,3101797.59,90432.32
6/1/25,2025,6,Europe,EU,United Kingdom,HMUK,AI Adoption,83.9,3101797.59,950604.79
6/1/25,2025,6,Europe,EU,France,HMF,Performance & Coverage,72.3,2327445.34,140256.07
6/1/25,2025,6,Europe,EU,France,HMF,Quality Excellence,77.6,2327445.34,997041.6
6/1/25,2025,6,Europe,EU,France,HMF,Data Infrastructure,77.1,2327445.34,1173146.52
6/1/25,2025,6,Europe,EU,France,HMF,AI Adoption,77.2,2327445.34,17001.15
6/1/25,2025,6,Europe,EU,Spain,HMS,Performance & Coverage,71.4,2144403.29,317731.65
6/1/25,2025,6,Europe,EU,Spain,HMS,Quality Excellence,63.3,2144403.29,1350070.32
6/1/25,2025,6,Europe,EU,Spain,HMS,Data Infrastructure,72.2,2144403.29,196794.45
6/1/25,2025,6,Europe,EU,Spain,HMS,AI Adoption,75.3,2144403.29,279806.87
6/1/25,2025,6,Europe,EU,Italy,HMI,Performance & Coverage,74.6,2753318.77,718830.41
6/1/25,2025,6,Europe,EU,Italy,HMI,Quality Excellence,74.6,2753318.77,38688.76
6/1/25,2025,6,Europe,EU,Italy,HMI,Data Infrastructure,69.2,2753318.77,720675.13
6/1/25,2025,6,Europe,EU,Italy,HMI,AI Adoption,71,2753318.77,1275124.48
6/1/25,2025,6,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,65.6,848210.56,17430.96
6/1/25,2025,6,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,76.9,848210.56,191079.38
6/1/25,2025,6,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,76,848210.56,263398.96
6/1/25,2025,6,Asia Pacific,APAC,Australia,HMCA,AI Adoption,77.4,848210.56,376301.27
6/1/25,2025,6,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,64.1,388802.18,8931.45
6/1/25,2025,6,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,59.1,388802.18,237958.85
6/1/25,2025,6,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,45,388802.18,107828.4
6/1/25,2025,6,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,61.8,388802.18,34083.49
6/1/25,2025,6,Asia Pacific,APAC,India,HMIL,Performance & Coverage,68.2,1161683.67,372816.99
6/1/25,2025,6,Asia Pacific,APAC,India,HMIL,Quality Excellence,69.5,1161683.67,165124.22
6/1/25,2025,6,Asia Pacific,APAC,India,HMIL,Data Infrastructure,67.4,1161683.67,71050.04
6/1/25,2025,6,Asia Pacific,APAC,India,HMIL,AI Adoption,70.9,1161683.67,552692.43
6/1/25,2025,6,Central & South America,CS,Brazil,HMB,Performance & Coverage,68,1150875.11,352105.68
6/1/25,2025,6,Central & South America,CS,Brazil,HMB,Quality Excellence,65.2,1150875.11,381399.28
6/1/25,2025,6,Central & South America,CS,Brazil,HMB,Data Infrastructure,63.1,1150875.11,389751.69
6/1/25,2025,6,Central & South America,CS,Brazil,HMB,AI Adoption,69.7,1150875.11,27618.46
7/1/25,2025,7,North America,NA,USA,HMA,Performance & Coverage,82.9,7933976.44,7387703.57
7/1/25,2025,7,North America,NA,USA,HMA,Quality Excellence,81.5,7933976.44,201100.47
7/1/25,2025,7,North America,NA,USA,HMA,Data Infrastructure,81.3,7933976.44,326782.18
7/1/25,2025,7,North America,NA,USA,HMA,AI Adoption,77.9,7933976.44,18390.22
7/1/25,2025,7,North America,NA,Canada,HAC,Performance & Coverage,62.1,1323957.7,524715.3
7/1/25,2025,7,North America,NA,Canada,HAC,Quality Excellence,76.4,1323957.7,362937.02
7/1/25,2025,7,North America,NA,Canada,HAC,Data Infrastructure,71,1323957.7,111901
7/1/25,2025,7,North America,NA,Canada,HAC,AI Adoption,76,1323957.7,324404.39
7/1/25,2025,7,North America,NA,Mexico,HMM,Performance & Coverage,49.8,830075.86,311973.54
7/1/25,2025,7,North America,NA,Mexico,HMM,Quality Excellence,65.6,830075.86,307701.67
7/1/25,2025,7,North America,NA,Mexico,HMM,Data Infrastructure,68.9,830075.86,37025.42
7/1/25,2025,7,North America,NA,Mexico,HMM,AI Adoption,62.6,830075.86,173375.22
7/1/25,2025,7,Europe,EU,Germany,HMD,Performance & Coverage,85.7,3672033.83,267786.93
7/1/25,2025,7,Europe,EU,Germany,HMD,Quality Excellence,85.7,3672033.83,1430566.1
7/1/25,2025,7,Europe,EU,Germany,HMD,Data Infrastructure,75.9,3672033.83,454068.79
7/1/25,2025,7,Europe,EU,Germany,HMD,AI Adoption,80.6,3672033.83,1519612.01
7/1/25,2025,7,Europe,EU,United Kingdom,HMUK,Performance & Coverage,88.4,2808058.03,180845.97
7/1/25,2025,7,Europe,EU,United Kingdom,HMUK,Quality Excellence,73.5,2808058.03,366557.25
7/1/25,2025,7,Europe,EU,United Kingdom,HMUK,Data Infrastructure,64.1,2808058.03,1822376.8
7/1/25,2025,7,Europe,EU,United Kingdom,HMUK,AI Adoption,82.9,2808058.03,438278
7/1/25,2025,7,Europe,EU,France,HMF,Performance & Coverage,72.7,2075896.65,146944.68
7/1/25,2025,7,Europe,EU,France,HMF,Quality Excellence,75.2,2075896.65,14872.46
7/1/25,2025,7,Europe,EU,France,HMF,Data Infrastructure,72.2,2075896.65,1830466.86
7/1/25,2025,7,Europe,EU,France,HMF,AI Adoption,73.5,2075896.65,83612.65
7/1/25,2025,7,Europe,EU,Spain,HMS,Performance & Coverage,74,1625029.86,631426.05
7/1/25,2025,7,Europe,EU,Spain,HMS,Quality Excellence,77,1625029.86,25055.15
7/1/25,2025,7,Europe,EU,Spain,HMS,Data Infrastructure,67.1,1625029.86,492673.62
7/1/25,2025,7,Europe,EU,Spain,HMS,AI Adoption,72.9,1625029.86,475875.04
7/1/25,2025,7,Europe,EU,Italy,HMI,Performance & Coverage,72.9,1902268.7,164603.41
7/1/25,2025,7,Europe,EU,Italy,HMI,Quality Excellence,71.9,1902268.7,475066.24
7/1/25,2025,7,Europe,EU,Italy,HMI,Data Infrastructure,72.2,1902268.7,1011777.72
7/1/25,2025,7,Europe,EU,Italy,HMI,AI Adoption,72,1902268.7,250821.33
7/1/25,2025,7,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,74.5,940144.25,89311.72
7/1/25,2025,7,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,75.7,940144.25,31872.45
7/1/25,2025,7,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,77,940144.25,704843.64
7/1/25,2025,7,Asia Pacific,APAC,Australia,HMCA,AI Adoption,72.5,940144.25,114116.43
7/1/25,2025,7,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,62.6,299996.72,90305.54
7/1/25,2025,7,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,64.1,299996.72,134828.95
7/1/25,2025,7,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,64.1,299996.72,34919.75
7/1/25,2025,7,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,63.1,299996.72,39942.49
7/1/25,2025,7,Asia Pacific,APAC,India,HMIL,Performance & Coverage,70.4,1092498.93,150045.47
7/1/25,2025,7,Asia Pacific,APAC,India,HMIL,Quality Excellence,68.9,1092498.93,404935.06
7/1/25,2025,7,Asia Pacific,APAC,India,HMIL,Data Infrastructure,74.6,1092498.93,388766.35
7/1/25,2025,7,Asia Pacific,APAC,India,HMIL,AI Adoption,71.3,1092498.93,148752.05
7/1/25,2025,7,Central & South America,CS,Brazil,HMB,Performance & Coverage,72.7,918402.45,246739.58
7/1/25,2025,7,Central & South America,CS,Brazil,HMB,Quality Excellence,65.3,918402.45,156300.55
7/1/25,2025,7,Central & South America,CS,Brazil,HMB,Data Infrastructure,68.2,918402.45,92785.63
7/1/25,2025,7,Central & South America,CS,Brazil,HMB,AI Adoption,70.3,918402.45,422576.69
8/1/25,2025,8,North America,NA,USA,HMA,Performance & Coverage,83.4,8991325.57,4775148.83
8/1/25,2025,8,North America,NA,USA,HMA,Quality Excellence,80.8,8991325.57,3251807.34
8/1/25,2025,8,North America,NA,USA,HMA,Data Infrastructure,78.7,8991325.57,431181.49
8/1/25,2025,8,North America,NA,USA,HMA,AI Adoption,83.6,8991325.57,533187.91
8/1/25,2025,8,North America,NA,Canada,HAC,Performance & Coverage,74.1,1358900.61,529606.86
8/1/25,2025,8,North America,NA,Canada,HAC,Quality Excellence,76.7,1358900.61,74195.9
8/1/25,2025,8,North America,NA,Canada,HAC,Data Infrastructure,76.8,1358900.61,350823.3
8/1/25,2025,8,North America,NA,Canada,HAC,AI Adoption,62.5,1358900.61,404274.54
8/1/25,2025,8,North America,NA,Mexico,HMM,Performance & Coverage,68.7,635730.54,188884.42
8/1/25,2025,8,North America,NA,Mexico,HMM,Quality Excellence,72.8,635730.54,141343.46
8/1/25,2025,8,North America,NA,Mexico,HMM,Data Infrastructure,66.7,635730.54,174596.08
8/1/25,2025,8,North America,NA,Mexico,HMM,AI Adoption,68.8,635730.54,130906.58
8/1/25,2025,8,Europe,EU,Germany,HMD,Performance & Coverage,77,3317781.22,702926.41
8/1/25,2025,8,Europe,EU,Germany,HMD,Quality Excellence,79.6,3317781.22,555609.25
8/1/25,2025,8,Europe,EU,Germany,HMD,Data Infrastructure,85.4,3317781.22,1435739.19
8/1/25,2025,8,Europe,EU,Germany,HMD,AI Adoption,81.3,3317781.22,785945.35
8/1/25,2025,8,Europe,EU,United Kingdom,HMUK,Performance & Coverage,78.5,2387781.72,433663.72
8/1/25,2025,8,Europe,EU,United Kingdom,HMUK,Quality Excellence,81,2387781.72,287174.04
8/1/25,2025,8,Europe,EU,United Kingdom,HMUK,Data Infrastructure,84.4,2387781.72,976369.47
8/1/25,2025,8,Europe,EU,United Kingdom,HMUK,AI Adoption,77.6,2387781.72,690574.49
8/1/25,2025,8,Europe,EU,France,HMF,Performance & Coverage,72.3,2084135.87,366440.82
8/1/25,2025,8,Europe,EU,France,HMF,Quality Excellence,72.3,2084135.87,294115.35
8/1/25,2025,8,Europe,EU,France,HMF,Data Infrastructure,58.5,2084135.87,1181166.45
8/1/25,2025,8,Europe,EU,France,HMF,AI Adoption,74.9,2084135.87,242413.25
8/1/25,2025,8,Europe,EU,Spain,HMS,Performance & Coverage,70.4,1706959.04,294140.07
8/1/25,2025,8,Europe,EU,Spain,HMS,Quality Excellence,64.2,1706959.04,869587.77
8/1/25,2025,8,Europe,EU,Spain,HMS,Data Infrastructure,73.9,1706959.04,129279.95
8/1/25,2025,8,Europe,EU,Spain,HMS,AI Adoption,76.1,1706959.04,413951.26
8/1/25,2025,8,Europe,EU,Italy,HMI,Performance & Coverage,70.2,1628151.08,542330.94
8/1/25,2025,8,Europe,EU,Italy,HMI,Quality Excellence,72.7,1628151.08,407121.78
8/1/25,2025,8,Europe,EU,Italy,HMI,Data Infrastructure,71.8,1628151.08,136088.78
8/1/25,2025,8,Europe,EU,Italy,HMI,AI Adoption,68.3,1628151.08,542609.57
8/1/25,2025,8,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,76.8,771228.31,317497.26
8/1/25,2025,8,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,78.2,771228.31,253281.73
8/1/25,2025,8,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,73.5,771228.31,174864.5
8/1/25,2025,8,Asia Pacific,APAC,Australia,HMCA,AI Adoption,76.2,771228.31,25584.81
8/1/25,2025,8,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,62,309517.33,50317.77
8/1/25,2025,8,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,60.8,309517.33,202.16
8/1/25,2025,8,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,56.9,309517.33,108169.71
8/1/25,2025,8,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,62.8,309517.33,150827.7
8/1/25,2025,8,Asia Pacific,APAC,India,HMIL,Performance & Coverage,69,1035581.2,8370.1
8/1/25,2025,8,Asia Pacific,APAC,India,HMIL,Quality Excellence,67.5,1035581.2,163243.48
8/1/25,2025,8,Asia Pacific,APAC,India,HMIL,Data Infrastructure,67.2,1035581.2,92752.58
8/1/25,2025,8,Asia Pacific,APAC,India,HMIL,AI Adoption,73.4,1035581.2,771215.04
8/1/25,2025,8,Central & South America,CS,Brazil,HMB,Performance & Coverage,69.2,952813.24,346964.26
8/1/25,2025,8,Central & South America,CS,Brazil,HMB,Quality Excellence,65.2,952813.24,334097.32
8/1/25,2025,8,Central & South America,CS,Brazil,HMB,Data Infrastructure,71,952813.24,172265.5
8/1/25,2025,8,Central & South America,CS,Brazil,HMB,AI Adoption,65.8,952813.24,99486.16
9/1/25,2025,9,North America,NA,USA,HMA,Performance & Coverage,79.1,6460813.27,100265.74
9/1/25,2025,9,North America,NA,USA,HMA,Quality Excellence,86,6460813.27,235967.42
9/1/25,2025,9,North America,NA,USA,HMA,Data Infrastructure,83.3,6460813.27,5207716.28
9/1/25,2025,9,North America,NA,USA,HMA,AI Adoption,87.7,6460813.27,916863.84
9/1/25,2025,9,North America,NA,Canada,HAC,Performance & Coverage,78.9,1213177.29,240418.82
9/1/25,2025,9,North America,NA,Canada,HAC,Quality Excellence,81.8,1213177.29,626232.6
9/1/25,2025,9,North America,NA,Canada,HAC,Data Infrastructure,77.7,1213177.29,289205.73
9/1/25,2025,9,North America,NA,Canada,HAC,AI Adoption,76.9,1213177.29,57320.15
9/1/25,2025,9,North America,NA,Mexico,HMM,Performance & Coverage,70.1,616628.77,229608.31
9/1/25,2025,9,North America,NA,Mexico,HMM,Quality Excellence,70.6,616628.77,94056.1
9/1/25,2025,9,North America,NA,Mexico,HMM,Data Infrastructure,71,616628.77,159877.1
9/1/25,2025,9,North America,NA,Mexico,HMM,AI Adoption,68.6,616628.77,133087.26
9/1/25,2025,9,Europe,EU,Germany,HMD,Performance & Coverage,75.1,2960891.61,903015.28
9/1/25,2025,9,Europe,EU,Germany,HMD,Quality Excellence,76.8,2960891.61,1015242.08
9/1/25,2025,9,Europe,EU,Germany,HMD,Data Infrastructure,81.6,2960891.61,455138.69
9/1/25,2025,9,Europe,EU,Germany,HMD,AI Adoption,82.6,2960891.61,587495.55
9/1/25,2025,9,Europe,EU,United Kingdom,HMUK,Performance & Coverage,77.4,2600971.96,155510.83
9/1/25,2025,9,Europe,EU,United Kingdom,HMUK,Quality Excellence,80.7,2600971.96,564788.66
9/1/25,2025,9,Europe,EU,United Kingdom,HMUK,Data Infrastructure,85.8,2600971.96,520030.94
9/1/25,2025,9,Europe,EU,United Kingdom,HMUK,AI Adoption,83.1,2600971.96,1360641.52
9/1/25,2025,9,Europe,EU,France,HMF,Performance & Coverage,77.1,1701484.67,637311.34
9/1/25,2025,9,Europe,EU,France,HMF,Quality Excellence,74.1,1701484.67,267655.76
9/1/25,2025,9,Europe,EU,France,HMF,Data Infrastructure,73,1701484.67,234095.31
9/1/25,2025,9,Europe,EU,France,HMF,AI Adoption,70.4,1701484.67,562422.26
9/1/25,2025,9,Europe,EU,Spain,HMS,Performance & Coverage,73.1,1342046.99,585802.69
9/1/25,2025,9,Europe,EU,Spain,HMS,Quality Excellence,78.1,1342046.99,50612.98
9/1/25,2025,9,Europe,EU,Spain,HMS,Data Infrastructure,76.6,1342046.99,682453.14
9/1/25,2025,9,Europe,EU,Spain,HMS,AI Adoption,73.3,1342046.99,23178.19
9/1/25,2025,9,Europe,EU,Italy,HMI,Performance & Coverage,77.4,1864321.43,427502.76
9/1/25,2025,9,Europe,EU,Italy,HMI,Quality Excellence,72.2,1864321.43,790329.71
9/1/25,2025,9,Europe,EU,Italy,HMI,Data Infrastructure,73.1,1864321.43,527247.67
9/1/25,2025,9,Europe,EU,Italy,HMI,AI Adoption,71.4,1864321.43,119241.29
9/1/25,2025,9,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,82.3,673796.1,38020.58
9/1/25,2025,9,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,83.1,673796.1,55441.98
9/1/25,2025,9,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,77.3,673796.1,537623.2
9/1/25,2025,9,Asia Pacific,APAC,Australia,HMCA,AI Adoption,82.3,673796.1,42710.34
9/1/25,2025,9,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,63.2,257637.7,137531.6
9/1/25,2025,9,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,60.4,257637.7,50685.58
9/1/25,2025,9,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,62.3,257637.7,68538.44
9/1/25,2025,9,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,67.2,257637.7,882.08
9/1/25,2025,9,Asia Pacific,APAC,India,HMIL,Performance & Coverage,68.9,934500.41,249597.77
9/1/25,2025,9,Asia Pacific,APAC,India,HMIL,Quality Excellence,67.6,934500.41,81621.61
9/1/25,2025,9,Asia Pacific,APAC,India,HMIL,Data Infrastructure,68.6,934500.41,135432.62
9/1/25,2025,9,Asia Pacific,APAC,India,HMIL,AI Adoption,69.3,934500.41,467848.42
9/1/25,2025,9,Central & South America,CS,Brazil,HMB,Performance & Coverage,76.3,947158.44,49879.85
9/1/25,2025,9,Central & South America,CS,Brazil,HMB,Quality Excellence,69.2,947158.44,250994.63
9/1/25,2025,9,Central & South America,CS,Brazil,HMB,Data Infrastructure,63,947158.44,309857.42
9/1/25,2025,9,Central & South America,CS,Brazil,HMB,AI Adoption,51.6,967703.27,464335.1
10/1/25,2025,10,North America,NA,USA,HMA,Performance & Coverage,86.4,8899364.47,1350686.43
10/1/25,2025,10,North America,NA,USA,HMA,Quality Excellence,75.3,8899364.47,2017798.41
10/1/25,2025,10,North America,NA,USA,HMA,Data Infrastructure,87.9,8899364.47,4890452.19
10/1/25,2025,10,North America,NA,USA,HMA,AI Adoption,82.9,8899364.47,640427.44
10/1/25,2025,10,North America,NA,Canada,HAC,Performance & Coverage,80.7,1039090.06,176172.72
10/1/25,2025,10,North America,NA,Canada,HAC,Quality Excellence,73.9,1039090.06,64436.69
10/1/25,2025,10,North America,NA,Canada,HAC,Data Infrastructure,83.8,1039090.06,5003.89
10/1/25,2025,10,North America,NA,Canada,HAC,AI Adoption,82,1039090.06,793476.76
10/1/25,2025,10,North America,NA,Mexico,HMM,Performance & Coverage,70.5,661902.76,206561
10/1/25,2025,10,North America,NA,Mexico,HMM,Quality Excellence,65.3,661902.76,271914.89
10/1/25,2025,10,North America,NA,Mexico,HMM,Data Infrastructure,62.8,661902.76,133491.12
10/1/25,2025,10,North America,NA,Mexico,HMM,AI Adoption,66.7,661902.76,49935.75
10/1/25,2025,10,Europe,EU,Germany,HMD,Performance & Coverage,83.6,3146251.75,166436.09
10/1/25,2025,10,Europe,EU,Germany,HMD,Quality Excellence,84.6,3146251.75,1050649.94
10/1/25,2025,10,Europe,EU,Germany,HMD,Data Infrastructure,86,3146251.75,1107152.73
10/1/25,2025,10,Europe,EU,Germany,HMD,AI Adoption,86.8,3146251.75,822012.99
10/1/25,2025,10,Europe,EU,United Kingdom,HMUK,Performance & Coverage,83.4,2685623.92,2501649.31
10/1/25,2025,10,Europe,EU,United Kingdom,HMUK,Quality Excellence,75.7,2685623.92,51573.05
10/1/25,2025,10,Europe,EU,United Kingdom,HMUK,Data Infrastructure,78.3,2685623.92,40538
10/1/25,2025,10,Europe,EU,United Kingdom,HMUK,AI Adoption,82.2,2685623.92,91863.56
10/1/25,2025,10,Europe,EU,France,HMF,Performance & Coverage,74.1,1820649.7,960586.32
10/1/25,2025,10,Europe,EU,France,HMF,Quality Excellence,73.5,1820649.7,99301.69
10/1/25,2025,10,Europe,EU,France,HMF,Data Infrastructure,75.2,1820649.7,345769.2
10/1/25,2025,10,Europe,EU,France,HMF,AI Adoption,74.6,1820649.7,414992.48
10/1/25,2025,10,Europe,EU,Spain,HMS,Performance & Coverage,70.7,1674641.63,106787.95
10/1/25,2025,10,Europe,EU,Spain,HMS,Quality Excellence,73.8,1674641.63,332808.95
10/1/25,2025,10,Europe,EU,Spain,HMS,Data Infrastructure,73.4,1674641.63,1229898.76
10/1/25,2025,10,Europe,EU,Spain,HMS,AI Adoption,74.1,1674641.63,5145.98
10/1/25,2025,10,Europe,EU,Italy,HMI,Performance & Coverage,72,1941636.42,1111469.23
10/1/25,2025,10,Europe,EU,Italy,HMI,Quality Excellence,69.6,1941636.42,326951.05
10/1/25,2025,10,Europe,EU,Italy,HMI,Data Infrastructure,71.2,1941636.42,372789.56
10/1/25,2025,10,Europe,EU,Italy,HMI,AI Adoption,73.5,1941636.42,130426.58
10/1/25,2025,10,Asia Pacific,APAC,Australia,HMCA,Performance & Coverage,77.7,679900.5,158409.59
10/1/25,2025,10,Asia Pacific,APAC,Australia,HMCA,Quality Excellence,78.1,679900.5,62384.56
10/1/25,2025,10,Asia Pacific,APAC,Australia,HMCA,Data Infrastructure,77.4,679900.5,21670.01
10/1/25,2025,10,Asia Pacific,APAC,Australia,HMCA,AI Adoption,79.8,679900.5,437436.34
10/1/25,2025,10,Asia Pacific,APAC,Indonesia,HMID,Performance & Coverage,65.4,379128.27,4415.68
10/1/25,2025,10,Asia Pacific,APAC,Indonesia,HMID,Quality Excellence,63.7,379128.27,243883.1
10/1/25,2025,10,Asia Pacific,APAC,Indonesia,HMID,Data Infrastructure,66.7,379128.27,118865.6
10/1/25,2025,10,Asia Pacific,APAC,Indonesia,HMID,AI Adoption,62.2,379128.27,11963.9
10/1/25,2025,10,Asia Pacific,APAC,India,HMIL,Performance & Coverage,77.6,943498.89,437299.89
10/1/25,2025,10,Asia Pacific,APAC,India,HMIL,Quality Excellence,67.2,943498.89,407137.71
10/1/25,2025,10,Asia Pacific,APAC,India,HMIL,Data Infrastructure,56.4,943498.89,80353.62
10/1/25,2025,10,Asia Pacific,APAC,India,HMIL,AI Adoption,71.1,943498.89,18707.68
10/1/25,2025,10,Central & South America,CS,Brazil,HMB,Performance & Coverage,67.1,850368.82,271700.76
10/1/25,2025,10,Central & South America,CS,Brazil,HMB,Quality Excellence,73.4,850368.82,53930.59
10/1/25,2025,10,Central & South America,CS,Brazil,HMB,Data Infrastructure,66.7,850368.82,379650.96
10/1/25,2025,10,Central & South America,CS,Brazil,HMB,AI Adoption,74.4,850368.82,145086.51"""

COORDINATES = {
  'HMA': {'lat': 37.0902, 'lng': -95.7129}, # USA
  'HAC': {'lat': 56.1304, 'lng': -106.3468}, # Canada
  'HMM': {'lat': 23.6345, 'lng': -102.5528}, # Mexico
  'HMD': {'lat': 51.1657, 'lng': 10.4515}, # Germany
  'HMUK': {'lat': 55.3781, 'lng': -3.4360}, # UK
  'HMF': {'lat': 46.2276, 'lng': 2.2137}, # France
  'HMS': {'lat': 40.4637, 'lng': -3.7492}, # Spain
  'HMI': {'lat': 41.8719, 'lng': 12.5674}, # Italy
  'HMCA': {'lat': -25.2744, 'lng': 133.7751}, # Australia
  'HMID': {'lat': -0.7893, 'lng': 113.9213}, # Indonesia
  'HMIL': {'lat': 20.5937, 'lng': 78.9629}, # India
  'HMB': {'lat': -14.2350, 'lng': -51.9253}, # Brazil
}

# ==========================================
# 3. Data Processing Functions
# ==========================================
@st.cache_data
def load_and_process_data():
    # Read CSV from string
    df = pd.read_csv(io.StringIO(RAW_CSV_DATA))
    
    # Standardize Month Names for display
    df['Month_Name'] = df['Month'].apply(lambda x: datetime.date(1900, x, 1).strftime('%b'))
    df['Quarter'] = df['Month'].apply(lambda x: (x - 1) // 3 + 1)
    
    # Normalize Region name
    df['Region'] = df['Region'].replace('Central & South America', 'LATAM')
    
    return df

def get_aggregated_data(df, year, quarter, month, region_filter):
    # Filter
    filtered = df[df['Year'] == year].copy()
    if quarter != 'All':
        filtered = filtered[filtered['Quarter'] == int(quarter)]
    if month != 'All':
        month_num = datetime.datetime.strptime(month, '%b').month
        filtered = filtered[filtered['Month'] == month_num]
    if region_filter != 'All':
        filtered = filtered[filtered['Region'] == region_filter]
        
    if filtered.empty:
        return None, None

    # Group by NSC (Region Code) to get averages across filtered timeframe
    # We average the scores, but sum the budget? 
    # Note: Budget is likely per month. If viewing a quarter, we might want sum.
    # For simplicity in this dashboard view which mimics a snapshot, let's take mean of scores and sum of budget.
    
    # Pivot Framework scores first
    # The data is in long format: one row per framework. 
    # We need wide format: columns for Performance, Quality, etc.
    
    pivot_df = filtered.pivot_table(
        index=['NSC', 'FullName', 'Region', 'Country', 'Year', 'Month'], 
        columns='Framework', 
        values='Framework_Score'
    ).reset_index()
    
    # Merge back budget (Budget is repeated per framework row in raw data, so we take mean or max per month/nsc)
    budget_df = filtered.groupby(['NSC', 'Year', 'Month'])['Monthly_Total_Budget'].max().reset_index()
    pivot_df = pd.merge(pivot_df, budget_df, on=['NSC', 'Year', 'Month'])
    
    # Now aggregate over time (if multiple months selected)
    final_agg = pivot_df.groupby(['NSC', 'FullName', 'Region', 'Country']).agg({
        'Performance & Coverage': 'mean',
        'Quality Excellence': 'mean',
        'Data Infrastructure': 'mean',
        'AI Adoption': 'mean',
        'Monthly_Total_Budget': 'sum' # Sum budget over the period
    }).reset_index()
    
    # Calculate Overall Score
    final_agg['Overall_Score'] = final_agg[['Performance & Coverage', 'Quality Excellence', 'Data Infrastructure', 'AI Adoption']].mean(axis=1)
    
    # Add Coordinates
    final_agg['lat'] = final_agg['NSC'].map(lambda x: COORDINATES.get(x, {}).get('lat'))
    final_agg['lng'] = final_agg['NSC'].map(lambda x: COORDINATES.get(x, {}).get('lng'))
    
    # Calculate Global Stats
    global_stats = {
        'avg_score': final_agg['Overall_Score'].mean(),
        'total_budget': final_agg['Monthly_Total_Budget'].sum(),
        'top_performer': final_agg.loc[final_agg['Overall_Score'].idxmax()],
        'worst_performer': final_agg.loc[final_agg['Overall_Score'].idxmin()]
    }
    
    # Calculate MoM Change (approximate using previous period if available, or just 0 for simplicity in this static demo)
    # In a real app with full history, we'd calculate this dynamically. 
    # Here we will simulate or set to 0 if not straightforward.
    global_stats['mom_change'] = 2.5 # Placeholder trend
    
    return final_agg, global_stats

def get_trend_data(df, region_filter):
    # For Trend Chart: Group by Date (Year-Month)
    filtered = df.copy()
    if region_filter != 'All':
        filtered = filtered[filtered['Region'] == region_filter]
        
    # Pivot to get average overall score per date
    daily = filtered.groupby(['Year', 'Month', 'NSC'])['Framework_Score'].mean().reset_index()
    
    # Global Average Trend
    trend = daily.groupby(['Year', 'Month'])['Framework_Score'].mean().reset_index()
    trend['Date'] = pd.to_datetime(trend[['Year', 'Month']].assign(DAY=1))
    
    return trend.sort_values('Date')

# ==========================================
# 4. UI: Sidebar Filters
# ==========================================
df_raw = load_and_process_data()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/44/Hyundai_Motor_Company_logo.svg", width=150)
    st.title("Dashboard Controls")
    
    # API Key Input
    api_key = st.text_input("Google Gemini API Key", type="password", help="Enter key for AI Consultant features")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)

    st.divider()
    
    # Filters
    available_years = sorted(df_raw['Year'].unique(), reverse=True)
    year = st.selectbox("Year", available_years, index=0)
    
    quarter = st.selectbox("Quarter", ["All", "1", "2", "3", "4"], index=0)
    
    # Filter months based on selection
    month_options = ["All"] + list(df_raw[df_raw['Year'] == year]['Month_Name'].unique())
    if quarter != "All":
        # Simple quarter logic logic
        q_months = {
            "1": ["Jan", "Feb", "Mar"], "2": ["Apr", "May", "Jun"],
            "3": ["Jul", "Aug", "Sep"], "4": ["Oct", "Nov", "Dec"]
        }
        month_options = ["All"] + [m for m in month_options if m in q_months[quarter]]
        
    month = st.selectbox("Month", month_options, index=len(month_options)-1 if "Oct" in month_options else 0)
    
    region = st.selectbox("Region", ["All"] + sorted(df_raw['Region'].unique().tolist()))

# ==========================================
# 5. Main Layout & Logic
# ==========================================

current_data, stats = get_aggregated_data(df_raw, year, quarter, month, region)

if current_data is None:
    st.error("No data available for the selected filters.")
    st.stop()

# --- Row 1: KPI Cards ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"{region if region != 'All' else 'Global'} Avg Score", 
        value=f"{stats['avg_score']:.1f}", 
        delta=f"{stats['mom_change']}%"
    )
with col2:
    st.metric(
        label="Top Performer", 
        value=stats['top_performer']['NSC'],
        delta=f"Score: {stats['top_performer']['Overall_Score']:.1f}"
    )
with col3:
    st.metric(
        label="Needs Attention", 
        value=stats['worst_performer']['NSC'],
        delta=f"Score: {stats['worst_performer']['Overall_Score']:.1f}",
        delta_color="inverse"
    )
with col4:
    # Format budget
    budget_formatted = f"${stats['total_budget']/1_000_000:.1f}M"
    st.metric(
        label="Total Media Budget", 
        value=budget_formatted
    )

# --- Row 2: Map & AI Consultant ---
col_map, col_ai = st.columns([2, 1])

with col_map:
    st.subheader("🌍 Global Status Map")
    
    # Pydeck Map
    # Color logic: Blue for high, Red for low
    def get_color(score):
        if score >= 80: return [0, 44, 95, 200] # Hyundai Dark Blue
        if score >= 60: return [59, 130, 246, 200] # Light Blue
        if score >= 50: return [234, 179, 8, 200] # Yellow
        return [239, 68, 68, 200] # Red

    current_data['color'] = current_data['Overall_Score'].apply(get_color)
    # Scale radius based on budget relative to max
    max_budget = current_data['Monthly_Total_Budget'].max()
    current_data['radius'] = (current_data['Monthly_Total_Budget'] / max_budget) * 500000 + 100000

    layer = pdk.Layer(
        "ScatterplotLayer",
        current_data,
        get_position=["lng", "lat"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.8,
        filled=True,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=2,
    )

    view_state = pdk.ViewState(latitude=20, longitude=10, zoom=1.5, pitch=0)
    
    # Tooltip
    tooltip = {
        "html": "<b>{FullName} ({NSC})</b><br>Score: <b>{Overall_Score}</b><br>Budget: ${Monthly_Total_Budget}",
        "style": {"backgroundColor": "white", "color": "black"}
    }

    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style="light")
    st.pydeck_chart(r)

with col_ai:
    st.subheader("✨ AI Strategy Consultant")
    
    with st.container(border=True):
        st.markdown("""
        **Context-Aware Analysis**  
        Analyzes current filters against yearly baselines.
        """)
        
        tab1, tab2, tab3 = st.tabs(["Exec Summary", "Gap Analysis", "Action Plan"])
        
        # Helper to generate insights
        def get_gemini_response(prompt_type):
            if not api_key:
                return "⚠️ Please enter a valid Google Gemini API Key in the sidebar to generate insights."
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash') # Or gemini-pro
                
                # Construct Prompt
                context_str = f"Period: {year} {month}, Region: {region}"
                data_summary = current_data[['NSC', 'Overall_Score', 'Performance & Coverage', 'Quality Excellence', 'Data Infrastructure', 'AI Adoption']].to_string()
                
                full_prompt = f"""
                You are a Senior Digital Strategy Consultant for Hyundai Global.
                Context: {context_str}
                Data: {data_summary}
                
                Task: Provide a concise {prompt_type} based on the data above.
                - High Score > 80, Low < 60.
                - Identify wins and critical gaps.
                - Format as markdown with bullet points.
                - Be brief and executive.
                """
                
                with st.spinner("Consulting AI..."):
                    response = model.generate_content(full_prompt)
                    return response.text
            except Exception as e:
                return f"Error generating insight: {str(e)}"

        with tab1:
            if st.button("Generate Summary", key="btn_exec"):
                st.markdown(get_gemini_response("Executive Summary"))
            else:
                st.info("Click to generate an executive summary of current performance.")
        
        with tab2:
            if st.button("Analyze Gaps", key="btn_gap"):
                st.markdown(get_gemini_response("Gap Analysis (Focus on Data & AI)"))
            else:
                st.info("Click to analyze gaps in Data Infrastructure and AI Adoption.")
                
        with tab3:
            if st.button("Create Plan", key="btn_plan"):
                st.markdown(get_gemini_response("Strategic Action Plan"))
            else:
                st.info("Click to generate tactical recommendations.")

# --- Row 3: Heatmap & Gap Analysis ---
col_heat, col_gap = st.columns([2, 1])

with col_heat:
    st.subheader("📊 Strategy Performance Heatmap")
    
    # Prepare display dataframe
    display_df = current_data[['FullName', 'NSC', 'Monthly_Total_Budget', 'Performance & Coverage', 'Quality Excellence', 'Data Infrastructure', 'AI Adoption', 'Overall_Score']].copy()
    display_df = display_df.sort_values('Overall_Score', ascending=False)
    
    st.dataframe(
        display_df,
        column_config={
            "Monthly_Total_Budget": st.column_config.ProgressColumn(
                "Budget",
                help="Monthly Media Spend",
                format="$%f",
                min_value=0,
                max_value=max_budget,
            ),
            "Overall_Score": st.column_config.NumberColumn(
                "Overall",
                format="%.1f"
            ),
            "Performance & Coverage": st.column_config.NumberColumn("Perf", format="%.0f"),
            "Quality Excellence": st.column_config.NumberColumn("Qual", format="%.0f"),
            "Data Infrastructure": st.column_config.NumberColumn("Data", format="%.0f"),
            "AI Adoption": st.column_config.NumberColumn("AI", format="%.0f"),
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )

with col_gap:
    st.subheader("📉 Gap Analysis")
    
    # Compare each region's Overall Score to the Global Average
    gap_df = current_data[['NSC', 'Overall_Score']].copy()
    avg_score = stats['avg_score']
    gap_df['Gap'] = gap_df['Overall_Score'] - avg_score
    gap_df['Color'] = gap_df['Gap'].apply(lambda x: '#002c5f' if x >= 0 else '#ef4444')
    gap_df = gap_df.sort_values('Gap')

    fig_gap = go.Figure()
    fig_gap.add_trace(go.Bar(
        y=gap_df['NSC'],
        x=gap_df['Gap'],
        orientation='h',
        marker_color=gap_df['Color'],
        text=gap_df['Gap'].apply(lambda x: f"{x:+.1f}"),
        textposition='auto'
    ))
    
    fig_gap.update_layout(
        title=f"Divergence from Avg ({avg_score:.1f})",
        xaxis_title="Gap Score",
        yaxis_title="Region",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='white',
    )
    st.plotly_chart(fig_gap, use_container_width=True)

# --- Row 4: Trend Chart ---
st.subheader("📈 Maturity Progression (Trend)")

trend_data = get_trend_data(df_raw, region)

fig_trend = px.line(
    trend_data, 
    x='Date', 
    y='Framework_Score', 
    markers=True,
    title=f"Average Maturity Trend - {region if region != 'All' else 'Global'}",
    line_shape='spline'
)
fig_trend.update_traces(line_color='#002c5f', line_width=3)
fig_trend.update_layout(
    xaxis_title="",
    yaxis_title="Score",
    yaxis=dict(range=[40, 100]),
    plot_bgcolor='white',
    hovermode="x unified"
)
fig_trend.update_xaxes(showgrid=False)
fig_trend.update_yaxes(showgrid=True, gridcolor='#f1f5f9')

st.plotly_chart(fig_trend, use_container_width=True)
