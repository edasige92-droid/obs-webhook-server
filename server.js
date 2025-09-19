const express = require("express");
const bodyParser = require("body-parser");

const app = express();
const PORT = process.env.PORT || 10000;

// Use your verify token
const VERIFY_TOKEN = process.env.VERIFY_TOKEN || "Personal92!";

app.use(bodyParser.json());

// Webhook verification
app.get("/facebook-webhook", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode === "subscribe" && token === VERIFY_TOKEN) {
    console.log("Webhook verified!");
    res.status(200).send(challenge);
  } else {
    console.log("Verification failed.");
    res.sendStatus(403);
  }
});

// Webhook event receiver
app.post("/facebook-webhook", (req, res) => {
  console.log("Incoming webhook:", JSON.stringify(req.body, null, 2));
  res.sendStatus(200);
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
