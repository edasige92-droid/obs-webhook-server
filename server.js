// server.js
const express = require("express");
const bodyParser = require("body-parser");
const WebSocket = require("ws");

const app = express();
const PORT = process.env.PORT || 3000;

// ✅ Your secret verification token
const VERIFY_TOKEN = "Personal92!";

// Middleware
app.use(bodyParser.json());
app.use(express.static("static"));

// WebSocket Server (for OBS overlay)
const server = app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
const wss = new WebSocket.Server({ server });

let commentsQueue = [];
let wsClients = [];

// Facebook Webhook Verification (GET)
app.get("/", (req, res) => {
  let mode = req.query["hub.mode"];
  let token = req.query["hub.verify_token"];
  let challenge = req.query["hub.challenge"];

  if (mode && token && mode === "subscribe" && token === VERIFY_TOKEN) {
    console.log("✅ Webhook verified!");
    res.status(200).send(challenge);
  } else {
    console.log("❌ Verification failed. Tokens do not match.");
    res.sendStatus(403);
  }
});

// Facebook Webhook Receiver (POST)
app.post("/", (req, res) => {
  let body = req.body;

  if (body.object === "page") {
    body.entry.forEach((entry) => {
      let changes = entry.changes || [];
      changes.forEach((change) => {
        if (change.field === "feed" && change.value.comment_id) {
          let comment = {
            from: change.value.from ? change.value.from.name : "Anonymous",
            message: change.value.message,
          };

          console.log("💬 New Comment:", comment);
          commentsQueue.push(comment);
          broadcastComments();
        }
      });
    });

    res.sendStatus(200);
  } else {
    res.sendStatus(404);
  }
});

// WebSocket Connection
wss.on("connection", (ws) => {
  console.log("🔗 New WebSocket client connected");
  wsClients.push(ws);

  ws.on("close", () => {
    wsClients = wsClients.filter((client) => client !== ws);
  });
});

// Function to broadcast comments (loop through queue)
function broadcastComments() {
  if (commentsQueue.length === 0) return;

  let comment = commentsQueue.shift();

  wsClients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(comment));
    }
  });

  // Push back to queue (looping effect)
  commentsQueue.push(comment);

  // Delay before showing next comment
  setTimeout(broadcastComments, 5000); // 5 seconds per comment
}
