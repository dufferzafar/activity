#!/usr/bin/env python3
"""
Cluster YouTube Music search queries (short, multilingual, transliterated) with BERTopic.
Improvements over v1:
- Aggressive text normalization (remove filler words like "song", "lyrics", "full", "hd", etc.)
- Custom CountVectorizer with n-grams (1..3) and custom stopwords (incl. common Hindi/Urdu/Punjabi fillers)
- UMAP tuned for short texts (cosine, n_neighbors/min_dist configurable)
- HDBSCAN knobs exposed (min_cluster_size/min_samples), metric on reduced space
- Guided topics via seed_topic_list to steer to known buckets
- KeyBERTInspired representation to improve labels
- Outlier reduction and automatic topic reduction (nr_topics="auto")
- Saves clean report CSVs
Usage:
  pip install "bertopic[hdbscan]" sentence-transformers umap-learn scikit-learn
  python cluster_ytmusic_queries_v2.py --input ytmusic_search_terms.txt --model bge-m3 \
      --min-cluster-size 5 --min-samples 2 --n-neighbors 25 --min-dist 0.0 --auto-reduce
"""
import argparse
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any

import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
import hdbscan

from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired

# ------------------------ Parsing & Cleaning ------------------------

FILLER_REGEXES = [
    r'\b(full|official|audio|video|lyrics?|lyric|status|ringtone|hd|4k|8k|mp3|remix|song|songs?)\b',
    r'\b(new|latest|old|original|live|slowed|reverb|cover|female|male|version|feat|ft)\b',
    r'\b(hq|hq audio|hq video|ost|soundtrack)\b',
    r'[\(\)\[\]\{\}]',  # brackets
]

ROMAN_HI_UR_STOPWORDS = set("""
ka ki ke mein me mai hai hoon ho hun hona honaa hun
tum tumhe tumhi tumko tere teri tera teray
main mujhe mujh muj
mera meri mere hum hume hame ham
woh voh wo voh vo
aur ya yaa par per bhi bahut bahot bahut hi
se ko kaise kahan kaha kahaN
jab tak ho jaa jaye jayein hona tha thi the hain
pyar ishq mohabbat dil geet gana ganae gaana
""".split())

def clean_query(q: str) -> str:
    x = q.lower().strip()
    # normalize separators and punctuation
    x = re.sub(r'[-_/]+', ' ', x)
    x = re.sub(r'\s+', ' ', x)
    # remove filler tokens
    for pat in FILLER_REGEXES:
        x = re.sub(pat, ' ', x, flags=re.IGNORECASE)
    # normalize common phrases
    x = x.replace("jawab e shikwa", "jawab-e-shikwa")
    x = x.replace("noor ul khuda", "noor-ul-khuda")
    x = x.replace("ad duha", "ad-duha")
    x = x.replace("ar rahman", "ar-rahman")
    # strip extra spaces
    x = re.sub(r'\s+', ' ', x).strip()
    return x

def load_queries_df(json_path: str) -> pd.DataFrame:
    """
    Load DataFrame from a JSON file formatted like ytmusic.search.queries.json:
    [
      {"date": "YYYY-MM-DD", "queries": ["q1", "q2", ...]},
      ...
    ]
    Returns a DataFrame with columns: date (datetime.date), query (str), query_norm (str)
    """
    import json
    rows: List[Dict[str, Any]] = []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        date_str = entry.get("date")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        except Exception:
            dt = None
        for q in entry.get("queries", []) or []:
            if q is None:
                continue
            rows.append({"date": dt, "query": str(q)})
    df = pd.DataFrame(rows).dropna(how="all")
    if df.empty:
        return df
    df["query_norm"] = df["query"].str.replace(r"\s+", " ", regex=True).str.strip()
    return df

# ------------------------ Buckets (regex high-precision) ------------------------
BUCKET_RULES: List[Tuple[str, str]] = [
    (r'\b(surah|ayat|qur[\'`]?an|qirat|tilawat|ar[-\s]?rahman|rehman|mishary|alafasy|ad[-\s]?duha)\b', 'quran_recitation'),
    (r'\b(nusrat|nfak|abida|qawwal|qawwali|ghazal|shikwa|jawab[-\s]*e\s*shikwa|maikada|ishq)\b', 'sufi_qawwali_ghazal'),
    (r'\b(shiv|shivaya|bholenath|mahadev|bhajan|aarti)\b', 'hindu_devotional'),
    (r'\b(rap|hip[-\s]?hop|seedhemaut|talha anjum|badshah|gully|mumbai rap)\b', 'indian_hiphop_rap'),
    (r'\b(haryanvi|punjabi|khatola|ndee kundu|masoom sharma|gaadi paache|jattan ka chora|khapitar|toye bade|teer te taj)\b', 'regional_pop_haryanvi_punjabi'),
    (r'\b(kabhi khushi|javed bashir|aisa banna|tere bina|tumhe jo maine dekha|saiyaara|aap jaisa koi|rehnuma|atrangi yaari|yun hi koi mil gaya|ek mulakat|jab tak hai jaan|sajna ji vari|mera pehla pehla pyar|sang hoon tere|metro in dino|challa|humsafar|samjhawan|yahaan|tum bin|jannat)\b', 'bollywood_romance_pop'),
    (r'\b(veer ras|aarambh hai prachand|soorma|bhaag milkha|paan singh tomar|highway|dangal|kesari|motivation)\b', 'motivational_patriotic_ost'),
    (r'\b(kings of leon|deadmau5|your hand in mine|band perry|social network soundtrack|eye of the tiger)\b', 'western_rock_edm_instrumental'),
]

def apply_bucket_rules(text: str) -> str:
    t = text.lower()
    for pat, bucket in BUCKET_RULES:
        if re.search(pat, t, flags=re.IGNORECASE):
            return bucket
    return 'other_or_ambiguous'

# ------------------------ Model helpers ------------------------

def choose_model(name: str) -> SentenceTransformer:
    if name.lower() == 'bge-m3':
        model_name = 'BAAI/bge-m3'
    elif name.lower() == 'minilm':
        model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    else:
        raise ValueError("Unknown model. Use 'bge-m3' or 'minilm'.")
    return SentenceTransformer(model_name, device="mps")

def build_vectorizer():
    stop = ROMAN_HI_UR_STOPWORDS
    return CountVectorizer(
        ngram_range=(1,4),
        min_df=1,
        max_df=0.95,
        stop_words=list(stop),
        token_pattern=r"(?u)\b[\w'-]+\b"
    )

def build_umap(n_neighbors=25, min_dist=0.0, n_components=5, metric='cosine', random_state=42):
    return UMAP(n_neighbors=n_neighbors, min_dist=min_dist, n_components=n_components,
                metric=metric, random_state=random_state, verbose=False)

def build_hdbscan(min_cluster_size=5, min_samples=2):
    return hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                           min_samples=min_samples,
                           prediction_data=True)

# Seed topics to gently steer clusters towards known music buckets
SEED_TOPIC_LIST = [
    ["surah","quran","tilawat","qirat","rahman","duha","mishary","alafasy"],
    ["nusrat","nfak","abida","shikwa","jawab-e-shikwa","qawwali","ghazal","maikada","ishq"],
    ["shiv","shivaya","mahadev","bholenath","bhajan","aarti"],
    ["rap","hiphop","seedhemaut","talha","badshah","gully","mumbai"],
    ["haryanvi","punjabi","khatola","ndee","masoom","gaadi","jattan","khapitar","toye","teer"],
    ["romance","love","pyar","humsafar","samjhawan","yahaan","jannat","tum bin","kabhi khushi","rehnuma","saiyaara","aap jaisa"],
    ["veer","aarambh","soorma","bhaag","milkha","paan","singh","tomar","dangal","kesari","motivation"],
    ["kings of leon","deadmau5","your hand in mine","band perry","soundtrack","instrumental","edm","rock"],
]

def fit_model(docs: List[str], model_name: str,
              min_cluster_size: int, min_samples: int,
              n_neighbors: int, min_dist: float,
              auto_reduce: bool):
    embedder = choose_model(model_name)
    umap_model = build_umap(n_neighbors=n_neighbors, min_dist=min_dist)
    hdb_model = build_hdbscan(min_cluster_size=min_cluster_size, min_samples=min_samples)
    vectorizer_model = build_vectorizer()

    topic_model = BERTopic(
        embedding_model=embedder,
        umap_model=umap_model,
        hdbscan_model=hdb_model,
        vectorizer_model=vectorizer_model,
        language="multilingual",
        seed_topic_list=SEED_TOPIC_LIST,
        calculate_probabilities=False,
        verbose=True,
    )
    topics, _ = topic_model.fit_transform(docs)

    # Improve labels
    try:
        updated_model = topic_model.update_topics(docs, representation_model=KeyBERTInspired())
        # Some BERTopic versions return None (in-place update). If not None, use returned instance.
        if updated_model is not None:
            topic_model = updated_model    
    except Exception:
        pass

    # Reduce outliers: reassign -1 docs to nearest topics
    try:
        new_topics = topic_model.reduce_outliers(docs, topics)
        topics = new_topics
    except Exception:
        pass

    # Optional: auto-merge similar topics
    if auto_reduce:
        try:
            topic_model, topics = topic_model.reduce_topics(docs, nr_topics="auto")
        except Exception:
            pass

    return topic_model, topics

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="ytmusic_topics_v2")
    ap.add_argument("--model", default="bge-m3", choices=["bge-m3","minilm"])
    ap.add_argument("--min-cluster-size", type=int, default=4)
    ap.add_argument("--min-samples", type=int, default=1)
    ap.add_argument("--n-neighbors", type=int, default=25)
    ap.add_argument("--min-dist", type=float, default=0.0)
    ap.add_argument("--auto-reduce", action="store_true", default=True)
    ap.add_argument("--disable-ssl-verify", action="store_true", help="Disable SSL verification when downloading models (insecure)")
    args = ap.parse_args()

    if args.disable_ssl_verify:
        # Best-effort hooks to relax SSL verification in various stacks
        try:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]
        except Exception:
            pass
        os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFICATION", "1")
        os.environ.setdefault("PYTHONHTTPSVERIFY", "0")
        os.environ.setdefault("CURL_CA_BUNDLE", "")

    df = load_queries_df(args.input)
    docs = df["query_norm"].tolist()
    topic_model, topics = fit_model(
        docs, args.model, args.min_cluster_size, args.min_samples,
        args.n_neighbors, args.min_dist, args.auto_reduce
    )

    # Buckets via regex layer
    df["bucket"] = df["query_norm"].map(apply_bucket_rules)
    df["topic"] = topics

    # Topic labels
    def topic_label(tid: int) -> str:
        if tid == -1:
            return "Noise"
        words = topic_model.get_topic(tid)
        if not words:
            return f"Topic {tid}"
        return ', '.join([w for w, _ in words[:6]])

    df["topic_label"] = [topic_label(t) for t in topics]

    # Save
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)
    df.to_csv(f"{outdir}/assignments_v2.csv", index=False)
    topic_model.get_topic_info().to_csv(f"{outdir}/topics_v2.csv", index=False)

    # Print quick diagnostics
    n = len(df)
    noise = (df["topic"] == -1).sum()
    print(f"Total: {n} | Noise: {noise} ({noise/n:.1%}) | Topics: {df['topic'].nunique() - (1 if -1 in df['topic'].unique() else 0)}")

if __name__ == "__main__":
    import os
    main()
