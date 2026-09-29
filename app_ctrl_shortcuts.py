import os
import base64
import hashlib
import html
import time

import truststore
truststore.inject_into_ssl()

import httpx
import streamlit as st
import streamlit.components.v1 as components

from rag_agent import ask_agent

from voice import (
    speech_to_text,
    text_to_speech,
    get_audio_duration,
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKGROUND_IMAGE = os.path.join(
    BASE_DIR,
    "assets",
    "Background.png",
)

AIRA_LOGO = os.path.join(
    BASE_DIR,
    "assets",
    "Logo.png",
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Aira - AI Assistant",
    page_icon=AIRA_LOGO if os.path.isfile(AIRA_LOGO) else "🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_STATE = {
    "intro_complete": False,
    "intro_started": False,
    "intro_audio_path": None,
    "messages": [],
    "processed_audio": None,
    "voice_audio_path": None,
    "is_speaking": False,
    "speaking_started": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# AIRA INTRO
# =========================================================

AIRA_INTRO = (
    "Welcome everyone. "
    "I am Ayra, your AI Hackathon host for today. "
    "Thanks for joining. "
    "Before we inaugurate the Hackathon, "
    "I would like to welcome our leaders from TCS and ING. "
    "Today we are bringing Human and AI together "
    "to explore new ideas, build, learn and innovate. "
    "I wish all participants the very best. "
    "Happy Coding. Thank you."
)


# =========================================================
# KEYBOARD SHORTCUT SCRIPTS
# =========================================================

SHORTCUT_SCRIPTS = {
    "F1": (
        "Welcome everyone. "
        "I am Ayra, your AI Hackathon host for today."
    ),

    "F2": (
        "The hackathon theme is CodING with TCS."
    ),

    "F3": (
        "I welcome all the engineers for the hackathon. "
        "Please come and pick up your use cases."
    ),

    "F4": (
        "Here are the rules for participation. "
        "You should be part of the ING account, "
        "be an out of the box thinker, "
        "and be an AI enthusiast. "
        "For other participation criteria and questions, "
        "please reach out to the organiser."
    ),

    "F5": (
        "Thanks for joining. "
        "Hope you all had a good day. "
        "Ayra signing off."
    ),
}


# =========================================================
# IMAGE -> BASE64
# =========================================================

def image_to_base64(path):

    if not os.path.isfile(path):
        return ""

    try:
        with open(path, "rb") as file:
            return base64.b64encode(
                file.read()
            ).decode("utf-8")

    except Exception:
        return ""


background_b64 = image_to_base64(
    BACKGROUND_IMAGE
)


# =========================================================
# BACKGROUND CSS
# =========================================================

if background_b64:

    background_css = (
        "background-image:"
        "linear-gradient("
        "rgba(1,8,24,0.08),"
        "rgba(1,8,24,0.18)"
        "),"
        f"url('data:image/png;base64,{background_b64}');"
        "background-size:cover;"
        "background-position:center center;"
        "background-repeat:no-repeat;"
    )

else:

    background_css = (
        "background:"
        "radial-gradient("
        "circle at 50% 40%,"
        "#0d3764,"
        "#020817 70%"
        ");"
    )


# =========================================================
# CSS
# =========================================================

CSS_TEMPLATE = """
<style>

html,
body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    overflow: hidden !important;
    background: #031333 !important;
}


[data-testid="stApp"] {
    width: 100vw !important;
    height: 100vh !important;
    background: #031333 !important;
    overflow: hidden !important;
}


[data-testid="stAppViewContainer"] {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;

    __BACKGROUND__
}


[data-testid="stMain"] {
    background: transparent !important;
}


[data-testid="stMainBlockContainer"] {
    width: 100vw !important;
    height: 100vh !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
}


/* ========================================================
   HIDE STREAMLIT CHROME
   ======================================================== */

#MainMenu {
    visibility: hidden;
}


footer {
    visibility: hidden;
}


[data-testid="stHeader"] {
    background: transparent !important;
}


/* ========================================================
   INTRO
   ======================================================== */

.aira-intro {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 9000 !important;

    background:
        linear-gradient(
            135deg,
            rgba(1,8,24,0.62),
            rgba(4,31,78,0.35)
        );

    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}


/* ========================================================
   INTRO LOGO
   ======================================================== */

[data-testid="stImage"] {
    position: fixed !important;
    left: 50% !important;
    top: calc(50% - 110px) !important;
    transform: translate(-50%, -50%) !important;
    z-index: 10001 !important;
    width: 160px !important;
}


[data-testid="stImage"] img {
    width: 160px !important;
    height: 160px !important;
    object-fit: contain !important;

    filter:
        drop-shadow(
            0 0 25px
            rgba(74,190,255,0.85)
        );

    animation:
        logoPulse
        2s
        ease-in-out
        infinite;
}


@keyframes logoPulse {

    0%,
    100% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.06);
    }
}


/* ========================================================
   INTRO CONTENT
   ======================================================== */

.aira-intro-content {
    position: fixed !important;
    left: 50% !important;
    top: calc(50% + 25px) !important;
    transform: translateX(-50%) !important;
    z-index: 10001 !important;
    width: 100%;

    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    pointer-events: none;
}


.aira-intro-title {
    color: white;
    font-family: Arial, sans-serif;
    font-size: 40px;
    font-weight: 800;
    letter-spacing: 11px;
    margin-left: 11px;

    text-shadow:
        0 0 15px
        rgba(72,180,255,0.90);
}


.aira-intro-subtitle {
    margin-top: 7px;
    color: rgba(255,255,255,0.65);
    font-family: Arial, sans-serif;
    font-size: 11px;
    letter-spacing: 5px;
}


.intro-status {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 28px;
    color: white;
    font-family: Arial, sans-serif;
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 30px;

    border:
        1px solid
        rgba(80,185,255,0.55);

    background:
        rgba(2,14,36,0.55);

    backdrop-filter: blur(10px);
}


.intro-bars {
    display: flex;
    align-items: center;
    height: 24px;
    gap: 4px;
}


.intro-bars span {
    display: block;
    width: 3px;
    height: 7px;
    border-radius: 5px;
    background: #62c7ff;

    animation:
        introWave
        0.7s
        infinite
        ease-in-out;
}


.intro-bars span:nth-child(2) {
    animation-delay: 0.1s;
}

.intro-bars span:nth-child(3) {
    animation-delay: 0.2s;
}

.intro-bars span:nth-child(4) {
    animation-delay: 0.3s;
}

.intro-bars span:nth-child(5) {
    animation-delay: 0.4s;
}


@keyframes introWave {

    0%,
    100% {
        height: 6px;
    }

    50% {
        height: 23px;
    }
}


/* ========================================================
   START BUTTON
   ======================================================== */

div[data-testid="stButton"] {
    position: fixed !important;
    left: 50vw !important;
    top: calc(50vh + 35px) !important;
    transform: translate(-50%, -50%) !important;

    width: 190px !important;

    margin: 0 !important;
    padding: 0 !important;

    z-index: 11000 !important;
}


div[data-testid="stButton"] button {
    width: 190px !important;
    height: 48px !important;

    margin: 0 !important;
    padding: 0 !important;

    border-radius: 30px !important;

    border:
        1px solid
        rgba(91,193,255,0.85)
        !important;

    background:
        rgba(2,20,52,0.90)
        !important;

    color: white !important;

    font-weight: 600 !important;
    letter-spacing: 1px !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    box-shadow:
        0 0 25px
        rgba(0,140,255,0.25)
        !important;
}


div[data-testid="stButton"] button:hover {
    border-color: #62c7ff !important;

    color: white !important;

    background:
        rgba(4,35,80,0.95)
        !important;

    box-shadow:
        0 0 35px
        rgba(0,165,255,0.55)
        !important;
}


/* ========================================================
   MAIN BRAND
   ======================================================== */

.aira-brand {
    position: fixed;

    top: 30px;
    right: 42px;

    z-index: 1000;

    color: white;

    font-family: Arial, sans-serif;

    font-size: 30px;
    font-weight: 800;

    letter-spacing: 6px;

    text-align: right;

    text-shadow:
        0 0 12px
        rgba(64,170,255,0.90),

        0 0 30px
        rgba(30,100,255,0.50);
}


.aira-subtitle {
    position: fixed;

    top: 72px;
    right: 42px;

    z-index: 1000;

    color:
        rgba(255,255,255,0.68);

    font-family: Arial, sans-serif;

    font-size: 11px;

    letter-spacing: 3px;

    text-align: right;
}


/* ========================================================
   CHAT HISTORY
   ======================================================== */

.chat-overlay {
    position: fixed;

    top: 110px;
    right: 35px;

    width: min(400px,30vw);

    max-height: 57vh;

    overflow-y: auto;

    z-index: 700;

    padding: 12px;

    scroll-behavior: smooth;
}


.user-bubble {
    width: fit-content;

    max-width: 88%;

    margin:
        10px
        0
        10px
        auto;

    padding:
        12px
        16px;

    border-radius:
        18px
        18px
        4px
        18px;

    background:
        linear-gradient(
            135deg,
            rgba(23,117,225,0.94),
            rgba(17,65,145,0.94)
        );

    color: white;

    font-family: Arial, sans-serif;

    font-size: 14px;

    line-height: 1.5;

    box-shadow:
        0 5px 20px
        rgba(0,0,0,0.25);
}


.assistant-bubble {
    width: fit-content;

    max-width: 92%;

    margin:
        10px
        auto
        10px
        0;

    padding:
        13px
        17px;

    border-radius:
        18px
        18px
        18px
        4px;

    border:
        1px solid
        rgba(75,171,255,0.40);

    background:
        rgba(3,15,38,0.88);

    color: white;

    font-family: Arial, sans-serif;

    font-size: 14px;

    line-height: 1.55;

    backdrop-filter:
        blur(12px);

    box-shadow:
        0 5px 25px
        rgba(0,0,0,0.30);
}


/* ========================================================
   MICROPHONE
   ======================================================== */

[data-testid="stAudioInput"] {
    position: fixed !important;

    left: 40px !important;
    right: auto !important;

    top: 50% !important;
    bottom: auto !important;

    transform:
        translateY(-50%)
        !important;

    width: 280px !important;

    z-index: 2000 !important;

    margin: 0 !important;
    padding: 0 !important;
}


[data-testid="stAudioInput"] > label {
    display: none !important;
}


/* ========================================================
   SPEAKING
   ======================================================== */

.aira-speaking,
.aira-stopped {
    position: fixed !important;

    left: 40px !important;

    top:
        calc(50% + 80px)
        !important;

    width: 280px !important;
    max-width: 280px !important;

    box-sizing: border-box !important;

    z-index: 2100;

    display: flex;

    align-items: center;
    justify-content: center;

    padding: 11px 12px;

    border-radius: 30px;

    background:
        rgba(2,14,36,0.88);

    color: white;

    font-family: Arial, sans-serif;

    font-size: 12px;

    backdrop-filter:
        blur(12px);
}


.aira-speaking {
    border:
        1px solid
        rgba(80,185,255,0.75);

    animation:
        speakingGlow
        1.2s
        infinite;
}


.aira-stopped {
    border:
        1px solid
        rgba(255,255,255,0.20);

    color:
        rgba(255,255,255,0.80);
}


@keyframes speakingGlow {

    0%,
    100% {
        box-shadow:
            0 0 10px
            rgba(0,140,255,0.25);
    }

    50% {
        box-shadow:
            0 0 30px
            rgba(0,165,255,0.75);
    }
}


/* ========================================================
   VOICE BARS
   ======================================================== */

.voice-bars {
    display: flex;

    align-items: center;

    height: 25px;

    margin-right: 10px;
}


.voice-bar {
    display: inline-block;

    width: 3px;
    height: 6px;

    margin: 0 2px;

    border-radius: 4px;

    background: #62c7ff;

    animation:
        voiceWave
        0.65s
        infinite
        ease-in-out;
}


.voice-bar:nth-child(2) {
    animation-delay: 0.1s;
}

.voice-bar:nth-child(3) {
    animation-delay: 0.2s;
}

.voice-bar:nth-child(4) {
    animation-delay: 0.3s;
}

.voice-bar:nth-child(5) {
    animation-delay: 0.4s;
}


@keyframes voiceWave {

    0%,
    100% {
        height: 5px;
    }

    50% {
        height: 22px;
    }
}


/* ========================================================
   BOTTOM
   ======================================================== */

[data-testid="stBottom"] {
    position: fixed !important;

    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;

    width: 100vw !important;

    background:
        transparent
        !important;

    border:
        none
        !important;

    box-shadow:
        none
        !important;

    z-index: 1000 !important;
}


[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div {
    background:
        transparent
        !important;

    border:
        none
        !important;

    box-shadow:
        none
        !important;
}


/* ========================================================
   CHAT INPUT
   ======================================================== */

[data-testid="stChatInput"] {
    position: fixed !important;

    left: 50% !important;

    bottom: 25px !important;

    transform:
        translateX(-50%);

    width:
        min(700px,60vw)
        !important;

    z-index: 1100;
}


[data-testid="stChatInput"] textarea {
    background:
        rgba(3,14,34,0.90)
        !important;

    color:
        white !important;

    border:
        1px solid
        rgba(78,170,255,0.65)
        !important;

    border-radius:
        30px !important;

    backdrop-filter:
        blur(14px);

    box-shadow:
        0 0 25px
        rgba(0,119,255,0.20);
}


[data-testid="stChatInput"]
textarea::placeholder {
    color:
        rgba(255,255,255,0.55)
        !important;
}


/* ========================================================
   HIDE AUDIO PLAYER
   ======================================================== */

[data-testid="stAudio"] {
    position: fixed !important;

    width: 1px !important;
    height: 1px !important;

    right: 0 !important;
    bottom: 0 !important;

    opacity: 0 !important;

    pointer-events: none !important;

    overflow: hidden !important;

    z-index: -1 !important;
}


/* ========================================================
   SCROLLBAR
   ======================================================== */

::-webkit-scrollbar {
    width: 4px;
}


::-webkit-scrollbar-thumb {
    background:
        rgba(70,160,255,0.55);

    border-radius: 10px;
}


/* ========================================================
   LARGE SCREEN
   ======================================================== */

@media (min-width: 1500px) {

    .aira-brand {
        right: 3vw;
        top: 4vh;
    }

    .aira-subtitle {
        right: 3vw;
        top: 9vh;
    }

    .chat-overlay {
        right: 3vw;
        top: 12vh;

        width: 420px;

        max-height: 60vh;
    }

    [data-testid="stChatInput"] {
        width:
            min(760px,55vw)
            !important;
    }

    [data-testid="stAudioInput"] {
        left: 3vw !important;
    }

    .aira-speaking,
    .aira-stopped {
        left: 3vw !important;
    }
}


/* ========================================================
   MOBILE
   ======================================================== */

@media (max-width: 800px) {

    [data-testid="stAppViewContainer"] {
        background-position:
            55% center
            !important;
    }

    .aira-brand {
        top: 20px;
        right: 20px;
        font-size: 22px;
    }

    .aira-subtitle {
        top: 52px;
        right: 20px;
    }

    .chat-overlay {
        top: 85px;
        right: 10px;

        width: 290px;

        max-height: 50vh;
    }

    [data-testid="stChatInput"] {
        width:
            65vw !important;

        left:
            42% !important;
    }

    [data-testid="stAudioInput"] {
        left: 18px !important;
        width: 260px !important;
    }

    .aira-speaking,
    .aira-stopped {
        left: 18px !important;
        width: 260px !important;
        max-width: 260px !important;
    }

    [data-testid="stImage"] {
        width: 120px !important;

        top:
            calc(50% - 100px)
            !important;
    }

    [data-testid="stImage"] img {
        width: 120px !important;
        height: 120px !important;
    }

    .aira-intro-title {
        font-size: 28px;
        letter-spacing: 8px;
    }

    div[data-testid="stButton"] {
        top:
            calc(50% + 30px)
            !important;
    }
}

</style>
"""


# =========================================================
# APPLY CSS
# =========================================================

css = CSS_TEMPLATE.replace(
    "__BACKGROUND__",
    background_css,
)

st.markdown(
    css,
    unsafe_allow_html=True,
)


# =========================================================
# INTRO SCREEN
# =========================================================

if not st.session_state.intro_complete:

    logo_exists = os.path.isfile(
        AIRA_LOGO
    )

    # =====================================================
    # BEFORE START
    # =====================================================

    if not st.session_state.intro_started:

        st.markdown(
            '<div class="aira-intro"></div>',
            unsafe_allow_html=True,
        )

        if logo_exists:

            st.image(
                AIRA_LOGO,
                width=160,
            )

        else:

            st.error(
                "Logo.png was not found.\n\n"
                f"Expected location: {AIRA_LOGO}"
            )

        if st.button(
            "START AIRA",
            key="start_aira",
        ):

            try:

                with st.spinner(
                    "Preparing Aira..."
                ):

                    intro_audio_path = (
                        text_to_speech(
                            AIRA_INTRO
                        )
                    )

                if (
                    intro_audio_path
                    and os.path.isfile(
                        intro_audio_path
                    )
                ):

                    st.session_state.intro_audio_path = (
                        intro_audio_path
                    )

                    st.session_state.intro_started = True

                    st.rerun()

                else:

                    st.error(
                        "Aira's intro audio "
                        "could not be generated."
                    )

            except Exception as e:

                st.error(
                    "Intro voice error: "
                    + str(e)
                )

        st.stop()

    # =====================================================
    # INTRO STARTED
    # =====================================================

    intro_audio = (
        st.session_state.intro_audio_path
    )

    if (
        intro_audio
        and os.path.isfile(
            intro_audio
        )
    ):

        st.markdown(
            '<div class="aira-intro"></div>',
            unsafe_allow_html=True,
        )

        if logo_exists:

            st.image(
                AIRA_LOGO,
                width=160,
            )

        intro_content_html = (
            '<div class="aira-intro-content">'
            '<div class="aira-intro-title">AIRA</div>'
            '<div class="aira-intro-subtitle">AI ASSISTANT</div>'
            '<div class="intro-status">'
            '<div class="intro-bars">'
            '<span></span>'
            '<span></span>'
            '<span></span>'
            '<span></span>'
            '<span></span>'
            '</div>'
            '<span>Aira is speaking</span>'
            '</div>'
            '</div>'
        )

        st.markdown(
            intro_content_html,
            unsafe_allow_html=True,
        )

        st.audio(
            intro_audio,
            format="audio/mp3",
            autoplay=True,
        )

        try:

            intro_duration = (
                get_audio_duration(
                    intro_audio
                )
            )

        except Exception as e:

            print(
                "Intro duration error:",
                str(e),
            )

            intro_duration = 0

        if intro_duration > 0:

            time.sleep(
                intro_duration + 0.5
            )

        else:

            time.sleep(3)

        st.session_state.intro_complete = True
        st.session_state.intro_started = False
        st.session_state.intro_audio_path = None

        st.rerun()

    else:

        st.session_state.intro_started = False
        st.session_state.intro_audio_path = None

        st.rerun()


# =========================================================
# KEYBOARD SHORTCUT SYSTEM
#
# This is intentionally added without changing the existing
# RAG, microphone, intro, chat, or normal TTS flow.
#
# Ctrl + 1 -> Welcome
# Ctrl + 2 -> Theme
# Ctrl + 3 -> Participant instructions
# Ctrl + 4 -> Rules
# Ctrl + 5 -> Closing
#
# The shortcut audio is generated by the SAME text_to_speech()
# function used by Aira, then played directly in the browser.
# =========================================================

if "shortcut_audio_paths" not in st.session_state:
    st.session_state.shortcut_audio_paths = {}


def prepare_shortcut_audio():

    for shortcut_key, shortcut_text in SHORTCUT_SCRIPTS.items():

        existing_path = st.session_state.shortcut_audio_paths.get(
            shortcut_key
        )

        if (
            existing_path
            and os.path.isfile(existing_path)
        ):
            continue

        try:

            generated_path = text_to_speech(
                shortcut_text
            )

            if (
                generated_path
                and os.path.isfile(generated_path)
            ):

                st.session_state.shortcut_audio_paths[
                    shortcut_key
                ] = generated_path

        except Exception as e:

            print(
                f"Shortcut audio generation failed "
                f"for {shortcut_key}: {e}"
            )


# Generate each shortcut voice only once per Streamlit session.
prepare_shortcut_audio()


shortcut_audio_data = {}

for (
    shortcut_key,
    shortcut_path
) in st.session_state.shortcut_audio_paths.items():

    if (
        shortcut_path
        and os.path.isfile(shortcut_path)
    ):

        try:

            with open(
                shortcut_path,
                "rb"
            ) as shortcut_file:

                encoded_audio = (
                    base64.b64encode(
                        shortcut_file.read()
                    ).decode("utf-8")
                )

            shortcut_audio_data[
                shortcut_key
            ] = (
                "data:audio/mpeg;base64,"
                + encoded_audio
            )

        except Exception as e:

            print(
                f"Shortcut audio encoding failed "
                f"for {shortcut_key}: {e}"
            )


# st.html with unsafe_allow_javascript=True is NOT iframe-based.
# This lets the keyboard listener attach directly to the Streamlit
# page, unlike components.html(), which is sandboxed in an iframe.

shortcut_html = f"""
<script>
(() => {{

    const shortcutAudio = {{
        F1: {shortcut_audio_data.get("F1", "")!r},
        F2: {shortcut_audio_data.get("F2", "")!r},
        F3: {shortcut_audio_data.get("F3", "")!r},
        F4: {shortcut_audio_data.get("F4", "")!r},
        F5: {shortcut_audio_data.get("F5", "")!r}
    }};


    function userIsTyping() {{

        const active =
            document.activeElement;

        if (!active) {{
            return false;
        }}

        const tag =
            active.tagName;

        return (
            tag === "INPUT" ||
            tag === "TEXTAREA" ||
            active.isContentEditable
        );
    }}


    function stopAllAiraAudio() {{

        if (
            window.__airaShortcutAudio
        ) {{

            try {{
                window.__airaShortcutAudio.pause();
                window.__airaShortcutAudio.currentTime = 0;
            }}
            catch (error) {{
                console.log(error);
            }}

            window.__airaShortcutAudio = null;
        }}


        document
            .querySelectorAll("audio")
            .forEach((audio) => {{

                try {{
                    audio.pause();
                    audio.currentTime = 0;
                }}
                catch (error) {{
                    console.log(error);
                }}

            }});
    }}


    function playShortcut(key) {{

        const source =
            shortcutAudio[key];

        if (!source) {{
            console.warn(
                "No Aira shortcut audio available for",
                key
            );
            return;
        }}


        stopAllAiraAudio();


        const audio =
            new Audio(source);

        window.__airaShortcutAudio =
            audio;


        audio.addEventListener(
            "ended",
            () => {{

                if (
                    window.__airaShortcutAudio
                    === audio
                ) {{
                    window.__airaShortcutAudio =
                        null;
                }}

            }}
        );


        audio.play().catch(
            (error) => {{

                console.error(
                    "Unable to play Aira shortcut:",
                    error
                );

            }}
        );
    }}


    if (
        window.__airaKeyboardShortcutHandler
    ) {{

        document.removeEventListener(
            "keydown",
            window.__airaKeyboardShortcutHandler,
            true
        );
    }}


    window.__airaKeyboardShortcutHandler =
        (event) => {{

            if (userIsTyping()) {{
                return;
            }}


            const key =
                event.key;


            // =============================================
            // CTRL + NUMBER SHORTCUTS
            //
            // Ctrl + 1 -> F1 script
            // Ctrl + 2 -> F2 script
            // Ctrl + 3 -> F3 script
            // Ctrl + 4 -> F4 script
            // Ctrl + 5 -> F5 script
            // =============================================

            const ctrlShortcuts = {{
                "1": "F1",
                "2": "F2",
                "3": "F3",
                "4": "F4",
                "5": "F5"
            }};


            if (
                event.ctrlKey &&
                !event.altKey &&
                !event.metaKey &&
                Object.prototype.hasOwnProperty.call(
                    ctrlShortcuts,
                    key
                )
            ) {{

                event.preventDefault();
                event.stopPropagation();

                playShortcut(
                    ctrlShortcuts[key]
                );

                return;
            }}


            if (
                event.code === "Space" ||
                event.key === " "
            ) {{

                event.preventDefault();
                event.stopPropagation();

                stopAllAiraAudio();
            }}
        }};


    document.addEventListener(
        "keydown",
        window.__airaKeyboardShortcutHandler,
        true
    );

}})();
</script>
"""


try:

    st.html(
        shortcut_html,
        unsafe_allow_javascript=True,
    )

except TypeError:

    st.error(
        "Keyboard shortcuts require Streamlit 1.52 or newer. "
        "Run: pip install --upgrade streamlit"
    )


# =========================================================
# MAIN AIRA BRAND
# =========================================================

main_brand_html = (
    '<div class="aira-brand">AIRA</div>'
    '<div class="aira-subtitle">AI ASSISTANT</div>'
)

st.markdown(
    main_brand_html,
    unsafe_allow_html=True,
)


# =========================================================
# CHAT HISTORY
# =========================================================

if st.session_state.messages:

    chat_parts = [
        '<div class="chat-overlay">'
    ]

    for message in st.session_state.messages:

        safe_content = html.escape(
            str(
                message["content"]
            )
        ).replace(
            "\n",
            "<br>",
        )

        if message["role"] == "user":

            chat_parts.append(
                '<div class="user-bubble">'
                + safe_content
                + '</div>'
            )

        else:

            chat_parts.append(
                '<div class="assistant-bubble">'
                + safe_content
                + '</div>'
            )

    chat_parts.append(
        "</div>"
    )

    st.markdown(
        "".join(chat_parts),
        unsafe_allow_html=True,
    )


# =========================================================
# GET RAG ANSWER
# =========================================================

def generate_answer(question):

    try:

        result = ask_agent(
            question
        )

        if isinstance(result, dict):

            return result.get(
                "answer",
                "Sorry, I couldn't find an answer.",
            )

        return str(result)

    except Exception as e:

        st.error(
            "Agent error: "
            + str(e)
        )

        return (
            "Sorry, I couldn't process "
            "your question."
        )


# =========================================================
# PREPARE RESPONSE VOICE
# =========================================================

def prepare_voice(answer):

    try:

        audio_path = text_to_speech(
            answer
        )

        if (
            not audio_path
            or not os.path.isfile(
                audio_path
            )
        ):

            return False

        st.session_state.voice_audio_path = (
            audio_path
        )

        st.session_state.is_speaking = True

        st.session_state.speaking_started = (
            time.time()
        )

        return True

    except Exception as e:

        st.session_state.voice_audio_path = None

        st.session_state.is_speaking = False

        st.session_state.speaking_started = None

        st.error(
            "Text-to-speech failed: "
            + str(e)
        )

        return False


# =========================================================
# CHAT INPUT
# =========================================================

user_question = st.chat_input(
    " Type your questions here..."
)


# =========================================================
# PROCESS TEXT QUESTION
# =========================================================

if user_question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.spinner(
        "Aira is thinking..."
    ):

        answer = generate_answer(
            user_question
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    with st.spinner(
        "Preparing Aira's voice..."
    ):

        prepare_voice(
            answer
        )

    st.rerun()


# =========================================================
# MICROPHONE
# =========================================================

audio_value = st.audio_input(
    "Record your question",
    sample_rate=16000,
    key="aira_microphone",
    label_visibility="collapsed",
)


# =========================================================
# PROCESS MICROPHONE
# =========================================================

if audio_value:

    audio_bytes = (
        audio_value.getvalue()
    )

    audio_hash = hashlib.md5(
        audio_bytes
    ).hexdigest()

    if (
        st.session_state.processed_audio
        != audio_hash
    ):

        st.session_state.processed_audio = (
            audio_hash
        )

        try:

            with st.spinner(
                "Listening..."
            ):

                question = speech_to_text(
                    audio_value
                )

        except Exception as e:

            question = ""

            st.error(
                "Speech-to-text failed: "
                + str(e)
            )

        if question:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            with st.spinner(
                "Aira is thinking..."
            ):

                answer = generate_answer(
                    question
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            with st.spinner(
                "Preparing Aira's voice..."
            ):

                prepare_voice(
                    answer
                )

            st.rerun()


# =========================================================
# RESPONSE SPEAKING STATE
# =========================================================

audio_path = (
    st.session_state.voice_audio_path
)

if (
    audio_path
    and os.path.isfile(
        audio_path
    )
):

    try:

        duration = get_audio_duration(
            audio_path
        )

    except Exception:

        duration = 0


    elapsed = 0


    if st.session_state.speaking_started:

        elapsed = (
            time.time()
            -
            st.session_state.speaking_started
        )


    # =====================================================
    # AIRA SPEAKING
    # =====================================================

    if (
        st.session_state.is_speaking
        and duration > 0
        and elapsed < duration
    ):

        speaking_html = (
            '<div class="aira-speaking">'
            '<div class="voice-bars">'
            '<span class="voice-bar"></span>'
            '<span class="voice-bar"></span>'
            '<span class="voice-bar"></span>'
            '<span class="voice-bar"></span>'
            '<span class="voice-bar"></span>'
            '</div>'
            '<span>Aira is speaking</span>'
            '</div>'
        )

        st.markdown(
            speaking_html,
            unsafe_allow_html=True,
        )


        # =================================================
        # PLAY RESPONSE
        # =================================================

        st.audio(
            audio_path,
            format="audio/mp3",
            autoplay=True,
        )


        # =================================================
        # STOP BUTTON
        # =================================================

        if st.button(
            "⏹ STOP SPEAKING",
            key="stop_aira_speaking",
        ):

            st.session_state.is_speaking = False

            st.session_state.speaking_started = None

            st.session_state.voice_audio_path = None

            st.rerun()


    # =====================================================
    # AIRA STOPPED
    # =====================================================

    else:

        st.session_state.is_speaking = False

        st.session_state.speaking_started = None


        stopped_html = (
            '<div class="aira-stopped">'
            '<span>✓ Aira stopped speaking</span>'
            '</div>'
        )

        st.markdown(
            stopped_html,
            unsafe_allow_html=True,
        )