// viewer.js -- Interactive bundle viewer
// Copyright 2026 Terrene Foundation (Apache 2.0)
// Renders bundle data into the HTML and triggers verification

class BundleViewer {
  constructor() {
    this.session = null;
    this.chain = null;
    this.deliberation = null;
    this.constraints = null;
    this.metadata = null;
    this.keys = null;
  }

  /**
   * Load all data from the embedded bundle-data.js global.
   * Data is available as window.PRAXIS_BUNDLE (embedded via <script> tag).
   */
  async load() {
    if (typeof window.PRAXIS_BUNDLE === "undefined") {
      this._showError(
        "Bundle data not found. Ensure bundle-data.js is present in the data/ directory.",
      );
      return false;
    }

    const bundle = window.PRAXIS_BUNDLE;
    this.session = bundle.session;
    this.chain = bundle.chain;
    this.deliberation = bundle.deliberation;
    this.constraints = bundle.constraints;
    this.metadata = bundle.metadata;
    this.keys = bundle.keys;
    return true;
  }

  /**
   * Run verification and render all sections.
   */
  async run() {
    const loaded = await this.load();
    if (!loaded) return;

    // Run verification
    const verifier = new ChainVerifier();
    const result = await verifier.verify(this.chain, this.keys);

    // Hide loading
    document.getElementById("loading").classList.add("hidden");

    // Render sections
    this.renderIntegrityResults(result);
    this.renderSessionSummary(this.session, this.metadata);
    this.renderTimeline(this.deliberation);
    this.renderConstraints(this.constraints);
    this.renderChainDetail(this.chain, result);
  }

  /**
   * Render integrity verification results.
   */
  renderIntegrityResults(result) {
    const section = document.getElementById("integrity");
    const container = document.getElementById("integrity-results");
    section.classList.remove("hidden");

    const statusClass = result.valid ? "status-valid" : "status-invalid";
    const statusText = result.valid ? "CHAIN VALID" : "CHAIN BROKEN";
    const statusIcon = result.valid ? "\u2713" : "\u2717";

    let html = '<div class="integrity-status ' + statusClass + '">';
    html += '<span class="status-icon">' + statusIcon + "</span>";
    html += '<span class="status-text">' + statusText + "</span>";
    html += "</div>";

    html += '<div class="integrity-details">';
    html +=
      "<p>Total entries: <strong>" + result.totalEntries + "</strong></p>";
    html += "<p>Verified: <strong>" + result.verifiedEntries + "</strong></p>";

    if (!result.ed25519Supported) {
      html += '<div class="warning-box">';
      html += "<p>Your browser does not support Ed25519 verification. ";
      html +=
        "The chain data is still viewable but cannot be cryptographically verified ";
      html +=
        "in this browser. Try Chrome 113+, Firefox 122+, or Safari 17+.</p>";
      html += "</div>";
    }

    if (result.breaks.length > 0) {
      html += "<h3>Breaks Found</h3>";
      html += '<ul class="breaks-list">';
      for (const brk of result.breaks) {
        html += '<li class="break-item">';
        html += "<strong>Position " + brk.position + ":</strong> ";
        html += '<span class="break-reason">' + brk.reason + "</span> &mdash; ";
        html += escapeHtml(brk.details);
        html += "</li>";
      }
      html += "</ul>";
    }

    html += "</div>";
    container.innerHTML = html;
  }

  /**
   * Render session summary information.
   */
  renderSessionSummary(session, metadata) {
    const section = document.getElementById("summary");
    const container = document.getElementById("session-summary");
    section.classList.remove("hidden");

    const duration = metadata.duration_seconds;
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const durationStr =
      hours > 0 ? hours + "h " + minutes + "m" : minutes + "m";

    let html = '<table class="summary-table">';
    html +=
      '<tr><td>Session ID</td><td class="mono">' +
      escapeHtml(session.session_id) +
      "</td></tr>";
    html +=
      "<tr><td>Domain</td><td>" +
      escapeHtml(session.domain || "unknown") +
      "</td></tr>";
    html +=
      "<tr><td>Workspace</td><td>" +
      escapeHtml(session.workspace_id || metadata.workspace_name || "unknown") +
      "</td></tr>";
    html += "<tr><td>Duration</td><td>" + durationStr + "</td></tr>";
    html +=
      "<tr><td>Trust Chain Entries</td><td>" +
      metadata.total_anchors +
      "</td></tr>";
    html +=
      "<tr><td>Decisions Recorded</td><td>" +
      metadata.total_decisions +
      "</td></tr>";
    html +=
      "<tr><td>Created</td><td>" +
      escapeHtml(session.created_at || "") +
      "</td></tr>";
    if (session.ended_at) {
      html +=
        "<tr><td>Ended</td><td>" + escapeHtml(session.ended_at) + "</td></tr>";
    }
    html += "</table>";

    container.innerHTML = html;
  }

  /**
   * Render the deliberation timeline.
   */
  renderTimeline(deliberation) {
    const section = document.getElementById("timeline");
    const container = document.getElementById("timeline-entries");
    section.classList.remove("hidden");

    if (!deliberation || deliberation.length === 0) {
      container.innerHTML =
        '<p class="empty-message">No deliberation records in this session.</p>';
      return;
    }

    let html = '<div class="timeline">';
    for (const record of deliberation) {
      const typeClass = "timeline-" + (record.record_type || "unknown");
      html += '<div class="timeline-entry ' + typeClass + '">';
      html += '<div class="timeline-header">';
      html +=
        '<span class="timeline-type">' +
        escapeHtml(record.record_type || "unknown") +
        "</span>";
      html +=
        '<span class="timeline-actor">' +
        escapeHtml(record.actor || "") +
        "</span>";
      html +=
        '<span class="timeline-time">' +
        escapeHtml(record.created_at || "") +
        "</span>";
      html += "</div>";

      // Render content based on type
      const content = record.content || {};
      if (record.record_type === "decision") {
        html += '<div class="timeline-content">';
        html +=
          "<p><strong>Decision:</strong> " +
          escapeHtml(content.decision || "") +
          "</p>";
        if (content.alternatives && content.alternatives.length > 0) {
          html +=
            "<p><strong>Alternatives considered:</strong> " +
            content.alternatives.map(escapeHtml).join(", ") +
            "</p>";
        }
        html += "</div>";
      } else if (record.record_type === "observation") {
        html += '<div class="timeline-content">';
        html += "<p>" + escapeHtml(content.observation || "") + "</p>";
        html += "</div>";
      } else if (record.record_type === "escalation") {
        html += '<div class="timeline-content">';
        html +=
          "<p><strong>Issue:</strong> " +
          escapeHtml(content.issue || "") +
          "</p>";
        html +=
          "<p><strong>Context:</strong> " +
          escapeHtml(content.context || "") +
          "</p>";
        html += "</div>";
      }

      // Confidence
      if (record.confidence !== null && record.confidence !== undefined) {
        html += '<div class="timeline-confidence">';
        html += "Confidence: " + (record.confidence * 100).toFixed(0) + "%";
        html += "</div>";
      }

      // Hash
      if (record.reasoning_hash) {
        html += '<div class="timeline-hash mono">';
        html +=
          "Hash: " + escapeHtml(record.reasoning_hash.substring(0, 16)) + "...";
        html += "</div>";
      }

      html += "</div>";
    }
    html += "</div>";
    container.innerHTML = html;
  }

  /**
   * Render constraint compliance summary.
   */
  renderConstraints(constraints) {
    const section = document.getElementById("constraints");
    const container = document.getElementById("constraint-summary");
    section.classList.remove("hidden");

    if (!constraints || constraints.length === 0) {
      container.innerHTML =
        '<p class="empty-message">No constraint evaluations in this session.</p>';
      return;
    }

    // Aggregate by verdict
    const byVerdict = {};
    for (const evt of constraints) {
      const v = evt.verdict || "unknown";
      byVerdict[v] = (byVerdict[v] || 0) + 1;
    }

    let html = '<div class="constraint-overview">';
    html += "<h3>Evaluation Summary</h3>";
    html += '<div class="verdict-grid">';
    for (const [verdict, count] of Object.entries(byVerdict)) {
      const cls = "verdict-" + verdict.replace("_", "-");
      html += '<div class="verdict-card ' + cls + '">';
      html += '<span class="verdict-count">' + count + "</span>";
      html += '<span class="verdict-label">' + escapeHtml(verdict) + "</span>";
      html += "</div>";
    }
    html += "</div>";

    // Individual events
    html += "<h3>Evaluation Log</h3>";
    html += '<table class="constraint-table">';
    html += "<thead><tr>";
    html += "<th>Action</th><th>Resource</th><th>Verdict</th>";
    html += "<th>Dimension</th><th>Utilization</th><th>Time</th>";
    html += "</tr></thead><tbody>";
    for (const evt of constraints) {
      const verdictClass =
        "verdict-" + (evt.verdict || "unknown").replace("_", "-");
      html += "<tr>";
      html += "<td>" + escapeHtml(evt.action || "") + "</td>";
      html += '<td class="mono">' + escapeHtml(evt.resource || "-") + "</td>";
      html +=
        '<td class="' +
        verdictClass +
        '">' +
        escapeHtml(evt.verdict || "") +
        "</td>";
      html += "<td>" + escapeHtml(evt.dimension || "") + "</td>";
      html +=
        "<td>" +
        (evt.utilization !== undefined
          ? (evt.utilization * 100).toFixed(0) + "%"
          : "-") +
        "</td>";
      html += "<td>" + escapeHtml(evt.evaluated_at || "") + "</td>";
      html += "</tr>";
    }
    html += "</tbody></table>";
    html += "</div>";
    container.innerHTML = html;
  }

  /**
   * Render trust chain detail view.
   */
  renderChainDetail(chain, verificationResult) {
    const section = document.getElementById("chain-detail");
    const container = document.getElementById("chain-entries");
    section.classList.remove("hidden");

    if (!chain || chain.length === 0) {
      container.innerHTML = '<p class="empty-message">No chain entries.</p>';
      return;
    }

    const breakPositions = new Set(
      (verificationResult.breaks || []).map((b) => b.position),
    );

    let html = "";
    for (let i = 0; i < chain.length; i++) {
      const entry = chain[i];
      const payload = entry.payload || {};
      const isBreak = breakPositions.has(i);
      const entryClass = isBreak
        ? "chain-entry chain-entry-broken"
        : "chain-entry chain-entry-valid";

      html += '<div class="' + entryClass + '">';
      html += '<div class="chain-entry-header">';
      html += '<span class="chain-position">#' + i + "</span>";
      html +=
        '<span class="chain-type">' +
        escapeHtml(payload.type || "unknown") +
        "</span>";
      if (isBreak) {
        html += '<span class="chain-status-bad">\u2717 BREAK</span>';
      } else {
        html += '<span class="chain-status-good">\u2713 VALID</span>';
      }
      html += "</div>";

      html += '<div class="chain-entry-body">';
      if (payload.action) {
        html +=
          "<p><strong>Action:</strong> " + escapeHtml(payload.action) + "</p>";
      }
      if (payload.actor) {
        html +=
          "<p><strong>Actor:</strong> " + escapeHtml(payload.actor) + "</p>";
      }
      if (payload.result) {
        html +=
          "<p><strong>Result:</strong> " + escapeHtml(payload.result) + "</p>";
      }
      if (payload.resource) {
        html +=
          '<p><strong>Resource:</strong> <span class="mono">' +
          escapeHtml(payload.resource) +
          "</span></p>";
      }
      html +=
        '<p class="mono hash-display"><strong>Hash:</strong> ' +
        escapeHtml(entry.content_hash || "") +
        "</p>";
      if (entry.parent_hash) {
        html +=
          '<p class="mono hash-display"><strong>Parent:</strong> ' +
          escapeHtml(entry.parent_hash) +
          "</p>";
      }
      html += "</div>";
      html += "</div>";
    }
    container.innerHTML = html;
  }

  /**
   * Show an error message in the loading section.
   */
  _showError(message) {
    const loading = document.getElementById("loading");
    loading.innerHTML =
      '<div class="error-box"><p>' + escapeHtml(message) + "</p></div>";
  }
}

/**
 * Escape HTML special characters to prevent XSS.
 */
function escapeHtml(text) {
  if (text === null || text === undefined) return "";
  const str = String(text);
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// Auto-run on page load
document.addEventListener("DOMContentLoaded", function () {
  const viewer = new BundleViewer();
  viewer.run().catch(function (err) {
    console.error("Bundle viewer error:", err);
    const loading = document.getElementById("loading");
    if (loading) {
      loading.innerHTML =
        '<div class="error-box"><p>Verification error: ' +
        escapeHtml(err.message) +
        "</p></div>";
    }
  });
});

// Export for testing
window.BundleViewer = BundleViewer;
