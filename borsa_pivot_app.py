import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

# Sayfa yapılandırması
st.set_page_config(
    page_title="BIST Pivot Analizi",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sayfanın arka plan rengini değiştirmek için CSS
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: white;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        height: 3em;
        width: 100%;
        border-radius: 5px;
    }
    .stSelectbox>div>div {
        background-color: #262730;
        color: white;
    }
    .pivot-card {
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .value-text {
        font-size: 18px;
        font-weight: bold; 
        color: white;
    }
    .header-text {
        font-size: 22px;
        font-weight: bold;
        color: #1E88E5;
    }
    .status-olumlu {
        color: #4CAF50;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(76, 175, 80, 0.1);
    }
    .status-olumsuz {
        color: #F44336;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(244, 67, 54, 0.1);
    }
    .status-dengede {
        color: #FFC107;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(255, 193, 7, 0.1);
    }
    .timeframe-selector {
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def calculate_pivots(high, low, close):
    """Pivot noktalarını hesapla"""
    pp1 = float(high + low + close) / 3
    pp2 = float(high + low) / 2
    
    r1 = float(pp1 * 2) - low
    s1 = float(pp1 * 2) - high
    r2 = float(high - low) + pp1
    s2 = pp1 - float(high - low)
    hr2 = float(r1 + r2) / 2
    hs2 = float(s1 + s2) / 2
    hr1 = float(pp1 + r1) / 2
    hs1 = float(pp1 + s1) / 2
    
    return {
        'PP1': float(pp1),
        'PP2': float(pp2),
        'R1': float(r1),
        'S1': float(s1),
        'R2': float(r2),
        'S2': float(s2),
        'HR2': float(hr2),
        'HS2': float(hs2),
        'HR1': float(hr1),
        'HS1': float(hs1)
    }

def get_stock_pivots(symbol, timeframe="Haftalık"):
    """Seçilen hisse için pivot noktalarını hesapla"""
    # Bugünün tarihi
    today = datetime.now()
    
    # Zaman aralığına göre veri çekme ayarları
    if timeframe == "Günlük":
        start_date = today - timedelta(days=14)  # Son 2 hafta
        chart_days = 7  # Son 7 gün grafikte
        period_days = 3  # Son 3 gün pivot hesaplama
    elif timeframe == "Haftalık":
        start_date = today - timedelta(days=60)  # Son 2 ay
        chart_days = 21  # Son 21 gün grafikte
        period_days = 7  # Son 7 gün pivot hesaplama
    elif timeframe == "Aylık":
        start_date = today - timedelta(days=180)  # Son 6 ay
        chart_days = 60  # Son 60 gün grafikte
        period_days = 30  # Son 30 gün pivot hesaplama
    else:  # 3 Aylık
        start_date = today - timedelta(days=365)  # Son 1 yıl
        chart_days = 90  # Son 90 gün grafikte
        period_days = 90  # Son 90 gün pivot hesaplama
    
    # Veriyi çek
    data = yf.download(symbol, start=start_date, end=today)
    
    if data.empty:
        return None, None, None, None, None
    
    # Son kapanış fiyatını al
    last_close = float(data['Close'].iloc[-1])
    
    # Pivot hesaplama için veri periyodu
    period_data = data.tail(period_days)
    
    # Periyoda göre high, low ve close değerlerini hesapla
    period_high = float(period_data['High'].max())
    period_low = float(period_data['Low'].min())
    period_close = float(period_data['Close'].iloc[-1])
    
    # Pivot noktalarını hesapla
    pivots = calculate_pivots(period_high, period_low, period_close)
    
    # Grafik için veri hazırla
    chart_data = data.tail(chart_days)
    
    return pivots, last_close, data, chart_data, timeframe

def evaluate_pivot_position(price, pivots):
    """Fiyatın pivot değerlerine göre durumunu değerlendir"""
    pp1 = pivots['PP1']
    pp2 = pivots['PP2']
    
    # PP değerleri arasındaysa DENGEDE
    if min(pp1, pp2) <= price <= max(pp1, pp2):
        return "DENGEDE"
    # PP değerlerinin üzerindeyse OLUMLU
    elif price > max(pp1, pp2):
        return "OLUMLU"
    # PP değerlerinin altındaysa OLUMSUZ
    else:
        return "OLUMSUZ"

def create_price_chart(chart_data, pivots, stock_name, last_close, timeframe):
    """Fiyat grafiği ve pivot seviyelerini içeren grafik oluştur"""
    fig = go.Figure()
    
    # Mum grafiği ekle
    fig.add_trace(go.Candlestick(
        x=chart_data.index,
        open=chart_data['Open'],
        high=chart_data['High'],
        low=chart_data['Low'],
        close=chart_data['Close'],
        name=stock_name,
        increasing_line_color='#4CAF50',
        decreasing_line_color='#F44336'
    ))
    
    # Son kapanış fiyatını belirgin bir sembolle göster
    fig.add_trace(go.Scatter(
        x=[chart_data.index[-1]],
        y=[last_close],
        mode='markers',
        marker=dict(
            color='yellow',
            size=15,
            symbol='square',
            line=dict(
                color='black',
                width=2
            )
        ),
        name=f'Son Fiyat: {last_close:.2f}'
    ))
    
    # Pivot seviyelerini yatay çizgi olarak ekle
    pivot_colors = {
        'R2': '#1E88E5', 'HR2': '#90CAF9',
        'R1': '#4CAF50', 'HR1': '#A5D6A7',
        'PP1': '#FFC107', 'PP2': '#FFE082',
        'HS1': '#FF9800', 'S1': '#F44336',
        'HS2': '#FFCCBC', 'S2': '#EF5350'
    }
    
    for name, value in pivots.items():
        fig.add_shape(
            type="line",
            x0=chart_data.index[0],
            y0=value,
            x1=chart_data.index[-1],
            y1=value,
            line=dict(
                color=pivot_colors.get(name, "#FFFFFF"),
                width=2,
                dash="dash",
            ),
        )
        
        # Pivot isimlerini ekle
        fig.add_annotation(
            x=chart_data.index[-1],
            y=value,
            text=f"{name}: {value:.2f}",
            showarrow=False,
            xshift=50,
            font=dict(
                color=pivot_colors.get(name, "#FFFFFF"),
                size=12
            )
        )
    
    # Grafik düzeni
    fig.update_layout(
        title=f"{stock_name} {timeframe} Pivot Analizi",
        xaxis_title="Tarih",
        yaxis_title="Fiyat (TL)",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        legend=dict(y=1.1, x=0.5),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig

# Ana başlık
st.title("📊 BIST Pivot Analizi")
st.markdown("##### Pivot noktaları ile hisselerin durumunu analiz edin")

# İki sütunlu düzen
col1, col2 = st.columns([1, 3])

# BIST hisseleri listesi (örnek olarak popüler hisseler)
bist_stocks = {
    "Tüpraş": "TUPRS.IS",
    "Şişe Cam": "SISE.IS",
    "Sabancı Holding": "SAHOL.IS",
    "Garanti Bankası": "GARAN.IS",
    "İş Bankası": "ISCTR.IS",
    "Tofaş": "TOASO.IS",
    "Koç Holding": "KCHOL.IS",
    "Ereğli Demir Çelik": "EREGL.IS",
    "Türk Hava Yolları": "THYAO.IS",
    "Akbank": "AKBNK.IS",
    "Ford Otosan": "FROTO.IS",
    "Arçelik": "ARCLK.IS",
    "Bim Mağazalar": "BIMAS.IS",
    "Halk Bankası": "HALKB.IS",
    "Türk Telekom": "TTKOM.IS",
    "Vakıflar Bankası": "VAKBN.IS",
    "Yapı Kredi": "YKBNK.IS",
    "Migros": "MGROS.IS",
    "Petkim": "PETKM.IS",
    "Turkcell": "TCELL.IS"
}

with col1:
    st.markdown("### Hisse Seçimi")
    
    # Hisse seçimi
    selected_stock_name = st.selectbox(
        "Hisse Seçin",
        options=list(bist_stocks.keys())
    )
    
    # Seçilen hissenin sembolü
    selected_symbol = bist_stocks[selected_stock_name]
    
    # Zaman aralığı seçimi
    st.markdown("### Zaman Aralığı")
    selected_timeframe = st.selectbox(
        "Analiz Periyodu Seçin",
        options=["Günlük", "Haftalık", "Aylık", "3 Aylık"],
        index=1,  # Varsayılan olarak "Haftalık" seçili
    )
    
    if st.button(f"{selected_stock_name} Analiz Et"):
        with st.spinner(f"{selected_stock_name} için {selected_timeframe} veriler alınıyor..."):
            # Pivot hesaplama ve değerlendirme
            pivots, last_close, full_data, chart_data, timeframe = get_stock_pivots(selected_symbol, selected_timeframe)
            
            if pivots and last_close is not None:
                position = evaluate_pivot_position(last_close, pivots)
                
                # Pivot değerlerini sakla (diğer sütunda kullanmak için)
                st.session_state['pivots'] = pivots
                st.session_state['last_close'] = last_close
                st.session_state['position'] = position
                st.session_state['selected_stock_name'] = selected_stock_name
                st.session_state['selected_symbol'] = selected_symbol
                st.session_state['chart_data'] = chart_data
                st.session_state['timeframe'] = timeframe
            else:
                st.error(f"{selected_stock_name} için veri alınamadı!")

with col2:
    st.markdown("### Pivot Analizi")
    
    # Eğer pivot değerleri hesaplanmışsa göster
    if 'pivots' in st.session_state and 'last_close' in st.session_state:
        pivots = st.session_state['pivots']
        last_close = st.session_state['last_close']
        position = st.session_state['position']
        selected_stock_name = st.session_state['selected_stock_name']
        selected_symbol = st.session_state['selected_symbol']
        chart_data = st.session_state['chart_data']
        timeframe = st.session_state['timeframe']
        
        # Fiyat bilgisi ve durum
        price_col1, price_col2 = st.columns([2, 1])
        
        with price_col1:
            st.markdown(f"#### {selected_stock_name} (Son Kapanış)")
            st.markdown(f"<h2 style='text-align: left; color: #1E88E5;'>{last_close:.2f} TL</h2>", unsafe_allow_html=True)
        
        with price_col2:
            status_class = f"status-{position.lower()}"
            st.markdown(f"#### {timeframe} Durum")
            st.markdown(f"<div class='{status_class}'>{position}</div>", unsafe_allow_html=True)
        
        # Grafik gösterimi
        fig = create_price_chart(chart_data, pivots, selected_stock_name, last_close, timeframe)
        st.plotly_chart(fig, use_container_width=True)
        
        # Pivot değerleri tablosu
        st.markdown(f"#### {timeframe} Pivot Değerleri")
        
        # Pivot değerlerini kart şeklinde göster
        grid1, grid2, grid3, grid4, grid5 = st.columns(5)
        
        # Direnç seviyeleri - Pivot değerlerini doğrudan göster
        with grid1:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>R2</p><p class='value-text'>{pivots['R2']:.2f}</p></div>", unsafe_allow_html=True)
        
        with grid2:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>HR2</p><p class='value-text'>{pivots['HR2']:.2f}</p></div>", unsafe_allow_html=True)
        
        with grid3:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>R1</p><p class='value-text'>{pivots['R1']:.2f}</p></div>", unsafe_allow_html=True)
        
        with grid4:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>HR1</p><p class='value-text'>{pivots['HR1']:.2f}</p></div>", unsafe_allow_html=True)
            
        with grid5:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>PP1</p><p class='value-text'>{pivots['PP1']:.2f}</p></div>", unsafe_allow_html=True)
        
        # Pivot ve destek seviyeleri
        grid6, grid7, grid8, grid9, grid10 = st.columns(5)
        
        with grid6:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>PP2</p><p class='value-text'>{pivots['PP2']:.2f}</p></div>", unsafe_allow_html=True)
        
        with grid7:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>HS1</p><p class='value-text'>{pivots['HS1']:.2f}</p></div>", unsafe_allow_html=True)
            
        with grid8:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>S1</p><p class='value-text'>{pivots['S1']:.2f}</p></div>", unsafe_allow_html=True)
            
        with grid9:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>HS2</p><p class='value-text'>{pivots['HS2']:.2f}</p></div>", unsafe_allow_html=True)
            
        with grid10:
            st.markdown(f"<div class='pivot-card'><p class='header-text'>S2</p><p class='value-text'>{pivots['S2']:.2f}</p></div>", unsafe_allow_html=True)
        
        # Zaman aralığına göre açıklama
        timeframe_info = {
            "Günlük": "günlük bazda",
            "Haftalık": "haftalık bazda",
            "Aylık": "aylık bazda",
            "3 Aylık": "3 aylık bazda"
        }
        
        info_text = timeframe_info.get(timeframe, "")
        
        # Genel durum açıklaması
        if position == "OLUMLU":
            st.success(f"📈 Fiyat, pivot seviyelerinin üzerinde {info_text} seyretmektedir. Yükseliş eğilimi gösteriyor.")
        elif position == "OLUMSUZ":
            st.error(f"📉 Fiyat, pivot seviyelerinin altında {info_text} seyretmektedir. Düşüş eğilimi gösteriyor.")
        else:
            st.warning(f"⚖️ Fiyat, ana pivot seviyeleri arasında {info_text} dengededir.")
    
    else:
        st.info("👈 Analiz için sol taraftan bir hisse seçin ve 'Analiz Et' butonuna tıklayın.")
        
# Footer
st.markdown("---")
st.markdown("##### 📊 BIST Pivot Analiz Uygulaması | Veriler yfinance API'si üzerinden alınmaktadır.")
st.markdown("##### ⚠️ Bu uygulama yatırım tavsiyesi değildir. Sadece teknik analiz aracıdır.") 

