import express, { Request, Response } from "express";
import * as k8s from "@kubernetes/client-node";
import * as fs from "fs";

// ─────────────────────────────────────────────────────────────────────────────
// Kubernetes client setup using in-cluster service account
//
// When this pod runs inside Kubernetes, these files are auto-mounted:
//   /var/run/secrets/kubernetes.io/serviceaccount/ca.crt    ← TLS cert
//   /var/run/secrets/kubernetes.io/serviceaccount/token     ← Bearer token
//   /var/run/secrets/kubernetes.io/serviceaccount/namespace ← our namespace
//
// loadFromCluster() reads all three and points the client at:
//   https://kubernetes.default.svc  (the API server, reachable from any pod)
//
// No kubectl needed — the SDK speaks the k8s REST API directly over HTTPS.
// ─────────────────────────────────────────────────────────────────────────────

const SA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount";

function buildK8sClient(): k8s.CoreV1Api {
  const kc = new k8s.KubeConfig();

  if (fs.existsSync(`${SA_PATH}/token`)) {
    // Running inside a Kubernetes pod — use the mounted service account
    kc.loadFromCluster();
    console.log("[k8s] loaded in-cluster config from service account");
  } else {
    // Local development fallback — use your ~/.kube/config
    kc.loadFromDefault();
    console.log("[k8s] loaded from default kubeconfig (local dev)");
  }

  return kc.makeApiClient(k8s.CoreV1Api);
}

// Read our own namespace from the service account file (or fall back to env/default)
function getNamespace(): string {
  if (fs.existsSync(`${SA_PATH}/namespace`)) {
    return fs.readFileSync(`${SA_PATH}/namespace`, "utf8").trim();
  }
  return process.env.NAMESPACE ?? "default";
}

const k8sApi = buildK8sClient();
const NAMESPACE = getNamespace();

console.log(`[app] operating in namespace: ${NAMESPACE}`);

// ─────────────────────────────────────────────────────────────────────────────
// Express app
// ─────────────────────────────────────────────────────────────────────────────

const app = express();
app.use(express.json());

// Health check
app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// ─── POST /create ─────────────────────────────────────────────────────────────
// Body: { "name": "my-nginx" }
// Spins up a Pod running nginx:alpine and a NodePort Service to reach it.
// ─────────────────────────────────────────────────────────────────────────────

app.post("/create", async (req: Request, res: Response) => {
  const { name } = req.body as { name?: string };

  if (!name || !/^[a-z0-9-]+$/.test(name)) {
    res.status(400).json({
      error: "name is required and must be lowercase alphanumeric + hyphens",
    });
    return;
  }

  try {
    // 1. Create the Pod
    await k8sApi.createNamespacedPod(NAMESPACE, {
      apiVersion: "v1",
      kind: "Pod",
      metadata: {
        name,
        namespace: NAMESPACE,
        labels: { app: name, "managed-by": "nginx-operator" },
      },
      spec: {
        containers: [
          {
            name: "nginx",
            image: "nginx:alpine",
            ports: [{ containerPort: 80 }],
            resources: {
              requests: { cpu: "50m", memory: "64Mi" },
              limits: { cpu: "100m", memory: "128Mi" },
            },
          },
        ],
      },
    });

    // 2. Create a NodePort Service so you can hit it from outside the cluster
    const svcResult = await k8sApi.createNamespacedService(NAMESPACE, {
      apiVersion: "v1",
      kind: "Service",
      metadata: {
        name,
        namespace: NAMESPACE,
        labels: { "managed-by": "nginx-operator" },
      },
      spec: {
        type: "NodePort",
        selector: { app: name },
        ports: [{ port: 80, targetPort: 80 as unknown as k8s.IntOrString }],
      },
    });

    const nodePort = svcResult.body.spec?.ports?.[0]?.nodePort;

    res.status(201).json({
      message: `nginx pod "${name}" created`,
      pod: name,
      service: name,
      nodePort,
      // For Kind: kubectl get nodes -o wide → grab the node IP, then hit nodePort
      hint: `curl http://<node-ip>:${nodePort}`,
    });
  } catch (err: unknown) {
    const e = err as { body?: { message?: string }; message?: string };
    const msg = e?.body?.message ?? e?.message ?? String(err);

    // 409 = already exists
    if (msg.includes("already exists")) {
      res.status(409).json({ error: `"${name}" already exists` });
      return;
    }

    console.error("[create] error:", msg);
    res.status(500).json({ error: msg });
  }
});

// ─── DELETE /delete ───────────────────────────────────────────────────────────
// Body: { "name": "my-nginx" }
// Deletes the Pod and Service created above.
// ─────────────────────────────────────────────────────────────────────────────

app.delete("/delete", async (req: Request, res: Response) => {
  const { name } = req.body as { name?: string };

  if (!name) {
    res.status(400).json({ error: "name is required" });
    return;
  }

  const results: Record<string, string> = {};

  // Delete Pod — ignore 404 (already gone)
  try {
    await k8sApi.deleteNamespacedPod(name, NAMESPACE);
    results.pod = "deleted";
  } catch (err: unknown) {
    const e = err as { body?: { code?: number } };
    results.pod = e?.body?.code === 404 ? "not found" : `error: ${String(err)}`;
  }

  // Delete Service — ignore 404
  try {
    await k8sApi.deleteNamespacedService(name, NAMESPACE);
    results.service = "deleted";
  } catch (err: unknown) {
    const e = err as { body?: { code?: number } };
    results.service =
      e?.body?.code === 404 ? "not found" : `error: ${String(err)}`;
  }

  res.json({ message: `"${name}" torn down`, results });
});

// ─────────────────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.PORT ?? "3000", 10);
app.listen(PORT, () => console.log(`[app] listening on :${PORT}`));
