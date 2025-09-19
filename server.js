// server.js
const express = require("express");
const bodyParser = require("body-parser");
const http = require("http");
const WebSocket = require("ws");

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// ====== CONFIG ======
const VERIFY_TOKEN = "Personal92!"; // your Facebook Verify Token
let clients = [];
let commentQueue = [];
let currentIndex = 0;

// Middleware
app.use(bodyParser.json());
app.use(express.static(__dirname)); // Serve overlay.html

// ====== FACEBOOK WEBHOOK VERIFY ======
app.get("/facebook-webhook", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode === "subscribe" && token === VERIFY_TOKEN) {
    console.log("✅ Webhook verified");
    res.status(200).send(challenge);
  } else {
    console.log("❌ Verification failed");
    res.sendStatus(403);
  }
});

// ====== RECEIVE FACEBOOK EVENTS ======
app.post("/facebook-webhook", (req, res) => {
  if (req.body.object === "page") {
    req.body.entry.forEach((entry) => {
      const changes = entry.changes || [];
      changes.forEach((change) => {
        if (
          change.field === "feed" &&
          change.value &&
          change.value.item === "comment"
        ) {
          const message = change.value.message || "";
          const from = change.value.from ? change.value.from.name : "Anonymous";
          const fullComment = `${from}: ${message}`;
          console.log("💬 New Comment:", fullComment);

          // Push to queue
          commentQueue.push(fullComment);
        }
      });
    });
    res.sendStatus(200);
  } else {
    res.sendStatus(404);
  }
});

// ====== WEBSOCKET HANDLING ======
wss.on("connection", (ws) => {
  console.log("🔌 Client connected");
  clients.push(ws);

  ws.on("close", () => {
    clients = clients.filter((c) => c !== ws);
    console.log("❌ Client disconnected");
  });
});

// ====== LOOP COMMENTS ======
setInterval(() => {
  if (commentQueue.length > 0 && clients.length > 0) {
    const comment = commentQueue[currentIndex];
    clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(comment);
      }
    });

    // Cycle through comments
    currentIndex = (currentIndex + 1) % commentQueue.length;
  }
}, 5000); // every 5 seconds

// ====== START SERVER ======
const PORT = process.env.PORT || 10000;
server.listen(PORT, () => {
  console.log(`🚀 Facebook Webhook + Overlay Server running on port ${PORT}`);
});
