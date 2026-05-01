# Codespaces

--8<-- "snippets/bizevent-codespaces.js"

GitHub Codespaces gives you a fully configured cloud development environment — Kind cluster, EasyTrade, and all tooling pre-installed — without any local setup.

---

## 1. Launch Codespace

Click the badge below to open a new Codespace from the `main` branch:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/joshDynatrace/livedebugger-file-coverage-dashboard){target="_blank"}

---

## 2. Codespace Configuration

!!! tip "Machine sizing & secrets"
    **Machine type**

    Select **4-core** for enough resources to run the Kind cluster and all EasyTrade services.

    **Secrets** — enter your credentials in the following Codespace secrets before launching:

    | Secret | Description |
    |--------|-------------|
    | `DT_ENVIRONMENT_ID` | Your Dynatrace environment ID, e.g. `abc12345` from `https://abc12345.live.dynatrace.com` |
    | `DT_ENVIRONMENT_TYPE` | Your environment type: `live`, `sprint`, or `dev`. If unsure, use `live`. |
    | `DT_PLATFORM_TOKEN` | Dynatrace Platform token for `dtctl` — see required scopes below |
    | `DT_API_TOKEN` | Dynatrace API token — requires the `installerDownload` scope for OneAgent installation |
    | `DT_DATA_INGEST_TOKEN` | Dynatrace API token — requires `metrics.ingest`, `logs.ingest`, and `openTelemetryTrace.ingest` scopes |

### DT_PLATFORM_TOKEN Scopes

Your platform token requires at least these scopes:

- `app-engine:apps:run`
- `dev-obs:breakpoints:set`
- `storage:application.snapshots:read`

See the full list at [dtctl token-scope docs](https://dynatrace-oss.github.io/dtctl/docs/token-scopes){target=_blank}.

---

## 3. What Gets Deployed

Once the Codespace finishes initialising, the following is ready:

- A local **Kind** Kubernetes cluster
- **EasyTrade** — deployed to the `easytrade` namespace
- **Dynatrace OneAgent** — deployed via the Dynatrace Operator into the cluster
- `dtctl` — installed via the devcontainer feature

---

## 4. Authenticate dtctl

Configure your token and environment context:

```bash
dtctl config set-credentials my-token \
  --token "$DT_PLATFORM_TOKEN"

dtctl config set-context my-env \
  --environment "https://abc12345.apps.dynatrace.com" \
  --token-ref my-token
```

Then verify the connection:

```bash
dtctl doctor
```

---

## 5. Set Workspace Filters

`dtctl` resolves the Live Debugger workspace from the current working directory.
Before creating breakpoints, tell it which workload to target:

```bash
dtctl update breakpoint --filters k8s.namespace.name:easytrade
```

Replace `easytrade` with your actual namespace if different.
You can also filter by a specific process group instance:

```bash
dtctl update breakpoint --filters k8s.namespace.name:easytrade,dt.entity.process_group_instance:PROCESS_GROUP_INSTANCE-1234567890ABCDEF
```

---

## 6. Troubleshooting

### Cluster health

Confirm the Kind cluster is running:

```bash
kubectl cluster-info
```

### Pod status

Check that all EasyTrade services are up:

```bash
kubectl get pods -n easytrade
```

All pods should show `Running`. If any are in `CrashLoopBackOff` or `Pending`, check the logs:

```bash
kubectl logs -f deployment/<pod-name> -n easytrade
```

<div class="grid cards" markdown>
- [Step 1: Setting up Coverage Data :octicons-arrow-right-24:](setting-up-coverage-data.md)
</div>
