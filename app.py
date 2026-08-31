import streamlit as st
import glob
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import moviepy.video.fx.all as vfx
import numpy as np

# Page Layout Configuration
st.set_page_config(page_title="Video Auto-Editor", page_icon="🎬", layout="centered")

st.title("🎬 Mobile Video Auto-Editor")
st.write("अपनी वीडियो अपलोड करें और 15-Edit Auto Sequence अप्लाई करें!")

def manual_zoom(clip, zoom_factor):
    def zoom_frame(image):
        h, w, c = image.shape
        crop_h, crop_w = int(h / zoom_factor), int(w / zoom_factor)
        top = (h - crop_h) // 2
        left = (w - crop_w) // 2
        cropped = image[top:top+crop_h, left:left+crop_w]
        row_indices = (np.linspace(0, crop_h - 1, h)).astype(int)
        col_indices = (np.linspace(0, crop_w - 1, w)).astype(int)
        return cropped[row_indices[:, None], col_indices]
    return clip.fl_image(zoom_frame)

def apply_custom_effects(clip, edit_num):
    if edit_num in [2, 8]:
        clip = manual_zoom(clip, 1.10)
    elif edit_num == 3:
        clip = clip.speedx(1.3)
    elif edit_num in [4, 13]:
        clip = clip.fx(vfx.colorx, 0.85)
    elif edit_num in [5, 11, 15]:
        clip = clip.fx(vfx.colorx, 1.30)
    elif edit_num == 6:
        clip = clip.fl_image(lambda img: img[:, ::-1])
    elif edit_num == 7:
        clip = clip.fx(vfx.colorx, 1.15)
    elif edit_num == 9:
        clip = clip.speedx(1.2)
    elif edit_num == 10:
        clip = manual_zoom(clip, 1.05)
    elif edit_num == 12:
        clip = manual_zoom(clip, 1.15)
    elif edit_num == 14:
        clip = clip.fl_image(lambda img: img[:, ::-1]).speedx(1.25)

    delay_factors = {
        1: 1.000, 2: 0.973, 3: 0.946, 4: 0.919, 5: 0.892, 6: 0.865, 
        7: 1.000, 8: 0.973, 9: 0.946, 10: 0.919, 11: 0.892, 12: 0.865,
        13: 1.000, 14: 0.973, 15: 0.946                            
    }
    speed_factor = delay_factors.get(edit_num, 1.0)
    if clip.audio is not None and speed_factor != 1.0:
        audio = clip.audio.fl_time(lambda t: t * speed_factor)
        clip.audio = audio.set_duration(clip.duration)

    return clip

# File Uploader UI Component
uploaded_file = st.file_uploader("यहाँ वीडियो फाइल सेलेक्ट करें (.mp4)", type=["mp4", "mov", "mkv"])

if uploaded_file is not None:
    # Save uploaded file
    input_path = "temp_input.mp4"
    output_path = "output_website_final.mp4"
    
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())
        
    st.success("वीडियो सफलतापूर्वक अपलोड हो गई!")
    
    if st.button("🚀 Start Auto-Editing"):
        with st.spinner("वीडियो एडिट हो रही है... कृपया इंतज़ार करें..."):
            video = VideoFileClip(input_path)
            total_duration = video.duration
            pattern_duration = 30.0

            clips = []
            current_time = 0.0

            while current_time < total_duration:
                for edit_idx in range(1, 16):
                    start = (edit_idx - 1) * 2.0
                    end = edit_idx * 2.0
                    seg_start = current_time + start
                    if seg_start >= total_duration:
                        break
                    seg_end = current_time + end
                    actual_end = min(seg_end, total_duration)
                    if seg_start >= actual_end:
                        continue

                    subclip = video.subclip(seg_start, actual_end)
                    edited_subclip = apply_custom_effects(subclip, edit_idx)
                    clips.append(edited_subclip)

                current_time += pattern_duration

            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        st.balloons()
        st.success("एडिटिंग पूरी हो गई!")
        
        # Download Button for Mobile
        with open(output_path, "rb") as file:
            st.download_button(
                label="📥 Edited Video Download करें",
                data=file,
                file_name="Edited_Video.mp4",
                mime="video/mp4"
            )