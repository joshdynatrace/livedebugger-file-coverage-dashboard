--8<-- "snippets/bizevent-whats-next.js"

# What's Next?

You've built a runtime file-coverage dashboard backed by Live Debugger snapshots. Here are some ideas for taking the pattern further.

## Expand Coverage

**Instrument more files**

Generate one dashboard per critical file and track which paths are exercised across a full service.

**Track coverage across deployments**

Compare the scatter set and hit counts before and after a deployment to verify that expected code paths are still being reached.

**Compare across environments**

Run the same scatter set against different namespaces or process groups — for example, `staging` vs `prod` — and compare the resulting dashboards.

## Deepen the Analysis

**Link hit lines back to live values**

Snapshots capture variable values at the breakpoint location.
Use decoded snapshots to understand not just *which* lines were hit, but *what data* was present when they were.

**Add branch coverage signals**

Instrument both branches of a conditional by placing breakpoints on each branch's first executable line.
The hit ratio between the two breakpoints shows branch coverage directly in the dashboard.

## Automate the Workflow

**Embed in CI**

Wrap the scatter/apply/query flow in a CI job that runs after deployment.
Fail the job if coverage drops below a threshold or if a critical function shows zero hits.

**Dynatrace Workflow integration**

Use a Dynatrace Workflow to trigger the scatter set, wait for traffic, query snapshots, and publish coverage results as a custom event — all without manual steps.

**Refine the scatter set over time**

Start broad and narrow: after a few runs, remove breakpoints that are never hit (dead code candidates) and add breakpoints around lines that surface interesting data.

## More Dynatrace Resources

- [Dynatrace Live Debugger docs](https://docs.dynatrace.com/docs/observe/application-observability/live-debugger){target=_blank}
- [dtctl documentation](https://dynatrace-oss.github.io/dtctl/){target=_blank}
- [Dynatrace Community](https://community.dynatrace.com/){target=_blank}
- [Dynatrace University](https://university.dynatrace.com/){target=_blank}
