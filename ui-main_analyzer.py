import subprocess
import streamlit as st
from datetime import date
import sys
import pandas as pd
import os
import time
from pathlib import Path
from io import BytesIO, StringIO

from newswatch.scrapers.ui_sentiment_integration import (
    run_scraping_with_sentiment,
    display_sentiment_analysis_results,
    create_download_button_with_sentiment,
    SENTIMENT_AVAILABLE,
)

st.set_page_config(
    page_title="FAKTA: Fenomena Aktual Terkini",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="auto",
)

# background image
# st.markdown("""
# <style>
# [data-testid="stAppViewContainer"] {
#    background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e');
#    background-size: cover;
#    background-position: center;
#    background-attachment: fixed;
# }
# </style>
# """, unsafe_allow_html=True)


# Header Section
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #FF9A00 0%, #FFD93D 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        text-align: center;
        color: white;
    }
    
    .header-title {
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 2 rem;
        font-weight: 500;
        opacity: 0.9;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="main-header">
    <div class="header-title">📰 FAKTA: Fenomena Aktual Terkini</div>
</div>
""",
    unsafe_allow_html=True,
)

# Deskripsi dengan tampilan lebar dan jarak bawah
st.markdown(
    """
<div style="
    background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem 2rem;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
    width: 100%;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
">
    <p style="font-size:1.2rem; color:#444; margin:0;">
        Aplikasi ini digunakan sebagai mesin ekstraksi data berita secara otomatis</b> 
        dari berbagai situs berita yang telah disediakan. <br>
        Kamu dapat menentukan <b>kata kunci</b>, <b>tanggal mulai</b>, <b>tanggal akhir</b>, dan <b>sumber berita</b> 
        untuk pencarian yang lebih spesifik dan efisien.
    </p>
</div>
""",
    unsafe_allow_html=True,
)


# Available scrapers
available_scrapers = [
    # "all",
    "antaranews",
    "alurnews",
    "batampos",
    "bisnis",
    "bloombergtechnoz",
    "cnbcindonesia",
    # "detik",
    "hariankepri",
    "jawapos",
    "katadata",
    "kepriantaranews",
    "keprinews",
    # "kompas",
    "kontan",
    "mediaindonesia",
    "metrotvnews",
    "okezone",
    "tempo",
    "ulasan",
    "viva",
]


def show_dataframe_preview(
    df,
    output_format,
    only_kepri=False,
    duration=None,
    keywords="",
    scrapers="",
    start_date="",
    end_date=None,
):
    """Show preview of the dataframe"""
    try:
        # Filter berdasarkan date range
        if "publish_date" in df.columns:
            # Convert publish_date to datetime if it's not already
            df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")

            # Filter by start date
            if start_date:
                df = df[df["publish_date"] >= pd.to_datetime(start_date)]

            # Filter by end date if provided
            if end_date:
                end_date_with_time = (
                    pd.to_datetime(end_date)
                    + pd.Timedelta(days=1)
                    - pd.Timedelta(seconds=1)
                )
                df = df[df["publish_date"] <= end_date_with_time]

        if only_kepri and "content" in df.columns:
            df = df[
                df["content"].str.contains("kepri ", case=False, na=False)
                | df["content"].str.contains("kepulauan riau", case=False, na=False)
                | df["content"].str.contains("batam", case=False, na=False)
                | df["content"].str.contains("tanjungpinang", case=False, na=False)
                | df["content"].str.contains("tanjung pinang", case=False, na=False)
                | df["content"].str.contains("bintan ", case=False, na=False)
                | df["content"].str.contains("lingga", case=False, na=False)
                | df["content"].str.contains("karimun", case=False, na=False)
                | df["content"].str.contains("anambas", case=False, na=False)
                | df["content"].str.contains("natuna", case=False, na=False)
            ]

        st.write("### 📊 Scraping Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            if duration is not None:
                st.metric("Scraping Time", f"{duration:.2f} s")
        with col3:
            st.metric("Scrapers", scrapers if scrapers else None)

        # Tampilkan informasi filter tanggal
        if start_date or end_date:
            st.write(
                f"**Filter Tanggal:** {start_date} hingga {end_date if end_date else 'Sekarang'}"
            )

        st.write("### 🔍 Preview Hasil")
        st.dataframe(df.set_index(pd.Index(range(1, len(df) + 1))))

        # Generate download filename
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        keywords_short = keywords.replace(",", "_")[:30] if keywords else "news"
        scrapers_short = scrapers.replace(",", "_")[:20] if scrapers else None

        if only_kepri:
            download_name = (
                f"{keywords_short}_{scrapers_short}_kepri_{timestamp}.{output_format}"
            )
        else:
            download_name = (
                f"{keywords_short}_{scrapers_short}_{timestamp}.{output_format}"
            )

        # Download button
        if output_format == "csv":
            buffer = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download hasil (CSV)",
                data=buffer,
                file_name=download_name,
                mime="text/csv",
            )
        else:
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="📥 Download hasil (XLSX)",
                data=buffer,
                file_name=download_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        return df

    except Exception as e:
        st.error(f"❌ Error memproses data: {e}")
        return None


# Main form
with st.form("scraper_form"):
    st.write("### ⚙️ Konfigurasi Ekstraksi Berita")

    # Pilih mode
    mode = st.radio(
        "Mode Ekstraksi:",
        ["📰 Ekstraksi Saja", "🔍 Ekstraksi + Analisis Sentimen"],
        horizontal=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        keywords = st.text_input(
            "Keywords (comma-separated)", "Harga Cabai, prabowo, BPS"
        )
        start_date = st.date_input("Start Date", None)
        only_kepri = st.checkbox("Fokuskan hanya berita kepri?")

    with col2:
        scrapers = st.multiselect("Pilih Scrapers", available_scrapers, default=None)
        end_date = st.date_input("End Date (optional)", None)
        output_format = st.selectbox("Output Format", ["csv", "xlsx"])

    submitted = st.form_submit_button("🚀 Run Ekstraksi", type="primary")

# Handle form submission
if submitted:
    # Validasi input wajib
    if not keywords.strip():
        st.warning(
            "⚠️ Harap isi minimal satu **keyword** sebelum menjalankan ekstraksi."
        )
        st.stop()

    if not scrapers and len(available_scrapers) > 1:
        st.warning(
            "⚠️ Harap pilih minimal satu **scraper** sebelum menjalankan ekstraksi."
        )
        st.stop()

    if not start_date:
        st.warning(
            "⚠️ Harap pilih **tanggal mulai (Start Date)** sebelum menjalankan ekstraksi."
        )
        st.stop()

    # PISAHKAN BERDASARKAN MODE
    if mode == "🔍 Ekstraksi + Analisis Sentimen":
        # Mode Sentiment Analysis
        if not SENTIMENT_AVAILABLE:
            st.error(
                "❌ Module sentiment analyzer tidak tersedia. Pastikan file sentiment_analyzer.py ada."
            )
            st.stop()

        st.write("---")
        st.write("### 🔄 Eksekusi: Ekstraksi + Analisis Sentimen")

        with st.spinner("🔄 Menjalankan ekstraksi & analisis..."):
            df_analyzed, duration, error = run_scraping_with_sentiment(
                keywords=keywords,
                start_date=str(start_date),
                scrapers=scrapers,
                output_format=output_format,
                only_kepri=only_kepri,
            )

            if error:
                st.error(f"❌ {error}")
            elif df_analyzed is not None and not df_analyzed.empty:
                st.success("✅ Ekstraksi & Analisis Selesai!")

                # Filter berdasarkan date range
                if "publish_date" in df_analyzed.columns:
                    # Convert publish_date to datetime if it's not already
                    df_analyzed["publish_date"] = pd.to_datetime(
                        df_analyzed["publish_date"], errors="coerce"
                    )

                    # Filter by start date
                    if start_date:
                        df_analyzed = df_analyzed[
                            df_analyzed["publish_date"] >= pd.to_datetime(start_date)
                        ]

                    # Filter by end date if provided
                    if end_date:
                        df_analyzed = df_analyzed[
                            df_analyzed["publish_date"] <= pd.to_datetime(end_date)
                        ]

                # Display results
                filtered_df = display_sentiment_analysis_results(df_analyzed, duration)

                # Download button
                if filtered_df is not None:
                    create_download_button_with_sentiment(
                        filtered_df,
                        output_format,
                        keywords,
                        ",".join(scrapers),
                        only_kepri,
                    )
            else:
                st.warning("⚠️ Tidak ada data ditemukan")

    else:
        # Mode Ekstraksi Saja (📰 Ekstraksi Saja)
        temp_output = Path("temp_output")
        temp_output.mkdir(exist_ok=True)

        cmd = [sys.executable, "-m", "newswatch.cli"]

        if keywords:
            cmd += ["--keywords", keywords]
        if start_date:
            cmd += ["--start_date", str(start_date)]
        if scrapers:
            cmd += ["--scrapers", ",".join(scrapers)]
        if output_format:
            cmd += ["--output_format", output_format]

        st.write("---")
        st.write("### 🔄 Execution")
        st.code(" ".join(cmd), language="bash")

        # Progress indicator
        with st.spinner("🔄 Menjalankan ekstraksi..."):
            try:
                start_time = time.time()

                # Get list of files before scraping
                output_dir = Path("output")
                if output_dir.exists():
                    before_files = set(output_dir.glob(f"*.{output_format}"))
                else:
                    before_files = set()

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True, timeout=600
                )
                duration = time.time() - start_time
                st.success("✅ Ekstraksi selesai!")

                # Show command output
                if result.stdout:
                    with st.expander("📄 Command Output", expanded=False):
                        st.code(result.stdout)

                # Find the newly created file
                if output_dir.exists():
                    after_files = set(output_dir.glob(f"*.{output_format}"))
                    new_files = after_files - before_files

                    if new_files:
                        latest_file = max(new_files, key=os.path.getctime)

                        if output_format == "csv":
                            df = pd.read_csv(latest_file)
                        else:
                            df = pd.read_excel(latest_file)

                        st.write("---")
                        st.write(f"### 📈 Hasil Scraping")
                        show_dataframe_preview(
                            df,
                            output_format,
                            only_kepri=only_kepri,
                            duration=duration,
                            keywords=keywords,
                            scrapers=",".join(scrapers),
                            start_date=str(start_date),
                            end_date=end_date,
                        )

                        try:
                            latest_file.unlink()
                        except:
                            pass
                    else:
                        st.warning("⚠️ Tidak ada data ditemukan dari ekstraksi ini.")
                else:
                    st.warning("⚠️ Output folder tidak ditemukan.")

            except subprocess.TimeoutExpired:
                st.error("❌ Ekstraksi timed out setelah 10 menit")
            except subprocess.CalledProcessError as e:
                st.error("❌ Error saat menjalankan ekstraksi")
                st.code(e.stderr)
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Footer
st.write("---")
st.write("### ℹ️ Information")
st.write(
    """
**Note: Hasil ekstraksi hanya dimunculkan sekali, silahkan unduh hasilnya untuk penyimpanan permanen.**
         
**Expected output columns:**
1. `title` - Article title
2. `publish_date` - Publication date
3. `author` - Article author
4. `content` - Article content
5. `keyword` - Search keyword used
6. `category` - Article category
7. `source` - News source website
8. `link` - Original article URL
"""
)

# Copyright footer
st.markdown(
    """
<style>
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: #f9f9f9;
    color: gray;
    text-align: center;
    padding: 6px 0;
    font-size: 0.9rem;
    border-top: 1px solid #ddd;
}
</style>

<div class="footer">
    © 2025 <b>Tim IT BPS Provinsi Kepulauan Riau</b>. All rights reserved.
</div>
""",
    unsafe_allow_html=True,
)
