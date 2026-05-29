# MovieMate (Streamlit MVP)

This is a minimal Streamlit MVP for "watch together" with group/subgroup chat.

Features:
- Create or join rooms by ID
- Host can upload an MP4 that everyone in the room can play together
- Host controls: play / pause / seek (server-side state)
- Clients can click "Sync to host" to jump to host's position
- Global chat and create subgroups (subgroup messages visible to members; host can view all)
- Local camera preview and mic toggle (local only in this MVP)

Limitations and next steps:
- Live camera/mic streaming between participants (WebRTC) is NOT included in this MVP. To add real-time audio/video, integrate a WebRTC solution (e.g., streamlit-webrtc, Janus, or a hosted WebRTC signaling service).
- Automatic client-side video seeking/continuous syncing is limited; users can click "Sync to host" to jump to the host position. A richer solution would use a Streamlit component with bi-directional JS to apply host timestamps automatically.

Run locally:
1. Create a venv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
streamlit run main.py
```

3. Create a room in the sidebar (check "I'm the host"), upload an MP4, then share the URL from your browser with participants.

This is an MVP to iterate from; tell me if you want me to add WebRTC-based live cameras/mic next.
# QuisUP-dey
Online Quiz Dashboard - Stop using laymen Google form.
