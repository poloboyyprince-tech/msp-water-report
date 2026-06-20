#!/bin/bash
# Double-click this file to start MSP Pure Water and open it in your browser.
# Keep the window that opens up while you use the app; close it to stop.

cd "$(dirname "$0")" || exit 1
PORT=5050

clear
echo "======================================================"
echo "   MSP Pure Water  —  Water Report Generator"
echo "======================================================"
echo

# 1) Make sure the needed Python packages are installed (first run only).
if ! python3 -c "import flask, reportlab" >/dev/null 2>&1; then
  echo "Setting up for the first time (installing components)..."
  python3 -m pip install --user -q flask reportlab >/dev/null 2>&1
fi

# 2) If it's already running, just open the browser and stop.
if curl -s -m 2 "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then
  echo "Already running — opening your browser..."
  open "http://127.0.0.1:$PORT/"
  echo
  echo "The app is open in your browser. You can close this window."
  exit 0
fi

# 3) Start the server in the background.
echo "Starting the app..."
PORT=$PORT python3 app.py >/tmp/msp_water.log 2>&1 &
SERVER_PID=$!

# 4) Wait until it answers, then open the browser.
for i in $(seq 1 30); do
  if curl -s -m 2 "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if curl -s -m 2 "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then
  open "http://127.0.0.1:$PORT/"
  echo
  echo "  ✅  MSP Pure Water is running."
  echo "      It just opened in your web browser."
  echo "      (If not, go to:  http://127.0.0.1:$PORT )"
  echo
  echo "  ⚠️   KEEP THIS WINDOW OPEN while you use the app."
  echo "      To stop: close this window or press  Control-C."
  echo "======================================================"
  wait $SERVER_PID
else
  echo
  echo "  ❌  Could not start the app. Details:"
  echo "  ----------------------------------------------------"
  tail -20 /tmp/msp_water.log
  echo "  ----------------------------------------------------"
  echo "  Press any key to close."
  read -n 1 -s
fi
