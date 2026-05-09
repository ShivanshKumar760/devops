const express = require("express");
const os = require("os");

const app = express();
const PORT = 4000;

app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  next();
});

// Responds when api-service calls it internally
app.get("/pong", (req, res) => {
  res.json({
    service: "ping-service",
    hostname: os.hostname(),
    internalIP: getInternalIP(),
    message: "PONG! I am ping-service. You reached me via Docker internal DNS!",
    receivedAt: new Date().toISOString()
  });
});

// Info about this container
app.get("/info", (req, res) => {
  res.json({
    service: "ping-service",
    hostname: os.hostname(),
    internalIP: getInternalIP(),
    port: PORT,
    message: "I am ping-service — living inside the Docker network"
  });
});

function getInternalIP() {
  const ifaces = os.networkInterfaces();
  for (const iface of Object.values(ifaces)) {
    for (const addr of iface) {
      if (addr.family === "IPv4" && !addr.internal) return addr.address;
    }
  }
  return "unknown";
}

app.listen(PORT, () => {
  console.log(`[ping-service] Running on port ${PORT}`);
  console.log(`[ping-service] Container hostname: ${os.hostname()}`);
  console.log(`[ping-service] Internal IP: ${getInternalIP()}`);
});