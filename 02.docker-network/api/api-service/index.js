const express = require("express");
const axios = require("axios");
const os = require("os");

const app = express();
const PORT = 3000;

app.use(express.json());
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  next();
});

// Who am I?
app.get("/info", (req, res) => {
  res.json({
    service: "api-service",
    hostname: os.hostname(), // Container ID in Docker
    platform: os.platform(),
    internalIP: getInternalIP(), // Container's IP inside Docker network
    port: PORT,
    message: "Hello from api-service container!",
  });
});

// Talk to ping-service using Docker internal DNS (container name)
app.get("/talk-to-ping", async (req, res) => {
  try {
    // "ping-service" is the container name → Docker resolves it internally
    const response = await axios.get("http://ping-service:4000/pong");
    res.json({
      from: "api-service",
      message: "Successfully talked to ping-service via internal Docker DNS",
      pingServiceSaid: response.data,
      howItWorked:
        "Used hostname 'ping-service' — Docker's internal DNS resolved it to the container IP automatically",
    });
  } catch (err) {
    res.status(500).json({
      error: "Could not reach ping-service",
      reason: err.message,
      tip: "Make sure both containers are on the same Docker network",
    });
  }
});

// Call an external public API (internet access from inside container)
app.get("/external", async (req, res) => {
  try {
    const response = await axios.get(
      "https://jsonplaceholder.typicode.com/todos/1"
    );
    res.json({
      from: "api-service",
      message:
        "Successfully called an EXTERNAL API from inside a Docker container!",
      externalApiResponse: response.data,
      howItWorked:
        "Docker routes outbound traffic through the host machine's network interface",
    });
  } catch (err) {
    res
      .status(500)
      .json({ error: "External call failed", reason: err.message });
  }
});

// Show all network interfaces (to visualize container's network)
app.get("/network", (req, res) => {
  const interfaces = os.networkInterfaces();
  const simplified = {};
  for (const [name, addrs] of Object.entries(interfaces)) {
    simplified[name] = addrs.map((a) => ({
      address: a.address,
      family: a.family,
    }));
  }
  res.json({
    service: "api-service",
    hostname: os.hostname(),
    networkInterfaces: simplified,
    explanation: {
      eth0: "Container's virtual NIC — this is how it talks inside the Docker network",
      lo: "Loopback — localhost inside the container",
    },
  });
});

function getInternalIP() {
  const ifaces = os.networkInterfaces();
  console.log(
    `[api-service] Available network interfaces: ${JSON.stringify(ifaces)}`
  );
  /*
  this is what ifaces looks like:
{
  lo: [
    {
    },
  ],
  eth0: [
    {}
  ]
}
  */
  for (const iface of Object.values(ifaces)) {
    console.log(`[api-service] Checking interface: ${JSON.stringify(iface)}`);
    // for (const iface of Object.values(os.networkInterfaces()))=>means
    // Loop through all network interfaces available on the container
    //here Object.values(os.networkInterfaces()) returns an array of all network interfaces, and we iterate over each one with the outer loop.
    //here Object.values is a method used for retrieving the values of an object's properties as an array. In this case, it is used to get an array of all network interfaces from the object returned by os.networkInterfaces().
    // Each iface is an array of address objects for that interface (e.g., eth0 might have multiple addresses)
    for (const addr of iface) {
      //const addr of iface=>means Loop through each address object associated with the current network interface (iface). Each addr represents a specific IP address configuration for that interface.
      //lets see how looping will be done
      /*
      {
   "lo":[
      {
         "address":"127.0.0.1",
         "netmask":"255.0.0.0",
         "family":"IPv4",
         "mac":"00:00:00:00:00:00",
         "internal":true,
         "cidr":"127.0.0.1/8"
      }
   ],
   "eth0":[
      {
         "address":"172.24.0.3",
         "netmask":"255.255.0.0",
         "family":"IPv4",
         "mac":"02:42:ac:18:00:03",
         "internal":false,
         "cidr":"172.24.0.3/16"
      }
   ]
}

lopping will be done as follows:
- First, the outer loop iterates over each network interface (lo and eth0).
- For the lo interface, the inner loop checks the address object. It sees that the family is "IPv4" but internal is true, so it skips it.
How <of> works? in addr of iface=> means Loop through each element in the array iface, where each element is an address object. The variable addr will represent the current address object being processed in each iteration of the inner loop.
      */
      console.log(
        `[api-service] Checking address: ${addr.address} (${addr.family})`
      );
      if (addr.family === "IPv4" && !addr.internal) return addr.address;
    }
  }
  return "unknown";
}

app.listen(PORT, () => {
  console.log(`[api-service] Running on port ${PORT}`);
  console.log(`[api-service] Container hostname: ${os.hostname()}`);
  console.log(`[api-service] Internal IP: ${getInternalIP()}`);
});
