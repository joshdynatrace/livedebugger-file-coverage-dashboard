# Live Debugger File Coverage Dashboard

A GitHub Codespaces environment for building a runtime file-coverage dashboard using Dynatrace Live Debugger and `dtctl`.

The walkthrough shows how to scatter Live Debugger breakpoints across a source file, collect snapshots from `application.snapshots`, and turn them into a Dynatrace dashboard that behaves like a lightweight runtime code-coverage view.

## Prerequisites

- A Dynatrace environment
- The following Codespaces secrets configured:

| Secret | Description |
|--------|-------------|
| `DT_ENVIRONMENT_ID` | Your environment ID, e.g. `abc12345` from `https://abc12345.live.dynatrace.com` |
| `DT_ENVIRONMENT_TYPE` | `live`, `sprint`, or `dev`. If unsure, use `live`. |
| `DT_PLATFORM_TOKEN` | Dynatrace Platform token for use with the `dtctl` command line tool |

## Getting started

Open this repository in GitHub Codespaces. The environment will automatically:

1. Install the RunMe CLI
2. Create a local Kind Kubernetes cluster
3. Deploy the [EasyTrade](https://github.com/Dynatrace/easytrade) demo application via Helm

## Accessing EasyTrade

Once the Codespace is ready, expose the EasyTrade frontend with:

```bash
kubectl port-forward -n easytrade svc/easytrade-frontendreverseproxy 8080:8080
```

Then open port `8080` in the Codespaces port forwarding panel.

Default credentials: `demouser` / `demopass`
