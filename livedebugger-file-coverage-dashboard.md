# Build a file-coverage dashboard with `dtctl` and Dynatrace Live Debugger

This walkthrough shows how to use `dtctl` to do two things end to end:

1. scatter and place Live Debugger breakpoints across a source file
2. turn the resulting snapshot stream in `application.snapshots` into a Dynatrace dashboard that behaves like a lightweight runtime code-coverage view

This is intentionally hands-on.

It is also important to be precise about what kind of “coverage” you are building.
This is **runtime hit coverage for the lines you instrumented with Live Debugger**, not compiler-grade unit test coverage.
In practice, that is often exactly what you want when you are validating a path through a real service in a real environment.

---

## What you will build

By the end, you will have:

- a set of breakpoints scattered across one file
- snapshots landing in the `application.snapshots` bucket
- DQL queries that summarize hits by file, function, and line
- a dashboard that shows:
  - how many instrumented lines were hit
  - which functions were exercised
  - which lines were hit most often

---

## Prerequisites

You need:

- a configured Dynatrace context
- OAuth login for Live Debugger operations
- `dtctl` running from the repository folder that should define the Live Debugger workspace
- a target workload selected through workspace filters

Example:

```bash
dtctl auth login

dtctl update breakpoint --filters k8s.namespace.name:prod,dt.entity.process_group_instance:PROCESS_GROUP_INSTANCE-1234567890ABCDEF
```

`dtctl` resolves the Live Debugger workspace from the current working directory, so running from the repository root is the easiest way to keep breakpoint management tied to the code you are looking at.

---

## Step 1: pick a file and identify candidate lines

For this example, use a Java file called `OrderController.java`.
The same pattern works for any file type that Live Debugger can instrument.

Assume the source file in the repository is:

```text
src/main/java/com/dynatrace/easytrade/creditcardorderservice/OrderController.java
```

Because breakpoint creation uses the source location format `File.java:line`, keep both values around:

```bash
SRC=src/main/java/com/dynatrace/easytrade/creditcardorderservice/OrderController.java
FILE=$(basename "$SRC")
```

Start by listing the file with line numbers:

```bash
nl -ba "$SRC" | sed -n '100,340p'
```

At this point you have two choices:

- **manual placement**: choose exact lines that matter
- **scatter placement**: generate a broader set of candidate lines and instrument them in bulk

For coverage-style analysis, scatter placement is the better fit.

---

## Step 2: scatter breakpoints across executable-looking lines

A simple way to generate candidate lines is to skip blank lines and obvious comment-only lines, then sample the rest.

```bash
SRC=src/main/java/com/dynatrace/easytrade/creditcardorderservice/OrderController.java
FILE=$(basename "$SRC")

awk '
  {
    line = $0
    sub(/^[[:space:]]+/, "", line)
    sub(/[[:space:]]+$/, "", line)
  }
  line == "" { next }
  line ~ /^\/\// { next }
  line ~ /^\/\*/ { next }
  line ~ /^\*/ { next }
  line ~ /^@/ { next }
  line ~ /^(package|import)[[:space:]]/ { next }
  line ~ /^[{}]+$/ { next }
  line ~ /^(public|protected|private|abstract|final|sealed|non-sealed)?[[:space:]]*(class|interface|enum|record)[[:space:]]/ { next }
  line ~ /^(public|protected|private|static|final|abstract|synchronized|native|default|strictfp)[[:space:]]/ && line ~ /\)[[:space:]]*(throws[[:space:]].*)?\{?$/ { next }
  { print NR }
' "$SRC" \
  | shuf \
  | head -n 20 \
  | sort -n \
  > breakpoint-lines.txt

cat breakpoint-lines.txt
```

That gives you a reproducible list of candidate line numbers while skipping obvious non-executable lines such as comments, annotations, imports, braces, class declarations, and likely method signatures.

Create one Live Debugger breakpoint per line:

```bash
while read -r line; do
  echo "Creating breakpoint at ${FILE}:${line}"
  dtctl create breakpoint "${FILE}:${line}"
done < breakpoint-lines.txt
```

If you want to start with a smaller hand-picked set before scattering wider, use a file like this instead:

```bash
cat > breakpoint-lines.txt <<'EOF'
113
115
121
132
157
188
214
241
267
300
306
EOF
```

Then run the same loop.

---

## Step 3: verify the breakpoint set

List the breakpoints in the current workspace:

```bash
dtctl get breakpoints
```

Inspect a specific location:

```bash
dtctl describe breakpoint "OrderController.java:306"
```

If you want a structured inventory of the scatter set:

```bash
dtctl get breakpoints -o json 
```

A practical pattern is to store the total number of instrumented lines as your denominator for the dashboard:

```bash
TARGET_LINES=$(wc -l < breakpoint-lines.txt | tr -d ' ')
echo "$TARGET_LINES"
```

If `TARGET_LINES=11`, your dashboard can compute a percentage from snapshot activity alone.

---

## Step 4: generate traffic through the file

Now hit the application path that exercises the file.
This can be:

- a curl loop against the service endpoint
- an integration test suite
- a replay workload
- a synthetic monitor
- a workflow that calls the service

For example:

```bash
for _ in $(seq 1 50); do
  curl -sS "https://your-service.example/api/orders/latest-status" > /dev/null
done
```

Each time one of your scattered breakpoints is hit, Live Debugger emits a snapshot record into `application.snapshots`.

---

## Step 5: inspect raw coverage data from `application.snapshots`

Before building the dashboard, validate the data path directly with `dtctl query`.

### Most recent snapshots for the file

```bash
dtctl query '
fetch application.snapshots
| filter code.filepath == "OrderController.java"
| sort timestamp desc
| fields timestamp, code.filepath, code.function, code.line.number, snapshot.id, trace.id
| limit 20
'
```

### Distinct hit lines in the file

```bash
dtctl query '
fetch application.snapshots
| filter code.filepath == "OrderController.java"
| summarize covered_lines = countDistinct(code.line.number)
'
```

### Hits by function and line

```bash
dtctl query '
fetch application.snapshots
| filter code.filepath == "OrderController.java"
| fieldsAdd line = toLong(code.line.number)
| summarize hits = count(), by: { code.function, line }
| sort code.function asc, line asc
'
```

### Coverage summary for the scattered set

Replace `11` with the number of breakpoints you actually created.

```bash
dtctl query '
fetch application.snapshots
| filter code.filepath == "OrderController.java"
| summarize total_hits = count(), covered_lines = countDistinct(code.line.number), functions_hit = countDistinct(code.function)
| fieldsAdd target_lines = 11
| fieldsAdd coverage_pct = round(100.0 * covered_lines / target_lines, decimals: 2)
'
```

This is the core trick: the numerator comes from distinct line numbers in `application.snapshots`, and the denominator comes from the set of lines you intentionally instrumented.

---

## Step 6: create the dashboard manifest

Now turn that query logic into a Dynatrace dashboard you can version and re-apply.

Create `dashboard-file-coverage.yaml` in the repository root:

```yaml
type: dashboard
name: Live Debugger File Coverage - OrderController.java
description: Runtime line-hit coverage from application.snapshots for scattered Live Debugger breakpoints
content:
  version: 21
  importedWithCode: true
  settings: {}
  variables: []
  layouts:
    "0":
      x: 0
      y: 0
      w: 6
      h: 4
    "1":
      x: 6
      y: 0
      w: 6
      h: 4
    "2":
      x: 0
      y: 4
      w: 6
      h: 5
    "3":
      x: 6
      y: 4
      w: 6
      h: 5
    "4":
      x: 0
      y: 9
      w: 12
      h: 6
  tiles:
    "0":
      type: markdown
      content: |
        # Live Debugger file coverage

        This dashboard shows runtime hit coverage for the instrumented lines in `OrderController.java`.

        - **Source bucket:** `application.snapshots`
        - **Coverage denominator:** 11 scattered breakpoints
        - **Coverage dimensions:** `code.filepath`, `code.function`, `code.line.number`

        This is runtime execution coverage of the lines you instrumented, not full compiler-grade line coverage.
    "1":
      title: Coverage %
      type: data
      query: |
        fetch application.snapshots
        | filter code.filepath == "OrderController.java"
        | summarize covered_lines = countDistinct(code.line.number)
        | fieldsAdd target_lines = 11
        | fieldsAdd coverage_pct = round(100.0 * covered_lines / target_lines, decimals: 2)
        | fields `Coverage %` = concat(toString(coverage_pct), "%")
      visualization: singleValue
      visualizationSettings:
        singleValue:
          labelMode: none
          recordField: Coverage %
          isIconVisible: false
          alignment: start
          trend:
            isVisible: false
            isRelative: false
        autoSelectVisualization: false
      querySettings:
        maxResultRecords: 1000
        defaultScanLimitGbytes: 500
        maxResultMegaBytes: 1
        defaultSamplingRatio: 10
        enableSampling: false
      davis:
        enabled: false
        davisVisualization:
          isAvailable: true
    "2":
      title: Covered lines by function
      type: data
      query: |
        fetch application.snapshots
        | filter code.filepath == "OrderController.java"
        | summarize covered_lines = countDistinct(code.line.number), total_hits = count(), by: { code.function }
        | sort covered_lines desc, total_hits desc
        | fields `Function` = code.function, `Covered lines` = covered_lines, `Hits` = total_hits
      visualization: table
      visualizationSettings:
        table:
          hideColumnsForLargeResults: false
        autoSelectVisualization: false
      querySettings:
        maxResultRecords: 1000
        defaultScanLimitGbytes: 500
        maxResultMegaBytes: 100
        defaultSamplingRatio: 10
        enableSampling: false
      davis:
        enabled: false
        davisVisualization:
          isAvailable: true
    "3":
      title: Line hit map
      type: data
      query: |
        fetch application.snapshots
        | filter code.filepath == "OrderController.java"
        | fieldsAdd line = toLong(code.line.number)
        | summarize hits = count(), by: { code.function, line }
        | sort code.function asc, line asc
        | fields `Function` = code.function, `Line` = line, `Hits` = hits
      visualization: table
      visualizationSettings:
        table:
          hideColumnsForLargeResults: false
        autoSelectVisualization: false
      querySettings:
        maxResultRecords: 1000
        defaultScanLimitGbytes: 500
        maxResultMegaBytes: 100
        defaultSamplingRatio: 10
        enableSampling: false
      davis:
        enabled: false
        davisVisualization:
          isAvailable: true
    "4":
      title: Hot lines
      type: data
      query: |
        fetch application.snapshots
        | filter code.filepath == "OrderController.java"
        | fieldsAdd line = toLong(code.line.number)
        | summarize hits = count(), traces = countDistinct(trace.id), by: { line, code.function }
        | sort hits desc
        | limit 50
        | fields `Line` = line, `Function` = code.function, `Hits` = hits, `Traces` = traces
      visualization: table
      visualizationSettings:
        table:
          hideColumnsForLargeResults: false
        autoSelectVisualization: false
      querySettings:
        maxResultRecords: 1000
        defaultScanLimitGbytes: 500
        maxResultMegaBytes: 100
        defaultSamplingRatio: 10
        enableSampling: false
      davis:
        enabled: false
        davisVisualization:
          isAvailable: true
```

A few practical notes:

- Current dashboards use the newer schema with `type: markdown` and `type: data`, plus a separate `content.layouts` section for placement.
- The markdown tile is useful for documenting the denominator directly in the dashboard.
- The most important tile is the summary query with `coverage_pct`.
- If you change the scatter set later, update the hard-coded denominator in both the markdown note and the summary query.

---

## Step 7: apply the dashboard with `dtctl`

Preview first if you want:

```bash
dtctl apply -f dashboard-file-coverage.yaml --dry-run
```

Then create or update the dashboard:

```bash
dtctl apply -f dashboard-file-coverage.yaml
```

`dtctl` will print the resulting dashboard URL after a successful apply.

If you already created an earlier invalid draft of the dashboard, delete that one first so you do not end up with two dashboards of the same name:

```bash
dtctl delete dashboard "Live Debugger File Coverage - OrderController.java" -y
dtctl create dashboard -f dashboard-file-coverage.yaml
```

If you prefer a create-only flow:

```bash
dtctl create dashboard -f dashboard-file-coverage.yaml
```

---

## Step 8: tighten the dashboard to one source file

The examples above filter on:

- `code.filepath`
- `code.function`
- `code.line.number`

That is enough to create a clean file-level coverage board.

If you want to narrow further, add filters such as:

- `dt.entity.process_group_instance`
- `k8s.namespace.name`
- `dt.entity.service`
- `trace.id`
- timeframe restrictions

Example:

```dql
fetch application.snapshots
| filter code.filepath == "OrderController.java"
| filter k8s.namespace.name == "prod"
| filter timestamp > now() - 2h
| summarize hits = count(), by: { code.function, code.line.number }
```

That turns the dashboard from “all observed runtime hits” into “hits for this file in this workload and this time window”.

---

## Step 9: treat the scatter set as declarative instrumentation

Once this pattern works, stop thinking of breakpoints as one-off interactive debugging actions.
Think of them as a declarative instrumentation set.

A simple workflow looks like this:

1. generate `breakpoint-lines.txt`
2. apply the scatter set with a loop
3. drive traffic through the service
4. read coverage from `application.snapshots`
5. publish a dashboard with a known denominator
6. refine the scatter set and re-run

That makes Live Debugger useful not only for root-cause inspection, but also for runtime verification.

---

## Cleanup

Remove the breakpoint scatter set when you are done:

```bash
dtctl delete breakpoint --all -y
```

If you want to remove only specific lines:

```bash
while read -r line; do
  dtctl delete breakpoint "${FILE}:${line}" -y
done < breakpoint-lines.txt
```

You can also delete the dashboard later:

```bash
dtctl delete dashboard "Live Debugger File Coverage - OrderController.java" -y
```

---

## Where to take this next

Once you have the basic file-coverage dashboard working, the natural extensions are:

- generate one dashboard per critical file
- track coverage before and after a deployment
- compare coverage across namespaces or process groups
- use decoded snapshots to link hit lines back to live values and branches
- embed the scatter/apply/query flow into a workflow or CI gate

The key idea is simple: if `dtctl` can place breakpoints reproducibly and `application.snapshots` records `code.filepath`, `code.function`, and `code.line.number`, then Live Debugger becomes a practical runtime coverage system for the exact file paths you care about.
