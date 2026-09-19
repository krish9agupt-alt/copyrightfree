import os
import re
import time
import json
import glob
import gc
import hashlib
import threading
import secrets
import shutil
import urllib.parse
from datetime import datetime, timedelta

# ============================================================
# BypassTube.in - Multi-Brand Creator Suite (YT + FB + IG)
# Streamlit Single-File Application
# ============================================================

# -----------------------------
# CPU/Thread Limits & Performance Optimization
# -----------------------------
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")

import streamlit as st
import streamlit.components.v1 as components

try:
    import extra_streamlit_components as stx
except ImportError:
    stx = None

import numpy as np
from PIL import Image

# Help MoviePy locate FFmpeg
try:
    import imageio_ffmpeg
    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", imageio_ffmpeg.get_ffmpeg_exe())
except Exception:
    pass

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx
    from proglog import ProgressBarLogger
except ImportError:
    st.error(
        "MoviePy/proglog is missing. Please install the required packages and ensure FFmpeg is available on your system."
    )
    st.stop()

# Pillow Resampling Compatibility Fix
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# -----------------------------
# Global Application Configuration
# -----------------------------
MAX_VIDEO_MB = int(os.getenv("MAX_VIDEO_MB", "200"))
MAX_VIDEO_BYTES = MAX_VIDEO_MB * 1024 * 1024

try:
    st.set_option("server.maxUploadSize", MAX_VIDEO_MB)
except Exception:
    pass

st.set_page_config(
    page_title="BypassTube.in",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "BypassTube.in"
DB_FILE = "database.json"
EXPORT_DIR = "exports"
TEMP_DIR = "temp_files"

TELEGRAM_SUPPORT_URL = os.getenv(
    "TELEGRAM_SUPPORT_URL",
    "https://t.me/+Yhr7ZJWcqBwyNmFl",
)
DEFAULT_UPI = os.getenv("UPI_ID", "cinepoliis@ibl").strip()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "Krish9agupt@gmail.com").strip().lower()
ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE", "Krish9@")

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ============================================================
# Database Engine
# ============================================================
def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def get_default_watch_tasks():
    tasks = []
    sample_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
        "https://www.youtube.com/watch?v=L_LUpnjgPso",
        "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
        "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
        "https://www.youtube.com/watch?v=2Vv-BfVoq4g",
        "https://www.youtube.com/watch?v=60ItHLz5WEA",
        "https://www.youtube.com/watch?v=paper_clip_1",
        "https://www.youtube.com/watch?v=creator_vid_9",
        "https://www.youtube.com/watch?v=creator_vid_10"
    ]
    for i in range(1, 11):
        tasks.append({
            "id": f"watch_{i}",
            "title": f"▶️ Watch Creator Video #{i}",
            "url": sample_urls[i-1],
            "reward": 10,
            "seconds": 30,
        })
    return tasks

def default_db():
    return {
        "users": {},
        "passwords": {},
        "moderators": {},
        "pending_requests": [],
        "support_tickets": [],
        "claimed_tasks": {},
        "task_claim_times": {},
        "history": {},
        "exports": {},
        "login_tokens": {},
        "admin_links": {
            "yt_url": "https://youtube.com",
            "insta_url": "https://instagram.com",
            "fb_url": "https://facebook.com",
            "wa_channel_url": "https://whatsapp.com/channel/",
            "upi_id": DEFAULT_UPI,
        },
        "watch_tasks": get_default_watch_tasks(),
        "settings": {
            "credits_per_rupee": 2,
            "signup_credits": 50,
            "youtube_task_credits": 10,
            "instagram_task_credits": 10,
            "facebook_task_credits": 10,
        },
    }

def load_db():
    base = default_db()
    if not os.path.exists(DB_FILE):
        save_db(base)
        return base

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)

        for key, value in base.items():
            if key not in db:
                db[key] = value

        for section in ["admin_links", "settings"]:
            db.setdefault(section, {})
            for key, value in base[section].items():
                db[section].setdefault(key, value)

        db.setdefault("moderators", {})
        db.setdefault("task_claim_times", {})

        if "watch_tasks" not in db or not isinstance(db["watch_tasks"], list) or len(db["watch_tasks"]) < 10:
            existing = {t.get("id"): t for t in db.get("watch_tasks", []) if isinstance(t, dict)}
            new_tasks = []
            for i in range(1, 11):
                tid = f"watch_{i}"
                if tid in existing:
                    new_tasks.append(existing[tid])
                else:
                    new_tasks.append({
                        "id": tid,
                        "title": f"▶️ Watch Creator Video #{i}",
                        "url": "https://youtube.com",
                        "reward": 10,
                        "seconds": 30,
                    })
            db["watch_tasks"] = new_tasks

        return db
    except Exception:
        return base

def save_db(data):
    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DB_FILE)


# ============================================================
# General Utilities
# ============================================================
def safe_filename(name: str, fallback="video.mp4") -> str:
    name = os.path.basename(name or fallback)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:160] or fallback

def format_time(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def file_size_mb(path):
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return 0

def cleanup_storage(temp_file=None, max_age_hours=24):
    if temp_file:
        try:
            if os.path.isfile(temp_file):
                os.remove(temp_file)
        except OSError:
            pass

    now = time.time()
    for directory in [TEMP_DIR, EXPORT_DIR]:
        for path in glob.glob(os.path.join(directory, "*")):
            if not os.path.isfile(path):
                continue
            try:
                age = (now - os.path.getmtime(path)) / 3600
                if age > max_age_hours:
                    os.remove(path)
            except OSError:
                pass
    gc.collect()

def validate_url(url):
    try:
        parsed = urllib.parse.urlparse(url.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False

def get_yt_embed_url(url):
    """Convert standard YouTube URL to Embed URL"""
    if not url:
        return ""
    if "youtube.com/embed/" in url:
        return url

    video_id = None
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    elif "youtube.com/watch" in url:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "v" in params:
            video_id = params["v"][0]

    if video_id:
        return f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&autoplay=1"
    return url


# ============================================================
# Global Render Engine Slot Locking
# ============================================================
@st.cache_resource
def get_render_engine():
    return {
        "lock": threading.Lock(),
        "active_user": None,
        "started_at": None,
    }

def acquire_render_slot(user_email):
    engine = get_render_engine()
    with engine["lock"]:
        if engine["active_user"] is None:
            engine["active_user"] = user_email
            engine["started_at"] = time.time()
            return True, None
        if engine["active_user"] == user_email:
            return True, None
        return False, engine["active_user"]

def release_render_slot(user_email):
    engine = get_render_engine()
    with engine["lock"]:
        if engine["active_user"] == user_email:
            engine["active_user"] = None
            engine["started_at"] = None


# ============================================================
# Session & Persistent Auto-Login Authentication
# ============================================================
COOKIE_NAME = "bypasstube_login_session"
LOGIN_TOKEN_DAYS = 60

@st.cache_resource
def get_cookie_manager():
    if stx is None:
        return None
    return stx.CookieManager(key="bypasstube_cookie_manager")

def _get_cookie(name):
    manager = get_cookie_manager()
    if manager is None:
        return None
    try:
        val = manager.get(name)
        return val
    except Exception:
        return None

def _set_cookie(name, value, days=LOGIN_TOKEN_DAYS):
    manager = get_cookie_manager()
    if manager is None:
        return False
    try:
        manager.set(
            name,
            value,
            expires_at=datetime.now() + timedelta(days=days),
        )
        return True
    except Exception:
        return False

def _delete_cookie(name):
    manager = get_cookie_manager()
    if manager is None:
        return False
    try:
        manager.delete(name)
        return True
    except Exception:
        return False

def create_login_token(email, role):
    token = secrets.token_urlsafe(48)
    token_hash = hash_text(token)
    db = load_db()

    now = time.time()
    tokens = db.setdefault("login_tokens", {})
    for old_hash, data in list(tokens.items()):
        try:
            if float(data.get("expires_at", 0)) <= now:
                del tokens[old_hash]
        except Exception:
            del tokens[old_hash]

    tokens[token_hash] = {
        "email": email.strip().lower(),
        "role": role,
        "expires_at": now + (LOGIN_TOKEN_DAYS * 24 * 60 * 60),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_db(db)
    return token

def remove_login_token(token):
    if not token:
        return
    token_hash = hash_text(str(token))
    db = load_db()
    tokens = db.setdefault("login_tokens", {})
    if token_hash in tokens:
        del tokens[token_hash]
        save_db(db)

def restore_login_from_cookie():
    token = _get_cookie(COOKIE_NAME)
    if not token:
        return False

    token_hash = hash_text(str(token))
    db = load_db()
    record = db.get("login_tokens", {}).get(token_hash)
    if not record:
        return False

    try:
        if float(record.get("expires_at", 0)) <= time.time():
            del db["login_tokens"][token_hash]
            save_db(db)
            _delete_cookie(COOKIE_NAME)
            return False
    except Exception:
        return False

    email = str(record.get("email", "")).strip().lower()
    role = str(record.get("role", "user"))

    if not email:
        return False

    valid = (email == ADMIN_EMAIL) if role == "admin" else (email in db.get("passwords", {}))
    if not valid:
        remove_login_token(token)
        _delete_cookie(COOKIE_NAME)
        return False

    st.session_state["logged_in"] = True
    st.session_state["user_email"] = email
    st.session_state["role"] = "admin" if role == "admin" else "user"
    st.session_state["remember_me"] = True
    return True

def save_remembered_login(email, role):
    db = load_db()
    tokens = db.setdefault("login_tokens", {})
    for token_hash, record in list(tokens.items()):
        if str(record.get("email", "")).strip().lower() == email.strip().lower():
            del tokens[token_hash]
    save_db(db)

    token = create_login_token(email, role)
    _set_cookie(COOKIE_NAME, token, LOGIN_TOKEN_DAYS)

def clear_remembered_login():
    token = _get_cookie(COOKIE_NAME)
    if token:
        remove_login_token(token)
    _delete_cookie(COOKIE_NAME)

def init_session():
    defaults = {
        "logged_in": False,
        "user_email": "",
        "role": "user",
        "active_menu": "Home",
        "vid_watch_data": {},
        "seo_result": None,
        "processing_message": "",
        "remember_me": True,
        "cookie_restore_checked": False,
        "wa_popup_dismissed": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state["logged_in"] and not st.session_state["cookie_restore_checked"]:
        st.session_state["cookie_restore_checked"] = True
        restore_login_from_cookie()

def logout():
    clear_remembered_login()
    for key in ["logged_in", "user_email", "role", "active_menu", "vid_watch_data", "seo_result", "processing_message", "remember_me", "cookie_restore_checked", "wa_popup_dismissed"]:
        st.session_state.pop(key, None)
    st.rerun()

def authenticate(email, passcode):
    email = email.strip().lower()
    passcode = passcode.strip()

    if (
        email == ADMIN_EMAIL
        and ADMIN_PASSCODE
        and hash_text(passcode) == hash_text(ADMIN_PASSCODE)
    ):
        return True, "admin"

    db = load_db()
    stored_pwd_hash = db.get("passwords", {}).get(email)
    if stored_pwd_hash and stored_pwd_hash == hash_text(passcode):
        return True, "user"

    return False, "user"

init_session()


# ============================================================
# High-Speed File Transfer & Video Pipeline (Optimized for Fast Uploads)
# ============================================================
def save_uploaded_file_fast(uploaded_file, prefix="upload", progress_bar=None, status_text=None):
    """
    High-Speed Video File Transfer Engine:
    Optimized with 8MB buffered chunks and throttled UI updates for maximum upload speed and stability.
    """
    if uploaded_file is None:
        raise ValueError("No video file selected.")
    if not uploaded_file.name:
        raise ValueError("The uploaded file has no filename.")
    if uploaded_file.size <= 0:
        raise ValueError("The uploaded file is empty.")
    if uploaded_file.size > MAX_VIDEO_BYTES:
        raise ValueError(f"Video exceeds maximum allowed limit of {MAX_VIDEO_MB} MB.")

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        raise ValueError("Unsupported video format.")

    safe_name = safe_filename(uploaded_file.name)
    filename = f"{prefix}_{int(time.time() * 1000)}_{safe_name}"
    path = os.path.join(TEMP_DIR, filename)

    started = time.time()
    total_size = uploaded_file.size

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    # Increased chunk size to 8MB for blazing fast upload performance
    chunk_size = 8 * 1024 * 1024
    bytes_written = 0
    last_update_time = 0.0

    with open(path, "wb") as f:
        while True:
            chunk = uploaded_file.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            bytes_written += len(chunk)

            now = time.time()
            if progress_bar and total_size > 0 and (now - last_update_time >= 0.1 or bytes_written == total_size):
                last_update_time = now
                pct = int((bytes_written / total_size) * 100)
                elapsed = max(now - started, 0.001)
                speed_mb = (bytes_written / (1024 * 1024)) / elapsed
                remaining_bytes = total_size - bytes_written
                eta_seconds = (remaining_bytes / (bytes_written / elapsed)) if bytes_written > 0 else 0

                progress_bar.progress(min(100, max(0, pct)))
                if status_text:
                    status_text.markdown(
                        f"""
                        <div class="processing-status-card upload-animating">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b>🚀 Turbo Uploading to BypassTube.in:</b>
                                <span class="pct-glow">{pct}%</span>
                            </div>
                            <div style="margin-top:6px; font-size:0.85rem;">
                                ⚡ Transfer Speed: <b style="color:#00F2FE;">{speed_mb:.2f} MB/s</b> | ⏱️ ETA: {int(eta_seconds)}s | Processed: {bytes_written / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    actual_size = os.path.getsize(path)
    if actual_size <= 0:
        cleanup_storage(path)
        raise IOError("Upload integrity check failed.")

    return path, round(time.time() - started, 2)


class StreamlitProgressLogger(ProgressBarLogger):
    def __init__(self, progress_bar, status_text, start_time):
        super().__init__()
        self.progress_bar = progress_bar
        self.status_text = status_text
        self.start_time = start_time

    def bars_callback(self, bar, attr, value, old_value):
        if bar != "t":
            return
        try:
            total = self.bars[bar]["total"]
            if total and total > 0:
                pct = int((value / total) * 100)
                elapsed = max(time.time() - self.start_time, 0.01)
                speed = value / elapsed

                self.progress_bar.progress(min(100, max(0, pct)))
                self.status_text.markdown(
                    f"""
                    <div class="processing-status-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b>🔥 Anti-Copyright Engine Rendering...</b>
                            <span class="pct-glow">{pct}%</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem;">
                            ⚡ Render Speed: <b style="color:#00F2FE;">{speed:.2f}x</b> | ⏱️ Elapsed: {int(elapsed)}s
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

def manual_zoom(clip, zoom_factor):
    zoom_factor = max(1.0, float(zoom_factor))
    def zoom_frame(frame):
        h, w = frame.shape[:2]
        crop_h = max(2, int(h / zoom_factor))
        crop_w = max(2, int(w / zoom_factor))
        top = max(0, (h - crop_h) // 2)
        left = max(0, (w - crop_w) // 2)
        cropped = frame[top:top + crop_h, left:left + crop_w]
        resampler = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.BICUBIC
        return np.array(Image.fromarray(cropped).resize((w, h), resampler))
    return clip.fl_image(zoom_frame)

def apply_custom_effects(clip, edit_num=1):
    if edit_num in [2, 8]: clip = manual_zoom(clip, 1.10)
    elif edit_num == 3: clip = clip.speedx(1.1) if hasattr(clip, 'speedx') else clip
    elif edit_num in [4, 13]: clip = clip.fx(vfx.colorx, 0.90) if hasattr(vfx, 'colorx') else clip
    elif edit_num in [5, 11, 15]: clip = clip.fx(vfx.colorx, 1.20) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 6: clip = clip.fl_image(lambda img: img[:, ::-1])
    elif edit_num == 7: clip = clip.fx(vfx.colorx, 1.10) if hasattr(vfx, 'colorx') else clip
    elif edit_num == 9: clip = clip.speedx(1.15) if hasattr(clip, 'speedx') else clip
    elif edit_num == 10: clip = manual_zoom(clip, 1.05)
    elif edit_num == 12: clip = manual_zoom(clip, 1.12)
    elif edit_num == 14:
        clip = clip.fl_image(lambda img: img[:, ::-1])
        if hasattr(clip, 'speedx'): clip = clip.speedx(1.1)
    return clip

def process_video(input_path, output_path, target_height, bitrate, progress, status, edit_strength=True):
    video = None
    final_clip = None
    clips = []
    try:
        status.info("🎬 Initializing BypassTube Accelerated Engine...")
        progress.progress(5)
        video = VideoFileClip(input_path)
        if not video.duration or video.duration <= 0:
            raise ValueError("Invalid video file duration.")

        duration = max(float(video.duration), 0.1)
        segment = duration / 15.0

        for idx in range(1, 16):
            start = (idx - 1) * segment
            end = min(idx * segment, duration)
            subclip = video.subclip(start, end)
            edited = apply_custom_effects(subclip, idx) if edit_strength else subclip
            clips.append(edited)
            progress.progress(min(70, 10 + idx * 4))

        status.info("🧩 Injecting Multi-Layered Anti-Copyright Audio/Visual Hashes...")
        final_clip = concatenate_videoclips(clips, method="compose")

        orig_w, orig_h = video.size
        aspect = orig_w / float(orig_h or 1)

        if target_height and orig_h != target_height:
            new_w = max(2, int(target_height * aspect))
            if new_w % 2: new_w += 1
            final_clip = final_clip.resize(newsize=(new_w, target_height))

        progress.progress(80)
        start_render_time = time.time()
        custom_logger = StreamlitProgressLogger(progress, status, start_render_time)
        temp_audio = os.path.join(TEMP_DIR, f"render_audio_{int(time.time() * 1000)}.m4a")

        ffmpeg_params = ["-preset", "ultrafast", "-tune", "fastdecode"]

        final_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac", bitrate=bitrate, preset="ultrafast",
            threads=4, ffmpeg_params=ffmpeg_params, logger=custom_logger, temp_audiofile=temp_audio, remove_temp=True,
        )

        progress.progress(100)
        status.success("✅ Anti-Copyright Export Rendered Successfully!")
    finally:
        try:
            if final_clip: final_clip.close()
        except Exception: pass
        for clip in clips:
            try: clip.close()
            except Exception: pass
        try:
            if video: video.close()
        except Exception: pass

def process_clips(input_path, interval, user_email, progress, status):
    video = None
    created = []
    try:
        video = VideoFileClip(input_path)
        if not video.duration or video.duration <= 0:
            raise ValueError("Could not read video duration.")

        current = 0.0
        count = 1
        total_duration = float(video.duration)

        while current < total_duration:
            end = min(current + interval, total_duration)
            start_str, end_str = format_time(current), format_time(end)
            status.info(f"✂️ Generating Clip Part {count}: {start_str} → {end_str}")
            sub = None
            try:
                sub = apply_custom_effects(video.subclip(current, end), count)
                out_name = f"BypassTube_Clip_{count}_{int(time.time())}_{hash_text(user_email)[:8]}.mp4"
                out_path = os.path.join(EXPORT_DIR, out_name)
                sub.write_videofile(out_path, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4, ffmpeg_params=["-preset", "ultrafast"], logger=None)
                created.append({"path": out_path, "name": out_name, "start": start_str, "end": end_str})
                pct = int(min(100, (end / total_duration) * 100))
                progress.progress(pct)
            finally:
                if sub:
                    try: sub.close()
                    except Exception: pass
            current = end
            count += 1

        status.success(f"✅ {len(created)} Clip(s) Split & Exported Successfully!")
        return created
    finally:
        if video:
            try: video.close()
            except Exception: pass


# ============================================================
# AI SEO Generator
# ============================================================
def generate_seo_from_topic(topic, platform="YouTube", tone="Viral"):
    clean = topic.strip().title()
    if tone == "Viral":
        titles = [
            f"🔥 Why Everyone Is Talking About {clean} 😱 #Shorts",
            f"🚀 {clean} Unfiltered Highlights You Must See!",
            f"⚡ The Secrets Behind {clean} Revealed"
        ]
    elif tone == "Educational":
        titles = [
            f"💡 Complete Masterclass Guide to {clean}",
            f"📚 {clean} Explained in Under 60 Seconds",
            f"🛠️ Step-by-Step Breakdown of {clean}"
        ]
    else:
        titles = [
            f"✨ Cinematic Experience: {clean} 4K",
            f"🎬 Unbelievable Aesthetic Moments of {clean}",
            f"🌟 Exploring {clean} Like Never Before"
        ]

    desc = (f"🎬 {clean}\n\n"
            f"Watch the ultimate coverage and analysis on {clean}. "
            f"Processed with {APP_NAME} for anti-copyright compatibility.\n\n"
            f"📌 Timestamps:\n0:00 - Intro & Key Highlights\n0:30 - Main Event Breakdown\n1:00 - Deep Dive Analysis\n1:30 - Summary & Outro\n\n"
            f"🔔 Subscribe and hit the bell for more viral content updates!")

    tags = [clean.lower(), f"{clean.lower()} shorts", "bypasstube", "viral reels", "trending video", "creator tools"]
    hashtags = f"#shorts #viral #trending #reels #{re.sub(r'[^A-Za-z0-9]', '', clean)} #BypassTube #CreatorStudio"

    if platform == "Instagram":
        main_text = f"✨ {clean} | Multi-Brand Edition 🚀\n\n{hashtags}\n\n📲 Follow for daily viral video highlights!"
    elif platform == "Facebook":
        main_text = f"📘 Featured Video Breakdown: {clean}\n\n{desc}\n\n{hashtags}"
    else:
        main_text = desc

    return {"titles": titles, "description": main_text, "tags": tags, "hashtags": hashtags, "score": 99}

def generate_upi_qr(upi_id, amount, name=APP_NAME):
    pay_url = f"upi://pay?pa={urllib.parse.quote(upi_id)}&pn={urllib.parse.quote(name)}&am={amount}&cu=INR"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(pay_url)}"


# ============================================================
# Advanced Brand CSS with Upload Animation
# ============================================================
st.markdown(
    """
<style>
:root {
    --bg-dark: #07090e;
    --yt-red: #FF0000;
    --yt-red-glow: #FF2A2A;
    --fb-blue: #1877F2;
    --fb-blue-glow: #0066FF;
    --ig-magenta: #E1306C;
    --ig-purple: #833AB4;
    --ig-gradient: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
    --panel-card: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(7, 12, 23, 0.98));
    --border-card: rgba(255, 255, 255, 0.12);
    --text-white: #FFFFFF;
    --text-muted: #94A3B8;
    --cyan-glow: #00F2FE;
}

#MainMenu, header, footer { visibility: hidden; }

.stApp {
    background: radial-gradient(circle at 10% 10%, rgba(255, 0, 0, 0.12), transparent 30%),
                radial-gradient(circle at 90% 20%, rgba(24, 119, 242, 0.15), transparent 35%),
                radial-gradient(circle at 50% 90%, rgba(225, 48, 108, 0.12), transparent 40%),
                var(--bg-dark) !important;
}

.block-container { max-width: 1550px; padding: 10px 16px 80px !important; }
p, span, label, li { color: var(--text-muted) !important; }
h1, h2, h3, h4, h5, h6 { color: var(--text-white) !important; font-weight: 900 !important; }

/* Upload Pulse Animation */
@keyframes uploadPulse {
    0% { box-shadow: 0 0 10px #FF0000; border-color: #FF0000; }
    50% { box-shadow: 0 0 30px #00F2FE; border-color: #00F2FE; }
    100% { box-shadow: 0 0 10px #FF0000; border-color: #FF0000; }
}

.upload-animating {
    animation: uploadPulse 1.8s infinite ease-in-out !important;
    background: rgba(0, 242, 254, 0.06) !important;
}

/* Animated Text Under BypassTube.in */
@keyframes brandColorCycle {
    0%, 30% { color: #FF0000; text-shadow: 0 0 15px rgba(255, 0, 0, 0.8); }
    33%, 63% { color: #1877F2; text-shadow: 0 0 15px rgba(24, 119, 242, 0.8); }
    66%, 96% { color: #E1306C; text-shadow: 0 0 15px rgba(225, 48, 108, 0.8); }
    100% { color: #FF0000; text-shadow: 0 0 15px rgba(255, 0, 0, 0.8); }
}

.animated-brand-subtext {
    font-size: 1.05rem;
    font-weight: 900;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    animation: brandColorCycle 6s infinite ease-in-out;
    display: inline-block;
    margin-top: 2px;
}

/* Glassmorphism Cards */
.card-box, .task-card, .hero-card, .upload-card {
    background: var(--panel-card);
    border: 1px solid var(--border-card);
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(16px);
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.card-box:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 42, 42, 0.4);
    box-shadow: 0 20px 45px rgba(255, 0, 0, 0.2), inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

/* Header Banner */
.app-header {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
    padding: 16px 24px; background: linear-gradient(135deg, rgba(255,0,0,0.15), rgba(24,119,242,0.15), rgba(225,48,108,0.15));
    border: 1px solid rgba(255,255,255,0.2); border-radius: 24px; margin-bottom: 18px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.3);
}

.brand-title {
    font-size: 2.1rem; font-weight: 950; color: white !important; letter-spacing: -0.5px;
    display: flex; align-items: center; gap: 8px;
}

/* Default Button Styling */
.stButton > button, div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #FF0000 0%, #1877F2 50%, #E1306C 100%) !important;
    background-size: 200% 200% !important;
    color: #FFFFFF !important; border: none !important; border-radius: 16px !important;
    min-height: 50px !important; font-weight: 950 !important; font-size: 0.98rem !important;
    box-shadow: 0 6px 0 #880000, 0 12px 25px rgba(255, 0, 0, 0.35) !important;
    transform: translateY(0px); transition: all 0.2s ease !important;
}
.stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {
    background-position: right center !important;
    box-shadow: 0 8px 0 #0044aa, 0 15px 30px rgba(225, 48, 108, 0.45) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active, div[data-testid="stDownloadButton"] > button:active {
    transform: translateY(4px) !important;
    box-shadow: 0 2px 0 #880000, 0 5px 10px rgba(255, 0, 0, 0.3) !important;
}
.stButton > button p, .stButton > button span, div[data-testid="stDownloadButton"] > button p, div[data-testid="stDownloadButton"] > button span {
    color: #FFFFFF !important; font-weight: 950 !important;
}

/* Feature Cards */
.feature-card {
    background: linear-gradient(145deg, rgba(255,0,0,0.08), rgba(24,119,242,0.08));
    border: 1px solid rgba(255,255,255,0.15); border-radius: 20px; padding: 20px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4), inset 0 1px 1px rgba(255,255,255,0.2);
    transition: transform 0.3s ease;
}
.feature-card:hover { transform: translateY(-5px); border-color: #E1306C; }

/* Status Speed Display */
.processing-status-card {
    background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(8,13,24,0.99));
    border: 1px solid var(--yt-red); border-radius: 18px; padding: 16px 20px;
    box-shadow: 0 0 30px rgba(255,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.2);
}
.pct-glow {
    color: var(--yt-red-glow) !important; font-size: 1.4rem; font-weight: 950;
    text-shadow: 0 0 12px rgba(255,42,42,0.8);
}

/* Form Inputs */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea {
    background: rgba(15,23,42,0.95) !important; border: 1px solid var(--border-card) !important;
    color: white !important; border-radius: 14px !important; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5) !important;
}
input { color: white !important; }

/* Badges */
.badge-yt { background: #FF0000; color: white !important; padding: 6px 16px; border-radius: 999px; font-weight: 900; font-size: 0.8rem; }
.badge-ig { background: var(--ig-gradient); color: white !important; padding: 6px 16px; border-radius: 999px; font-weight: 900; font-size: 0.8rem; }
.badge-fb { background: #1877F2; color: white !important; padding: 6px 16px; border-radius: 999px; font-weight: 900; font-size: 0.8rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# Header Banner
# ============================================================
st.markdown(
    f"""
<div class="app-header">
    <div>
        <div class="brand-title">🎬 BypassTube.in</div>
        <div class="animated-brand-subtext">
            🔴 YouTube &nbsp;•&nbsp; 📸 Instagram &nbsp;•&nbsp; 📘 Facebook
        </div>
    </div>
    <a href="{TELEGRAM_SUPPORT_URL}" target="_blank"
       style="color:#FFF; text-decoration:none; font-weight:900; font-size:.85rem; background:linear-gradient(45deg,#0088cc,#00f2fe); padding:10px 20px; border-radius:14px; box-shadow:0 6px 20px rgba(0,136,204,0.4);">
       ✈️ Telegram Support Desk
    </a>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# WhatsApp Channel Popup Widget
# ============================================================
db = load_db()
wa_channel_link = db.get("admin_links", {}).get("wa_channel_url", "https://whatsapp.com/channel/")

if not st.session_state.get("wa_popup_dismissed", False) and wa_channel_link:
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, #128C7E, #25D366); padding:14px 20px; border-radius:18px; color:white; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; box-shadow:0 10px 25px rgba(37,211,102,0.3);">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:2rem;">💬</span>
                <div>
                    <div style="font-weight:950; font-size:1.05rem; color:white;">Join Our Official WhatsApp Channel!</div>
                    <small style="color:#E8F5E9 !important;">Get daily anti-copyright presets, instant credit alerts & updates!</small>
                </div>
            </div>
            <a href="{wa_channel_link}" target="_blank" style="background:white; color:#128C7E; font-weight:900; text-decoration:none; padding:10px 22px; border-radius:12px; font-size:0.9rem; box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                🚀 Join Channel Now →
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# Auth Portal (Sign In / Sign Up)
# ============================================================
if not st.session_state.logged_in:

    st.markdown(
        """
<div class="hero-card" style="text-align:center;">
    <div style="font-size:3.8rem; filter:drop-shadow(0 0 20px rgba(255,0,0,0.6)); margin-bottom:10px;">▶️</div>
    <h1 style="font-size:2.8rem; margin-bottom:2px;">BypassTube.in</h1>
    <div class="animated-brand-subtext" style="font-size:1.2rem; margin-bottom:12px;">
        YouTube &nbsp;•&nbsp; Instagram &nbsp;•&nbsp; Facebook
    </div>
    <p style="font-size:1.1rem; color:#94A3B8 !important;">Advanced Anti-Copyright Video Processor for Creator Content</p>
    <div style="display:flex; justify-content:center; gap:12px; margin-top:15px; flex-wrap:wrap;">
        <span class="badge-yt">🔴 YouTube</span>
        <span class="badge-ig">📸 Instagram</span>
        <span class="badge-fb">📘 Facebook</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    login_tab, signup_tab = st.tabs(["🔐 Sign In", "✨ Create Account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="Enter your email address")
            password = st.text_input("Passcode", type="password", placeholder="Enter passcode")
            remember = st.checkbox("Keep me logged in (Persistent Session)", value=True)
            submitted = st.form_submit_button("Sign In  →", use_container_width=True)

            if submitted:
                ok, role = authenticate(email, password)
                if ok:
                    clean_email = email.strip().lower()
                    db = load_db()
                    if role == "user":
                        db["users"].setdefault(clean_email, int(db["settings"].get("signup_credits", 50)))
                    save_db(db)

                    st.session_state.logged_in = True
                    st.session_state.user_email = clean_email
                    st.session_state.role = role
                    st.session_state.remember_me = remember
                    st.session_state.active_menu = "Home"

                    if remember:
                        save_remembered_login(clean_email, role)

                    st.rerun()
                else:
                    st.error("❌ Invalid email address or passcode.")

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("Email Address", placeholder="you@example.com", key="signup_email")
            new_pass = st.text_input("Create Passcode", type="password", placeholder="Create secure passcode", key="signup_pass")
            confirm_pass = st.text_input("Confirm Passcode", type="password", placeholder="Repeat passcode", key="signup_confirm")
            signup_submitted = st.form_submit_button("Create Account & Start  →", use_container_width=True)

            if signup_submitted:
                clean_email = new_email.strip().lower()
                if not clean_email or "@" not in clean_email:
                    st.error("❌ Please enter a valid email address.")
                elif len(new_pass) < 6:
                    st.error("❌ Passcode must contain at least 6 characters.")
                elif new_pass != confirm_pass:
                    st.error("❌ Passcodes do not match.")
                else:
                    db = load_db()
                    if clean_email in db["passwords"] or clean_email == ADMIN_EMAIL:
                        st.error("❌ An account with this email already exists.")
                    else:
                        signup_credits = int(db["settings"].get("signup_credits", 50))
                        db["passwords"][clean_email] = hash_text(new_pass)
                        db["users"][clean_email] = signup_credits
                        db["history"].setdefault(clean_email, [])
                        db["claimed_tasks"].setdefault(clean_email, [])
                        db["task_claim_times"].setdefault(clean_email, {})
                        save_db(db)

                        st.session_state.logged_in = True
                        st.session_state.user_email = clean_email
                        st.session_state.role = "user"
                        st.session_state.active_menu = "Home"

                        save_remembered_login(clean_email, "user")
                        st.success(f"🎉 Account created! {signup_credits} credits added.")
                        st.rerun()

    st.stop()


# ============================================================
# Logged-In Application Environment
# ============================================================
current_user = st.session_state.user_email
is_admin = st.session_state.role == "admin"
db = load_db()

is_moderator = is_admin or bool(db.get("moderators", {}).get(current_user, False))
user_coins = 99999 if is_admin else int(db["users"].get(current_user, 0))

# ============================================================
# User Status Dashboard Bar
# ============================================================
c1, c2, c3 = st.columns([1.3, 1.1, .75])
with c1: st.metric("🪙 Available Balance", "∞" if is_admin else f"{user_coins} Credits")
with c2: st.metric("👤 Account Status", "Master Admin" if is_admin else ("Moderator" if is_moderator else "Active Member"))
with c3:
    if st.button("↪ Sign Out", use_container_width=True):
        logout()

# ============================================================
# Main Brand Navigation Bar
# ============================================================
user_menu = [
    ("Home", "🏠", "#FF0000"),               # YouTube Red
    ("Bypass engine", "🎬", "#E1306C"),        # Instagram Pink
    ("AI SEO", "📈", "#1877F2"),               # Facebook Blue
    ("Free Tasks", "🎁", "#FF8C00"),           # Orange
    ("Recharge", "🪙", "#00C853"),             # Green
    ("Download", "📁", "#00F2FE"),             # Cyan
    ("Help & Support", "💬", "#833AB4"),       # Purple
    ("My Profile", "👤", "#3F51B5"),           # Indigo
]

if is_moderator and not is_admin:
    user_menu.append(("Manage Links", "🔗", "#009688"))

if is_admin:
    user_menu.extend([
        ("Storage Cleaner", "🧹", "#D32F2F"),
        ("Admin Panel", "👑", "#FFD700")
    ])

st.markdown('<div style="font-weight:900; color:white; font-size:1.1rem; margin:10px 0 8px;">☰ &nbsp; BypassTube.in Menu</div>', unsafe_allow_html=True)
nav_cols = st.columns(4)

for idx, (menu_name, icon, btn_color) in enumerate(user_menu):
    with nav_cols[idx % 4]:
        st.markdown(f"""
        <style>
        div.stButton > button[key="nav_{idx}_{menu_name}"] {{
            background: {btn_color} !important;
            box-shadow: 0 6px 0 {btn_color}aa, 0 12px 25px rgba(0,0,0,0.4) !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        if st.button(f"{icon}  {menu_name}", key=f"nav_{idx}_{menu_name}", use_container_width=True):
            st.session_state.active_menu = menu_name
            st.rerun()

selected = st.session_state.active_menu
st.divider()


# ============================================================
# SECTION 1: HOME
# ============================================================
if selected == "Home":
    st.markdown(
        """
<div class="hero-card">
    <div class="animated-brand-subtext" style="font-size:1rem;">🔴 YouTube • 📸 Instagram • 📘 Facebook</div>
    <h2 style="margin-top:6px;">🚀 Welcome to BypassTube.in</h2>
    <p>AI Powered Anti-Copyright Bypass Engine for YouTube Shorts, Reels & FB Videos</p>
</div>
""", unsafe_allow_html=True)

    features = [
        ("🎬", "Bypass Engine", "High-Speed Turbo uploading & Anti-Copyright rendering for YouTube, IG & FB."),
        ("📈", "AI SEO Pack", "Generate viral titles, descriptions, tags & timestamps optimized for social growth."),
        ("✂️", "Clipping Engine", "Automatically split long videos into Anti-Copyright short clips."),
        ("🎁", "10 Watch Tasks", "Complete 10 creator watch tasks sequentially with 24h cooldown to earn free editing credits."),
        ("🪙", "Instant Recharge", "Dynamic UPI QR code payment system with automated UTR verification."),
        ("📁", "Cloud Downloads", "Access and download all your exported render files anytime."),
    ]
    feature_cols = st.columns(3)
    for i, (icon, title, text) in enumerate(features):
        with feature_cols[i % 3]:
            st.markdown(f'<div class="feature-card"><div style="font-size:2.2rem;">{icon}</div><div style="font-weight:900; font-size:1.1rem; color:white; margin-top:6px;">{title}</div><div style="font-size:0.85rem; margin-top:5px;">{text}</div></div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Quick Launch")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("🎬 Launch Bypass Engine", use_container_width=True): st.session_state.active_menu = "Bypass engine"; st.rerun()
    with q2:
        if st.button("📈 AI Video SEO Tool", use_container_width=True): st.session_state.active_menu = "AI SEO"; st.rerun()
    with q3:
        if st.button("🎁 Earn Free Credits", use_container_width=True): st.session_state.active_menu = "Free Tasks"; st.rerun()

    st.markdown("### 📊 Account Snapshot")
    history = db.get("history", {}).get(current_user, [])
    claims = db.get("claimed_tasks", {}).get(current_user, [])
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.metric("🪙 Balance", "∞" if is_admin else user_coins)
    with s2: st.metric("📁 Exports", len(history))
    with s3: st.metric("🎁 Tasks Completed", len(claims))
    with s4:
        pending = len([x for x in db.get("pending_requests", []) if x.get("email") == current_user])
        st.metric("🪙 Pending Recharges", pending)

    if history:
        st.markdown("### 🕘 Recent Renders")
        for item in history[-5:][::-1]:
            st.markdown(f'<div class="card-box"><b style="color:white;">📄 {item.get("file","Export")}</b><br><small>{item.get("date","")}</small><br><span class="badge-yt" style="margin-top:6px;">{item.get("mode","Video")}</span></div>', unsafe_allow_html=True)


# ============================================================
# SECTION 2: BYPASS ENGINE (WITH UPLOAD ANIMATION)
# ============================================================
elif selected == "Bypass engine":
    st.markdown(
        """
<div class="hero-card">
    <div class="animated-brand-subtext">FAST RENDER ENGINE</div>
    <h2 style="margin-top:6px;">🎬 Anti-Copyright Video Studio</h2>
    <p>High-Speed Upload Buffer &amp; Anti-Copyright Multi-Hash Injector<br><strong style="color:#FF2A2A !important;">Supported: YouTube Shorts, Instagram Reels, Facebook Videos</strong></p>
</div>
""", unsafe_allow_html=True)

    st.markdown(
        f"""
<div class="upload-card upload-animating" style="text-align:center;">
    <div style="font-size:3.2rem; filter:drop-shadow(0 0 15px rgba(0,242,254,0.6));">☁️</div>
    <h3 style="margin:8px 0 3px;">Select Video File for BypassTube Processing</h3>
    <small>Supported Formats: MP4, MOV, MKV, AVI, WEBM | Max Limit: {MAX_VIDEO_MB} MB</small>
</div>
""",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Choose Video File", type=["mp4", "mov", "mkv", "avi", "webm"],
        help=f"Maximum upload limit: {MAX_VIDEO_MB} MB.", label_visibility="collapsed"
    )

    if uploaded:
        size_mb = uploaded.size / (1024 * 1024)
        base_charge = 10 if size_mb <= 50 else 20
        st.info(f"📦 Selected File Size: **{size_mb:.2f} MB** • Base Processing Charge: **{base_charge} Credits**")

        if uploaded.size > MAX_VIDEO_BYTES:
            st.error(f"❌ File size exceeds configured limit of {MAX_VIDEO_MB} MB.")
            st.stop()

        mode = st.radio("Processing Mode", ["Full Video", "Clipping Mode"], horizontal=True)

        if mode == "Full Video":
            quality_options = ["480p (Free - 0 Credits)", "720p (5 Credits)", "1080p (10 Credits)", "2K / 1440p (20 Credits)"]
            quality = st.radio("Resolution & Output Quality", quality_options)
            res_map = {
                "480p (Free - 0 Credits)": (480, "2000k", 0),
                "720p (5 Credits)": (720, "4000k", 5),
                "1080p (10 Credits)": (1080, "8000k", 10),
                "2K / 1440p (20 Credits)": (1440, "14000k", 20),
            }
            target_h, bitrate, quality_charge = res_map[quality]
            total = base_charge + quality_charge
            st.warning(f"🪙 Total Charge: **{total} Credits** (Base: {base_charge} + Quality: {quality_charge})")

            if st.button("🚀 Render Anti-Copyright Video  →", use_container_width=True):
                if not is_admin and user_coins < total:
                    st.error(f"❌ Insufficient credits. You need {total} credits.")
                    st.stop()

                acquired, active_user = acquire_render_slot(current_user)
                if not acquired:
                    st.warning("⚠️ Render engine is busy processing another file. Please try again in a few moments.")
                    st.stop()

                temp_path = out_path = None
                try:
                    upload_progress = st.progress(0)
                    upload_status = st.empty()

                    temp_path, upload_seconds = save_uploaded_file_fast(
                        uploaded, "temp_video", progress_bar=upload_progress, status_text=upload_status
                    )
                    upload_status.success(f"⚡ Turbo Stream Transfer Completed in {upload_seconds:.2f} seconds!")

                    out_name = f"BypassTube_{os.path.splitext(safe_filename(uploaded.name))[0]}_{int(time.time())}.mp4"
                    out_path = os.path.join(EXPORT_DIR, out_name)

                    render_progress = st.progress(0)
                    render_status = st.empty()

                    process_video(temp_path, out_path, target_h, bitrate, render_progress, render_status, edit_strength=True)

                    if not os.path.isfile(out_path):
                        raise IOError("Failed to create export output file.")

                    if not is_admin:
                        db = load_db()
                        db["users"][current_user] = max(0, int(db["users"].get(current_user, 0)) - total)
                        save_db(db)

                    db = load_db()
                    record = {
                        "file": out_name, "owner": current_user, "mode": "Full Video",
                        "quality": target_h, "size_mb": round(file_size_mb(out_path), 2),
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    db.setdefault("history", {}).setdefault(current_user, []).append(record)
                    db.setdefault("exports", {})[out_name] = record
                    save_db(db)

                    st.success("🎉 Anti-Copyright video ready!")
                    st.video(out_path)
                    with open(out_path, "rb") as f:
                        st.download_button("📥 Download Rendered Video", f, file_name=out_name, mime="video/mp4", use_container_width=True)
                except Exception as exc:
                    st.error(f"❌ Processing error: {type(exc).__name__}: {exc}")
                finally:
                    cleanup_storage(temp_path)
                    release_render_slot(current_user)
        else:
            interval = st.number_input("Clip Duration (Seconds)", min_value=5, max_value=600, value=30, step=5)
            st.warning(f"🪙 Clipping Charge: **{base_charge} Credits**")

            if st.button("✂️ Split Video into Anti-Copyright Clips  →", use_container_width=True):
                if not is_admin and user_coins < base_charge:
                    st.error(f"❌ You need {base_charge} credits.")
                    st.stop()

                acquired, active_user = acquire_render_slot(current_user)
                if not acquired:
                    st.warning("⚠️ Engine busy. Please try again in a moment.")
                    st.stop()

                temp_path = None
                try:
                    upload_progress = st.progress(0)
                    upload_status = st.empty()

                    temp_path, upload_seconds = save_uploaded_file_fast(
                        uploaded, "temp_clip", progress_bar=upload_progress, status_text=upload_status
                    )
                    upload_status.success(f"⚡ Turbo Upload Completed in {upload_seconds:.2f} seconds.")

                    clip_progress = st.progress(0)
                    clip_status = st.empty()

                    created = process_clips(temp_path, int(interval), current_user, clip_progress, clip_status)

                    if not is_admin:
                        db = load_db()
                        db["users"][current_user] = max(0, int(db["users"].get(current_user, 0)) - base_charge)
                        save_db(db)

                    db = load_db()
                    for clip in created:
                        record = {
                            "file": clip["name"], "owner": current_user, "mode": "Clipping Mode",
                            "quality": "Original", "size_mb": round(file_size_mb(clip["path"]), 2),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "timestamp": f"{clip['start']} → {clip['end']}",
                        }
                        db.setdefault("history", {}).setdefault(current_user, []).append(record)
                        db.setdefault("exports", {})[clip["name"]] = record
                    save_db(db)

                    st.success(f"🎉 Created {len(created)} clips successfully!")
                    for clip in created:
                        st.info(f"✂️ Segment: {clip['start']} → {clip['end']}")
                        with open(clip["path"], "rb") as f:
                            st.download_button(f"📥 Download Part {clip['start']} - {clip['end']}", f, file_name=clip["name"], mime="video/mp4", key=f"clip_dl_{clip['name']}", use_container_width=True)
                except Exception as exc:
                    st.error(f"❌ Clipping error: {type(exc).__name__}: {exc}")
                finally:
                    cleanup_storage(temp_path)
                    release_render_slot(current_user)


# ============================================================
# SECTION 3: AI SEO GENERATOR
# ============================================================
elif selected == "AI SEO":
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">AI SEO CREATOR</div><h2>📈 Multi-Platform AI Video SEO Generator</h2><p>Generate high-converting titles, descriptions, tags, and timestamps for YouTube, Instagram & Facebook.</p></div>', unsafe_allow_html=True)
    topic_input = st.text_input("Video Topic or Keywords", placeholder="e.g. Viral Shorts Editing Tips 2026")
    platform = st.selectbox("Target Social Platform", ["YouTube", "Instagram", "Facebook"])
    tone = st.radio("Content Tone", ["Viral", "Educational", "Cinematic"], horizontal=True)

    if st.button("✨ Generate AI SEO Pack  ↗", use_container_width=True):
        if not topic_input.strip():
            st.error("Please enter a topic or title.")
        else:
            seo = generate_seo_from_topic(topic_input, platform, tone)
            st.session_state.seo_result = seo

    if st.session_state.seo_result:
        seo = st.session_state.seo_result
        st.markdown(f'<div class="feature-card"><div style="font-weight:900; color:white;">🎯 SEO Score</div><div style="font-size:2.4rem; color:#00F2FE; font-weight:950;">{seo["score"]}/100</div></div>', unsafe_allow_html=True)
        st.markdown("### 🔥 Title Suggestions")
        for title in seo["titles"]: st.code(title)
        st.text_area("Description / Caption", value=seo["description"], height=230)
        st.text_input("Recommended Tags", value=", ".join(seo["tags"]))
        st.text_input("Hashtags", value=seo["hashtags"])


# ============================================================
# SECTION 4: FREE TASKS (SEQUENTIAL 1-10 WATCH & 24H COOLDOWN)
# ============================================================
elif selected == "Free Tasks":
    settings = db.get("settings", {})
    links = db.get("admin_links", {})
    watch_tasks = db.get("watch_tasks", get_default_watch_tasks())
    claims = db.get("claimed_tasks", {}).get(current_user, [])
    task_claim_times = db.get("task_claim_times", {}).get(current_user, {})

    yt_reward = int(settings.get("youtube_task_credits", 10))
    insta_reward = int(settings.get("instagram_task_credits", 10))
    fb_reward = int(settings.get("facebook_task_credits", 10))

    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">FREE CREDITS</div><h2>🎁 Creator Social Tasks & 10 Sequential Watch Video Tabs</h2><p>Complete creator social tasks and watch videos sequentially from Tab 1 to Tab 10. Each completed watch task unlocks a 24-hour cooldown before earning again.</p></div>', unsafe_allow_html=True)

    st.markdown("### 🌐 Social Subscription Tasks")
    social_tasks = [
        ("youtube", "🔴", "Subscribe YouTube Channel", links.get("yt_url", "https://youtube.com"), yt_reward, "Subscribe Channel"),
        ("instagram", "📸", "Follow Instagram Page", links.get("insta_url", "https://instagram.com"), insta_reward, "Follow Instagram"),
        ("facebook", "📘", "Like Facebook Page", links.get("fb_url", "https://facebook.com"), fb_reward, "Like Facebook"),
    ]

    sc1, sc2, sc3 = st.columns(3)
    for idx, (task_id, icon, title, url, reward, action) in enumerate(social_tasks):
        col = [sc1, sc2, sc3][idx % 3]
        with col:
            st.markdown(f'<div class="card-box"><div style="font-weight:900; font-size:1.1rem; color:white;">{icon} {title}</div><div style="color:#00F2FE; font-size:1.3rem; font-weight:950; margin:6px 0;">+{reward} Credits</div></div>', unsafe_allow_html=True)
            if validate_url(url):
                st.markdown(f'<a href="{url}" target="_blank" style="display:block; text-align:center; padding:10px; background:rgba(255,255,255,0.1); border-radius:12px; color:white; text-decoration:none; font-weight:900; margin-bottom:8px;">{action} →</a>', unsafe_allow_html=True)

            if task_id in claims:
                st.success("✅ Reward Claimed")
            else:
                if st.button(f"Claim +{reward} Credits", key=f"claim_social_{task_id}", use_container_width=True):
                    db = load_db()
                    existing = db.setdefault("claimed_tasks", {}).setdefault(current_user, [])
                    if task_id not in existing:
                        db["users"][current_user] = int(db["users"].get(current_user, 0)) + reward
                        existing.append(task_id)
                        save_db(db)
                        st.success(f"🎉 +{reward} Credits added to balance!")
                        st.rerun()

    st.divider()
    st.markdown("### ▶️ Sequential 10-Watch Video Tasks (Tab 1 to Tab 10)")
    st.info("📌 **Rule:** Watch Tab 1 first, then Tab 2, and so on up to Tab 10 sequentially. Once completed, each task has a **24-hour cooldown** before it can be watched and earned from again.")

    watch_tabs = st.tabs([f"Watch #{i}" for i in range(1, 11)])
    now = time.time()
    COOLDOWN_DURATION = 24 * 3600 # 24 Hours in seconds

    for i, tab in enumerate(watch_tabs):
        task_idx = i + 1
        task_data = watch_tasks[i] if i < len(watch_tasks) else {
            "id": f"watch_{task_idx}", "title": f"Watch Video #{task_idx}", "url": "https://youtube.com", "reward": 10, "seconds": 30
        }

        tid = task_data.get("id", f"watch_{task_idx}")
        title = task_data.get("title", f"Watch Video #{task_idx}")
        v_url = task_data.get("url", "https://youtube.com")
        reward = int(task_data.get("reward", 10))
        required_sec = int(task_data.get("seconds", 30))

        # Cooldown check
        last_claimed_time = task_claim_times.get(tid, 0)
        time_since_claim = now - last_claimed_time
        on_cooldown = time_since_claim < COOLDOWN_DURATION
        cooldown_remaining = max(0, COOLDOWN_DURATION - time_since_claim)

        # Sequential check (Task i requires Task i-1 to be completed in the active 24h cycle)
        is_unlocked = True
        if task_idx > 1:
            prev_tid = f"watch_{task_idx - 1}"
            prev_claim_time = task_claim_times.get(prev_tid, 0)
            prev_time_since = now - prev_claim_time
            # Previous task must have been completed within the last 24 hours
            if prev_time_since >= COOLDOWN_DURATION:
                is_unlocked = False

        with tab:
            st.markdown(
                f"""
                <div class="card-box">
                    <div style="font-weight:900; font-size:1.2rem; color:white;">{title} (Step {task_idx} of 10)</div>
                    <div style="color:#00F2FE; font-size:1.3rem; font-weight:950; margin:6px 0;">
                        Reward: +{reward} Credits &nbsp;|&nbsp; Required Duration: {required_sec}s
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if on_cooldown:
                hours_left = int(cooldown_remaining // 3600)
                mins_left = int((cooldown_remaining % 3600) // 60)
                st.warning(f"⏳ **24-Hour Cooldown Active:** You have already claimed this task. Available again in **{hours_left}h {mins_left}m**.")
            elif not is_unlocked:
                st.error(f"🔒 **Task Locked:** You must complete and claim **Watch Task #{task_idx - 1}** first before unlocking Task #{task_idx}!")
            else:
                if tid in claims and not on_cooldown:
                    # Cooldown expired, ready for next cycle
                    pass

                watch_state = st.session_state.vid_watch_data.get(tid, {"status": "stopped", "start_time": 0, "elapsed": 0})
                status = watch_state.get("status", "stopped")

                embed_url = get_yt_embed_url(v_url)
                if embed_url:
                    st.components.v1.iframe(embed_url, height=360)

                ctrl_1, ctrl_2, ctrl_3 = st.columns(3)

                with ctrl_1:
                    if st.button(f"▶️ Start Watching & Run Timer #{task_idx}", key=f"play_v_{tid}", use_container_width=True):
                        st.session_state.vid_watch_data[tid] = {
                            "status": "playing",
                            "start_time": time.time(),
                            "elapsed": 0
                        }
                        st.rerun()

                with ctrl_2:
                    if st.button(f"⏸️ Pause / Stop Video", key=f"pause_v_{tid}", use_container_width=True):
                        if status in ["playing", "ready_to_claim"]:
                            st.session_state.vid_watch_data[tid] = {
                                "status": "failed",
                                "start_time": 0,
                                "elapsed": 0
                            }
                            st.rerun()

                with ctrl_3:
                    if st.button(f"🔄 Rewatch Video (Reset)", key=f"rewatch_v_{tid}", use_container_width=True):
                        st.session_state.vid_watch_data[tid] = {
                            "status": "stopped",
                            "start_time": 0,
                            "elapsed": 0
                        }
                        st.rerun()

                if status == "playing":
                    start_t = watch_state.get("start_time", time.time())
                    curr_elapsed = int(time.time() - start_t)
                    rem = max(0, required_sec - curr_elapsed)

                    if rem > 0:
                        st.markdown(f"""
                        <div class="processing-status-card upload-animating" style="margin-top:12px;">
                            <div style="font-weight:900; color:#00F2FE; font-size:1.1rem;">⏱️ Video Watching in Progress...</div>
                            <div style="font-size:1.5rem; font-weight:950; color:white; margin-top:4px;">{rem}s Remaining</div>
                            <small style="color:#FF2A2A !important;">⚠️ Do not pause or leave page! Stopping will fail the task.</small>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.vid_watch_data[tid] = {"status": "ready_to_claim", "start_time": 0, "elapsed": required_sec}
                        st.rerun()

                elif status == "ready_to_claim":
                    st.success("🎉 Full Video Watched! Click below to claim your credits.")
                    if st.button(f"🎁 Claim +{reward} Credits Now", key=f"claim_v_{tid}", use_container_width=True):
                        db = load_db()
                        user_claims = db.setdefault("claimed_tasks", {}).setdefault(current_user, [])
                        if tid not in user_claims:
                            user_claims.append(tid)

                        db.setdefault("task_claim_times", {}).setdefault(current_user, {})[tid] = time.time()
                        db["users"][current_user] = int(db["users"].get(current_user, 0)) + reward
                        save_db(db)

                        st.session_state.vid_watch_data[tid] = {"status": "completed", "start_time": 0, "elapsed": required_sec}
                        st.success(f"🎉 Watch Task #{task_idx} completed successfully! +{reward} Credits Added. Next task unlocked!")
                        st.rerun()

                elif status == "failed":
                    st.error("❌ **Task Failed!** You paused or interrupted video playback. Click **'Rewatch Video (Reset)'** to re-watch from start.")
                elif status == "completed":
                    st.success("✅ Watch task completed successfully for this 24-hour cycle.")
                else:
                    st.write(f"👉 Click **'Start Watching & Run Timer #{task_idx}'** above and watch continuously to earn your credits and unlock the next tab.")


# ============================================================
# SECTION 5: ACCOUNT RECHARGE
# ============================================================
elif selected == "Recharge":
    active_upi = db.get("admin_links", {}).get("upi_id", DEFAULT_UPI)
    credits_per_rupee = int(db.get("settings", {}).get("credits_per_rupee", 2))
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">RECHARGE</div><h2>🪙 UPI Payment & Credit Recharge</h2><p>Scan the dynamic UPI QR code, make the payment, and submit your UTR / Ref Number.</p></div>', unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        amount = st.number_input("1. Enter Amount in INR (₹)", min_value=5, max_value=10000, value=100, step=10)
        coins = int(amount * credits_per_rupee)
        st.success(f"🎉 You will receive **{coins} Credits** (Rate: ₹1 = {credits_per_rupee} Credits)")
        if active_upi:
            st.image(generate_upi_qr(active_upi, amount), caption=f"Scan & Pay ₹{amount} via UPI", width=280)
            st.code(active_upi, language="text")
    with right:
        with st.form("payment_form"):
            st.markdown("### 2. Submit Transaction Reference")
            utr = st.text_input("UTR / Transaction Reference Number", placeholder="e.g. 402918273645")
            submitted = st.form_submit_button("📩 Submit UTR for Admin Approval", use_container_width=True)
            if submitted:
                if not utr.strip() or len(utr.strip()) < 4:
                    st.error("Please enter a valid UTR transaction number.")
                else:
                    db = load_db()
                    duplicate = any(req.get("utr") == utr.strip() for req in db.get("pending_requests", []))
                    if duplicate:
                        st.error("This UTR has already been submitted.")
                    else:
                        db.setdefault("pending_requests", []).append({
                            "email": current_user, "utr": utr.strip(), "amount": int(amount), "coins": coins,
                            "plan": f"₹{amount} ({coins} Credits)", "status": "pending",
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })
                        save_db(db)
                        st.success("✅ Payment request submitted! Credits will be added upon admin review.")


# ============================================================
# SECTION 6: OUTPUT LIBRARY
# ============================================================
elif selected == "Download":
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">EXPORT LIBRARY</div><h2>📁 My Exported Video Renders</h2><p>Download your rendered anti-copyright video files anytime.</p></div>', unsafe_allow_html=True)
    own_history = db.get("history", {}).get(current_user, [])
    if not own_history:
        st.info("📁 No video exports found yet. Process a video in the Bypass engine.")
    else:
        for item in reversed(own_history):
            filename = item.get("file", "")
            path = os.path.join(EXPORT_DIR, filename)
            if not os.path.isfile(path): continue
            size = file_size_mb(path)
            st.markdown(f'<div class="card-box"><b style="color:white;">🎬 {filename}</b><br><small>{size:.2f} MB • Mode: {item.get("mode","Video")} • Date: {item.get("date","")}</small></div>', unsafe_allow_html=True)
            with open(path, "rb") as f:
                st.download_button("📥 Download Video File", f, file_name=filename, mime="video/mp4", key=f"dl_lib_{filename}", use_container_width=True)


# ============================================================
# SECTION 7: HELP & SUPPORT
# ============================================================
elif selected == "Help & Support":
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">SUPPORT DESK</div><h2>💬 Support & Live Help Desk</h2><p>Send direct ticket messages to the BypassTube admin team.</p></div>', unsafe_allow_html=True)
    tickets = db.get("support_tickets", [])
    mine = [ticket for ticket in tickets if ticket.get("user") == current_user]
    st.markdown("### 💬 Ticket History")
    if not mine:
        st.info("No support messages submitted yet.")
    for ticket in mine:
        st.markdown(f'<div class="card-box"><b style="color:white;">👤 You</b> <small>({ticket.get("date","")})</small><p style="margin-top:5px;">{ticket.get("msg","")}</p></div>', unsafe_allow_html=True)
        if ticket.get("reply"):
            st.success(f"👑 Admin Reply:\n\n{ticket['reply']}")
        else:
            st.warning("⏳ Awaiting admin reply.")

    st.markdown("### ✍️ Submit Ticket")
    with st.form("support_form"):
        message = st.text_area("How can we assist you?", placeholder="Describe your question or technical issue...", height=140)
        submitted = st.form_submit_button("📤 Send Message to Support Desk", use_container_width=True)
        if submitted:
            if not message.strip():
                st.error("Please enter a message.")
            else:
                db = load_db()
                db.setdefault("support_tickets", []).append({
                    "id": int(time.time() * 1000), "user": current_user, "msg": message.strip(), "reply": "",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                save_db(db)
                st.success("✅ Support ticket submitted successfully.")
                st.rerun()


# ============================================================
# SECTION 8: USER PROFILE
# ============================================================
elif selected == "My Profile":
    history = db.get("history", {}).get(current_user, [])
    st.markdown(f'<div class="hero-card"><div class="animated-brand-subtext">USER PROFILE</div><h2>👤 Account Overview</h2><p>{current_user}</p></div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1: st.metric("🪙 Credit Balance", "∞" if is_admin else f"{user_coins} Credits")
    with p2: st.metric("📁 Total Video Renders", len(history))

    st.markdown("### ⚙️ Quick Actions")
    if st.button("💬 Open Support Messages", use_container_width=True):
        st.session_state.active_menu = "Help & Support"; st.rerun()
    if st.button("🎁 View Free Tasks", use_container_width=True):
        st.session_state.active_menu = "Free Tasks"; st.rerun()


# ============================================================
# SECTION 9: MODERATOR PANEL (FOR MODERATORS TO CHANGE YT LINKS)
# ============================================================
elif selected == "Manage Links":
    if not is_moderator: st.error("Access denied."); st.stop()
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">MODERATOR PANEL</div><h2>🔗 Manage Creator Video Links</h2></div>', unsafe_allow_html=True)

    watch_tasks_list = db.get("watch_tasks", get_default_watch_tasks())

    with st.form("mod_watch_tasks_form"):
        updated_tasks = []
        for idx in range(10):
            curr = watch_tasks_list[idx] if idx < len(watch_tasks_list) else {}
            st.markdown(f"#### 🎥 Watch Task #{idx+1}")
            wt_title = st.text_input(f"Task #{idx+1} Title", value=curr.get("title", f"Watch Video #{idx+1}"), key=f"mod_wt_t_{idx}")
            wt_url = st.text_input(f"Task #{idx+1} Video URL", value=curr.get("url", "https://youtube.com"), key=f"mod_wt_u_{idx}")
            wt_reward = st.number_input(f"Task #{idx+1} Credit Reward", min_value=1, max_value=500, value=int(curr.get("reward", 10)), key=f"mod_wt_r_{idx}")
            wt_sec = st.number_input(f"Task #{idx+1} Required Seconds", min_value=5, max_value=3600, value=int(curr.get("seconds", 30)), key=f"mod_wt_s_{idx}")

            updated_tasks.append({
                "id": f"watch_{idx+1}",
                "title": wt_title.strip(),
                "url": wt_url.strip(),
                "reward": int(wt_reward),
                "seconds": int(wt_sec)
            })
            st.divider()

        if st.form_submit_button("💾 Save All YouTube Video Links", use_container_width=True):
            db = load_db()
            db["watch_tasks"] = updated_tasks
            save_db(db)
            st.success("🎉 Video links updated successfully!")
            st.rerun()


# ============================================================
# SECTION 10: ADMIN STORAGE CLEANER
# ============================================================
elif selected == "Storage Cleaner":
    if not is_admin: st.error("Access denied."); st.stop()
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">ADMIN TOOL</div><h2>🧹 Server Storage Cleaner</h2></div>', unsafe_allow_html=True)
    exports = [p for p in glob.glob(os.path.join(EXPORT_DIR, "*")) if os.path.isfile(p)]
    temp_files = [p for p in glob.glob(os.path.join(TEMP_DIR, "*")) if os.path.isfile(p)]
    total_size = sum(file_size_mb(p) for p in exports + temp_files)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("📁 Export Files", len(exports))
    with c2: st.metric("🧪 Temporary Files", len(temp_files))
    with c3: st.metric("💾 Disk Usage", f"{total_size:.2f} MB")

    confirm = st.checkbox("I confirm deletion of all cached temporary and export files.")
    if st.button("🚨 Purge All Server Storage Files", use_container_width=True):
        if not confirm:
            st.error("Please check the confirmation box.")
        else:
            removed = 0
            for path in exports + temp_files:
                try: os.remove(path); removed += 1
                except OSError: pass
            gc.collect()
            st.success(f"✅ Successfully deleted {removed} cached/exported video files.")


# ============================================================
# SECTION 11: MASTER ADMIN PANEL
# ============================================================
elif selected == "Admin Panel":
    if not is_admin: st.error("Access denied."); st.stop()
    st.markdown('<div class="hero-card"><div class="animated-brand-subtext">ADMIN CONTROL</div><h2>👑 Master Admin Control Center</h2></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔗 App Links", "▶️ 10 Watch Tasks Admin", "💬 Support Desk", "🪙 Payments", "👥 Users & Coins"])

    with tab1:
        links, settings = db.get("admin_links", {}), db.get("settings", {})
        with st.form("admin_settings_form"):
            yt = st.text_input("YouTube Channel Link", value=links.get("yt_url", ""))
            insta = st.text_input("Instagram Page Link", value=links.get("insta_url", ""))
            fb = st.text_input("Facebook Page Link", value=links.get("fb_url", ""))
            wa = st.text_input("WhatsApp Channel Link", value=links.get("wa_channel_url", ""))
            upi = st.text_input("Active Admin UPI ID", value=links.get("upi_id", DEFAULT_UPI))
            credits_per_rupee = st.number_input("Credits per ₹1", min_value=1, max_value=20, value=int(settings.get("credits_per_rupee", 2)))
            signup_credits = st.number_input("New Signup Bonus Credits", min_value=0, max_value=1000, value=int(settings.get("signup_credits", 50)))

            if st.form_submit_button("💾 Save App Settings", use_container_width=True):
                db["admin_links"] = {
                    "yt_url": yt.strip(), "insta_url": insta.strip(), "fb_url": fb.strip(),
                    "wa_channel_url": wa.strip(), "upi_id": upi.strip()
                }
                db["settings"]["credits_per_rupee"] = int(credits_per_rupee)
                db["settings"]["signup_credits"] = int(signup_credits)
                save_db(db)
                st.success("✅ App settings updated successfully!")
                st.rerun()

    with tab2:
        st.markdown("### ⚙️ Configure All 10 Watch Tasks Links & Rewards")
        watch_tasks_list = db.get("watch_tasks", get_default_watch_tasks())

        with st.form("admin_watch_tasks_form"):
            updated_tasks = []
            for idx in range(10):
                curr = watch_tasks_list[idx] if idx < len(watch_tasks_list) else {}
                st.markdown(f"#### 🎥 Watch Task #{idx+1}")
                wt_title = st.text_input(f"Task #{idx+1} Title", value=curr.get("title", f"Watch Video #{idx+1}"), key=f"wt_t_{idx}")
                wt_url = st.text_input(f"Task #{idx+1} Video URL", value=curr.get("url", "https://youtube.com"), key=f"wt_u_{idx}")
                wt_reward = st.number_input(f"Task #{idx+1} Credit Reward", min_value=1, max_value=500, value=int(curr.get("reward", 10)), key=f"wt_r_{idx}")
                wt_sec = st.number_input(f"Task #{idx+1} Required Seconds", min_value=5, max_value=3600, value=int(curr.get("seconds", 30)), key=f"wt_s_{idx}")

                updated_tasks.append({
                    "id": f"watch_{idx+1}",
                    "title": wt_title.strip(),
                    "url": wt_url.strip(),
                    "reward": int(wt_reward),
                    "seconds": int(wt_sec)
                })
                st.divider()

            if st.form_submit_button("💾 Save All 10 Watch Video Tasks", use_container_width=True):
                db["watch_tasks"] = updated_tasks
                save_db(db)
                st.success("🎉 All 10 Watch Video tasks successfully updated!")
                st.rerun()

    with tab3:
        tickets = db.get("support_tickets", [])
        if not tickets: st.info("No support messages submitted yet.")
        for idx, ticket in enumerate(tickets):
            st.markdown(f'<div class="card-box"><b style="color:white;">👤 {ticket.get("user","")}</b> <small>({ticket.get("date","")})</small><p style="margin-top:5px;">{ticket.get("msg","")}</p></div>', unsafe_allow_html=True)
            reply = st.text_area("Write Reply", value=ticket.get("reply", ""), key=f"reply_{ticket.get('id', idx)}")
            if st.button("Send Reply", key=f"send_reply_{ticket.get('id', idx)}", use_container_width=True):
                if reply.strip():
                    db["support_tickets"][idx]["reply"] = reply.strip()
                    save_db(db)
                    st.success("Reply saved successfully.")
                    st.rerun()

    with tab4:
        st.markdown("### 💳 Pending Payment Approvals")
        requests = db.get("pending_requests", [])
        if not requests:
            st.info("No pending payment approvals.")
        for idx, req in enumerate(requests):
            if req.get("status") == "pending":
                st.markdown(
                    f"""
                    <div class="card-box">
                        <b style="color:white;">👤 User: {req.get("email","")}</b>
                        <p style="margin:4px 0;">Plan: {req.get("plan","")} | Amount: ₹{req.get("amount",0)} | Coins: +{req.get("coins",0)}<br>
                        UTR: <code>{req.get("utr","")}</code> | Date: {req.get("date","")}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                app_col1, app_col2 = st.columns(2)
                with app_col1:
                    if st.button(f"✅ Approve ₹{req.get('amount')}", key=f"app_{idx}", use_container_width=True):
                        db = load_db()
                        u_email = req.get("email")
                        coins_to_add = int(req.get("coins", 0))
                        db["users"][u_email] = int(db["users"].get(u_email, 0)) + coins_to_add
                        db["pending_requests"][idx]["status"] = "approved"
                        save_db(db)
                        st.success(f"Approved! +{coins_to_add} coins added to {u_email}.")
                        st.rerun()
                with app_col2:
                    if st.button(f"❌ Reject Request", key=f"rej_{idx}", use_container_width=True):
                        db = load_db()
                        db["pending_requests"][idx]["status"] = "rejected"
                        save_db(db)
                        st.warning("Payment request rejected.")
                        st.rerun()

    with tab5:
        st.markdown("### 👥 Manage User Coins & Moderator Status")
        users_map = db.get("users", {})
        moderators_map = db.get("moderators", {})

        if not users_map:
            st.info("No registered users found.")
        else:
            user_list = list(users_map.keys())
            selected_user = st.selectbox("Select Target User", user_list)

            st.write(f"**Current Balance for `{selected_user}`:** `{users_map.get(selected_user, 0)} Credits`")
            st.write(f"**Moderator Role:** `{'Yes' if moderators_map.get(selected_user, False) else 'No'}`")

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                action_type = st.radio("Action", ["Add Coins", "Deduct Coins"], horizontal=True)
                coin_amount = st.number_input("Amount of Coins", min_value=1, max_value=100000, value=100, step=10)

                if st.button("Execute Coin Transaction", use_container_width=True):
                    db = load_db()
                    curr = int(db["users"].get(selected_user, 0))
                    if action_type == "Add Coins":
                        new_bal = curr + int(coin_amount)
                    else:
                        new_bal = max(0, curr - int(coin_amount))

                    db["users"][selected_user] = new_bal
                    save_db(db)
                    st.success(f"Updated `{selected_user}` balance to `{new_bal} Credits`.")
                    st.rerun()

            with c_act2:
                st.markdown("#### Toggle Moderator Role")
                is_mod_now = bool(moderators_map.get(selected_user, False))
                mod_btn_label = "Remove Moderator Role" if is_mod_now else "Make User Moderator"

                if st.button(mod_btn_label, use_container_width=True):
                    db = load_db()
                    db.setdefault("moderators", {})[selected_user] = not is_mod_now
                    save_db(db)
                    st.success(f"Moderator status for `{selected_user}` updated!")
                    st.rerun()

            st.divider()
            st.markdown("#### 📋 Full Users List")
            for u_email, u_bal in users_map.items():
                mod_status = "👑 Moderator" if moderators_map.get(u_email, False) else "User"
                st.markdown(f'<div class="card-box"><b style="color:white;">👤 {u_email}</b> — Balance: <code>{u_bal} Credits</code> | Role: <b>{mod_status}</b></div>', unsafe_allow_html=True)
