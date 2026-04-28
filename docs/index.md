# Live Debugger File Coverage Dashboard

--8<-- "snippets/bizevent-homepage.js"

## Overview

This lab aims to show you how to answer the question: **which lines of your code in your application are actually being hit in a live environment?**

Using `dtctl` and the Dynatrace Live Debugger, you will instrument a running service, collect execution data as it happens in real traffic, and surface that data as a Dynatrace dashboard — giving you a lightweight, runtime view into code coverage without any test harness or build pipeline changes.

The key insight is that the Live Debugger's `application.snapshots` bucket records `code.filepath`, `code.function`, and `code.line.number` every time a breakpoint is hit. `dtctl` makes it easy to place those breakpoints programmatically and query the results. Together, they turn Dynatrace into a runtime code coverage system you can point at any file you care about.

!!! note "What kind of coverage is this?"
    This is **runtime hit coverage for the lines you instrumented** — not compiler-grade unit test coverage. That distinction is a feature, not a limitation. It tells you what is actually executing under real load, in the environment that matters.

## What You Will Build

By the end of this lab, you will have:

- Live Debugger breakpoints placed across a source file in a running service
- Execution data flowing into `application.snapshots` as real traffic hits those lines
- DQL queries that summarize hits by file, function, and line
- A Dynatrace dashboard showing:
    - What percentage of instrumented lines were hit
    - Which functions were exercised
    - Which lines were hit most often

## Prerequisites

You need:

- A configured Dynatrace environment with Live Debugger enabled
- A Dynatrace Platform Token with Live Debugger scopes
- `dtctl` installed (handled automatically in Codespaces)
- A target workload — this lab uses **EasyTrade**, deployed to a local Kind cluster

The lab uses `OrderController.java` from the EasyTrade `creditcardorderservice` as the instrumentation target.
The same pattern works for any file type that Live Debugger can instrument.

<div class="grid cards" markdown>
- [Get Started :octicons-arrow-right-24:](codespaces.md)
</div>
