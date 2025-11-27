"""
Sentiment Analysis Module for News Articles
Supports Indonesian language sentiment analysis
"""

import pandas as pd
from typing import Optional
import re


def clean_text(text: str) -> str:
    """Clean text for sentiment analysis"""
    if not isinstance(text, str):
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Convert to lowercase
    text = text.lower()
    
    return text.strip()


def analyze_sentiment_simple(text: str) -> dict:
    """
    Simple rule-based sentiment analysis for Indonesian text
    Returns sentiment score and label
    """
    if not text or not isinstance(text, str):
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    
    text = clean_text(text)
    
    # Indonesian sentiment keywords
    positive_words = [
        'baik', 'bagus', 'hebat', 'senang', 'gembira', 'sukses', 'berhasil', 
        'positif', 'memuaskan', 'luar biasa', 'sempurna', 'mantap', 'optimal',
        'naik', 'meningkat', 'bertambah', 'berkembang', 'maju', 'unggul',
        'kemenangan', 'prestasi', 'pencapaian', 'apresiasi', 'pujian'
    ]
    
    negative_words = [
        'buruk', 'jelek', 'sedih', 'kecewa', 'gagal', 'negatif', 'tidak', 
        'kurang', 'sulit', 'masalah', 'kesulitan', 'krisis', 'bencana',
        'turun', 'menurun', 'berkurang', 'merosot', 'anjlok', 'jatuh',
        'korupsi', 'kriminal', 'kecelakaan', 'banjir', 'kebakaran', 'gempa',
        'kematian', 'keracunan', 'sakit', 'penyakit', 'covid', 'virus'
    ]
    
    # Count sentiment words
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    
    # Calculate score
    total_count = positive_count + negative_count
    
    if total_count == 0:
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    
    score = (positive_count - negative_count) / len(text.split()) * 100
    confidence = min(total_count / 10, 1.0)  # Max confidence at 10 sentiment words
    
    # Determine sentiment
    if score > 0.5:
        sentiment = "positive"
    elif score < -0.5:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "positive_count": positive_count,
        "negative_count": negative_count
    }


def analyze_dataframe_sentiment(df: pd.DataFrame, 
                                text_column: str = "content",
                                title_column: str = "title") -> pd.DataFrame:
    """
    Analyze sentiment for entire dataframe
    
    Args:
        df: Input dataframe with news articles
        text_column: Column name containing article content
        title_column: Column name containing article title
    
    Returns:
        DataFrame with added sentiment columns
    """
    
    if df is None or df.empty:
        return df
    
    # Check if required columns exist
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in dataframe")
    
    # Analyze sentiment for each row
    sentiments = []
    scores = []
    confidences = []
    
    for idx, row in df.iterrows():
        # Combine title and content for better analysis
        text_to_analyze = ""
        if title_column in df.columns and pd.notna(row[title_column]):
            text_to_analyze += str(row[title_column]) + " "
        if pd.notna(row[text_column]):
            text_to_analyze += str(row[text_column])
        
        result = analyze_sentiment_simple(text_to_analyze)
        sentiments.append(result["sentiment"])
        scores.append(result["score"])
        confidences.append(result["confidence"])
    
    # Add sentiment columns
    df_result = df.copy()
    df_result["sentiment"] = sentiments
    df_result["sentiment_score"] = scores
    df_result["sentiment_confidence"] = confidences
    
    return df_result


def get_sentiment_summary(df: pd.DataFrame) -> dict:
    """
    Get summary statistics of sentiment analysis
    
    Args:
        df: DataFrame with sentiment analysis results
    
    Returns:
        Dictionary with sentiment statistics
    """
    
    if df is None or df.empty or "sentiment" not in df.columns:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0
        }
    
    total = len(df)
    sentiment_counts = df["sentiment"].value_counts().to_dict()
    
    positive = sentiment_counts.get("positive", 0)
    negative = sentiment_counts.get("negative", 0)
    neutral = sentiment_counts.get("neutral", 0)
    
    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "positive_pct": round(positive / total * 100, 2) if total > 0 else 0.0,
        "negative_pct": round(negative / total * 100, 2) if total > 0 else 0.0,
        "neutral_pct": round(neutral / total * 100, 2) if total > 0 else 0.0
    }


def filter_by_sentiment(df: pd.DataFrame, sentiment: str) -> pd.DataFrame:
    """
    Filter dataframe by sentiment
    
    Args:
        df: DataFrame with sentiment analysis
        sentiment: Sentiment to filter ('positive', 'negative', 'neutral')
    
    Returns:
        Filtered DataFrame
    """
    
    if df is None or df.empty or "sentiment" not in df.columns:
        return df
    
    return df[df["sentiment"] == sentiment].copy()


# Example usage function for testing
def main():
    """Example usage"""
    
    # Sample data
    sample_data = {
        "title": [
            "Ekonomi Indonesia Tumbuh Positif",
            "Banjir Melanda Jakarta",
            "Harga Cabai Stabil"
        ],
        "content": [
            "Pertumbuhan ekonomi Indonesia menunjukkan tren positif dengan kenaikan 5.2 persen",
            "Banjir besar melanda Jakarta menyebabkan kerugian besar dan korban jiwa",
            "Harga cabai di pasar tradisional mengalami kestabilan setelah beberapa minggu"
        ]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Analyze sentiment
    df_analyzed = analyze_dataframe_sentiment(df)
    
    print("=== Sentiment Analysis Results ===")
    print(df_analyzed[["title", "sentiment", "sentiment_score", "sentiment_confidence"]])
    
    # Get summary
    summary = get_sentiment_summary(df_analyzed)
    print("\n=== Sentiment Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()