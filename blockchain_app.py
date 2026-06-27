import streamlit as st
import pandas as pd
from supabase import create_client, Client
import qrcode
from io import BytesIO

# 1. Supabase Bağlantısı (Güvenli Yöntem)
import streamlit as st

# Değerleri açıkça yazmıyoruz, Streamlit Secrets kasasından çekiyoruz
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="Hemithea Cold Chain Analytics", layout="wide")
st.title("🚚 Eker Soğuk Zincir Blockchain & AI Real-Time Dashboard")

# 2. Verileri Buluttan Çekme
def load_data():
    response = supabase.table("cold_chain_records").select("*").order("block_index", desc=True).execute()
    return pd.DataFrame(response.data)

df = load_data()

if not df.empty:
    # Metrik Kartları
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam Blok Sayısı", len(df))
    with col2:
        st.metric("Son Sıcaklık", f"{df['temperature_c'].iloc[0]} °C")
    with col3:
        st.metric("Ortalama Risk Skoru", f"{df['AI_Risk_Score'].mean():.2f}")
    with col4:
        st.metric("Kritik Anomali Sayısı", len(df[df['AI_Security_Status'] == 'ANOMALY']))

    # Grafik ve Tablo Yan Yana
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("📈 Gerçek Zamanlı Sıcaklık Takip Grafiği")
        st.line_chart(df.set_index('processed_timestamp')['temperature_c'])
        
        st.subheader("📋 Blockchain Ledger Verileri (Supabase)")
        st.dataframe(df)

    # ==========================================
    # 2. KAREKOD (QR CODE) DETAYI VE DOĞRULAMA
    # ==========================================
    with right_col:
        st.subheader("🔍 Ürün Karekod Doğrulama")
        
        # Panelden sorgulamak için bir ürün seçelim
        product_list = df['product_id'].unique()
        selected_product = st.selectbox("Doğrulanacak Ürünü Seçin", product_list)
        
        product_df = df[df['product_id'] == selected_product]
        
        if not product_df.empty:
            # Ürünün blockchain doğrulama URL'i (Yayına aldığımız link olacak)
            # Şimdilik simüle etmek için ürün ID'sini gömüyoruz
            verification_url = f"https://hemithea-coldchain.streamlit.app/?product_id={selected_product}"
            
            # Karekod Oluşturma
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(verification_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Streamlit'te göstermek için hafızaya kaydetme
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"{selected_product} için Blockchain Karekodu", use_container_width=True)
            
            st.success(f"🔐 Blockchain Durumu: {product_df['AI_Security_Status'].iloc[0]}")
            st.write(f"📍 Son Konum: {product_df['location'].iloc[0]}")
else:
    st.info("Henüz bulutta veri bulunamadı. Lütfen Spark Consumer'ı çalıştırın.")
