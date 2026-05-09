# Node.js `os` Module — Complete Reference

> Used in `api-service/index.js` to inspect the container's identity and network at runtime.

---

## What is the `os` Module?

The `os` module is a **built-in Node.js module** — no install needed. It provides utility functions to interact with the **operating system** the Node process is running on.

```js
const os = require("os");   // CommonJS
import os from "os";        // ESM
```

Inside a Docker container, `os` methods report the **container's OS info**, not the host machine's — making it perfect for debugging and introspection.

---

## Functions Used in This Project

### `os.hostname()`

Returns the hostname of the current machine (or container).

```js
os.hostname();
// Outside Docker → "MacBook-Pro.local"
// Inside Docker  → "3f1b65d8c9e6"  ← short container ID
```

**Why it matters in Docker:**
Docker sets the container's hostname to its short container ID by default.
This is how you can confirm your code is actually running inside a container.

---

### `os.platform()`

Returns the operating system platform as a string.

```js
os.platform();
// "linux"   ← inside a Docker container (always Linux)
// "darwin"  ← macOS
// "win32"   ← Windows
```

**Why it matters in Docker:**
Even if you develop on macOS/Windows, Docker containers always run on Linux.
`os.platform()` confirms this at runtime.

| Return Value | OS |
|---|---|
| `linux` | Linux / Docker containers |
| `darwin` | macOS |
| `win32` | Windows (even 64-bit) |
| `freebsd` | FreeBSD |

---

### `os.networkInterfaces()`

Returns an object describing all **network interfaces** on the machine — their IP addresses, MAC addresses, and families.

```js
os.networkInterfaces();
```

**Example output inside a Docker container:**

```json
{
  "lo": [
    { "address": "127.0.0.1", "family": "IPv4", "internal": true },
    { "address": "::1",       "family": "IPv6", "internal": true }
  ],
  "eth0": [
    { "address": "172.18.0.3", "family": "IPv4", "internal": false },
    { "address": "fe80::...",  "family": "IPv6", "internal": false }
  ]
}
```

**Key fields:**

| Field | Type | Description |
|---|---|---|
| `address` | string | The IP address |
| `family` | `"IPv4"` \| `"IPv6"` | IP version |
| `internal` | boolean | `true` = loopback (localhost), `false` = real NIC |
| `mac` | string | MAC address of the interface |
| `netmask` | string | Subnet mask |

**What each interface means inside Docker:**

| Interface | Address | Meaning |
|---|---|---|
| `lo` | `127.0.0.1` | Loopback — localhost inside the container |
| `eth0` | `172.18.x.x` | Docker's virtual NIC — container's IP on the bridge network |

> ⚠️ Your host machine's IP (e.g. `192.168.1.x`) is **NOT visible** inside the container.
> The container only sees its own virtual network interface.

---

### `os.cpus()`

Returns an array of objects describing each logical CPU core.

```js
os.cpus();
// [
//   { model: "Intel(R) Core(TM) i7", speed: 2800, times: { user, nice, sys, idle, irq } },
//   ...
// ]

os.cpus().length; // → number of CPU cores available to the container
```

**Useful for:** Deciding how many worker threads to spawn, load balancing.

---

### `os.totalmem()`

Returns total system memory in **bytes**.

```js
os.totalmem();               // → 8589934592  (bytes)
os.totalmem() / 1024 ** 3;  // → 8  (GB)
```

> Inside Docker: returns the memory available **to the container** (limited by `--memory` flag or compose config).

---

### `os.freemem()`

Returns currently free (unused) memory in **bytes**.

```js
os.freemem();               // → 2147483648  (bytes)
os.freemem() / 1024 ** 2;  // → 2048  (MB)
```

---

### `os.uptime()`

Returns system uptime in **seconds**.

```js
os.uptime();       // → 3600  (1 hour)
```

> Inside Docker: returns how long the **container** has been running, not the host.

---

### `os.arch()`

Returns the CPU architecture the Node.js binary was compiled for.

```js
os.arch();
// "x64"   ← 64-bit Intel/AMD
// "arm64" ← Apple Silicon / ARM servers
// "arm"   ← Raspberry Pi, etc.
```

**Important for Docker:** If you build an image on Apple Silicon (`arm64`) and deploy to an `x64` server, you'll get an architecture mismatch error. Always specify platform in your Dockerfile:

```dockerfile
FROM --platform=linux/amd64 node:18-alpine
```

---

### `os.tmpdir()`

Returns the OS's default temp directory path.

```js
os.tmpdir();
// Linux/Docker → "/tmp"
// macOS       → "/var/folders/..."
// Windows     → "C:\\Users\\User\\AppData\\Local\\Temp"
```

---

### `os.EOL`

The End-Of-Line string for the current OS. A constant, not a function.

```js
os.EOL;
// "\n"    on Linux/macOS
// "\r\n"  on Windows
```

**Use it when writing files** to avoid line-ending bugs across platforms:

```js
const lines = ["line1", "line2", "line3"];
fs.writeFileSync("out.txt", lines.join(os.EOL));
```

---

## The `getInternalIP()` Helper — Explained

This custom function from `api-service/index.js` uses `os.networkInterfaces()` to find the container's internal Docker IP:

```js
function getInternalIP() {
  const ifaces = os.networkInterfaces();         // Get all network interfaces

  for (const iface of Object.values(ifaces)) {  // Loop through each interface
    for (const addr of iface) {                  // Loop through each address on the interface
      if (addr.family === "IPv4" && !addr.internal) {
        return addr.address;                     // Return first non-loopback IPv4
      }
    }
  }
  return "unknown";
}
```

**Step-by-step:**

| Step | What happens |
|---|---|
| `os.networkInterfaces()` | Returns object: `{ lo: [...], eth0: [...] }` |
| `Object.values(ifaces)` | Gets arrays of addresses: `[ [lo addrs], [eth0 addrs] ]` |
| `addr.family === "IPv4"` | Skip IPv6 addresses |
| `!addr.internal` | Skip loopback (`127.0.0.1`) |
| `return addr.address` | Returns `172.18.0.3` — the container's Docker network IP |

---

## Quick Reference Table

| Method | Returns | Docker Context |
|---|---|---|
| `os.hostname()` | Container ID (hash) | Unique ID of the container |
| `os.platform()` | `"linux"` | Always Linux inside Docker |
| `os.arch()` | `"x64"` or `"arm64"` | CPU architecture of the image |
| `os.networkInterfaces()` | Object of NICs | Shows eth0 (Docker IP) and lo |
| `os.cpus()` | Array of CPU cores | Cores available to container |
| `os.totalmem()` | Bytes | Memory limit of the container |
| `os.freemem()` | Bytes | Free memory right now |
| `os.uptime()` | Seconds | How long the container has been up |
| `os.tmpdir()` | String path | `/tmp` on Linux/Docker |
| `os.EOL` | `"\n"` | Line ending on Linux/Docker |

---

## Full Usage Example

```js
const os = require("os");

console.log("=== Container / OS Info ===");
console.log("Hostname   :", os.hostname());
console.log("Platform   :", os.platform());
console.log("Arch       :", os.arch());
console.log("CPUs       :", os.cpus().length, "cores");
console.log("Total RAM  :", (os.totalmem() / 1024 ** 3).toFixed(2), "GB");
console.log("Free RAM   :", (os.freemem() / 1024 ** 2).toFixed(0), "MB");
console.log("Uptime     :", Math.floor(os.uptime() / 60), "minutes");
console.log("Temp Dir   :", os.tmpdir());

const ifaces = os.networkInterfaces();
console.log("\n=== Network Interfaces ===");
for (const [name, addrs] of Object.entries(ifaces)) {
  for (const addr of addrs) {
    if (addr.family === "IPv4") {
      console.log(`${name}: ${addr.address} (internal: ${addr.internal})`);
    }
  }
}
```

**Output inside Docker container:**

```
=== Container / OS Info ===
Hostname   : 3f1b65d8c9e6
Platform   : linux
Arch       : x64
CPUs       : 4 cores
Total RAM  : 8.00 GB
Free RAM   : 3200 MB
Uptime     : 12 minutes
Temp Dir   : /tmp

=== Network Interfaces ===
lo:   127.0.0.1  (internal: true)
eth0: 172.18.0.3 (internal: false)  ← Docker bridge network IP
```
