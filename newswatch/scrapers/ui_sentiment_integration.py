"""
Integration module for UI: Scraping + Sentiment Analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import subprocess
import sys
import time
import os
from io import BytesIO

# Import sentiment analyzer (pastikan file sentiment_analyzer.py ada)
try:
    from .sentiment_analyzer import (
        analyze_dataframe_sentiment,
        get_sentiment_summary,
        filter_by_sentiment
    )
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    st.warning("⚠️ Module sentiment_analyzer tidak ditemukan. Fitur analisis sentimen tidak tersedia.")


def create_sentiment_pie_chart(summary: dict) -> go.Figure:
    """Create pie chart for sentiment distribution"""
    
    labels = ['Positive', 'Negative', 'Neutral']
    values = [summary['positive'], summary['negative'], summary['neutral']]
    colors = ['#28a745', '#dc3545', '#ffc107']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont_size=14
    )])
    
    fig.update_layout(
        title="Distribusi Sentimen",
        showlegend=True,
        height=400,
        margin=dict(t=50, b=20, l=20, r=20)
    )
    
    return fig


def create_sentiment_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create bar chart for sentiment by source"""
    
    if 'source' not in df.columns or 'sentiment' not in df.columns:
        return None
    
    # Count sentiment by source
    sentiment_by_source = df.groupby(['source', 'sentiment']).size().reset_index(name='count')
    
    fig = px.bar(
        sentiment_by_source,
        x='source',
        y='count',
        color='sentiment',
        color_discrete_map={
            'positive': '#28a745',
            'negative': '#dc3545',
            'neutral': '#ffc107'
        },
        title='Sentimen per Sumber Berita',
        labels={'count': 'Jumlah Artikel', 'source': 'Sumber'}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        margin=dict(t=50, b=100, l=50, r=50)
    )
    
    return fig


def create_sentiment_timeline(df: pd.DataFrame) -> go.Figure:
    """Create timeline chart for sentiment"""
    
    if 'publish_date' not in df.columns or 'sentiment' not in df.columns:
        return None
    
    try:
        # Convert publish_date to datetime
        df_copy = df.copy()
        df_copy['publish_date'] = pd.to_datetime(df_copy['publish_date'])
        df_copy['date'] = df_copy['publish_date'].dt.date
        
        # Count sentiment by date
        sentiment_by_date = df_copy.groupby(['date', 'sentiment']).size().reset_index(name='count')
        
        fig = px.line(
            sentiment_by_date,
            x='date',
            y='count',
            color='sentiment',
            color_discrete_map={
                'positive': '#28a745',
                'negative': '#dc3545',
                'neutral': '#ffc107'
            },
            title='Tren Sentimen dari Waktu ke Waktu',
            labels={'count': 'Jumlah Artikel', 'date': 'Tanggal'}
        )
        
        fig.update_layout(
            height=400,
            margin=dict(t=50, b=50, l=50, r=50),
            hovermode='x unified'
        )
        
        return fig
    except:
        return None


def display_sentiment_analysis_results(df: pd.DataFrame, duration: float = None):
    """
    Display comprehensive sentiment analysis results
    
    Args:
        df: DataFrame with sentiment analysis
        duration: Scraping duration in seconds
    """

    if df is None or df.empty:
        st.warning("⚠️ Tidak ada data untuk dianalisis")
        return df

    # Get sentiment summary
    summary = get_sentiment_summary(df)

    st.write("## 📊 Hasil Analisis Sentimen")

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Artikel", summary['total'])
    with col2:
        st.metric("Positif", f"{summary['positive']} ({summary['positive_pct']}%)", 
                 delta=None, delta_color="normal")
    with col3:
        st.metric("Negatif", f"{summary['negative']} ({summary['negative_pct']}%)", 
                 delta=None, delta_color="inverse")
    with col4:
        st.metric("Netral", f"{summary['neutral']} ({summary['neutral_pct']}%)")

    if duration:
        st.info(f"⏱️ Waktu ekstraksi & analisis: {duration:.2f} detik")

    # Visualizations
    st.write("### 📈 Visualisasi Sentimen")

    tab1, tab2, tab3 = st.tabs(["📊 Distribusi", "📰 Per Sumber", "📅 Timeline"])

    with tab1:
        # Pie chart
        fig_pie = create_sentiment_pie_chart(summary)
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        # Bar chart by source
        fig_bar = create_sentiment_bar_chart(df)
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Data sumber tidak tersedia")

    with tab3:
        # Timeline
        fig_timeline = create_sentiment_timeline(df)
        if fig_timeline:
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("Data timeline tidak tersedia")

    display_df = df
    st.write(f"**Menampilkan {len(display_df)} dari {len(df)} artikel**")

    # Select columns to display
    display_columns = []
    if 'title' in display_df.columns:
        display_columns.append('title')
    if 'sentiment' in display_df.columns:
        display_columns.append('sentiment')
    if 'sentiment_score' in display_df.columns:
        display_columns.append('sentiment_score')
    if 'sentiment_confidence' in display_df.columns:
        display_columns.append('sentiment_confidence')
    if 'source' in display_df.columns:
        display_columns.append('source')
    if 'publish_date' in display_df.columns:
        display_columns.append('publish_date')
    if 'category' in display_df.columns:
        display_columns.append('category')
    if 'keyword' in display_df.columns:
        display_columns.append('keyword')

    # Display dataframe with index starting from 1
    if display_columns:
        st.dataframe(
            display_df[display_columns].reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

    # Show detailed articles in expander
    with st.expander("📰 Lihat Detail Artikel"):
        for idx, row in display_df.head(10).iterrows():  # Show first 10
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😞',
                'neutral': '😐'
            }

            st.markdown(f"### {sentiment_emoji.get(row.get('sentiment', 'neutral'), '📰')} {row.get('title', 'No Title')}")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write(f"**Sentimen:** {row.get('sentiment', 'N/A').title()}")
            with col_b:
                st.write(f"**Sumber:** {row.get('source', 'N/A')}")
            with col_c:
                st.write(f"**Tanggal:** {row.get('publish_date', 'N/A')}")

            if 'content' in row:
                content_preview = str(row['content'])[:300] + "..." if len(str(row['content'])) > 300 else str(row['content'])
                st.write(content_preview)

            if 'link' in row:
                st.markdown(f"[🔗 Baca selengkapnya]({row['link']})")

            st.divider()

    return display_df


def run_scraping_with_sentiment(
    keywords: str,
    start_date: str,
    scrapers: list,
    output_format: str,
    only_kepri: bool = False
) -> tuple:
    """
    Run scraping and sentiment analysis
    
    Returns:
        (df_analyzed, duration, error_message)
    """

    if not SENTIMENT_AVAILABLE:
        return None, 0, "Module sentiment_analyzer tidak tersedia"

    try:
        start_time = time.time()

        # Build command
        cmd = [sys.executable, "-m", "newswatch.cli"]

        if keywords:
            cmd += ["--keywords", keywords]
        if start_date:
            cmd += ["--start_date", str(start_date)]
        if scrapers:
            cmd += ["--scrapers", ",".join(scrapers)]
        if output_format:
            cmd += ["--output_format", output_format]

        # Get output directory
        output_dir = Path("output")
        if output_dir.exists():
            before_files = set(output_dir.glob(f"*.{output_format}"))
        else:
            before_files = set()

        # Run scraping
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            timeout=600
        )

        # Find new file
        if output_dir.exists():
            after_files = set(output_dir.glob(f"*.{output_format}"))
            new_files = after_files - before_files

            if new_files:
                latest_file = max(new_files, key=os.path.getctime)

                # Read file
                if output_format == "csv":
                    df = pd.read_csv(latest_file)
                else:
                    df = pd.read_excel(latest_file)

                # Filter Kepri if needed
                if only_kepri and "content" in df.columns:
                    df = df[
                        df["content"].str.contains("kepri ", case=False, na=False) |
                        df["content"].str.contains("kepulauan riau", case=False, na=False) |
                        df["content"].str.contains("batam", case=False, na=False) |
                        df["content"].str.contains("tanjungpinang", case=False, na=False) |
                        df["content"].str.contains("tanjung pinang", case=False, na=False) |
                        df["content"].str.contains("bintan ", case=False, na=False) |
                        df["content"].str.contains("lingga", case=False, na=False) |
                        df["content"].str.contains("karimun", case=False, na=False) |
                        df["content"].str.contains("anambas", case=False, na=False) |
                        df["content"].str.contains("natuna", case=False, na=False)
                    ]

                # Analyze sentiment
                df_analyzed = analyze_dataframe_sentiment(df)

                duration = time.time() - start_time

                # Delete temporary file
                try:
                    latest_file.unlink()
                except:
                    pass

                return df_analyzed, duration, None
            else:
                return None, 0, "Tidak ada data ditemukan dari ekstraksi"
        else:
            return None, 0, "Output folder tidak ditemukan"

    except subprocess.TimeoutExpired:
        return None, 0, "Ekstraksi timeout setelah 10 menit"
    except subprocess.CalledProcessError as e:
        return None, 0, f"Error saat ekstraksi: {e.stderr}"
    except Exception as e:
        return None, 0, f"Error: {str(e)}"


def create_download_button_with_sentiment(df: pd.DataFrame, 
                                          output_format: str,
                                          keywords: str,
                                          scrapers: str,
                                          only_kepri: bool = False):
    """
    Create download button for sentiment analysis results
    """
    
    if df is None or df.empty:
        return
    
    # Generate filename
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    keywords_short = keywords.replace(",", "_")[:30] if keywords else "news"
    scrapers_short = scrapers.replace(",", "_")[:20] if scrapers else "all"
    
    if only_kepri:
        download_name = f"{keywords_short}_{scrapers_short}_sentiment_kepri_{timestamp}.{output_format}"
    else:
        download_name = f"{keywords_short}_{scrapers_short}_sentiment_{timestamp}.{output_format}"
    
    # Create download button
    if output_format == "csv":
        buffer = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Hasil dengan Analisis Sentimen (CSV)",
            data=buffer,
            file_name=download_name,
            mime="text/csv",
            type="primary"
        )
    else:
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="📥 Download Hasil dengan Analisis Sentimen (XLSX)",
            data=buffer,
            file_name=download_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
