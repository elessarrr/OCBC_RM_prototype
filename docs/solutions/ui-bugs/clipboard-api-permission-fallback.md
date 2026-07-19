---
title: "Clipboard API permission denial needs a synchronous copy fallback"
date: 2026-07-19
category: ui-bugs
module: templates-ui
problem_type: ui_bug
component: templates_ui
symptoms:
  - "Copy brief and Copy email buttons show Copy failed in restricted browser contexts"
  - "navigator.clipboard.writeText rejects even on a localhost page"
root_cause: missing_permission
resolution_type: code_fix
severity: medium
tags: [clipboard, browser-permissions, javascript, copy-button, graceful-degradation, ui]
---

# Clipboard API permission denial needs a synchronous copy fallback

## Problem

The brief and client-email copy buttons relied only on `navigator.clipboard.writeText()`. Headless Chromium and some embedded or policy-restricted browser contexts expose the API but deny clipboard permission, so both controls displayed `Copy failed`.

## Root Cause

The asynchronous Clipboard API is permission-gated. Attempting a legacy fallback only after awaiting a rejected Clipboard API call also loses the transient user activation associated with the click, causing `document.execCommand("copy")` to fail too.

## Solution

Create a temporary, invisible textarea and call `document.execCommand("copy")` synchronously at the start of the click handler. If that is unavailable, fall back to `navigator.clipboard.writeText()` for modern browsers.

The shared `writeClipboard()` helper in `wealth-brief/static/app.js` now serves both the brief and email buttons. Browser QA verified both controls transition to `Copied` with no console errors.

## Prevention

- Test clipboard controls in a permission-restricted or headless browser, not only a normal local tab.
- Keep the legacy copy attempt synchronous so it retains the click's user activation.
- Route all copy controls through one helper to avoid divergent fallback behavior.
