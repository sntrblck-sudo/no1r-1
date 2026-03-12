# Auto-manage daemon
# Monitors gateway, dashboard, and usage; auto-restarts or switches models as needed.

**Status:** Running in background.

**What it does:**
- ✅ Restarts gateway if down
- ✅ Restarts dashboard if down  
- ✅ Switches to free model if daily cost > $0.50
- ✅ Logs all actions to `memory/automanage.log`
- ✅ Sends Telegram alerts (one per issue type per 2h)
- ✅ **Runs reflection every 6 hours** — analyzes patterns, updates MEMORY.md
- ✅ **Auto-commits changes every 10 min** — workspace backed up to git
- ✅ **Monitors @ClawiAi Twitter every 2 hours** — alerts on meaningful updates

**Safety rules:**
- Only safe toggles (model, restarts)
- Never deletes files or credentials
- Never touches auth configs
- Logs everything for review

**To check:**
```bash
cat /root/.openclaw/workspace/memory/automanage.log
```

**To stop:** `pkill -f automanage.py`

**To restart:** `python3 automanage.py &`

---

*Automanage is running silently in the background, fixing problems before you notice them.*