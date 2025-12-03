import subprocess
import streamlit as st
from datetime import date
import sys
import pandas as pd
import os
import time
from pathlib import Path
from io import BytesIO, StringIO
import threading

st.set_page_config(
    page_title="FAKTA: Fenomena Aktual Terkini",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="auto",
)

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
    
    .timer-inline {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        color: white;
        font-size: 1rem;
        font-weight: bold;
        margin-left: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
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


def format_time(seconds):
    """Format seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def show_dataframe_preview(
    df,
    output_format,
    only_kepri=False,
    duration=None,
    keywords="",
    scrapers="",
    start_date="",
    end_date="",
):
    """Show preview of the dataframe"""
    try:
        # Filter by end date if provided
        if end_date and "publish_date" in df.columns:
            # Convert publish_date to datetime if it's not already
            df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
            # Filter rows where publish_date is <= end_date
            end_date_dt = (
                pd.to_datetime(end_date)
                + pd.Timedelta(days=1)
                - pd.Timedelta(seconds=1)
            )
            df = df[df["publish_date"] <= end_date_dt]
            # Convert back to string for display
            df["publish_date"] = df["publish_date"].dt.strftime("%Y-%m-%d")

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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            if duration is not None:
                st.metric("Scraping Time", f"{format_time(duration)} ({duration:.2f}s)")
        with col3:
            # Hitung ukuran file hasil scraping (CSV atau XLSX)
            if output_format == "csv":
                buffer = df.to_csv(index=False).encode("utf-8")
                size_bytes = len(buffer)
            else:
                buffer_io = BytesIO()
                df.to_excel(buffer_io, index=False)
                size_bytes = len(buffer_io.getvalue())

            # Konversi ke KB dan MB
            size_kb = size_bytes / 1024
            size_mb = size_bytes / (1024**2)

            # Tentukan tampilan otomatis: jika < 1 MB tampilkan dalam KB
            if size_mb >= 1:
                size_display = f"{size_mb:.2f} MB"
            else:
                size_display = f"{size_kb:.2f} KB"

            st.metric("File Size", size_display)
        with col4:
            # Date range info
            if start_date and end_date:
                date_range = f"{start_date} to {end_date}"
            elif start_date:
                date_range = f"From {start_date}"
            elif end_date:
                date_range = f"Until {end_date}"
            else:
                date_range = "All dates"
            st.metric("Date Range", date_range)

        st.write("### 🔍 Preview Hasil")

        # Add link column configuration if link exists
        if "link" in df.columns:
            st.dataframe(
                df.set_index(pd.Index(range(1, len(df) + 1))),
                column_config={
                    "link": st.column_config.LinkColumn(
                        "Link Berita", display_text="🔗 Buka"
                    )
                },
            )
        else:
            st.dataframe(df.set_index(pd.Index(range(1, len(df) + 1))))

        # Generate download filename
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        keywords_short = keywords.replace(",", "_")[:30] if keywords else "news"
        scrapers_short = scrapers.replace(",", "_")[:20] if scrapers else "all"

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
                type="primary",
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
                type="primary",
            )

        return df

    except Exception as e:
        st.error(f"❌ Error memproses data: {e}")
        return None


# Main form
with st.form("scraper_form"):
    st.write("### ⚙️ Konfigurasi Ekstraksi Berita")

    col1, col2 = st.columns(2)

    with col1:
        keywords = st.text_input(
            "Keywords (comma-separated)", "Harga Cabai, prabowo, BPS"
        )
        start_date = st.date_input("Start Date", None)
        output_format = st.selectbox("Output Format", ["csv", "xlsx"])
        only_kepri = st.checkbox("Fokuskan hanya berita kepri?")

    with col2:
        scrapers = st.multiselect("Pilih Scrapers", available_scrapers)
        end_date = st.date_input("End Date", None)

    submitted = st.form_submit_button("🚀 Run Ekstraksi", type="primary")

# Handle form submission
if submitted:
    # Validasi input wajib
    if not keywords.strip():
        st.warning(
            "⚠️ Harap isi minimal satu **keyword** sebelum menjalankan ekstraksi."
        )
        st.stop()

    if not scrapers:
        st.warning(
            "⚠️ Harap pilih minimal satu **scraper** sebelum menjalankan ekstraksi."
        )
        st.stop()

    if not start_date:
        st.warning(
            "⚠️ Harap pilih **tanggal mulai (Start Date)** sebelum menjalankan ekstraksi."
        )
        st.stop()

    # Validate date range
    if start_date > end_date:
        st.warning("⚠️ Tanggal mulai tidak boleh lebih dari tanggal akhir.")
        st.stop()

    # Use a temporary output directory
    temp_output = Path("temp_output")
    temp_output.mkdir(exist_ok=True)

    cmd = [sys.executable, "-m", "newswatch.cli"]

    if keywords:
        cmd += ["--keywords", keywords]
    if start_date:
        cmd += ["--start_date", str(start_date)]
    # Note: end_date is NOT passed to CLI, it will be used for filtering results
    if scrapers:
        cmd += ["--scrapers", ",".join(scrapers)]
    if output_format:
        cmd += ["--output_format", output_format]

    st.write("---")
    st.write("### 🔄 Execution")
    st.code(" ".join(cmd), language="bash")

    # Status display
    status_placeholder = st.empty()

    try:
        start_time = time.time()

        # Get list of files before scraping
        output_dir = Path("output")
        if output_dir.exists():
            before_files = set(output_dir.glob(f"*.{output_format}"))
        else:
            before_files = set()

        # Start subprocess
        status_placeholder.info("🔄 Memulai ekstraksi...")
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Update timer while process is running
        while process.poll() is None:
            elapsed = time.time() - start_time
            status_placeholder.markdown(
                f"""
            🔄 Memulai ekstraksi... <span class="timer-inline">⏱️ {format_time(elapsed)}</span>
            """,
                unsafe_allow_html=True,
            )
            time.sleep(0.1)

        # Get final duration
        duration = time.time() - start_time

        # Check if process was successful
        if process.returncode == 0:
            status_placeholder.success(
                f"✅ Ekstraksi selesai! Total waktu: {format_time(duration)} ({duration:.2f}s)"
            )

            # Get stdout
            stdout, stderr = process.communicate()

            # Show command output
            if stdout:
                with st.expander("📄 Command Output", expanded=False):
                    st.code(stdout)

            # Find the newly created file
            if output_dir.exists():
                after_files = set(output_dir.glob(f"*.{output_format}"))
                new_files = after_files - before_files

                if new_files:
                    # Get the most recent new file
                    latest_file = max(new_files, key=os.path.getctime)

                    # Read the file
                    if output_format == "csv":
                        df = pd.read_csv(latest_file)
                    else:
                        df = pd.read_excel(latest_file)

                    # Display results
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
                        end_date=str(end_date),
                    )

                    # Delete the file after reading
                    try:
                        latest_file.unlink()
                    except:
                        pass
                else:
                    st.warning("⚠️ Tidak ada data ditemukan dari ekstraksi ini.")
            else:
                st.warning("⚠️ Output folder tidak ditemukan.")
        else:
            stdout, stderr = process.communicate()
            status_placeholder.error("❌ Error saat menjalankan ekstraksi")
            if stderr:
                st.code(stderr)

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
