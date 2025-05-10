import os
import sys
import gc
import json
import threading
from pathlib import Path
from typing import Dict
from datetime import datetime, timedelta
import psutil

import streamlit as st
from streamlit.runtime import get_instance
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

from utils.logger import logger

# Constants
HEARTBEAT_TIMEOUT = 30  # 30 minutes (timeout for inactive sessions)
CLEANUP_INTERVAL = 300  # 5 minutes (cleanup frequency)

@st.cache_resource(show_spinner=False)
def get_heartbeat_manager():
    """Singleton instance of HeartbeatManager."""
    return HeartbeatManager()

@st.cache_resource(show_spinner=False)
def get_memory_manager():
    """Singleton instance of MemoryManager."""
    return MemoryManager()

def initialize_memory_and_heartbeat():
    """Initialize memory and heartbeat managers. Call once per session."""
    if "cleanup_initialized" not in st.session_state:
        memory_manager = get_memory_manager()
        memory_manager.start_periodic_cleanup()
        st.session_state['heartbeat_manager'] = get_heartbeat_manager()
        st.session_state.cleanup_initialized = True

def update_session_activity():
    """Update session's last activity timestamp. Call on every user interaction."""
    ctx = get_script_run_ctx()
    if ctx and (hm := st.session_state.get('heartbeat_manager')):
        hm.update_activity(ctx.session_id)
    else:
        logger.error("Activity update failed: missing context or manager")

# ---------------------------- HeartbeatManager Implementation ----------------------------
class HeartbeatManager:
    def __init__(self, storage_file: str = "session_heartbeats.json"):
        """Manages session activity and heartbeat tracking."""
        self.storage_file = Path(storage_file)
        self.lock = threading.Lock()
        self._ensure_storage_file()

    def _ensure_storage_file(self):
        """Create storage file if it doesn't exist."""
        if not self.storage_file.exists():
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)

    def _load_sessions(self) -> Dict:
        """Load session data from file."""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_sessions(self, sessions: Dict):
        """Save session data to file."""
        with open(self.storage_file, 'w') as f:
            json.dump(sessions, f, indent=2)

    def update_activity(self, session_id: str):
        """Update session's last activity and heartbeat timestamp."""
        current_time = datetime.now().isoformat()
        with self.lock:
            sessions = self._load_sessions()
            sessions[session_id] = {
                'heartbeat': current_time, 
                'last_activity': current_time
            }
            self._save_sessions(sessions)

    def cleanup_sessions(self, timeout_minutes: int = HEARTBEAT_TIMEOUT):
        """Remove inactive sessions based on last activity."""
        with self.lock:
            sessions = self._load_sessions()
            current_time = datetime.now()
            active_sessions = {}
            timeout = timedelta(minutes=timeout_minutes)
            
            for session_id, data in sessions.items():
                if not isinstance(data, dict) or 'last_activity' not in data:
                    continue
                try:
                    last_activity = datetime.fromisoformat(data['last_activity'])
                    if (current_time - last_activity) < timeout:
                        active_sessions[session_id] = data
                except (ValueError, TypeError):
                    continue
            self._save_sessions(active_sessions)
            return active_sessions

# ---------------------------- MemoryManager Implementation ----------------------------
class MemoryManager:
    def __init__(self, cleanup_interval: int = CLEANUP_INTERVAL):
        """Manages periodic cleanup of inactive sessions and memory."""
        self.cleanup_interval = cleanup_interval
        self.lock = threading.Lock()
        self._timer = None
        self.cleanup_running = False

    def cleanup_streamlit_resources(self):
        """Clean up Streamlit sessions and free memory."""
        
        with self.lock:
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss
            
            try:
                # Get Streamlit runtime instance
                runtime = get_instance()
            except Exception as e:
                logger.info(f"Streamlit runtime not available: {e}")
                return

            # Cleanup inactive sessions using heartbeats
            closed = 0
            if runtime is not None:
                try:
                    session_mgr = runtime._session_mgr
                    sessions = session_mgr.list_sessions()
                    logger.info(f"Found {len(sessions)} sessions")
                    
                    # Get active sessions from HeartbeatManager
                    heartbeat_manager = get_heartbeat_manager()
                    active_sessions = heartbeat_manager.cleanup_sessions()
                    active_session_ids = active_sessions.keys()

                    # Get Streamlit's active sessions
                    streamlit_sessions = [s.session.id for s in sessions]

                    # Close sessions in Streamlit that are not in the HeartbeatManager's active list
                    for session_id in streamlit_sessions:
                        if session_id not in active_session_ids:
                            runtime.close_session(session_id)
                            closed += 1
                    logger.info(f"Closed {closed} inactive sessions")
                except Exception as e:
                    logger.error(f"Session cleanup error: {str(e)}")

            # General memory cleanup
            gc.collect()
            mem_after = process.memory_info().rss
            if closed > 0:
                logger.info(f"Cleared up { (mem_before - mem_after) / 1e6:.1f}MB")

            # Linux memory trimming
            if os.name == 'posix' and sys.platform != 'darwin':
                try:
                    import ctypes
                    libc = ctypes.CDLL('libc.so.6')
                    libc.malloc_trim(0)
                    logger.info("Performed malloc_trim")
                except Exception as e:
                    logger.info(f"malloc_trim failed: {e}")

    def start_periodic_cleanup(self):
        """Start periodic cleanup in a background thread."""
        def cleanup_loop():
            try:
                self.cleanup_streamlit_resources()
            finally:
                self._timer = threading.Timer(self.cleanup_interval, cleanup_loop)
                self._timer.daemon = True
                add_script_run_ctx(self._timer)
                self._timer.start()

        # Start the first cleanup
        if not self.cleanup_running:
            self.cleanup_running = True
            self._timer = threading.Timer(self.cleanup_interval, cleanup_loop)
            self._timer.daemon = True
            add_script_run_ctx(self._timer)
            self._timer.start()
            self.cleanup_running = True