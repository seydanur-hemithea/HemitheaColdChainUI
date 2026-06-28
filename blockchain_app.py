import streamlit as st
import pandas as pd
from supabase import create_client, Client
import qrcode
from io import BytesIO

# URL'deki ?product_id=... parametresini otomatik okur (KAREKODDAN VERİ ÇEKME KISMI BURASI)
query_params = st.query_params
default_product = query_params.get("product_id", None)

# Değerleri açıkça yazmıyoruz, Streamlit Secrets kasasından çekiyoruz
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Mobil Ekran Optimizasyonu İçin Sayfa Ayarları (Layout'u telefona göre ortaladık)
st.set_page_config(page_title="Hemithea Cold Chain", layout="centered", page_icon="🚚")

# Mobil Uyumlu Başlık Tasarımı (Eker kelimeleri tamamen uçtu, saf Hemithea oldu)
st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🚚 Hemithea</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Smart Cold Chain: Blockchain & AI Verified</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. Verileri Buluttan Çekme
def load_data():
    response = supabase.table("cold_chain_records").select("*").order("block_index", desc=True).execute()
    return pd.DataFrame(response.data)

df = load_data()

if not df.empty:
    # ----------------------------------------------------------------------
    # 1. BÖLÜM: ÜRÜN SEÇİM ALANI (Karekoddan ID gelirse otomatik eşleşir)
    # ----------------------------------------------------------------------
    product_list = df['product_id'].unique()
    
    if default_product in product_list:
        selected_product = st.selectbox("📱 Sorgulanan Ürün Kimliği:", product_list, index=list(product_list).index(default_product))
    else:
        selected_product = st.selectbox("📱 Sorgulanacak Ürünü Seçin:", product_list)                                                              
    
    # Seçilen ürünün verilerini kronolojik sıraya sokuyoruz (Eskiden yeniye)
    product_df = df[df['product_id'] == selected_product].sort_values('block_index', ascending=True)
    
    if not product_df.empty:
        # En son istasyonun verilerini alıyoruz (Mevcut Durum)
        latest_record = product_df.iloc[-1]
        latest_status = latest_record['AI_Security_Status']
        latest_temp = latest_record['temperature_c']
        latest_location = latest_record['location']
        
        # ----------------------------------------------------------------------
        # 2. BÖLÜM: TÜKETİCİNİN ANLAYACAĞI RENKLİ GÜVENLİK DURUM KARTI
        # ----------------------------------------------------------------------
        st.markdown("### 🛡️ Güncel Tazelik Raporu")
        if latest_status == "SAFE":
            st.success(f"### ✅ ÜRÜN TAZELİĞİ ONAYLANDI\n\n**📍 Konum:** {latest_location}  \n**🌡️ Sıcaklık:** {latest_temp} °C  \n\n*Hemithea Yapay Zekası ve Blockchain Defteri, bu ürünün güvenle tüketilebileceğini garanti eder.*")
        elif latest_status == "WARNING":
            st.warning(f"### ⚠️ SINIRDA SICAKLIK UYARISI\n\n**📍 Konum:** {latest_location}  \n**🌡️ Sıcaklık:** {latest_temp} °C  \n\n*Ürün güvenli bölgede ancak sıcaklık ideal değerlerin biraz üzerinde seyretmiş.*")
        else:
            st.error(f"### 🚨 SOĞUK ZİNCİR KIRILMASI!\n\n**📍 Konum:** {latest_location}  \n**🌡️ Sıcaklık:** {latest_temp} °C  \n\n*Kritik sıcaklık eşiği aşılmıştır! Bozulma riski nedeniyle tüketilmesi kesinlikle önerilmez!*")
        
        # ----------------------------------------------------------------------
        # 3. BÖLÜM: TÜKETİCİ DOSTU LOKASYON BAZLI SICAKLIK GRAFİĞİ
        # ----------------------------------------------------------------------
        st.markdown("### 📈 Tedarik Zinciri Sıcaklık Seyri")
        # Teknik saat kodları yerine tüketicinin anladığı lokasyon adımlarını grafiğe basıyoruz
        chart_data = product_df.set_index('location')['temperature_c']
        st.area_chart(chart_data, color="#2563EB")
        
        # ----------------------------------------------------------------------
        # 4. BÖLÜM: HİKAYELEŞTİRİLMİŞ BLOCKCHAIN ZAMAN TÜNELİ
        # ----------------------------------------------------------------------
        st.markdown("### 📍 Şeffaf Blockchain İzlenebilirliği")
        for idx, row in product_df.iterrows():
            status_emoji = "🟢" if row['AI_Security_Status'] == "SAFE" else ("🟡" if row['AI_Security_Status'] == "WARNING" else "🔴")
            st.markdown(
                f"> {status_emoji} **{row['location']} İstasyonu** \n"
                f"Sıcaklık: `{row['temperature_c']}°C` | AI Risk Skoru: `%{int(row['AI_Risk_Score'] * 100)}`  \n"
                f"<small style='color:gray;'>Blok No: #{row['block_index']}</small>", 
                unsafe_allow_html=True
            )
            
        st.markdown("---")
        
        # ----------------------------------------------------------------------
        # 5. BÖLÜM: DİNAMİK KAREKOD ÜRETİM ALANI (Senin Gerçek Linkin)
        # ----------------------------------------------------------------------
        st.markdown("### 🔗 Ürüne Özel Karekod")
        verification_url = f"https://websydnrcvpy-v94hbqbo6agxbxtqsms6f8.streamlit.app/?product_id={selected_product}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(verification_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E3A8A", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"{selected_product} Dijital Kimlik Karekodu", use_container_width=True)
        
    # ---------------------------------------------------------------------
    # JÜRİ ÖZEL BÖLÜMÜ (Ham veriler alt tarafta şık bir kutuda gizli kalıyor)
    # ---------------------------------------------------------------------
    st.markdown("---")
    with st.expander("🔬 Jüri Özel: Teknik Supabase Veri Defteri"):
        st.write("Kriptografik blok indekslerine sahip ham veri tabanı kayıtları:")
        st.dataframe(df)
else:
    st.info("Henüz bulutta işlenmiş veri bulunamadı. Lütfen Spark Consumer'ı tetikleyin.")
