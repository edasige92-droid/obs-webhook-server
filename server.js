const express = require("express");
const bodyParser = require("body-parser");
const http = require("http");
const WebSocket = require("ws");

const app = express();
app.use(bodyParser.json());

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Store comments in memory
let comments = [];
let currentIndex = 0;

// Send comments one by one in a loop
function broadcastComments() {
  if (comments.length === 0) return;

  const comment = comments[currentIndex];
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(comment));
    }
  });

  // Move to next comment, loop if end reached
  currentIndex = (currentIndex + 1) % comments.length;

  // Show next comment after 6 seconds
  setTimeout(broadcastComments, 6000);
}

// Facebook webhook verification
app.get("/webhook", (req, res) => {
  const VERIFY_TOKEN = "Personal92!";
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode && token && mode === "subscribe" && token === VERIFY_TOKEN) {
    console.log("WEBHOOK_VERIFIED");
    res.status(200).send(challenge);
  } else {
    res.sendStatus(403);
  }
});

// Webhook receiver for comments
app.post("/webhook", (req, res) => {
  console.log("Webhook event:", JSON.stringify(req.body, null, 2));

  if (req.body.entry) {
    req.body.entry.forEach(entry => {
      if (entry.changes) {
        entry.changes.forEach(change => {
          if (
            change.field === "comments" &&
            change.value &&
            change.value.message
          ) {
            const newComment = {
              from: change.value.from ? change.value.from.name : "Anonymous",
              message: change.value.message,
            };
            comments.push(newComment);
            console.log("New comment added:", newComment);

            // Start broadcasting if it isn’t already running
            if (comments.length === 1) {
              currentIndex = 0;
              broadcastComments();
            }
          }
        });
      }
    });
  }

  res.status(200).send("EVENT_RECEIVED");
});

server.listen(process.env.PORT || 3000, () => {
  console.log("Server is running");
});
