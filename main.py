import streamlit as st
import streamlit.components.v1 as components
import os
import json
import time
import uuid
from datetime import datetime

ROOMS_FILE = "rooms.json"


def load_rooms(path=ROOMS_FILE):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def save_rooms(data, path=ROOMS_FILE):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def ensure_room(rooms, room_id):
    if room_id not in rooms:
        rooms[room_id] = {
            "id": room_id,
            "created": datetime.utcnow().isoformat(),
            "participants": {},
            "host": None,
            "video": None,
            "play_state": {"playing": False, "pos": 0.0, "updated": time.time()},
            "chats": {"global": []},
            "subgroups": {}
        }


def add_participant(rooms, room_id, name, is_host=False):
    p = {"name": name, "joined": datetime.utcnow().isoformat(), "is_host": is_host}
    rooms[room_id]["participants"][name] = p
    if is_host:
        rooms[room_id]["host"] = name


def add_message(rooms, room_id, chat_name, sender, text):
    msg = {"sender": sender, "text": text, "time": datetime.utcnow().isoformat()}
    if chat_name == "global":
        rooms[room_id]["chats"]["global"].append(msg)
    else:
        if chat_name in rooms[room_id]["subgroups"]:
            rooms[room_id]["subgroups"][chat_name]["messages"].append(msg)


def create_subgroup(rooms, room_id, name, members):
    rooms[room_id]["subgroups"][name] = {"members": members, "messages": []}


def update_play_state(rooms, room_id, playing=None, pos=None):
    stt = rooms[room_id]["play_state"]
    now = time.time()
    if pos is not None:
        stt["pos"] = float(pos)
        stt["updated"] = now
    if playing is not None:
        if playing and not stt.get("playing"):
            stt["updated"] = now
        stt["playing"] = bool(playing)


def compute_current_pos(play_state):
    if play_state.get("playing"):
        return play_state.get("pos", 0.0) + (time.time() - play_state.get("updated", time.time()))
    return play_state.get("pos", 0.0)


def get_query_params():
    if hasattr(st, "query_params"):
        return st.query_params
    if hasattr(st, "experimental_get_query_params"):
        return st.experimental_get_query_params()
    if hasattr(st, "get_query_params"):
        return st.get_query_params()
    return {}


def set_query_params(params):
    if hasattr(st, "query_params"):
        st.query_params = params
    elif hasattr(st, "experimental_set_query_params"):
        st.experimental_set_query_params(**params)
    elif hasattr(st, "set_query_params"):
        st.set_query_params(**params)


def main():
    st.set_page_config(page_title="MovieMate - Watch Together (MVP)", layout="wide")
    st.title("MovieMate — Watch movies together (MVP)")

    rooms = load_rooms()

    sidebar = st.sidebar
    sidebar.header("Join or Create Room")
    query_params = get_query_params()
    default_room = query_params.get("room", [""])[0] if isinstance(query_params, dict) else query_params.get("room", [""])[0]
    username = sidebar.text_input("Your name", value=f"User-{uuid.uuid4().hex[:4]}")
    room_id_input = sidebar.text_input("Room ID to join / create", value=default_room)
    create = sidebar.button("Create room")
    host_checkbox = sidebar.checkbox("I'm the host (when creating)")

    if "room" not in st.session_state:
        st.session_state["room"] = ""

    join = sidebar.button("Join room")

    if create:
        room_id = room_id_input.strip() or uuid.uuid4().hex[:8]
        ensure_room(rooms, room_id)
        add_participant(rooms, room_id, username, is_host=host_checkbox)
        save_rooms(rooms)
        st.session_state["room"] = room_id
        set_query_params({"room": [room_id]})
        st.success(f"Created room {room_id}")

    if join:
        room_id = room_id_input.strip()
        if room_id:
            ensure_room(rooms, room_id)
            add_participant(rooms, room_id, username, is_host=False)
            save_rooms(rooms)
            st.session_state["room"] = room_id
            set_query_params({"room": [room_id]})
            st.success(f"Joined room {room_id}")

    room = st.session_state.get("room", "")
    if not room and default_room:
        room = default_room
        ensure_room(rooms, room)
        add_participant(rooms, room, username, is_host=False)
        save_rooms(rooms)
        st.session_state["room"] = room
        set_query_params({"room": [room]})
        st.success(f"Auto-joined room {room} from share link")

    if not room:
        st.info("Create or enter a room ID to proceed.")
        return

    ensure_room(rooms, room)
    if username not in rooms[room]["participants"]:
        add_participant(rooms, room, username, is_host=False)
        save_rooms(rooms)

    st.header(f"Room: {room}")
    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Participants")
        for p in rooms[room]["participants"]:
            info = rooms[room]["participants"][p]
            host_tag = " (host)" if info.get("is_host") else ""
            st.write(f"- {info['name']}{host_tag}")

        st.markdown("---")
        st.subheader("Local camera / mic")
        cam = st.camera_input("Turn on your camera (local preview)")
        mic = st.checkbox("Mic on (local only)")

        st.markdown("---")
        st.subheader("Screen + audio sharing")
        components.html(
            """
            <button id=\"start\">Start screen + audio share</button>
            <button id=\"stop\" style=\"margin-left:10px;\">Stop</button>
            <video id=\"screenVideo\" autoplay playsinline controls style=\"width:100%; margin-top:12px; border:1px solid #ddd;\"></video>
            <script>
            const start = document.getElementById('start');
            const stop = document.getElementById('stop');
            const video = document.getElementById('screenVideo');
            let stream = null;
            start.onclick = async () => {
                try {
                    stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
                    video.srcObject = stream;
                    video.onloadedmetadata = () => video.play();
                } catch (err) {
                    alert(err.message || err);
                }
            };
            stop.onclick = () => {
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    video.srcObject = null;
                    stream = null;
                }
            };
            </script>
            """,
            height=320,
            scrolling=False,
        )
        st.caption("This starts a local screen+audio preview in your browser. Actual multi-user streaming is not yet implemented.")
        st.markdown("---")
        st.subheader("Mobile share link")
        room_js = json.dumps(room)
        components.html(
            """
            <div style=\"font-family: sans-serif;\">
              <p style=\"margin: 0 0 8px 0;\">Share this URL to join on mobile or any other device:</p>
              <input id=\"shareLink\" type=\"text\" style=\"width:100%; padding:10px; font-size:14px; border:1px solid #ccc; border-radius:6px;\" readonly />
              <button id=\"copyBtn\" style=\"margin-top:8px; width:100%; padding:10px; background:#0f62fe; color:white; border:none; border-radius:6px; cursor:pointer;\">Copy share link</button>
              <p style=\"margin:8px 0 0 0; font-size:13px; color:#666;\">Open this on mobile and it will prefill the room ID.</p>
            </div>
            <script>
            const roomId = """ + room_js + """;
            const current = new URL(window.location.href);
            current.searchParams.set('room', roomId);
            const shareLink = current.toString();
            document.getElementById('shareLink').value = shareLink;
            document.getElementById('copyBtn').onclick = async () => {
              await navigator.clipboard.writeText(shareLink);
              alert('Share link copied to clipboard');
            };
            </script>
            """,
            height=200,
            scrolling=False,
        )

    with col1:
        st.subheader("Video Area")
        video_file = rooms[room].get("video")
        is_host = rooms[room].get("host") == username
        if is_host:
            st.info("You are the host for this room")
            upload = st.file_uploader("Upload an MP4 video for the room (will be used by all)", type=["mp4", "mov", "m4v"])
            if upload is not None:
                os.makedirs(f"uploads/{room}", exist_ok=True)
                path = f"uploads/{room}/video.mp4"
                with open(path, "wb") as f:
                    f.write(upload.getbuffer())
                rooms[room]["video"] = path
                save_rooms(rooms)
                st.success("Video uploaded and set for the room")

        if video_file:
            pos = compute_current_pos(rooms[room]["play_state"])
            st.video(video_file, start_time=int(pos))
            if st.button("Sync to host"):
                pos2 = compute_current_pos(rooms[room]["play_state"])
                st.video(video_file, start_time=int(pos2))

            st.write(f"Host: {rooms[room].get('host')}")
            st.write(f"Playback: {'Playing' if rooms[room]['play_state'].get('playing') else 'Paused'}")
            st.write(f"Position (s): {int(pos)}")
        else:
            st.info("No video set for this room. Host can upload an MP4.")

        if is_host:
            st.subheader("Host playback controls")
            pos = compute_current_pos(rooms[room]["play_state"])
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Play"):
                    update_play_state(rooms, room, playing=True, pos=pos)
                    save_rooms(rooms)
                    st.experimental_rerun()
            with c2:
                if st.button("Pause"):
                    update_play_state(rooms, room, playing=False, pos=pos)
                    save_rooms(rooms)
                    st.experimental_rerun()
            with c3:
                seek = st.number_input("Seek to (seconds)", min_value=0.0, value=float(pos))
                if st.button("Seek"):
                    update_play_state(rooms, room, pos=seek)
                    save_rooms(rooms)
                    st.experimental_rerun()

        st.markdown("---")
        st.subheader("Chat & Subgroups")
        chat_col1, chat_col2 = st.columns([3, 1])
        with chat_col1:
            chat_options = ["global"] + list(rooms[room]["subgroups"].keys())
            chat_choice = st.selectbox("Choose chat", chat_options)
            msgs = rooms[room]["chats"]["global"] if chat_choice == "global" else rooms[room]["subgroups"][chat_choice]["messages"]
            for m in msgs[-200:]:
                st.write(f"**{m['sender']}**: {m['text']}  ")
            msg = st.text_input("Message")
            if st.button("Send") and msg.strip():
                add_message(rooms, room, chat_choice, username, msg.strip())
                save_rooms(rooms)
                st.experimental_rerun()

        with chat_col2:
            st.subheader("Create subgroup")
            sg_name = st.text_input("Subgroup name")
            members = st.multiselect("Members", list(rooms[room]["participants"].keys()))
            if st.button("Create subgroup") and sg_name.strip() and members:
                create_subgroup(rooms, room, sg_name.strip(), members)
                save_rooms(rooms)
                st.success("Subgroup created")


if __name__ == '__main__':
    main()
