// import express, { Request, Response } from "express";
// import * as k8s from "@kubernetes/client-node";
// import * as fs from "fs";

// // ─────────────────────────────────────────────────────────────────────────────
// // Kubernetes client setup using in-cluster service account
// //
// // When this pod runs inside Kubernetes, these files are auto-mounted:
// //   /var/run/secrets/kubernetes.io/serviceaccount/ca.crt    ← TLS cert
// //   /var/run/secrets/kubernetes.io/serviceaccount/token     ← Bearer token
// //   /var/run/secrets/kubernetes.io/serviceaccount/namespace ← our namespace
// //
// // loadFromCluster() reads all three and points the client at:
// //   https://kubernetes.default.svc  (the API server, reachable from any pod)
// //
// // No kubectl needed — the SDK speaks the k8s REST API directly over HTTPS.
// // ─────────────────────────────────────────────────────────────────────────────

// const SA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount";

// function buildK8sClient(): k8s.CoreV1Api {
//   const kc = new k8s.KubeConfig();

//   if (fs.existsSync(`${SA_PATH}/token`)) {
//     // Running inside a Kubernetes pod — use the mounted service account
//     kc.loadFromCluster();
//     console.log("[k8s] loaded in-cluster config from service account");
//   } else {
//     // Local development fallback — use your ~/.kube/config
//     kc.loadFromDefault();
//     console.log("[k8s] loaded from default kubeconfig (local dev)");
//   }

//   return kc.makeApiClient(k8s.CoreV1Api);
// }

// // Read our own namespace from the service account file (or fall back to env/default)
// function getNamespace(): string {
//   if (fs.existsSync(`${SA_PATH}/namespace`)) {
//     return fs.readFileSync(`${SA_PATH}/namespace`, "utf8").trim();
//   }
//   return process.env.NAMESPACE ?? "default";
// }

// const k8sApi = buildK8sClient();
// const NAMESPACE = getNamespace();

// console.log(`[app] operating in namespace: ${NAMESPACE}`);

// // ─────────────────────────────────────────────────────────────────────────────
// // Express app
// // ─────────────────────────────────────────────────────────────────────────────

// const app = express();
// app.use(express.json());

// // Health check
// app.get("/health", (_req, res) => {
//   res.json({ status: "ok" });
// });

// // ─── POST /create ─────────────────────────────────────────────────────────────
// // Body: { "name": "my-nginx" }
// // Spins up a Pod running nginx:alpine and a NodePort Service to reach it.
// // ─────────────────────────────────────────────────────────────────────────────

// app.post("/create", async (req: Request, res: Response) => {
//   const { name } = req.body as { name?: string };

//   if (!name || !/^[a-z0-9-]+$/.test(name)) {
//     res.status(400).json({
//       error: "name is required and must be lowercase alphanumeric + hyphens",
//     });
//     return;
//   }

//   try {
//     // 1. Create the Pod
//     await k8sApi.createNamespacedPod(NAMESPACE, {
//       apiVersion: "v1",
//       kind: "Pod",
//       metadata: {
//         name,
//         namespace: NAMESPACE,
//         labels: { app: name, "managed-by": "nginx-operator" },
//       },
//       spec: {
//         containers: [
//           {
//             name: "nginx",
//             image: "nginx:alpine",
//             ports: [{ containerPort: 80 }],
//             resources: {
//               requests: { cpu: "50m", memory: "64Mi" },
//               limits: { cpu: "100m", memory: "128Mi" },
//             },
//           },
//         ],
//       },
//     });

//     // 2. Create a NodePort Service so you can hit it from outside the cluster
//     const svcResult = await k8sApi.createNamespacedService(NAMESPACE, {
//       apiVersion: "v1",
//       kind: "Service",
//       metadata: {
//         name,
//         namespace: NAMESPACE,
//         labels: { "managed-by": "nginx-operator" },
//       },
//       spec: {
//         type: "NodePort",
//         selector: { app: name },
//         ports: [{ port: 80, targetPort: 80 as unknown as k8s.IntOrString }],
//       },
//     });

//     const nodePort = svcResult.body.spec?.ports?.[0]?.nodePort;

//     res.status(201).json({
//       message: `nginx pod "${name}" created`,
//       pod: name,
//       service: name,
//       nodePort,
//       // For Kind: kubectl get nodes -o wide → grab the node IP, then hit nodePort
//       hint: `curl http://<node-ip>:${nodePort}`,
//     });
//   } catch (err: unknown) {
//     const e = err as { body?: { message?: string }; message?: string };
//     const msg = e?.body?.message ?? e?.message ?? String(err);

//     // 409 = already exists
//     if (msg.includes("already exists")) {
//       res.status(409).json({ error: `"${name}" already exists` });
//       return;
//     }

//     console.error("[create] error:", msg);
//     res.status(500).json({ error: msg });
//   }
// });

// // ─── DELETE /delete ───────────────────────────────────────────────────────────
// // Body: { "name": "my-nginx" }
// // Deletes the Pod and Service created above.
// // ─────────────────────────────────────────────────────────────────────────────

// app.delete("/delete", async (req: Request, res: Response) => {
//   const { name } = req.body as { name?: string };

//   if (!name) {
//     res.status(400).json({ error: "name is required" });
//     return;
//   }

//   const results: Record<string, string> = {};

//   // Delete Pod — ignore 404 (already gone)
//   try {
//     await k8sApi.deleteNamespacedPod(name, NAMESPACE);
//     results.pod = "deleted";
//   } catch (err: unknown) {
//     const e = err as { body?: { code?: number } };
//     results.pod = e?.body?.code === 404 ? "not found" : `error: ${String(err)}`;
//   }

//   // Delete Service — ignore 404
//   try {
//     await k8sApi.deleteNamespacedService(name, NAMESPACE);
//     results.service = "deleted";
//   } catch (err: unknown) {
//     const e = err as { body?: { code?: number } };
//     results.service =
//       e?.body?.code === 404 ? "not found" : `error: ${String(err)}`;
//   }

//   res.json({ message: `"${name}" torn down`, results });
// });

// // ─────────────────────────────────────────────────────────────────────────────

// const PORT = parseInt(process.env.PORT ?? "3000", 10);
// app.listen(PORT, () => console.log(`[app] listening on :${PORT}`));

import express, { Request, Response } from "express";
import * as k8s from "@kubernetes/client-node";
import * as fs from "fs";

// ─────────────────────────────────────────────────────────────────────────────
// K8s client — same in-cluster pattern as before
// ─────────────────────────────────────────────────────────────────────────────

const SA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount";

function buildK8sClient(): k8s.CoreV1Api {
  const kc = new k8s.KubeConfig();
  if (fs.existsSync(`${SA_PATH}/token`)) {
    kc.loadFromCluster();
    console.log("[k8s] in-cluster config loaded");
  } else {
    kc.loadFromDefault();
    console.log("[k8s] local kubeconfig loaded");
  }
  return kc.makeApiClient(k8s.CoreV1Api);
}

function getNamespace(): string {
  if (fs.existsSync(`${SA_PATH}/namespace`)) {
    return fs.readFileSync(`${SA_PATH}/namespace`, "utf8").trim();
  }
  return process.env.NAMESPACE ?? "default";
}

const k8sApi = buildK8sClient();
const NAMESPACE = getNamespace();

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

// Wait for a pod to reach a terminal phase (Succeeded / Failed)
// Polls every 2s, times out after 60s
async function waitForPodCompletion(podName: string): Promise<string> {
  const MAX_WAIT_MS = 60_000;
  const POLL_INTERVAL_MS = 2_000;
  const deadline = Date.now() + MAX_WAIT_MS;

  while (Date.now() < deadline) {
    const res = await k8sApi.readNamespacedPod(podName, NAMESPACE);
    const phase = res.body.status?.phase ?? "Unknown";

    if (phase === "Succeeded" || phase === "Failed") {
      return phase;
    }

    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }

  return "Timeout";
}

// Fetch pod logs as a plain string
async function fetchPodLogs(podName: string): Promise<string> {
  const res = await k8sApi.readNamespacedPodLog(
    podName,
    NAMESPACE,
    "runner" // container name
  );
  return typeof res.body === "string" ? res.body : JSON.stringify(res.body);
}

// Delete a pod — silently ignore 404
async function deletePod(podName: string): Promise<void> {
  try {
    await k8sApi.deleteNamespacedPod(podName, NAMESPACE);
  } catch (err: unknown) {
    const e = err as { body?: { code?: number } };
    if (e?.body?.code !== 404) {
      console.error(`[delete] failed to delete ${podName}:`, err);
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Express app
// ─────────────────────────────────────────────────────────────────────────────

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => res.json({ status: "ok" }));

// ─── POST /run ────────────────────────────────────────────────────────────────
// Body: { "code": "console.log('hello world')" }
//
// Flow:
//  1. Write code to /tmp/<id>.js on THIS pod (in-memory, tmpfs)
//  2. Spin up a runner pod — pass the code as an env var
//  3. Runner does: node -e "$CODE"
//  4. Poll until the pod finishes (Succeeded or Failed)
//  5. Fetch and return the logs
//  6. Delete the runner pod
// ─────────────────────────────────────────────────────────────────────────────

app.post("/run", async (req: Request, res: Response) => {
  const { code } = req.body as { code?: string };

  if (!code || typeof code !== "string") {
    res.status(400).json({ error: "code (string) is required" });
    return;
  }

  // Unique ID for this run — used as pod name and tmp file name
  const runId = `runner-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 7)}`;

  // ── Step 1: Write to /tmp on this pod ──────────────────────────────────────
  // /tmp on a pod is an in-memory tmpfs — nothing hits disk
  const tmpFile = `/tmp/${runId}.js`;
  fs.writeFileSync(tmpFile, code, "utf8");
  console.log(`[run] wrote code to ${tmpFile}`);

  // ── Step 2: Spin up a runner pod ───────────────────────────────────────────
  // The code travels into the pod as the CODE env variable.
  // The pod runs: node -e "$CODE" then exits (restartPolicy: Never).
  try {
    await k8sApi.createNamespacedPod(NAMESPACE, {
      apiVersion: "v1",
      kind: "Pod",
      metadata: {
        name: runId,
        namespace: NAMESPACE,
        labels: { "managed-by": "code-runner" },
      },
      spec: {
        restartPolicy: "Never", // run once and exit — critical
        containers: [
          {
            name: "runner",
            image: "node:20-alpine",
            command: ["/bin/sh", "-c"],
            args: ['node -e "$CODE"'],
            env: [
              {
                name: "CODE",
                value: code, // code passed as env var
              },
            ],
            resources: {
              requests: { cpu: "50m", memory: "64Mi" },
              limits: { cpu: "200m", memory: "128Mi" },
            },
          },
        ],
      },
    });

    console.log(`[run] pod ${runId} created`);

    // ── Step 3: Poll until pod finishes ────────────────────────────────────────
    const phase = await waitForPodCompletion(runId);
    console.log(`[run] pod ${runId} finished with phase: ${phase}`);

    // ── Step 4: Fetch logs ─────────────────────────────────────────────────────
    const logs = await fetchPodLogs(runId);

    // ── Step 5: Clean up the tmp file on this pod ──────────────────────────────
    fs.unlinkSync(tmpFile);

    // ── Step 6: Delete the runner pod ─────────────────────────────────────────
    await deletePod(runId);
    console.log(`[run] pod ${runId} deleted`);

    res.json({
      runId,
      phase, // Succeeded | Failed | Timeout
      logs,
    });
  } catch (err: unknown) {
    const e = err as { body?: { message?: string }; message?: string };
    const msg = e?.body?.message ?? e?.message ?? String(err);
    console.error(`[run] error:`, msg);

    // Best-effort cleanup
    fs.existsSync(tmpFile) && fs.unlinkSync(tmpFile);
    await deletePod(runId);

    res.status(500).json({ error: msg });
  }
});

// ─── DELETE /delete ───────────────────────────────────────────────────────────
// Body: { "runId": "runner-1234567890-abc12" }
// Manual cleanup in case /run crashed before auto-deleting the pod.
// ─────────────────────────────────────────────────────────────────────────────

app.delete("/delete", async (req: Request, res: Response) => {
  const { runId } = req.body as { runId?: string };

  if (!runId) {
    res.status(400).json({ error: "runId is required" });
    return;
  }

  await deletePod(runId);

  // Also clean up tmp file if it somehow survived
  const tmpFile = `/tmp/${runId}.js`;
  if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);

  res.json({ message: `${runId} deleted` });
});

// ─────────────────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.PORT ?? "3000", 10);
app.listen(PORT, () =>
  console.log(`[app] listening on :${PORT} | namespace: ${NAMESPACE}`)
);
