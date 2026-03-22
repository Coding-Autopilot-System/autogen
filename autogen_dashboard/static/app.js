(() => {
  const API_BASE = "/api";
  const STORAGE_KEY = "autogen-dashboard:selected-session";
  const MODEL_CACHE_KEY = "autogen-dashboard:session-models";
  const REPO_STORAGE_KEY = "autogen-dashboard:selected-repo-root";
  const SESSION_MODE_KEY = "autogen-dashboard:session-modes";
  const DISABLED_PROVIDER_IDS = new Set(["openai"]);
  const PROVIDER_SORT_ORDER = [
    "gemini",
    "gemini-cli",
    "claude-cli",
    "codex-cli",
    "anthropic",
    "azure-openai",
    "ollama",
    "openai",
  ];
  const GEMINI_MODEL_PRESETS = [
    { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro (Stable)" },
    { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash (Stable)" },
    { value: "gemini-2.5-flash-lite", label: "Gemini 2.5 Flash-Lite (Stable)" },
    { value: "gemini-3-flash-preview", label: "Gemini 3 Flash (Preview)" },
    { value: "gemini-3.1-flash-lite-preview", label: "Gemini 3.1 Flash-Lite (Preview)" },
    { value: "gemini-3.1-pro-preview", label: "Gemini 3.1 Pro (Preview, Paid)" },
  ];
  const SESSION_MODES = [
    {
      id: "review",
      label: "Review",
      hint: "Focus on bugs, regressions, risk, and missing tests before changing anything.",
      placeholder: "Review this carefully and call out bugs, regressions, and missing tests.",
    },
    {
      id: "plan",
      label: "Plan",
      hint: "Break the task into concrete steps, tradeoffs, and the safest next move.",
      placeholder: "Plan the next steps for this task and explain the tradeoffs.",
    },
    {
      id: "implement",
      label: "Implement",
      hint: "Drive toward a concrete change, patch, or next implementation step.",
      placeholder: "Implement the next change and explain what will happen.",
    },
    {
      id: "general",
      label: "General",
      hint: "Use the note box for approval context or a follow-up instruction.",
      placeholder: "Add a note, correction, approval comment, or follow-up instruction.",
    },
  ];
  const OPERATOR_TABS = ["overview", "timeline", "agents", "routing", "artifacts"];
  const SPECIALIST_SOURCES = new Set([
    "assistant",
    "planner",
    "researcher",
    "implementer",
    "reviewer",
    "specialist",
  ]);

  const state = {
    providers: [],
    repos: [],
    sessions: [],
    sessionModels: loadSessionModelCache(),
    sessionModes: loadSessionModeCache(),
    selectedSessionId: localStorage.getItem(STORAGE_KEY) || null,
    selectedRepoRoot: localStorage.getItem(REPO_STORAGE_KEY) || "",
    selectedSession: null,
    stream: null,
    streamStatus: "Disconnected",
    activeProvider: null,
    createModelAutoValue: "",
    filter: "all",
    loading: {
      providers: false,
      sessions: false,
      detail: false,
      action: false,
      create: false,
    },
    selectedOperatorTab: "overview",
    noticeTimer: null,
  };

  const els = {
    activeProvider: document.getElementById("active-provider"),
    providerDetail: document.getElementById("provider-detail"),
    selectedSessionName: document.getElementById("selected-session-name"),
    selectedSessionStatus: document.getElementById("selected-session-status"),
    streamStatus: document.getElementById("stream-status"),
    syncStatus: document.getElementById("sync-status"),
    providerSummary: document.getElementById("provider-summary"),
    providerList: document.getElementById("provider-list"),
    sessionList: document.getElementById("session-list"),
    sessionFilter: document.getElementById("session-filter"),
    detailTitle: document.getElementById("detail-title"),
    detailBadges: document.getElementById("detail-badges"),
    activeRunFocus: document.getElementById("active-run-focus"),
    activeRouteStrip: document.getElementById("active-route-strip"),
    activeStageStrip: document.getElementById("active-stage-strip"),
    pauseBanner: document.getElementById("pause-banner"),
    orchestrationPanel: document.getElementById("orchestration-panel"),
    operatorTabContent: document.getElementById("operator-tab-content"),
    workspaceWarning: document.getElementById("workspace-warning"),
    detailDisclosure: document.getElementById("detail-disclosure"),
    detailMeta: document.getElementById("detail-meta"),
    detailEmpty: document.getElementById("detail-empty"),
    repoContextBanner: document.getElementById("repo-context-banner"),
    sessionModeCopy: document.getElementById("session-mode-copy"),
    approvalQueueCount: document.getElementById("approval-queue-count"),
    approvalQueue: document.getElementById("approval-queue"),
    transcript: document.getElementById("transcript"),
    messageCount: document.getElementById("message-count"),
    lastUpdated: document.getElementById("last-updated"),
    controlPending: document.getElementById("control-pending"),
    runStatusStrip: document.getElementById("run-status-strip"),
    controlGuide: document.getElementById("control-guide"),
    humanMessage: document.getElementById("human-message"),
    createForm: document.getElementById("create-session-form"),
    createProvider: document.getElementById("create-provider"),
    createRouteLane: document.getElementById("create-route-lane"),
    createRepoRoot: document.getElementById("create-repo-root"),
    createManualRepoRoot: document.getElementById("create-manual-repo-root"),
    createWorkspaceSummary: document.getElementById("create-workspace-summary"),
    createModel: document.getElementById("create-model"),
    modelHelp: document.getElementById("model-help"),
    modelPresets: document.getElementById("model-presets"),
    createTitle: document.getElementById("create-title"),
    createTask: document.getElementById("create-task"),
    createSystemMessage: document.getElementById("create-system-message"),
    seedSmokeTest: document.getElementById("seed-smoke-test"),
    seedExample: document.getElementById("seed-example"),
    refreshProviders: document.getElementById("refresh-providers"),
    refreshSessions: document.getElementById("refresh-sessions"),
    sendMessage: document.getElementById("send-message"),
    approveSession: document.getElementById("approve-session"),
    approveRunSession: document.getElementById("approve-run-session"),
    rejectSession: document.getElementById("reject-session"),
    rejectRunSession: document.getElementById("reject-run-session"),
    runSession: document.getElementById("run-session"),
    retrySession: document.getElementById("retry-session"),
    cancelSession: document.getElementById("cancel-session"),
    stopSession: document.getElementById("stop-session"),
    refreshQueue: document.getElementById("refresh-queue"),
    notice: document.getElementById("notice"),
  };

  const exampleSession = {
    title: "Meeting follow-up triage",
    task:
      "Review the latest notes, identify action items, and draft a short follow-up message for the team.",
    systemMessage:
      "You are a concise operations assistant. Prefer short, actionable updates. Pause when human approval is needed.",
  };

  const smokeTestSession = {
    title: "Gemini smoke test",
    task: "Reply with exactly READY",
    systemMessage: "You are a strict smoke test assistant. Reply with exactly READY.",
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function toText(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    if (Array.isArray(value)) {
      return value
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object") {
            return item.text || item.content || item.message || JSON.stringify(item);
          }
          return String(item);
        })
        .join("\n");
    }
    if (typeof value === "object") {
      return value.text || value.content || value.message || JSON.stringify(value, null, 2);
    }
    return String(value);
  }

  function normalizeArray(payload, keys = []) {
    if (Array.isArray(payload)) return payload;
    if (!payload || typeof payload !== "object") return [];
    for (const key of keys) {
      if (Array.isArray(payload[key])) return payload[key];
    }
    return [];
  }

  function pick(payload, keys, fallback = null) {
    if (!payload || typeof payload !== "object") return fallback;
    for (const key of keys) {
      const value = payload[key];
      if (value !== undefined && value !== null && value !== "") return value;
    }
    return fallback;
  }

  function normalizeProvider(item) {
    if (typeof item === "string") {
      return {
        id: item,
        name: item,
        ready: true,
        detail: "",
        active: false,
      };
    }
    return {
      id: pick(item, ["id", "name", "provider", "key"], "unknown"),
      name: pick(item, ["name", "id", "provider"], "unknown"),
      ready: Boolean(pick(item, ["ready", "available", "enabled"], false)),
      detail: pick(item, ["detail", "description", "note", "status"], ""),
      active: Boolean(pick(item, ["active", "selected", "current"], false)),
    };
  }

  function normalizeRepo(item) {
    if (typeof item === "string") {
      return {
        name: item,
        root: item,
        kind: "repo",
        branch: "",
        dirty: false,
        detail: "",
        changedFiles: [],
        recentCommits: [],
        stackHints: [],
        scannedAt: "",
        signature: "",
      };
    }
    return {
      name: pick(item, ["name", "repo_name", "repository", "label"], ""),
      root: pick(item, ["root", "repo_root", "path"], ""),
      kind: pick(item, ["kind", "workspace_kind", "workspaceKind"], "repo"),
      branch: pick(item, ["branch", "current_branch"], ""),
      dirty: Boolean(pick(item, ["dirty", "is_dirty"], false)),
      detail: pick(item, ["detail", "description", "note", "status"], ""),
      changedFiles: normalizeTextList(pick(item, ["changed_files", "changedFiles"], [])),
      recentCommits: normalizeTextList(pick(item, ["recent_commits", "recentCommits"], [])),
      stackHints: normalizeTextList(pick(item, ["stack_hints", "stackHints"], [])),
      scannedAt: pick(item, ["scanned_at", "scannedAt"], ""),
      signature: pick(item, ["signature"], ""),
    };
  }

  function normalizeRepoContext(item, fallbackRoot = "") {
    const source = item && typeof item === "object" ? item : {};
    return {
      name: pick(source, ["name", "repo_name", "repository", "label"], ""),
      kind: pick(source, ["kind", "workspace_kind", "workspaceKind"], "repo"),
      root: pick(source, ["root", "repo_root", "path"], fallbackRoot || ""),
      branch: pick(source, ["branch", "current_branch"], ""),
      dirty: Boolean(pick(source, ["dirty", "is_dirty"], false)),
      changedFiles: normalizeTextList(pick(source, ["changed_files", "changedFiles"], [])),
      recentCommits: normalizeTextList(pick(source, ["recent_commits", "recentCommits"], [])),
      stackHints: normalizeTextList(pick(source, ["stack_hints", "stackHints"], [])),
      scannedAt: pick(source, ["scanned_at", "scannedAt"], ""),
      signature: pick(source, ["signature"], ""),
      error: pick(source, ["error", "last_error", "lastError"], ""),
    };
  }

  function normalizePathKey(value) {
    return String(value || "")
      .trim()
      .replace(/[\\/]+$/, "")
      .replaceAll("/", "\\")
      .toLowerCase();
  }

  function effectiveCreateRepoRoot() {
    const manual = String(els.createManualRepoRoot?.value || "").trim();
    if (manual) return manual;
    return String(els.createRepoRoot?.value || "").trim();
  }

  function findRepoByRoot(root) {
    const key = normalizePathKey(root);
    if (!key) return null;
    return state.repos.find((repo) => normalizePathKey(repo.root) === key) || null;
  }

  function normalizeTextList(value) {
    if (value == null) return [];
    const items = Array.isArray(value) ? value : [value];
    return items
      .map((item) => {
        if (typeof item === "string") return item.trim();
        if (!item || typeof item !== "object") return String(item).trim();
        return (
          item.text ||
          item.content ||
          item.message ||
          item.name ||
          item.path ||
          item.title ||
          item.summary ||
          JSON.stringify(item)
        ).trim();
      })
      .filter(Boolean);
  }

  function normalizeStageTimeline(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        stage: pick(item, ["stage", "name", "id"], ""),
        status: pick(item, ["status", "state"], "pending"),
        pauseKind: pick(item, ["pause_kind", "pauseKind"], ""),
        startedAt: pick(item, ["started_at", "startedAt"], ""),
        completedAt: pick(item, ["completed_at", "completedAt"], ""),
        updatedAt: pick(item, ["updated_at", "updatedAt"], ""),
        attemptCount: Number(pick(item, ["attempt_count", "attemptCount"], 0)) || 0,
        error: pick(item, ["error", "last_error", "lastError"], ""),
        blockedQuestions: normalizeTextList(pick(item, ["blocked_questions", "blockedQuestions"], [])),
        autoAnswerCount: Number(pick(item, ["auto_answer_count", "autoAnswerCount"], 0)) || 0,
      }));
  }

  function normalizeApprovalScope(value) {
    if (!value || typeof value !== "object") return null;
    const scope = {
      actionKind: pick(value, ["action_kind", "actionKind"], ""),
      riskLevel: pick(value, ["risk_level", "riskLevel"], ""),
      reason: pick(value, ["reason"], ""),
      affectedPaths: normalizeTextList(pick(value, ["affected_paths", "affectedPaths"], [])),
      commands: normalizeTextList(pick(value, ["commands"], [])),
      externalTargets: normalizeTextList(pick(value, ["external_targets", "externalTargets"], [])),
    };
    if (
      !scope.actionKind &&
      !scope.riskLevel &&
      !scope.reason &&
      !scope.affectedPaths.length &&
      !scope.commands.length &&
      !scope.externalTargets.length
    ) {
      return null;
    }
    return scope;
  }

  function normalizeStageOutputs(value) {
    if (!value || typeof value !== "object") return {};
    const entries = {};
    Object.entries(value).forEach(([stageKey, payload]) => {
      if (!payload || typeof payload !== "object") return;
      const stage = pick(payload, ["stage", "name"], stageKey);
      entries[stage] = {
        stage,
        summary: pick(payload, ["summary", "text", "content"], ""),
        artifacts: normalizeTextList(pick(payload, ["artifacts"], [])),
        nextAction: pick(payload, ["next_action", "nextAction"], ""),
        needsApproval: Boolean(pick(payload, ["needs_approval", "needsApproval"], false)),
        needsInput: Boolean(pick(payload, ["needs_input", "needsInput"], false)),
        blockedQuestions: normalizeTextList(pick(payload, ["blocked_questions", "blockedQuestions"], [])),
        routeMetadata: pick(payload, ["route_metadata", "routeMetadata"], {}) || {},
        changedFiles: normalizeTextList(pick(payload, ["changed_files", "changedFiles"], [])),
        writeOperations: normalizeArray(payload, ["write_operations", "writeOperations"]).filter(Boolean),
        proposedWriteOperations: normalizeArray(payload, ["proposed_write_operations", "proposedWriteOperations"]).filter(Boolean),
        diffArtifacts: normalizeTextList(pick(payload, ["diff_artifacts", "diffArtifacts"], [])),
        validationCommands: normalizeArray(payload, ["validation_commands", "validationCommands"]).filter(Boolean),
        validationResults: normalizeArray(payload, ["validation_results", "validationResults"]).filter(Boolean),
        pendingApproval: normalizeApprovalScope(pick(payload, ["pending_approval", "pendingApproval"], null)),
      };
    });
    return entries;
  }

  function normalizeRoutePlan(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item, index) => ({
        order: Number(pick(item, ["order"], index)) || index,
        provider: pick(item, ["provider"], ""),
        model: pick(item, ["model"], ""),
        label: pick(item, ["label"], ""),
        executionMode: pick(item, ["execution_mode", "executionMode"], ""),
        toolsAvailable: Boolean(pick(item, ["tools_available", "toolsAvailable"], false)),
      }));
  }

  function normalizeRouteAttempts(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        provider: pick(item, ["provider"], ""),
        model: pick(item, ["model"], ""),
        status: pick(item, ["status"], "planned"),
        toolsAvailable: Boolean(pick(item, ["tools_available", "toolsAvailable"], false)),
        fallbackIndex: Number(pick(item, ["fallback_index", "fallbackIndex"], 0)) || 0,
        error: pick(item, ["error"], ""),
        startedAt: pick(item, ["started_at", "startedAt"], ""),
        completedAt: pick(item, ["completed_at", "completedAt"], ""),
      }));
  }

  function normalizeCapabilityChanges(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        name: pick(item, ["name", "kind"], ""),
        before: pick(item, ["before"], ""),
        after: pick(item, ["after"], ""),
        reason: pick(item, ["reason", "detail"], ""),
      }));
  }

  function normalizeSpecialistStates(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        role: pick(item, ["role"], ""),
        stage: pick(item, ["stage"], ""),
        status: pick(item, ["status"], "not_started"),
        currentTask: pick(item, ["current_task", "currentTask"], ""),
        latestOutputSummary: pick(
          item,
          ["latest_output_summary", "latestOutputSummary"],
          ""
        ),
        lastHandoffTarget: pick(item, ["last_handoff_target", "lastHandoffTarget"], ""),
        lastHandoffReason: pick(item, ["last_handoff_reason", "lastHandoffReason"], ""),
        startedAt: pick(item, ["started_at", "startedAt"], ""),
        updatedAt: pick(item, ["updated_at", "updatedAt"], ""),
        completedAt: pick(item, ["completed_at", "completedAt"], ""),
      }));
  }

  function normalizeSpecialistHandoffs(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item) => ({
        fromRole: pick(item, ["from_role", "fromRole"], ""),
        toRole: pick(item, ["to_role", "toRole"], ""),
        reason: pick(item, ["reason"], ""),
        requestedBy: pick(item, ["requested_by", "requestedBy"], ""),
        status: pick(item, ["status"], "requested"),
        createdAt: pick(item, ["created_at", "createdAt"], ""),
        updatedAt: pick(item, ["updated_at", "updatedAt"], ""),
        completedAt: pick(item, ["completed_at", "completedAt"], ""),
      }));
  }

  function normalizeSessionEvents(value) {
    const items = Array.isArray(value) ? value : [];
    return items
      .filter((item) => item && typeof item === "object")
      .map((item, index) => ({
        seq: Number(pick(item, ["seq"], index + 1)) || index + 1,
        type: pick(item, ["type", "event", "kind"], "event"),
        createdAt: pick(item, ["created_at", "createdAt", "timestamp", "time"], ""),
        payload: normalizeMetadataObject(pick(item, ["payload", "data", "metadata"], {})),
      }));
  }

  function basenameFromPath(value) {
    const normalized = String(value || "").replace(/[\\/]+$/, "");
    if (!normalized) return "";
    const parts = normalized.split(/[\\/]/).filter(Boolean);
    return parts.length ? parts[parts.length - 1] : normalized;
  }

  function repoSummary(session) {
    const repoContext = session?.repoContext;
    const root = session?.repoRoot || repoContext?.root || "";
    const name = repoContext?.name || basenameFromPath(root);
    const branch = repoContext?.branch || "";
    const dirty = repoContext && typeof repoContext.dirty === "boolean" ? repoContext.dirty : null;
    const parts = [name || root];
    if (branch) parts.push(branch);
    if (dirty === true) parts.push("dirty");
    if (dirty === false) parts.push("clean");
    return parts.filter(Boolean).join(" | ");
  }

  function repoDirtyLabel(dirty) {
    if (dirty === true) return "Dirty";
    if (dirty === false) return "Clean";
    return "Unknown";
  }

  function buildRoutingSummary(session) {
    const route = normalizeMetadataObject(session?.routeMetadata);
    const planned = Array.isArray(session?.routePlan) ? session.routePlan : [];
    const attempts = Array.isArray(session?.routeAttempts) ? session.routeAttempts : [];
    const requestedProvider = session?.requestedProvider || session?.provider || "";
    const requestedModel = session?.requestedModel || session?.model || "";
    const plannedProvider = pick(route, ["primary_provider"], "") || planned[0]?.provider || requestedProvider;
    const plannedModel = pick(route, ["primary_model"], "") || planned[0]?.model || requestedModel;
    const actualProvider = pick(route, ["active_provider"], "") || session?.lastProviderUsed || attempts.at(-1)?.provider || "";
    const actualModel = pick(route, ["active_model"], "") || session?.lastModelUsed || attempts.at(-1)?.model || "";
    const fallbackCount =
      Number(pick(route, ["fallback_count"], session?.lastFallbackCount ?? Math.max(0, attempts.length - 1))) ||
      0;
    return {
      requestedProvider,
      requestedModel,
      plannedProvider,
      plannedModel,
      actualProvider,
      actualModel,
      lane: session?.routeLane || pick(route, ["route_lane", "active_lane"], "") || "auto",
      tier: pick(route, ["route_tier"], "") || "",
      reason: pick(route, ["route_reason"], "") || "",
      fallbackCount,
      capabilityDrift: Array.isArray(session?.capabilityChanges) ? session.capabilityChanges.length : 0,
    };
  }

  function buildStageSummary(session) {
    const currentStage = session?.currentStage || "";
    const lastCompletedStage = session?.lastCompletedStage || "";
    const stageOutput = currentStage ? session?.stageOutputs?.[currentStage] : null;
    const stageRecord =
      Array.isArray(session?.stageTimeline) && currentStage
        ? session.stageTimeline.find((entry) => entry.stage === currentStage)
        : null;
    return {
      currentStage: currentStage || "Not started",
      currentStatus: stageRecord?.status || session?.status || "idle",
      pauseKind: session?.pauseKind || session?.pauseReason || "",
      lastCompletedStage: lastCompletedStage || "None",
      summary:
        stageOutput?.summary ||
        session?.pauseDetail ||
        session?.assistantMessage ||
        "The manager has not produced a stage summary yet.",
      blockedCount: Array.isArray(session?.blockedQuestions) ? session.blockedQuestions.length : 0,
    };
  }

  function renderActiveRunFocus(session) {
    if (!els.activeRunFocus || !els.activeRouteStrip || !els.activeStageStrip) return;
    if (!session) {
      els.activeRunFocus.hidden = true;
      els.activeRouteStrip.innerHTML = "";
      els.activeStageStrip.innerHTML = "";
      return;
    }
    const routing = buildRoutingSummary(session);
    const stage = buildStageSummary(session);
    const routeLead =
      [routing.actualProvider || routing.plannedProvider, routing.actualModel || routing.plannedModel]
        .filter(Boolean)
        .join(" / ") || "Route pending";
    els.activeRunFocus.hidden = false;
    els.activeRouteStrip.innerHTML = `
      <span class="active-strip-label">Route</span>
      <div class="active-strip-head">${escapeHtml(routeLead)}</div>
      <div class="active-strip-copy">${escapeHtml(
        routing.reason || "Model routing, lane selection, and fallback state for the active run."
      )}</div>
      <div class="active-strip-chips">
        <span class="tiny-chip">${escapeHtml(routing.lane)} lane</span>
        ${routing.tier ? `<span class="tiny-chip">${escapeHtml(routing.tier)}</span>` : ""}
        ${routing.requestedProvider ? `<span class="tiny-chip">requested ${escapeHtml(routing.requestedProvider)}</span>` : ""}
        ${routing.fallbackCount ? `<span class="tiny-chip">${escapeHtml(String(routing.fallbackCount))} fallbacks</span>` : ""}
      </div>
    `;
    els.activeStageStrip.innerHTML = `
      <span class="active-strip-label">Stage</span>
      <div class="active-strip-head">${escapeHtml(titleCaseWords(stage.currentStage))}</div>
      <div class="active-strip-copy">${escapeHtml(stage.summary)}</div>
      <div class="active-strip-chips">
        <span class="tiny-chip ${escapeHtml(statusKind(stage.currentStatus))}">${escapeHtml(stage.currentStatus)}</span>
        ${stage.pauseKind ? `<span class="tiny-chip">${escapeHtml(titleCaseWords(stage.pauseKind))}</span>` : ""}
        <span class="tiny-chip">last completed ${escapeHtml(titleCaseWords(stage.lastCompletedStage))}</span>
        ${stage.blockedCount ? `<span class="tiny-chip">${escapeHtml(String(stage.blockedCount))} blocked questions</span>` : ""}
      </div>
    `;
  }

  function renderTextList(items, emptyLabel) {
    const values = normalizeTextList(items);
    if (!values.length) {
      return `<div class="detail-list empty">${escapeHtml(emptyLabel)}</div>`;
    }
    return `<ul class="detail-list">${values
      .map((value) => `<li>${escapeHtml(value)}</li>`)
      .join("")}</ul>`;
  }

  function normalizeMetadataObject(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    return value;
  }

  function titleCaseWords(value) {
    return String(value || "")
      .split(/[\s_-]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }

  function messageRoleLabel(message, family) {
    if (family === "human") return message.source === "user" ? "Task" : "Human";
    if (family === "approval") {
      const decision =
        message.metadata?.decision || (message.source === "rejection" ? "reject" : "approve");
      return decision === "reject" ? "Reject" : "Approval";
    }
    if (family === "manager") return "Manager";
    if (family === "event") return "Event";
    if (family === "system") return "System";
    if (message.source && message.source !== "assistant") {
      return titleCaseWords(message.source);
    }
    return family === "specialist" ? "Specialist" : titleCaseWords(message.role || "message");
  }

  function routeMetadataFromMessage(message) {
    const metadata = normalizeMetadataObject(message?.metadata);
    const routeMetadata = normalizeMetadataObject(
      pick(metadata, ["route_metadata", "routeMetadata"], {})
    );
    const provider =
      pick(metadata, ["provider", "active_provider", "activeProvider"], "") ||
      pick(routeMetadata, ["active_provider", "provider"], "");
    const model =
      pick(metadata, ["model", "active_model", "activeModel"], "") ||
      pick(routeMetadata, ["active_model", "model"], "");
    const tier =
      pick(metadata, ["route_tier", "routeTier"], "") ||
      pick(routeMetadata, ["route_tier"], "");
    const lane =
      pick(metadata, ["route_lane", "routeLane"], "") ||
      pick(routeMetadata, ["route_lane", "active_lane"], "");
    return {
      provider,
      model,
      tier,
      lane,
      fallbackCount:
        Number(
          pick(metadata, ["fallback_count", "fallbackCount"], pick(routeMetadata, ["fallback_count"], 0))
        ) || 0,
    };
  }

  function messageFamilyForRole(message) {
    const role = String(message?.role || "").toLowerCase();
    const source = String(message?.source || "").toLowerCase();
    const metadata = normalizeMetadataObject(message?.metadata);
    if (source === "user" || source === "human" || role === "user") return "human";
    if (source === "approval" || source === "rejection" || metadata.decision) return "approval";
    if (source === "manager" || metadata.manager_update || metadata.current_stage) return "manager";
    if (role === "event" || source === "event") return "event";
    if (role === "system" || source === "system") return "system";
    if (SPECIALIST_SOURCES.has(source) || metadata.specialist_role || metadata.role === "specialist") {
      return "specialist";
    }
    if (role === "assistant") return "specialist";
    return role || "event";
  }

  function renderMessageMetaStrip(message, family) {
    const metadata = normalizeMetadataObject(message?.metadata);
    const route = routeMetadataFromMessage(message);
    const stage =
      message?.stage ||
      pick(metadata, ["stage", "current_stage", "currentStage"], "") ||
      "";
    const pauseKind = pick(metadata, ["pause_kind", "pauseKind"], "") || "";
    const chips = [];
    if (family === "approval" && metadata.decision) {
      chips.push(`<span class="message-meta-chip accent">${escapeHtml(metadata.decision)}</span>`);
    }
    if (stage) {
      chips.push(`<span class="message-meta-chip">${escapeHtml(titleCaseWords(stage))}</span>`);
    }
    if (pauseKind) {
      chips.push(`<span class="message-meta-chip">${escapeHtml(titleCaseWords(pauseKind))}</span>`);
    }
    if (route.provider) {
      chips.push(`<span class="message-meta-chip route">${escapeHtml(route.provider)}</span>`);
    }
    if (route.model) {
      chips.push(`<span class="message-meta-chip route">${escapeHtml(route.model)}</span>`);
    }
    if (route.tier) {
      chips.push(`<span class="message-meta-chip">${escapeHtml(route.tier)}</span>`);
    }
    if (route.lane && route.lane !== route.tier) {
      chips.push(`<span class="message-meta-chip">${escapeHtml(route.lane)} lane</span>`);
    }
    if (route.fallbackCount) {
      chips.push(
        `<span class="message-meta-chip warning">${escapeHtml(String(route.fallbackCount))} fallbacks</span>`
      );
    }
    if (!chips.length) return "";
    return `<div class="message-meta-strip">${chips.join("")}</div>`;
  }

  function renderMessageCard(message, index) {
    const family = messageFamilyForRole(message);
    const delay = Math.min(index * 30, 240);
    const metaStrip = renderMessageMetaStrip(message, family);
    return `
      <article class="message-card ${escapeHtml(family)}" style="animation-delay:${delay}ms">
        ${metaStrip}
        <div class="message-top">
          <div class="message-role">${escapeHtml(messageRoleLabel(message, family))}</div>
          <div class="message-meta">${escapeHtml(formatTimestamp(message.timestamp) || "")}</div>
        </div>
        <div class="message-content">${escapeHtml(message.content || "(empty)")}</div>
      </article>
    `;
  }

  function nextPromptSummary(session) {
    const queuedPrompt = String(session?.queuedPrompt || "").trim();
    if (queuedPrompt) {
      return {
        label: "Queued for next run",
        text: queuedPrompt,
      };
    }

    const lastPrompt = String(session?.lastPrompt || "").trim();
    if (lastPrompt) {
      return {
        label: "Latest prompt",
        text: lastPrompt,
      };
    }

    return {
      label: "No prompt queued",
      text: "Type a note and use Send message or Run next step.",
    };
  }

  function renderControlPending(session) {
    if (!els.controlPending) return;
    if (!session) {
      els.controlPending.innerHTML = "Select a session to see the next queued prompt.";
      return;
    }

    const summary = nextPromptSummary(session);
    els.controlPending.innerHTML = `
      <span class="pending-label">${escapeHtml(summary.label)}</span>
      <div class="pending-copy">${escapeHtml(summary.text)}</div>
    `;
  }

  function sessionRuntimeLabel(session) {
    if (!session) return "No session selected";
    if (session.statusKind === "running") {
      return `Running ${formatRelative(session.updatedAt)}`;
    }
    if (session.waitingForHuman) {
      return `Paused ${formatRelative(session.updatedAt)}`;
    }
    if (session.statusKind === "completed") {
      return `Completed ${formatRelative(session.updatedAt)}`;
    }
    if (session.statusKind === "error") {
      return `Failed ${formatRelative(session.updatedAt)}`;
    }
    if (session.statusKind === "stopped") {
      return `Stopped ${formatRelative(session.updatedAt)}`;
    }
    return `Updated ${formatRelative(session.updatedAt)}`;
  }

  function renderRunStatus(session) {
    if (!els.runStatusStrip) return;
    if (!session) {
      els.runStatusStrip.className = "run-status-strip";
      els.runStatusStrip.innerHTML =
        '<span class="run-status-label">Ready</span><div class="run-status-copy">Select a session to see the current run state and the next safe action.</div>';
      return;
    }

    const chips = [
      `<span class="tiny-chip">${escapeHtml(session.status)}</span>`,
      session.provider ? `<span class="tiny-chip">${escapeHtml(session.provider)}</span>` : "",
      session.model ? `<span class="tiny-chip">${escapeHtml(session.model)}</span>` : "",
      session.latestAttemptId ? `<span class="tiny-chip">${escapeHtml(session.latestAttemptId)}</span>` : "",
      session.workspaceStale
        ? '<span class="status-pill waiting">workspace stale</span>'
        : '<span class="status-pill completed">workspace fresh</span>',
      `<span class="tiny-chip">${escapeHtml(sessionRuntimeLabel(session))}</span>`,
    ]
      .filter(Boolean)
      .join("");

    let label = "Next move";
    let headline = "Ready for input";
    let copy = "Type in the note box, then queue it or run it.";

    if (session.statusKind === "running") {
      label = "Run active";
      headline = "The agent is working now";
      copy = "Wait for the transcript to update. While a run is active, the note box is for drafting only. Use Cancel if the run stalls.";
    } else if (session.waitingForHuman) {
      label = "Paused for you";
      headline = session.pauseTitle || "Review, then choose the next step";
      copy =
        "Read the transcript, type your note or approval text, then use Approve only, Approve + Run, Reject only, Reject + Run, or Run now.";
    } else if (session.statusKind === "completed") {
      label = "Completed";
      headline = "The session finished";
      copy = "If you want another step, type a follow-up in the note box and click Run now.";
    } else if (session.statusKind === "error") {
      label = "Attention";
      headline = "The last run failed";
      copy = session.error || session.pauseDetail || "Check the transcript, adjust the note, then retry or run again.";
    } else if (session.statusKind === "stopped") {
      label = "Stopped";
      headline = "This session is stopped";
      copy = "Stopped sessions are read-only. Create a new session if you want to continue the work.";
    } else if (session.queuedPrompt) {
      label = "Queued prompt";
      headline = "A prompt is already ready";
      copy = "Run now will execute the queued prompt shown above. Queue note only will replace it with what you type next.";
    }

    els.runStatusStrip.className = `run-status-strip state-${String(session.statusKind || "idle")}`;
    els.runStatusStrip.innerHTML = `
      <span class="run-status-label">${escapeHtml(label)}</span>
      <div class="run-status-head">${escapeHtml(headline)}</div>
      <div class="run-status-copy">${escapeHtml(copy)}</div>
      <div class="run-status-chips">${chips}</div>
    `;
  }

  function renderControlGuide(session) {
    if (!els.controlGuide) return;
    if (!session) {
      els.controlGuide.innerHTML = `
        <div class="guide-step">
          <span class="guide-label">1. Create a session</span>
          Pick <strong>gemini</strong>, click <strong>Use smoke test</strong>, then create the session.
        </div>
        <div class="guide-step">
          <span class="guide-label">2. Run it</span>
          Click <strong>Run now</strong>. The transcript should return <strong>READY</strong>.
        </div>
        <div class="guide-step">
          <span class="guide-label">3. Try a follow-up</span>
          Type a new instruction in the note box, then use <strong>Queue note only</strong> or <strong>Run now</strong>.
        </div>
      `;
      return;
    }

    if (session.statusKind === "running") {
      els.controlGuide.innerHTML = `
        <div class="guide-step">
          <span class="guide-label">Running now</span>
          The current step is active. Wait for the transcript to update or use <strong>Cancel</strong> if it is stuck.
        </div>
        <div class="guide-step">
          <span class="guide-label">Draft next note</span>
          You can type in the note box while waiting, but it will not be sent until the run finishes.
        </div>
      `;
      return;
    }

    if (session.waitingForHuman) {
      els.controlGuide.innerHTML = `
        <div class="guide-step">
          <span class="guide-label">Review first</span>
          Read the latest assistant output in the transcript.
        </div>
        <div class="guide-step">
          <span class="guide-label">Type your decision</span>
          Put approval text, a correction, or a redirect in <strong>Human message / note</strong>.
        </div>
        <div class="guide-step">
          <span class="guide-label">Choose the right button</span>
          <strong>Approve only</strong> and <strong>Reject only</strong> queue text. <strong>Approve + Run</strong> and <strong>Reject + Run</strong> continue immediately.
        </div>
      `;
      return;
    }

    els.controlGuide.innerHTML = `
      <div class="guide-step">
        <span class="guide-label">Type here</span>
        Use the note box for the next instruction, correction, or follow-up.
      </div>
      <div class="guide-step">
        <span class="guide-label">Queue or run</span>
        <strong>Queue note only</strong> saves the text for later. <strong>Run now</strong> uses the note box text immediately. If the box is empty, it runs the queued prompt shown above.
      </div>
      <div class="guide-step">
        <span class="guide-label">Manual smoke test</span>
        Create a Gemini session with <strong>Reply with exactly READY</strong>, run it, then send a short follow-up.
      </div>
    `;
  }

  function renderSessionMode(session) {
    const selectedMode = sessionModeConfig(session?.sessionMode || "general");
    document.querySelectorAll("[data-session-mode]").forEach((node) => {
      const active = session ? node.getAttribute("data-session-mode") === selectedMode.id : false;
      node.classList.toggle("active", active);
      node.disabled = !session;
    });

    if (els.sessionModeCopy) {
      els.sessionModeCopy.textContent = session
        ? selectedMode.hint
        : "Select a session to choose how this control panel should frame the next step.";
    }

    if (els.humanMessage) {
      els.humanMessage.placeholder = selectedMode.placeholder;
    }
  }

  function isDisabledProvider(providerId) {
    return DISABLED_PROVIDER_IDS.has(String(providerId || "").toLowerCase());
  }

  function providerSortKey(providerId) {
    const normalized = String(providerId || "").toLowerCase();
    const index = PROVIDER_SORT_ORDER.indexOf(normalized);
    return index === -1 ? PROVIDER_SORT_ORDER.length : index;
  }

  function sortProviders(items) {
    return [...items].sort((left, right) => {
      const orderDelta = providerSortKey(left.id) - providerSortKey(right.id);
      if (orderDelta !== 0) return orderDelta;
      return String(left.name || left.id).localeCompare(String(right.name || right.id));
    });
  }

  function eligibleCreateProviders() {
    const readyProviders = state.providers.filter((provider) => provider.ready && !isDisabledProvider(provider.id));
    if (readyProviders.length) return readyProviders;

    const fallbackProviders = state.providers.filter((provider) => !isDisabledProvider(provider.id));
    if (fallbackProviders.length) return fallbackProviders;

    return state.providers.filter((provider) => provider.ready);
  }

  function loadSessionModelCache() {
    try {
      const raw = localStorage.getItem(MODEL_CACHE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
      return Object.fromEntries(
        Object.entries(parsed).filter(([, value]) => typeof value === "string" && value.trim())
      );
    } catch {
      return {};
    }
  }

  function loadSessionModeCache() {
    try {
      const raw = localStorage.getItem(SESSION_MODE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
      return Object.fromEntries(
        Object.entries(parsed).filter(([, value]) =>
          SESSION_MODES.some((mode) => mode.id === String(value || "").trim())
        )
      );
    } catch {
      return {};
    }
  }

  function saveSessionModelCache() {
    try {
      localStorage.setItem(MODEL_CACHE_KEY, JSON.stringify(state.sessionModels));
    } catch {
      // Ignore storage failures; model selection still works for the live session.
    }
  }

  function saveSessionModeCache() {
    try {
      localStorage.setItem(SESSION_MODE_KEY, JSON.stringify(state.sessionModes));
    } catch {
      // Ignore storage failures; the mode still works during the live session.
    }
  }

  function rememberSessionModel(sessionId, model) {
    const normalized = String(model || "").trim();
    if (!sessionId || !normalized) return;
    state.sessionModels[sessionId] = normalized;
    saveSessionModelCache();
  }

  function lookupSessionModel(sessionId) {
    return state.sessionModels[sessionId] || "";
  }

  function rememberSessionMode(sessionId, modeId) {
    const normalized = String(modeId || "").trim();
    if (!sessionId || !SESSION_MODES.some((mode) => mode.id === normalized)) return;
    state.sessionModes[sessionId] = normalized;
    saveSessionModeCache();
  }

  function lookupSessionMode(sessionId) {
    return state.sessionModes[sessionId] || "general";
  }

  function sessionModeConfig(modeId) {
    return SESSION_MODES.find((mode) => mode.id === String(modeId || "").trim()) || SESSION_MODES[3];
  }

  function defaultModelForProvider(provider) {
    switch (String(provider || "").toLowerCase()) {
      case "gemini":
        return "gemini-2.5-pro";
      case "gemini-cli":
        return "gemini-2.5-pro";
      case "anthropic":
        return "claude-sonnet-4-20250514";
      case "azure-openai":
        return "gpt-4o";
      case "codex-cli":
        return "";
      case "claude-cli":
        return "";
      case "ollama":
        return "phi3:mini";
      default:
        return "";
    }
  }

  function modelHelpForProvider(provider) {
    switch (String(provider || "").toLowerCase()) {
      case "gemini":
      case "gemini-cli":
        return "Gemini presets are included. Leave blank to use the provider default.";
      case "anthropic":
        return "Enter a Claude model name or leave blank for the provider default.";
      case "azure-openai":
        return "Enter the deployment model you want the Azure endpoint to use.";
      case "codex-cli":
      case "claude-cli":
        return "Leave blank to use the CLI default, or enter a specific model if your CLI supports it.";
      case "ollama":
        return "Enter a local Ollama model name such as phi3:mini.";
      default:
        return "Choose a model or leave this blank to use the provider default.";
    }
  }

  function modelPresetsForProvider(provider) {
    switch (String(provider || "").toLowerCase()) {
      case "gemini":
      case "gemini-cli":
        return GEMINI_MODEL_PRESETS;
      case "ollama":
        return [{ value: "phi3:mini", label: "phi3:mini" }];
      case "anthropic":
        return [{ value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4" }];
      case "azure-openai":
        return [
          { value: "gpt-4o", label: "GPT-4o" },
          { value: "gpt-4.1-mini", label: "GPT-4.1 mini" },
        ];
      default:
        return [];
    }
  }

  function renderModelPresets(provider) {
    const presets = modelPresetsForProvider(provider);
    els.modelPresets.innerHTML = presets
      .map((item) => `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`)
      .join("");
    els.modelHelp.textContent = modelHelpForProvider(provider);
    if (!els.createModel.value.trim()) {
      const fallback = defaultModelForProvider(provider);
      els.createModel.value = fallback;
      state.createModelAutoValue = fallback;
    }
  }

  function syncCreateModelToProvider(provider, force = false) {
    const fallback = defaultModelForProvider(provider);
    const current = els.createModel.value.trim();
    if (force || !current || current === state.createModelAutoValue) {
      els.createModel.value = fallback;
    }
    state.createModelAutoValue = fallback;
    renderModelPresets(provider);
  }

  function renderRepoOptions() {
    if (!els.createRepoRoot) return;
    const repos = [...state.repos].sort((left, right) => {
      const leftName = left.name || basenameFromPath(left.root);
      const rightName = right.name || basenameFromPath(right.root);
      return String(leftName || left.root).localeCompare(String(rightName || right.root));
    });

    const values = ["", ...repos.map((repo) => repo.root).filter(Boolean)];
    const existing = Array.from(els.createRepoRoot.options).map((option) => option.value);
    const needsUpdate =
      existing.length !== values.length || values.some((value) => !existing.includes(value));

    if (!needsUpdate) {
      renderCreateWorkspaceSummary();
      return;
    }

    const selectedValue =
      values.includes(els.createRepoRoot.value) && els.createRepoRoot.value !== undefined
        ? els.createRepoRoot.value
        : state.selectedRepoRoot || "";
    const options = [
      `<option value="">Select a workspace</option>`,
      ...repos.map((repo) => {
        const labelName = repo.name || basenameFromPath(repo.root) || repo.root || "Repo";
        const suffixParts = [repo.kind || "repo"];
        if (repo.branch) suffixParts.push(repo.branch);
        suffixParts.push(repo.dirty ? "dirty" : "clean");
        const label = suffixParts.length ? `${labelName} - ${suffixParts.join(" - ")}` : labelName;
        return `<option value="${escapeHtml(repo.root)}">${escapeHtml(label)}</option>`;
      }),
    ];

    els.createRepoRoot.innerHTML = options.join("");
    els.createRepoRoot.value = selectedValue && values.includes(selectedValue) ? selectedValue : "";
    state.selectedRepoRoot = els.createRepoRoot.value;
    try {
      if (state.selectedRepoRoot) {
        localStorage.setItem(REPO_STORAGE_KEY, state.selectedRepoRoot);
      } else {
        localStorage.removeItem(REPO_STORAGE_KEY);
      }
    } catch {
      // Ignore storage failures.
    }
    renderCreateWorkspaceSummary();
  }

  function syncCreateRepoToSelection(root, force = false) {
    if (!els.createRepoRoot) return;
    const normalized = String(root || "").trim();
    const current = String(els.createRepoRoot.value || "").trim();
    if (force || current === state.selectedRepoRoot) {
      els.createRepoRoot.value = normalized;
    }
    state.selectedRepoRoot = normalized;
    try {
      if (normalized) {
        localStorage.setItem(REPO_STORAGE_KEY, normalized);
      } else {
        localStorage.removeItem(REPO_STORAGE_KEY);
      }
    } catch {
      // Ignore storage failures.
    }
    renderCreateWorkspaceSummary();
  }

  function renderCreateWorkspaceSummary() {
    if (!els.createWorkspaceSummary) return;
    const effectiveRoot = effectiveCreateRepoRoot();
    const repo = findRepoByRoot(effectiveRoot);
    const manualValue = String(els.createManualRepoRoot?.value || "").trim();

    if (!effectiveRoot) {
      els.createWorkspaceSummary.innerHTML = `
        <div class="workspace-summary-empty">
          Select a workspace to preview branch, dirty state, stack hints, and recent commits before you create the run.
        </div>
      `;
      return;
    }

    if (!repo) {
      els.createWorkspaceSummary.innerHTML = `
        <div class="workspace-summary-head">
          <div>
            <div class="workspace-summary-label">Workspace preview</div>
            <div class="workspace-summary-name">Preview unavailable</div>
          </div>
          <span class="status-pill waiting">needs match</span>
        </div>
        <div class="workspace-summary-root">${escapeHtml(effectiveRoot)}</div>
        <div class="workspace-summary-note">
          ${manualValue
            ? "The manual path will be validated on create and must resolve to a discovered repo or worktree inside the scan root."
            : "Select a discovered workspace to preview branch, dirty state, and recent commits."}
        </div>
      `;
      return;
    }

    const chips = [
      `<span class="tiny-chip">${escapeHtml(repo.kind || "repo")}</span>`,
      repo.branch ? `<span class="tiny-chip">${escapeHtml(repo.branch)}</span>` : "",
      `<span class="tiny-chip">${repo.dirty ? "dirty" : "clean"}</span>`,
    ]
      .filter(Boolean)
      .join("");
    els.createWorkspaceSummary.innerHTML = `
      <div class="workspace-summary-head">
        <div>
          <div class="workspace-summary-label">Workspace preview</div>
          <div class="workspace-summary-name">${escapeHtml(repo.name || basenameFromPath(repo.root) || "Workspace")}</div>
        </div>
        <div class="workspace-summary-chips">${chips}</div>
      </div>
      <div class="workspace-summary-root">${escapeHtml(repo.root)}</div>
      <div class="workspace-summary-grid">
        <section class="workspace-summary-block">
          <span class="meta-label">Stack hints</span>
          ${renderTextList(repo.stackHints, "No stack hints")}
        </section>
        <section class="workspace-summary-block">
          <span class="meta-label">Changed files</span>
          ${renderTextList(repo.changedFiles, "No changed files")}
        </section>
        <section class="workspace-summary-block">
          <span class="meta-label">Recent commits</span>
          ${renderTextList(repo.recentCommits, "No recent commits")}
        </section>
      </div>
    `;
  }

  function statusKind(value) {
    const normalized = String(value || "").toLowerCase();
    if (["ready", "ok", "available", "enabled"].includes(normalized)) return "ready";
    if (["running", "active", "in_progress", "in-progress"].includes(normalized)) return "running";
    if (
      [
        "waiting",
        "waiting_for_human",
        "pending",
        "paused",
        "needs_approval",
        "needs_input",
        "needs-human",
      ].includes(normalized)
    )
      return "waiting";
    if (["error", "failed", "bad"].includes(normalized)) return "error";
    if (["done", "complete", "completed"].includes(normalized)) return "completed";
    if (["stopped", "cancelled", "canceled"].includes(normalized)) return "stopped";
    if (["idle"].includes(normalized)) return "idle";
    return "idle";
  }

  function isHumanPause(status, pauseReason) {
    if (["needs_input", "needs_approval"].includes(String(pauseReason || "").toLowerCase())) {
      return true;
    }
    return statusKind(status) === "waiting";
  }

  function normalizeSession(item) {
    const id = pick(item, ["id", "session_id", "sessionId", "key"], "");
    const status = pick(item, ["status", "state", "phase"], "idle");
    const title = pick(item, ["title", "name", "summary"], id || "Session");
    const updatedAt = pick(item, ["updated_at", "updatedAt", "last_updated", "modified_at", "timestamp"], "");
    const createdAt = pick(item, ["created_at", "createdAt", "started_at", "startedAt"], "");
    const pauseReason = pick(item, ["pause_reason", "pauseReason", "pause_kind", "pauseKind"], "");
    const pauseKind = pick(item, ["pause_kind", "pauseKind"], pauseReason);
    const pauseTitle = pick(item, ["pause_title", "pauseTitle"], "");
    const pauseDetail = pick(item, ["pause_detail", "pauseDetail"], "");
    const lastPrompt = pick(item, ["last_prompt", "lastPrompt", "queued_prompt", "queuedPrompt"], "");
    const queuedPrompt = pick(item, ["queued_prompt", "queuedPrompt"], "");
    const lastStopReason = pick(item, ["last_stop_reason", "lastStopReason", "stop_reason", "stopReason"], "");
    const lastProviderUsed = pick(item, ["last_provider_used", "lastProviderUsed"], "");
    const lastModelUsed = pick(item, ["last_model_used", "lastModelUsed"], "");
    const lastAttempts = normalizeTextList(pick(item, ["last_attempts", "lastAttempts"], []));
    const lastFallbackCount =
      Number(pick(item, ["last_fallback_count", "lastFallbackCount"], 0)) || 0;
    const model = pick(item, ["model", "model_name", "modelName", "deployment_model"], "");
    const repoRoot = pick(item, ["repo_root", "repoRoot"], "");
    const workspaceKind = pick(item, ["workspace_kind", "workspaceKind"], "");
    const workspaceSnapshot = normalizeRepoContext(
      pick(item, ["workspace_snapshot", "workspaceSnapshot"], null),
      repoRoot
    );
    const repoContext = normalizeRepoContext(pick(item, ["repo_context", "repoContext"], null), repoRoot);
    const effectiveRepoContext = repoContext.root || repoContext.name ? repoContext : workspaceSnapshot;
    const workspaceLastCheckedAt = pick(
      item,
      ["workspace_last_checked_at", "workspaceLastCheckedAt"],
      effectiveRepoContext.scannedAt || ""
    );
    const stageTimeline = normalizeStageTimeline(pick(item, ["stage_timeline", "stageTimeline"], []));
    const stageOutputs = normalizeStageOutputs(pick(item, ["stage_outputs", "stageOutputs"], {}));
    const specialistStates = normalizeSpecialistStates(
      pick(item, ["specialist_states", "specialistStates"], [])
    );
    const specialistHandoffs = normalizeSpecialistHandoffs(
      pick(item, ["specialist_handoffs", "specialistHandoffs"], [])
    );
    const autoAnswerRecords = normalizeArray(item, ["auto_answer_records", "autoAnswerRecords"]).filter(Boolean);
    const blockedQuestions = normalizeTextList(pick(item, ["blocked_questions", "blockedQuestions"], []));
    const routeMetadata = pick(item, ["route_metadata", "routeMetadata"], {}) || {};
    const routeLane = pick(item, ["route_lane", "routeLane"], pick(routeMetadata, ["route_lane", "active_lane"], "auto"));
    const routePlan = normalizeRoutePlan(
      pick(item, ["route_plan", "routePlan"], pick(routeMetadata, ["route_plan"], []))
    );
    const routeAttempts = normalizeRouteAttempts(
      pick(item, ["route_attempts", "routeAttempts"], pick(routeMetadata, ["route_attempts"], []))
    );
    const capabilityChanges = normalizeCapabilityChanges(
      pick(item, ["capability_changes", "capabilityChanges"], pick(routeMetadata, ["capability_changes"], []))
    );
    return {
      raw: item,
      id,
      title,
      provider: pick(item, ["provider", "model_provider", "backend"], ""),
      status,
      statusKind: statusKind(status),
      waitingForHuman: Boolean(
        pick(item, ["waiting_for_human", "awaiting_human", "needs_human"], false) ||
          isHumanPause(status, pauseReason)
      ),
      updatedAt,
      createdAt,
      task: pick(item, ["original_task", "originalTask", "task", "goal", "prompt", "queued_prompt", "last_prompt"], ""),
      originalTask: pick(item, ["original_task", "originalTask", "task", "goal", "prompt"], ""),
      latestHumanNote: pick(item, ["latest_human_note", "latestHumanNote"], ""),
      lastPrompt,
      queuedPrompt,
      model: model || lookupSessionModel(id),
      preview: pick(item, ["preview", "last_message", "lastMessage", "summary_text"], ""),
      messageCount:
        Number(pick(item, ["message_count", "messageCount", "turn_count", "turns", "transcript_count"], 0)) ||
        0,
      error: pick(item, ["error", "last_error", "lastError"], ""),
      assistantMessage: pick(item, ["last_assistant_message", "lastAssistantMessage"], ""),
      systemMessage: pick(item, ["system_message", "systemMessage"], ""),
      eventCount: Number(pick(item, ["event_count", "eventCount"], 0)) || 0,
      stateSaved: Boolean(pick(item, ["state_saved", "stateSaved"], false)),
      attemptCount: Number(pick(item, ["attempt_count", "attemptCount"], 0)) || 0,
      latestAttemptId: pick(item, ["latest_attempt_id", "latestAttemptId"], ""),
      workspaceKind: workspaceKind || effectiveRepoContext.kind || "",
      workspaceSnapshot,
      workspaceStale: Boolean(pick(item, ["workspace_stale", "workspaceStale"], false)),
      workspaceStaleDetail: pick(item, ["workspace_stale_detail", "workspaceStaleDetail"], ""),
      workspaceLastCheckedAt,
      workspaceDriftFields: normalizeTextList(
        pick(item, ["workspace_drift_fields", "workspaceDriftFields"], [])
      ),
      sessionMode: lookupSessionMode(id),
      repoRoot: repoRoot || effectiveRepoContext.root || "",
      repoContext: effectiveRepoContext,
      pauseReason,
      pauseKind,
      pauseTitle,
      pauseDetail,
      currentStage: pick(item, ["current_stage", "currentStage"], ""),
      lastCompletedStage: pick(item, ["last_completed_stage", "lastCompletedStage"], ""),
      stageTimeline,
      stageOutputs,
      specialistStates,
      specialistHandoffs,
      autoAnswerRecords,
      blockedQuestions,
      pendingApproval: normalizeApprovalScope(pick(item, ["pending_approval", "pendingApproval"], null)),
      routeLane,
      requestedProvider: pick(item, ["requested_provider", "requestedProvider"], pick(routeMetadata, ["requested_provider"], "")),
      requestedModel: pick(item, ["requested_model", "requestedModel"], pick(routeMetadata, ["requested_model"], "")),
      routePlan,
      routeAttempts,
      capabilityChanges,
      routeMetadata,
      lastStopReason,
      lastProviderUsed,
      lastModelUsed,
      lastAttempts,
      lastFallbackCount,
    };
  }

  function normalizeMessage(item, index) {
    const role = String(
      pick(item, ["role", "sender", "author", "from", "speaker", "type"], "message")
    ).toLowerCase();
    const source = String(
      pick(item, ["source", "actor", "agent", "origin"], role === "user" ? "user" : role)
    ).toLowerCase();
    const metadata = normalizeMetadataObject(
      pick(item, ["metadata", "meta", "payload", "data"], {})
    );
    const route = routeMetadataFromMessage({ metadata });
    const stage =
      pick(item, ["stage", "current_stage", "currentStage"], "") ||
      pick(metadata, ["stage", "current_stage", "currentStage"], "");
    return {
      id: pick(item, ["id", "message_id", "messageId"], `message-${index}`),
      role: role,
      source: source,
      content: toText(pick(item, ["content", "text", "message", "body", "value"], "")),
      timestamp: pick(item, ["timestamp", "created_at", "createdAt", "time"], ""),
      label: pick(item, ["label", "kind", "type"], source || role),
      metadata: metadata,
      stage: stage,
      routeProvider: route.provider,
      routeModel: route.model,
      routeTier: route.tier,
      routeLane: route.lane,
      index,
    };
  }

  function normalizeSessionDetail(item) {
    const session = normalizeSession(item);
    const messages = normalizeArray(item, ["transcript", "messages", "history", "conversation"])
      .map(normalizeMessage)
      .filter((message) => message.content || message.role === "event");
    return {
      ...session,
      messages,
      systemMessage: pick(item, ["system_message", "systemMessage"], session.systemMessage || ""),
      humanPrompt: pick(item, ["human_prompt", "humanPrompt", "pending_message"], ""),
      lastEvent: pick(item, ["last_event", "lastEvent"], ""),
      streamUrl: pick(item, ["events_url", "eventsUrl"], ""),
      pauseReason: pick(item, ["pause_reason", "pauseReason"], session.pauseReason || ""),
      pauseKind: pick(item, ["pause_kind", "pauseKind"], session.pauseKind || session.pauseReason || ""),
      pauseTitle: pick(item, ["pause_title", "pauseTitle"], session.pauseTitle || ""),
      pauseDetail: pick(item, ["pause_detail", "pauseDetail"], session.pauseDetail || ""),
      lastPrompt: pick(item, ["last_prompt", "lastPrompt"], session.lastPrompt || ""),
      queuedPrompt: pick(item, ["queued_prompt", "queuedPrompt"], session.queuedPrompt || ""),
      lastStopReason: pick(item, ["last_stop_reason", "lastStopReason"], session.lastStopReason || ""),
      model: pick(item, ["model", "model_name", "modelName", "deployment_model"], session.model || ""),
      repoRoot: pick(item, ["repo_root", "repoRoot"], session.repoRoot || ""),
      repoContext: normalizeRepoContext(
        pick(item, ["repo_context", "repoContext", "workspace_snapshot", "workspaceSnapshot"], session.repoContext || null),
        pick(item, ["repo_root", "repoRoot"], session.repoRoot || "")
      ),
      workspaceSnapshot: normalizeRepoContext(
        pick(item, ["workspace_snapshot", "workspaceSnapshot"], session.workspaceSnapshot || null),
        pick(item, ["repo_root", "repoRoot"], session.repoRoot || "")
      ),
      workspaceKind: pick(item, ["workspace_kind", "workspaceKind"], session.workspaceKind || ""),
      workspaceStale: Boolean(
        pick(item, ["workspace_stale", "workspaceStale"], session.workspaceStale || false)
      ),
      workspaceStaleDetail: pick(
        item,
        ["workspace_stale_detail", "workspaceStaleDetail"],
        session.workspaceStaleDetail || ""
      ),
      workspaceLastCheckedAt: pick(
        item,
        ["workspace_last_checked_at", "workspaceLastCheckedAt"],
        session.workspaceLastCheckedAt || ""
      ),
      workspaceDriftFields: normalizeTextList(
        pick(
          item,
          ["workspace_drift_fields", "workspaceDriftFields"],
          session.workspaceDriftFields || []
        )
      ),
      currentStage: pick(item, ["current_stage", "currentStage"], session.currentStage || ""),
      lastCompletedStage: pick(
        item,
        ["last_completed_stage", "lastCompletedStage"],
        session.lastCompletedStage || ""
      ),
      stageTimeline: normalizeStageTimeline(
        pick(item, ["stage_timeline", "stageTimeline"], session.stageTimeline || [])
      ),
      stageOutputs: normalizeStageOutputs(
        pick(item, ["stage_outputs", "stageOutputs"], session.stageOutputs || {})
      ),
      specialistStates: normalizeSpecialistStates(
        pick(item, ["specialist_states", "specialistStates"], session.specialistStates || [])
      ),
      specialistHandoffs: normalizeSpecialistHandoffs(
        pick(item, ["specialist_handoffs", "specialistHandoffs"], session.specialistHandoffs || [])
      ),
      autoAnswerRecords: normalizeArray(
        item,
        ["auto_answer_records", "autoAnswerRecords"]
      ).filter(Boolean),
      blockedQuestions: normalizeTextList(
        pick(item, ["blocked_questions", "blockedQuestions"], session.blockedQuestions || [])
      ),
      events: normalizeSessionEvents(pick(item, ["events", "event_feed", "eventFeed"], [])),
      pendingApproval: normalizeApprovalScope(
        pick(item, ["pending_approval", "pendingApproval"], session.pendingApproval || null)
      ),
      routeLane: pick(item, ["route_lane", "routeLane"], session.routeLane || "auto"),
      requestedProvider: pick(
        item,
        ["requested_provider", "requestedProvider"],
        session.requestedProvider || ""
      ),
      requestedModel: pick(
        item,
        ["requested_model", "requestedModel"],
        session.requestedModel || ""
      ),
      routePlan: normalizeRoutePlan(
        pick(item, ["route_plan", "routePlan"], session.routePlan || [])
      ),
      routeAttempts: normalizeRouteAttempts(
        pick(item, ["route_attempts", "routeAttempts"], session.routeAttempts || [])
      ),
      capabilityChanges: normalizeCapabilityChanges(
        pick(item, ["capability_changes", "capabilityChanges"], session.capabilityChanges || [])
      ),
      routeMetadata: pick(item, ["route_metadata", "routeMetadata"], session.routeMetadata || {}) || {},
      latestAttemptId: pick(item, ["latest_attempt_id", "latestAttemptId"], session.latestAttemptId || ""),
      sessionMode: lookupSessionMode(session.id),
      raw: item,
    };
  }

  function formatTimestamp(value) {
    if (!value) return "unknown";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString([], {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  function formatRelative(value) {
    if (!value) return "unknown";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    const delta = date.getTime() - Date.now();
    const minutes = Math.round(delta / 60000);
    const abs = Math.abs(minutes);
    const suffix = minutes >= 0 ? "from now" : "ago";
    if (abs < 1) return "just now";
    if (abs < 60) return `${abs} min ${suffix}`;
    const hours = Math.round(abs / 60);
    if (hours < 24) return `${hours} h ${suffix}`;
    const days = Math.round(hours / 24);
    return `${days} d ${suffix}`;
  }

  function setLoading(key, value) {
    state.loading[key] = value;
    updateControls();
  }

  function showNotice(message, kind = "info") {
    const badgeClass = kind === "error" ? "error" : kind === "success" ? "success" : "info";
    els.notice.className = `notice show ${badgeClass}`;
    els.notice.textContent = message;
    clearTimeout(state.noticeTimer);
    state.noticeTimer = setTimeout(() => {
      els.notice.className = "notice";
    }, 3600);
  }

  function setStreamStatus(text) {
    state.streamStatus = text;
    els.streamStatus.textContent = text;
  }

  function setSelectedSession(id) {
    state.selectedSessionId = id;
    if (id) {
      localStorage.setItem(STORAGE_KEY, id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  async function apiFetch(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(options.headers || {}),
      },
      ...options,
      body:
        options.body && typeof options.body !== "string"
          ? JSON.stringify(options.body)
          : options.body,
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(text || `Request failed with ${response.status}`);
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return response.text();
  }

  function renderProviderControls() {
    const sortedProviders = sortProviders(state.providers);
    const available = state.providers.filter((provider) => provider.ready).length;
    const blocked = state.providers.length - available;
    els.providerSummary.innerHTML = [
      `<span class="badge">${state.providers.length} providers</span>`,
      `<span class="badge">${available} ready</span>`,
      `<span class="badge">${blocked} blocked</span>`,
    ].join("");

    els.providerList.innerHTML = sortedProviders.length
      ? sortedProviders
          .map((provider) => {
            const disabled = isDisabledProvider(provider.id);
            const statusClass = provider.ready && !disabled ? "ready" : "error";
            const activeClass = provider.active ? "active" : "";
            const statusText = disabled ? "disabled" : provider.ready ? "ready" : "blocked";
            return `
              <article class="provider-item ${activeClass}">
                <div class="provider-top">
                  <div class="provider-name">${escapeHtml(provider.name)}</div>
                  <span class="status-pill ${statusClass}">${statusText}</span>
                </div>
                <div class="provider-note">${escapeHtml(provider.id)}</div>
                ${provider.detail ? `<div class="provider-detail">${escapeHtml(provider.detail)}</div>` : ""}
              </article>
            `;
          })
          .join("")
      : `<div class="empty-state">No provider information yet.</div>`;

    const current =
      sortedProviders.find((provider) => provider.active) ||
      sortedProviders[0] ||
      (state.activeProvider
        ? {
            id: state.activeProvider,
            name: state.activeProvider,
            ready: true,
            detail: "Selected by the backend",
            active: true,
          }
        : null);
    if (current) {
      els.activeProvider.textContent = current.name;
      els.providerDetail.textContent = current.detail || (current.ready ? "Ready" : "Not ready");
    } else {
      els.activeProvider.textContent = "None";
      els.providerDetail.textContent = "Waiting for backend data";
    }

    const createProviders = eligibleCreateProviders();
    const values = createProviders.length
      ? createProviders.map((provider) => provider.id)
      : [state.activeProvider || "gemini"];
    const existing = Array.from(els.createProvider.options).map((option) => option.value);
    const needsUpdate =
      existing.length !== values.length || values.some((value) => !existing.includes(value));

    if (needsUpdate) {
      const selectedValue =
        values.find((value) => value === state.activeProvider) || values[0] || "gemini";
      els.createProvider.innerHTML = values
        .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
        .join("");
      els.createProvider.value = selectedValue;
      syncCreateModelToProvider(selectedValue, false);
    }
  }

  function renderRepoContextBanner(session) {
    if (!els.repoContextBanner) return;
    const repoContext = session?.repoContext;
    const repoRoot = session?.repoRoot || repoContext?.root || "";
    if (
      !repoRoot &&
      !repoContext?.name &&
      !repoContext?.branch &&
      !repoContext?.changedFiles?.length &&
      !repoContext?.recentCommits?.length &&
      !repoContext?.stackHints?.length &&
      !repoContext?.error
    ) {
      els.repoContextBanner.hidden = true;
      els.repoContextBanner.innerHTML = "";
      return;
    }

    const repoName = repoContext?.name || basenameFromPath(repoRoot) || "Repo context";
    const chips = [
      repoContext?.kind ? `<span class="tiny-chip">${escapeHtml(repoContext.kind)}</span>` : "",
      repoContext?.branch ? `<span class="tiny-chip">${escapeHtml(repoContext.branch)}</span>` : "",
      `<span class="tiny-chip">${escapeHtml(repoDirtyLabel(repoContext?.dirty))}</span>`,
      session?.latestAttemptId ? `<span class="tiny-chip">${escapeHtml(session.latestAttemptId)}</span>` : "",
      session?.workspaceStale
        ? '<span class="status-pill waiting">stale</span>'
        : '<span class="status-pill completed">fresh</span>',
      session?.workspaceLastCheckedAt
        ? `<span class="tiny-chip">Checked ${escapeHtml(formatTimestamp(session.workspaceLastCheckedAt))}</span>`
        : repoContext?.scannedAt
          ? `<span class="tiny-chip">Scanned ${escapeHtml(formatTimestamp(repoContext.scannedAt))}</span>`
          : "",
    ]
      .filter(Boolean)
      .join("");

    const rootDisplay = repoRoot || "No repo root recorded";
    const errorBlock = repoContext?.error
      ? `<div class="repo-context-error">Scan error: ${escapeHtml(repoContext.error)}</div>`
      : "";

    els.repoContextBanner.hidden = false;
    els.repoContextBanner.innerHTML = `
      <div class="repo-context-head">
        <div>
          <div class="repo-context-label">Repo context</div>
          <div class="repo-context-name">${escapeHtml(repoName)}</div>
          <div class="repo-context-root">${escapeHtml(rootDisplay)}</div>
        </div>
        <div class="repo-context-chips">${chips}</div>
      </div>
      <div class="repo-context-grid">
        <section class="repo-context-block">
          <span class="meta-label">Stack hints</span>
          ${renderTextList(repoContext?.stackHints, "No stack hints")}
        </section>
        <section class="repo-context-block">
          <span class="meta-label">Changed files</span>
          ${renderTextList(repoContext?.changedFiles, "No changed files")}
        </section>
        <section class="repo-context-block">
          <span class="meta-label">Recent commits</span>
          ${renderTextList(repoContext?.recentCommits, "No recent commits")}
        </section>
      </div>
      ${errorBlock}
    `;
  }

  function renderWorkspaceWarning(session) {
    if (!els.workspaceWarning) return;
    if (!session?.workspaceStale) {
      els.workspaceWarning.hidden = true;
      els.workspaceWarning.innerHTML = "";
      return;
    }

    const driftFields = normalizeTextList(session.workspaceDriftFields);
    const driftChips = driftFields.length
      ? driftFields.map((field) => `<span class="tiny-chip">${escapeHtml(field)}</span>`).join("")
      : '<span class="tiny-chip">workspace drift</span>';

    els.workspaceWarning.hidden = false;
    els.workspaceWarning.innerHTML = `
      <div class="workspace-warning-copy">
        <div class="workspace-warning-label">Workspace drift detected</div>
        <div class="workspace-warning-title">The repo changed after this run was created.</div>
        <div class="workspace-warning-detail">${escapeHtml(
          session.workspaceStaleDetail || "Refresh the repo summary before trusting older context."
        )}</div>
      </div>
      <div class="workspace-warning-meta">
        <div class="workspace-warning-chips">${driftChips}</div>
        <div class="workspace-warning-time">
          ${
            session.workspaceLastCheckedAt
              ? `Last checked ${escapeHtml(formatTimestamp(session.workspaceLastCheckedAt))}`
              : "Last checked time unavailable"
          }
        </div>
      </div>
    `;
  }

  function setOperatorTab(tabId, { render = true } = {}) {
    const normalized = OPERATOR_TABS.includes(tabId) ? tabId : "overview";
    state.selectedOperatorTab = normalized;
    document.querySelectorAll("[data-operator-tab]").forEach((node) => {
      const active = node.getAttribute("data-operator-tab") === normalized;
      node.classList.toggle("active", active);
      node.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (render && state.selectedSession) {
      renderOrchestrationPanel(state.selectedSession);
    }
  }

  function renderStageCards(session) {
    return (session.stageTimeline || [])
      .map((entry) => {
        const stageOutput = session.stageOutputs?.[entry.stage];
        return `
          <article class="stage-card stage-${escapeHtml(statusKind(entry.status))}">
            <div class="stage-card-head">
              <div class="stage-card-name">${escapeHtml(entry.stage || "stage")}</div>
              <span class="status-pill ${escapeHtml(statusKind(entry.status))}">${escapeHtml(entry.status)}</span>
            </div>
            <div class="stage-card-meta">
              ${entry.pauseKind ? `<span class="tiny-chip">${escapeHtml(entry.pauseKind)}</span>` : ""}
              ${entry.attemptCount ? `<span class="tiny-chip">${escapeHtml(entry.attemptCount)} attempts</span>` : ""}
              ${entry.autoAnswerCount ? `<span class="tiny-chip">${escapeHtml(entry.autoAnswerCount)} auto answers</span>` : ""}
            </div>
            <div class="stage-card-copy">${escapeHtml(stageOutput?.summary || entry.error || "No stage summary yet.")}</div>
          </article>
        `;
      })
      .join("");
  }

  function buildTimelineEntries(session) {
    const entries = [];
    (session.stageTimeline || []).forEach((entry, index) => {
      entries.push({
        id: `stage-${entry.stage}-${index}`,
        family: "stage",
        title: titleCaseWords(entry.stage || "stage"),
        copy:
          session.stageOutputs?.[entry.stage]?.summary ||
          entry.error ||
          "No stage summary recorded yet.",
        status: entry.status || "pending",
        meta: [entry.pauseKind, entry.attemptCount ? `${entry.attemptCount} attempts` : ""].filter(Boolean),
        timestamp: entry.updatedAt || entry.completedAt || entry.startedAt || "",
      });
    });
    (session.events || []).forEach((event) => {
      entries.push({
        id: `event-${event.seq}`,
        family: "event",
        title: titleCaseWords(event.type || "event"),
        copy: toText(event.payload?.summary || event.payload?.detail || event.payload?.message || ""),
        status: event.payload?.status || "",
        meta: [event.payload?.stage, event.payload?.pause_kind || event.payload?.pauseKind].filter(Boolean),
        timestamp: event.createdAt || "",
      });
    });
    if (session.pendingApproval) {
      entries.push({
        id: "timeline-pending-approval",
        family: "approval",
        title: "Approval scope",
        copy: session.pendingApproval.reason || "The manager is waiting for an approval decision.",
        status: session.pendingApproval.riskLevel || "needs approval",
        meta: [session.pendingApproval.actionKind].filter(Boolean),
        timestamp: session.updatedAt || "",
      });
    }
    return entries.sort((left, right) => new Date(left.timestamp || 0) - new Date(right.timestamp || 0));
  }

  function renderTimelineTab(session) {
    const entries = buildTimelineEntries(session);
    return `
      <div class="operator-grid">
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Timeline</span>
            <h3>Run progression</h3>
          </div>
          <div class="timeline-list">
            ${
              entries.length
                ? entries
                    .map(
                      (entry) => `
                        <article class="timeline-card timeline-${escapeHtml(entry.family)}">
                          <div class="timeline-card-head">
                            <div class="timeline-card-title">${escapeHtml(entry.title)}</div>
                            ${
                              entry.status
                                ? `<span class="status-pill ${escapeHtml(statusKind(entry.status))}">${escapeHtml(entry.status)}</span>`
                                : ""
                            }
                          </div>
                          <div class="timeline-card-copy">${escapeHtml(entry.copy || "No detail recorded.")}</div>
                          <div class="timeline-card-meta">
                            ${entry.meta.map((item) => `<span class="tiny-chip">${escapeHtml(titleCaseWords(item))}</span>`).join("")}
                            ${entry.timestamp ? `<span class="tiny-chip">${escapeHtml(formatTimestamp(entry.timestamp))}</span>` : ""}
                          </div>
                        </article>
                      `
                    )
                    .join("")
                : '<div class="empty-state">No timeline entries recorded yet.</div>'
            }
          </div>
        </section>
      </div>
    `;
  }

  function renderOutputCards(session) {
    return Object.values(session.stageOutputs || {})
      .map((output) => {
        const route = output.routeMetadata || {};
        const approvalCard = renderApprovalScope(output.pendingApproval, { compact: true });
        return `
          <article class="output-card">
            <div class="output-card-head">
              <div class="output-card-name">${escapeHtml(output.stage)}</div>
              <div class="output-card-route">
                ${route.active_provider ? `<span class="tiny-chip">${escapeHtml(route.active_provider)}</span>` : ""}
                ${route.active_model ? `<span class="tiny-chip">${escapeHtml(route.active_model)}</span>` : ""}
                ${route.route_tier ? `<span class="tiny-chip">${escapeHtml(route.route_tier)}</span>` : ""}
              </div>
            </div>
            <div class="output-card-copy">${escapeHtml(output.summary || "No summary captured.")}</div>
            ${approvalCard}
            ${
              output.nextAction
                ? `<div class="output-card-next"><span class="meta-label">Next action</span><div>${escapeHtml(output.nextAction)}</div></div>`
                : ""
            }
            ${
              output.changedFiles?.length
                ? `<div class="output-card-next"><span class="meta-label">Changed files</span><div class="output-card-artifacts">${output.changedFiles
                    .map((path) => `<span class="tiny-chip">${escapeHtml(path)}</span>`)
                    .join("")}</div></div>`
                : ""
            }
            ${
              output.validationResults?.length
                ? `<div class="output-card-next"><span class="meta-label">Validation</span><div class="output-card-artifacts">${output.validationResults
                    .map((result) => `<span class="tiny-chip">${escapeHtml(result.label || result.command?.join(" ") || "command")} | ${escapeHtml(result.status || "unknown")}</span>`)
                    .join("")}</div></div>`
                : ""
            }
            ${
              output.artifacts?.length
                ? `<div class="output-card-artifacts">${output.artifacts
                    .map((artifact) => `<span class="tiny-chip">${escapeHtml(artifact)}</span>`)
                    .join("")}</div>`
                : ""
            }
          </article>
        `;
      })
      .join("");
  }

  function renderOverviewTab(session) {
    const route = session.routeMetadata || {};
    const stageCards = renderStageCards(session);
    const outputCards = renderOutputCards(session);
    const pendingApproval =
      session.pendingApproval ||
      Object.values(session.stageOutputs || {})
        .map((output) => output.pendingApproval)
        .find(Boolean) ||
      null;
    return `
      <div class="operator-summary-grid">
        <article class="operator-stat-card">
          <span class="meta-label">Current stage</span>
          <strong>${escapeHtml(session.currentStage || "None")}</strong>
          <div class="operator-stat-subtle">${escapeHtml(session.pauseKind || session.pauseReason || "idle")}</div>
        </article>
        <article class="operator-stat-card">
          <span class="meta-label">Active route</span>
          <strong>${escapeHtml([route.active_provider, route.active_model].filter(Boolean).join(" / ") || "Pending")}</strong>
          <div class="operator-stat-subtle">${escapeHtml(route.route_tier || session.routeLane || "auto")} lane</div>
        </article>
        <article class="operator-stat-card">
          <span class="meta-label">Specialists</span>
          <strong>${escapeHtml(String(session.specialistStates?.length || 0))}</strong>
          <div class="operator-stat-subtle">${escapeHtml(String(session.specialistHandoffs?.length || 0))} handoffs tracked</div>
        </article>
        <article class="operator-stat-card">
          <span class="meta-label">Artifacts</span>
          <strong>${escapeHtml(String(Object.keys(session.stageOutputs || {}).length))}</strong>
          <div class="operator-stat-subtle">${escapeHtml(String(session.autoAnswerRecords?.length || 0))} auto answers saved</div>
        </article>
      </div>
      ${renderApprovalScope(pendingApproval)}
      <div class="operator-grid operator-grid-two">
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Timeline</span>
            <h3>Stage progress</h3>
          </div>
          <div class="stage-card-grid">${stageCards || '<div class="empty-state">No stage timeline yet.</div>'}</div>
        </section>
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Outputs</span>
            <h3>Stage summaries</h3>
          </div>
          <div class="output-card-grid">${outputCards || '<div class="empty-state">No stage outputs yet.</div>'}</div>
        </section>
      </div>
      ${
        session.blockedQuestions?.length
          ? `<div class="operator-alert">
              <span class="meta-label">Blocked questions</span>
              <div class="orchestration-list">${session.blockedQuestions
                .map((question) => `<span class="tiny-chip">${escapeHtml(question)}</span>`)
                .join("")}</div>
            </div>`
          : ""
      }
      ${
        session.autoAnswerRecords?.length
          ? `<div class="operator-alert">
              <span class="meta-label">Automatic GSD answers</span>
              <div class="orchestration-list">${session.autoAnswerRecords
                .map((record) => `<span class="tiny-chip">${escapeHtml(record.question || "question")}</span>`)
                .join("")}</div>
            </div>`
          : ""
      }
    `;
  }

  function renderApprovalScope(scope, options = {}) {
    if (!scope) return "";
    const compact = Boolean(options.compact);
    const classes = compact ? "approval-scope approval-scope-compact" : "approval-scope";
    const affectedPaths = scope.affectedPaths?.length
      ? `<div class="approval-scope-list">${scope.affectedPaths
          .map((path) => `<span class="tiny-chip">${escapeHtml(path)}</span>`)
          .join("")}</div>`
      : "";
    const commands = scope.commands?.length
      ? `<div class="approval-scope-list">${scope.commands
          .map((command) => `<span class="tiny-chip">${escapeHtml(command)}</span>`)
          .join("")}</div>`
      : "";
    const externalTargets = scope.externalTargets?.length
      ? `<div class="approval-scope-list">${scope.externalTargets
          .map((target) => `<span class="tiny-chip">${escapeHtml(target)}</span>`)
          .join("")}</div>`
      : "";
    return `
      <section class="${classes}">
        <div class="approval-scope-head">
          <div>
            <div class="approval-scope-label">Approval scope</div>
            <div class="approval-scope-title">${escapeHtml(scope.actionKind || "risky action")}</div>
          </div>
          ${scope.riskLevel ? `<span class="status-pill waiting">${escapeHtml(scope.riskLevel)}</span>` : ""}
        </div>
        ${scope.reason ? `<div class="approval-scope-copy">${escapeHtml(scope.reason)}</div>` : ""}
        ${affectedPaths ? `<div><span class="meta-label">Affected paths</span>${affectedPaths}</div>` : ""}
        ${commands ? `<div><span class="meta-label">Commands</span>${commands}</div>` : ""}
        ${externalTargets ? `<div><span class="meta-label">External targets</span>${externalTargets}</div>` : ""}
      </section>
    `;
  }

  function renderAgentsTab(session) {
    const specialistCards = (session.specialistStates || [])
      .map((specialist) => {
        const status = statusKind(specialist.status || "idle");
        return `
          <article class="specialist-card">
            <div class="specialist-card-head">
              <div>
                <div class="specialist-name">${escapeHtml(specialist.role || "specialist")}</div>
                <div class="specialist-note">${escapeHtml(specialist.stage || "unassigned stage")}</div>
              </div>
              <span class="status-pill ${escapeHtml(status)}">${escapeHtml(specialist.status || "not_started")}</span>
            </div>
            <div class="specialist-copy">${escapeHtml(specialist.currentTask || "No current task recorded.")}</div>
            ${
              specialist.latestOutputSummary
                ? `<div class="specialist-summary"><span class="meta-label">Latest output</span><div>${escapeHtml(specialist.latestOutputSummary)}</div></div>`
                : ""
            }
            <div class="specialist-meta">
              ${specialist.lastHandoffTarget ? `<span class="tiny-chip">handoff to ${escapeHtml(specialist.lastHandoffTarget)}</span>` : ""}
              ${specialist.lastHandoffReason ? `<span class="tiny-chip">${escapeHtml(specialist.lastHandoffReason)}</span>` : ""}
              ${specialist.updatedAt ? `<span class="tiny-chip">${escapeHtml(formatRelative(specialist.updatedAt))}</span>` : ""}
            </div>
          </article>
        `;
      })
      .join("");

    const handoffCards = (session.specialistHandoffs || [])
      .map((handoff) => {
        const status = statusKind(handoff.status || "idle");
        return `
          <article class="handoff-card">
            <div class="handoff-top">
              <div class="handoff-route">${escapeHtml(handoff.fromRole)} <span aria-hidden="true">→</span> ${escapeHtml(handoff.toRole)}</div>
              <span class="status-pill ${escapeHtml(status)}">${escapeHtml(handoff.status || "requested")}</span>
            </div>
            <div class="handoff-copy">${escapeHtml(handoff.reason || "No reason recorded.")}</div>
            <div class="handoff-meta">
              <span class="tiny-chip">requested by ${escapeHtml(handoff.requestedBy || "manager")}</span>
              ${handoff.updatedAt ? `<span class="tiny-chip">${escapeHtml(formatTimestamp(handoff.updatedAt))}</span>` : ""}
            </div>
          </article>
        `;
      })
      .join("");

    return `
      <div class="operator-summary-grid">
        <article class="operator-stat-card">
          <span class="meta-label">Visible specialists</span>
          <strong>${escapeHtml(String(session.specialistStates?.length || 0))}</strong>
          <div class="operator-stat-subtle">Manager, planner, researcher, implementer, reviewer</div>
        </article>
        <article class="operator-stat-card">
          <span class="meta-label">Latest handoff</span>
          <strong>${escapeHtml(
            session.specialistHandoffs?.length
              ? `${session.specialistHandoffs[session.specialistHandoffs.length - 1].fromRole} → ${session.specialistHandoffs[session.specialistHandoffs.length - 1].toRole}`
              : "None"
          )}</strong>
          <div class="operator-stat-subtle">${escapeHtml(session.currentStage || "workflow idle")}</div>
        </article>
      </div>
      <div class="operator-grid">
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Agents</span>
            <h3>Specialist roster</h3>
          </div>
          <div class="specialist-grid">${specialistCards || '<div class="empty-state">No specialist state recorded yet.</div>'}</div>
        </section>
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Handoffs</span>
            <h3>Delegation flow</h3>
          </div>
          <div class="handoff-list">${handoffCards || '<div class="empty-state">No specialist handoffs recorded yet.</div>'}</div>
        </section>
      </div>
    `;
  }

  function renderRoutingTab(session) {
    const route = session.routeMetadata || {};
    const planCards = (session.routePlan || [])
      .map((step) => {
        const active =
          step.provider === route.active_provider &&
          String(step.model || "") === String(route.active_model || "");
        return `
          <article class="routing-step ${active ? "active" : ""}">
            <div class="routing-step-top">
              <div class="routing-step-label">${escapeHtml(step.label || step.provider || "route step")}</div>
              <span class="tiny-chip">${escapeHtml(step.executionMode || "unknown")}</span>
            </div>
            <div class="routing-step-meta">
              <span class="tiny-chip">order ${escapeHtml(String(step.order ?? 0))}</span>
              <span class="tiny-chip">${step.toolsAvailable ? "tools available" : "tool-light"}</span>
            </div>
          </article>
        `;
      })
      .join("");

    const attemptCards = (session.routeAttempts || [])
      .map((attempt) => {
        const tone = statusKind(attempt.status || "idle");
        return `
          <article class="attempt-card">
            <div class="attempt-top">
              <div class="attempt-label">${escapeHtml([attempt.provider, attempt.model].filter(Boolean).join(" / ") || "attempt")}</div>
              <span class="status-pill ${escapeHtml(tone)}">${escapeHtml(attempt.status || "planned")}</span>
            </div>
            <div class="attempt-meta">
              <span class="tiny-chip">fallback ${escapeHtml(String(attempt.fallbackIndex ?? 0))}</span>
              <span class="tiny-chip">${attempt.toolsAvailable ? "tools available" : "tool-light"}</span>
              ${attempt.startedAt ? `<span class="tiny-chip">${escapeHtml(formatTimestamp(attempt.startedAt))}</span>` : ""}
            </div>
            ${attempt.error ? `<div class="attempt-error">${escapeHtml(attempt.error)}</div>` : ""}
          </article>
        `;
      })
      .join("");

    const capabilityCards = (session.capabilityChanges || [])
      .map((change) => `
        <article class="capability-card">
          <div class="capability-name">${escapeHtml(change.name || "change")}</div>
          <div class="capability-delta">${escapeHtml(String(change.before))} → ${escapeHtml(String(change.after))}</div>
          <div class="capability-reason">${escapeHtml(change.reason || "No reason recorded.")}</div>
        </article>
      `)
      .join("");

    return `
      <div class="operator-summary-grid">
        <article class="operator-stat-card">
          <span class="meta-label">Requested route</span>
          <strong>${escapeHtml([session.requestedProvider, session.requestedModel].filter(Boolean).join(" / ") || session.provider || "None")}</strong>
          <div class="operator-stat-subtle">${escapeHtml(session.routeLane || "auto")} lane</div>
        </article>
        <article class="operator-stat-card">
          <span class="meta-label">Actual route</span>
          <strong>${escapeHtml([route.active_provider, route.active_model].filter(Boolean).join(" / ") || "Pending")}</strong>
          <div class="operator-stat-subtle">${escapeHtml(route.route_reason || "Waiting for execution metadata.")}</div>
        </article>
        <article class="operator-stat-card">
          <span class="meta-label">Fallbacks used</span>
          <strong>${escapeHtml(String(route.fallback_count ?? session.lastFallbackCount ?? 0))}</strong>
          <div class="operator-stat-subtle">${escapeHtml(route.fallback_used ? "Fallback path was used" : "Primary route held")}</div>
        </article>
      </div>
      <div class="operator-grid">
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Plan</span>
            <h3>Planned route chain</h3>
          </div>
          <div class="routing-chain">${planCards || '<div class="empty-state">No route plan has been generated yet.</div>'}</div>
        </section>
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Attempts</span>
            <h3>Actual execution attempts</h3>
          </div>
          <div class="attempt-list">${attemptCards || '<div class="empty-state">No route attempts recorded yet.</div>'}</div>
        </section>
      </div>
      <section class="operator-section">
        <div class="orchestration-section-head">
          <span class="panel-kicker">Capability drift</span>
          <h3>What changed while routing</h3>
        </div>
        <div class="capability-grid">${capabilityCards || '<div class="empty-state">No capability changes were recorded.</div>'}</div>
      </section>
    `;
  }

  function renderArtifactsTab(session) {
    const artifactCards = Object.values(session.stageOutputs || {})
      .map((output) => `
        <article class="artifact-card">
          <div class="artifact-head">
            <div class="artifact-name">${escapeHtml(output.stage)}</div>
            <span class="tiny-chip">${escapeHtml(String(output.artifacts?.length || 0))} artifacts</span>
          </div>
          <div class="artifact-copy">${escapeHtml(output.summary || "No summary captured.")}</div>
          <div class="artifact-chip-row">
            ${(output.artifacts || [])
              .map((artifact) => `<span class="tiny-chip">${escapeHtml(artifact)}</span>`)
              .join("")}
          </div>
        </article>
      `)
      .join("");

    const answerCards = (session.autoAnswerRecords || [])
      .map((record) => `
        <article class="record-card">
          <div class="record-question">${escapeHtml(record.question || "question")}</div>
          <div class="record-answer">${escapeHtml(record.answer || "Awaiting input")}</div>
          <div class="record-meta">
            ${record.stage ? `<span class="tiny-chip">${escapeHtml(record.stage)}</span>` : ""}
            ${record.sources?.length ? `<span class="tiny-chip">${escapeHtml(record.sources.join(" | "))}</span>` : ""}
            <span class="tiny-chip">${escapeHtml(String(record.confidence ?? 0))}</span>
          </div>
        </article>
      `)
      .join("");

    const attemptTrail = normalizeTextList(session.lastAttempts || [])
      .map((line) => `<div class="attempt-trail-item">${escapeHtml(line)}</div>`)
      .join("");

    return `
      <div class="operator-grid">
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Artifacts</span>
            <h3>Saved stage outputs</h3>
          </div>
          <div class="artifact-grid">${artifactCards || '<div class="empty-state">No artifacts saved yet.</div>'}</div>
        </section>
        <section class="operator-section">
          <div class="orchestration-section-head">
            <span class="panel-kicker">Auto answers</span>
            <h3>Resolved GSD questions</h3>
          </div>
          <div class="record-grid">${answerCards || '<div class="empty-state">No automatic answers were recorded.</div>'}</div>
        </section>
      </div>
      <section class="operator-section">
        <div class="orchestration-section-head">
          <span class="panel-kicker">Attempt trail</span>
          <h3>Operator-visible execution log</h3>
        </div>
        <div class="attempt-trail">${attemptTrail || '<div class="empty-state">No attempt trail captured yet.</div>'}</div>
      </section>
    `;
  }

  function renderOrchestrationPanel(session) {
    if (!els.orchestrationPanel) return;
    if (!session) {
      els.orchestrationPanel.hidden = true;
      if (els.operatorTabContent) {
        els.operatorTabContent.innerHTML = "";
      }
      return;
    }
    els.orchestrationPanel.hidden = false;
    setOperatorTab(state.selectedOperatorTab, { render: false });
    const contentByTab = {
      overview: renderOverviewTab(session),
      timeline: renderTimelineTab(session),
      agents: renderAgentsTab(session),
      routing: renderRoutingTab(session),
      artifacts: renderArtifactsTab(session),
    };
    if (els.operatorTabContent) {
      els.operatorTabContent.innerHTML = contentByTab[state.selectedOperatorTab] || contentByTab.overview;
    }
  }

  function approvalItems() {
    return state.sessions
      .filter((session) => session.waitingForHuman)
      .sort((a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0));
  }

  function renderApprovalQueue() {
    const items = approvalItems();
    els.approvalQueueCount.textContent = `${items.length} waiting`;
    els.approvalQueue.innerHTML = items.length
      ? items
          .map((session) => {
            const selected = session.id === state.selectedSessionId ? "selected" : "";
            const approvalScope =
              session.pendingApproval ||
              Object.values(session.stageOutputs || {})
                .map((output) => output.pendingApproval)
                .find(Boolean) ||
              null;
            const reason = session.pauseTitle || session.pauseReason || "Waiting for human";
            const detail =
              approvalScope?.reason ||
              session.pauseDetail ||
              session.lastStopReason ||
              session.lastPrompt ||
              session.preview ||
              "Open the session to review the latest step.";
            return `
              <article class="queue-item ${selected}" data-queue-session-id="${escapeHtml(session.id)}">
                <div class="queue-top">
                  <div>
                    <div class="queue-name">${escapeHtml(session.title)}</div>
                    <div class="queue-provider">
                      ${escapeHtml(session.provider || "provider unknown")}
                      ${session.model ? ` | ${escapeHtml(session.model)}` : ""}
                      ${repoSummary(session) ? ` | ${escapeHtml(repoSummary(session))}` : ""}
                    </div>
                  </div>
                  <span class="status-pill waiting">waiting</span>
                </div>
                <div class="queue-reason">${escapeHtml(reason)}</div>
                <div class="queue-detail">${escapeHtml(detail)}</div>
                ${
                  approvalScope
                    ? `<div class="queue-subline">
                        ${approvalScope.riskLevel ? `<span class="tiny-chip">${escapeHtml(approvalScope.riskLevel)}</span>` : ""}
                        ${(approvalScope.affectedPaths || [])
                          .map((path) => `<span class="tiny-chip">${escapeHtml(path)}</span>`)
                          .join("")}
                      </div>`
                    : ""
                }
                <div class="queue-subline">
                  <span class="tiny-chip">${escapeHtml(formatRelative(session.updatedAt))}</span>
                  <span class="tiny-chip">${session.messageCount} messages</span>
                </div>
                <div class="queue-actions">
                  <button class="ghost-button queue-open" type="button" data-open-session="${escapeHtml(session.id)}">Open</button>
                </div>
              </article>
            `;
          })
          .join("")
      : `<div class="empty-state queue-empty">No sessions are waiting for you right now.</div>`;

    els.approvalQueue.querySelectorAll("[data-queue-session-id]").forEach((node) => {
      const id = node.getAttribute("data-queue-session-id");
      node.addEventListener("click", () => {
        selectSession(id);
      });
      node.querySelectorAll("[data-open-session]").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          selectSession(button.getAttribute("data-open-session"));
        });
      });
    });
  }

  function sessionMatchesFilter(session) {
    switch (state.filter) {
      case "active":
        return ["running", "waiting"].includes(session.statusKind);
      case "waiting":
        return session.waitingForHuman;
      case "stopped":
        return String(session.status || "").toLowerCase() === "stopped";
      case "error":
        return session.statusKind === "error";
      default:
        return true;
    }
  }

  function renderSessions() {
    const filtered = state.sessions.filter(sessionMatchesFilter);
    els.sessionList.innerHTML = filtered.length
      ? filtered
          .map((session) => {
            const selected = session.id === state.selectedSessionId ? "selected" : "";
            const statusClass = session.statusKind || "idle";
            const waitingBadge = session.waitingForHuman
              ? `<span class="status-pill waiting">waiting</span>`
              : "";
            const repoText = repoSummary(session);
            return `
              <article class="session-item ${selected}" data-session-id="${escapeHtml(session.id)}">
                <div class="session-title-row">
                  <div class="session-name">${escapeHtml(session.title)}</div>
                  <span class="status-pill ${statusClass}">${escapeHtml(session.status)}</span>
                </div>
                <div class="session-note">
                  ${escapeHtml(session.provider || "provider unknown")}
                  ${session.model ? ` | ${escapeHtml(session.model)}` : ""}
                  ${repoText ? ` | ${escapeHtml(repoText)}` : ""}
                </div>
                <div class="session-subline">
                  ${waitingBadge}
                  <span class="tiny-chip">${escapeHtml(formatRelative(session.updatedAt))}</span>
                  <span class="tiny-chip">${session.messageCount} messages</span>
                </div>
              </article>
            `;
          })
          .join("")
      : `<div class="empty-state">No sessions match the current filter.</div>`;

    els.sessionList.querySelectorAll("[data-session-id]").forEach((node) => {
      node.addEventListener("click", () => selectSession(node.getAttribute("data-session-id")));
    });
  }

  function renderMeta() {
    const session = state.selectedSession;
    els.selectedSessionName.textContent = session ? session.title : "None";
    els.selectedSessionStatus.textContent = session
      ? [
          session.status,
          session.waitingForHuman ? "waiting for human" : "",
          session.pauseReason ? session.pauseReason : "",
        ]
          .filter(Boolean)
          .join(" - ")
      : "No session selected";
    els.streamStatus.textContent = state.streamStatus;
    els.syncStatus.textContent = session
      ? state.loading.detail
        ? "Loading session detail"
        : `Updated ${formatRelative(session.updatedAt)}`
      : "Waiting for a session";

    if (!session) {
      els.detailTitle.textContent = "No run selected";
      els.detailBadges.innerHTML = "";
      renderActiveRunFocus(null);
      els.pauseBanner.hidden = true;
      els.pauseBanner.innerHTML = "";
      renderOrchestrationPanel(null);
      if (els.workspaceWarning) {
        els.workspaceWarning.hidden = true;
        els.workspaceWarning.innerHTML = "";
      }
      if (els.detailDisclosure) {
        els.detailDisclosure.hidden = true;
        els.detailDisclosure.open = false;
      }
      if (els.repoContextBanner) {
        els.repoContextBanner.hidden = true;
        els.repoContextBanner.innerHTML = "";
      }
      els.detailMeta.innerHTML = "";
      els.detailEmpty.style.display = "grid";
      els.transcript.innerHTML = `<div class="empty-state">Open a run to inspect the transcript, routing, specialists, and saved artifacts.</div>`;
      els.messageCount.textContent = "0 messages";
      els.lastUpdated.textContent = "Not updated yet";
      renderControlPending(null);
      renderRunStatus(null);
      renderControlGuide(null);
      renderSessionMode(null);
      return;
    }

    els.detailEmpty.style.display = "none";
    if (els.detailDisclosure) {
      els.detailDisclosure.hidden = false;
    }
    els.detailTitle.textContent = session.title;
    els.detailBadges.innerHTML = [
      `<span class="status-pill ${session.statusKind}">${escapeHtml(session.status)}</span>`,
      session.waitingForHuman ? `<span class="status-pill waiting">waiting for human</span>` : "",
      session.provider ? `<span class="badge">${escapeHtml(session.provider)}</span>` : "",
      session.model ? `<span class="badge">${escapeHtml(session.model)}</span>` : "",
      session.routeLane ? `<span class="badge">${escapeHtml(session.routeLane)} lane</span>` : "",
      session.requestedProvider ? `<span class="badge">requested ${escapeHtml(session.requestedProvider)}</span>` : "",
      session.requestedModel ? `<span class="badge">requested ${escapeHtml(session.requestedModel)}</span>` : "",
      session.lastProviderUsed ? `<span class="badge">used ${escapeHtml(session.lastProviderUsed)}</span>` : "",
      session.lastFallbackCount ? `<span class="badge">${escapeHtml(session.lastFallbackCount)} fallbacks</span>` : "",
      session.latestAttemptId ? `<span class="badge">${escapeHtml(session.latestAttemptId)}</span>` : "",
      session.attemptCount ? `<span class="badge">${escapeHtml(session.attemptCount)} attempts</span>` : "",
      session.workspaceStale
        ? `<span class="status-pill waiting">workspace stale</span>`
        : `<span class="status-pill completed">workspace fresh</span>`,
      `<span class="badge">mode: ${escapeHtml(sessionModeConfig(session.sessionMode).label)}</span>`,
      session.repoRoot || session.repoContext?.root ? `<span class="badge">repo</span>` : "",
    ]
      .filter(Boolean)
      .join("");

    renderActiveRunFocus(session);
    renderRepoContextBanner(session);
    renderWorkspaceWarning(session);
    renderOrchestrationPanel(session);

    const hasPauseState =
      session.waitingForHuman || session.pauseReason || session.pauseTitle || session.pauseDetail || session.lastStopReason;
    const pauseHeadline = session.pauseTitle || (session.waitingForHuman ? "Paused for human input" : "");
    const pauseBody =
      session.pauseDetail ||
      session.pauseReason ||
      session.lastStopReason ||
      (session.waitingForHuman ? session.lastPrompt || "The session is paused and waiting for your next action." : "");
    if (hasPauseState) {
      els.pauseBanner.hidden = false;
      els.pauseBanner.innerHTML = `
        <div class="pause-copy">
          <div class="pause-label">Pause state</div>
          <div class="pause-title">${escapeHtml(pauseHeadline || "Paused")}</div>
          <div class="pause-detail">${escapeHtml(pauseBody)}</div>
        </div>
        <div class="pause-tags">
          ${session.pauseReason ? `<span class="tiny-chip">${escapeHtml(session.pauseReason)}</span>` : ""}
          ${session.lastPrompt ? `<span class="tiny-chip">Last prompt: ${escapeHtml(session.lastPrompt)}</span>` : ""}
          ${session.lastStopReason ? `<span class="tiny-chip">Stop reason: ${escapeHtml(session.lastStopReason)}</span>` : ""}
        </div>
      `;
    } else {
      els.pauseBanner.hidden = true;
      els.pauseBanner.innerHTML = "";
    }

    const detailRows = [
      ["ID", session.id],
      ["Created", formatTimestamp(session.createdAt)],
      ["Updated", formatTimestamp(session.updatedAt)],
      ["Messages", String(session.messageCount)],
      ["Events", String(session.eventCount)],
      ["State saved", session.stateSaved ? "Yes" : "No"],
      ["Task", session.originalTask || session.task || "No task captured"],
      ["Workspace kind", session.workspaceKind || session.repoContext?.kind || "None"],
      ["Model", session.model || "Provider default"],
      ["Repo root", session.repoRoot || session.repoContext?.root || "None"],
      ["Repo branch", session.repoContext?.branch || "None"],
      ["Repo dirty", repoDirtyLabel(session.repoContext?.dirty)],
      ["Repo scanned", session.repoContext?.scannedAt ? formatTimestamp(session.repoContext.scannedAt) : "None"],
      ["Latest attempt", session.latestAttemptId || "None"],
      ["Attempt count", String(session.attemptCount || 0)],
      ["Workspace freshness", session.workspaceStale ? "Stale" : "Fresh"],
      ["Workspace checked", session.workspaceLastCheckedAt ? formatTimestamp(session.workspaceLastCheckedAt) : "None"],
      ["Workspace drift", session.workspaceDriftFields?.length ? session.workspaceDriftFields.join(" | ") : "None"],
      ["Current stage", session.currentStage || "None"],
      ["Last completed stage", session.lastCompletedStage || "None"],
      ["Pause kind", session.pauseKind || "None"],
      ["Blocked questions", session.blockedQuestions?.length ? session.blockedQuestions.join(" | ") : "None"],
      ["Auto answers", String(session.autoAnswerRecords?.length || 0)],
      ["Route provider", session.routeMetadata?.active_provider || "None"],
      ["Route model", session.routeMetadata?.active_model || "None"],
      ["Route tier", session.routeMetadata?.route_tier || "None"],
      ["Pause reason", session.pauseReason || "None"],
      ["Pause title", session.pauseTitle || "None"],
      ["Pause detail", session.pauseDetail || "None"],
      ["Last prompt", session.lastPrompt || "None"],
      ["Last provider used", session.lastProviderUsed || "None"],
      ["Last model used", session.lastModelUsed || "None"],
      ["Fallbacks used", String(session.lastFallbackCount || 0)],
      ["Attempt trail", session.lastAttempts?.length ? session.lastAttempts.join(" | ") : "None"],
      ["Last stop reason", session.lastStopReason || "None"],
      ["System message", session.systemMessage || "Default"],
      ["Stack hints", session.repoContext?.stackHints?.length ? session.repoContext.stackHints.join(" | ") : "None"],
      ["Changed files", session.repoContext?.changedFiles?.length ? session.repoContext.changedFiles.join(" | ") : "None"],
      ["Recent commits", session.repoContext?.recentCommits?.length ? session.repoContext.recentCommits.join(" | ") : "None"],
      ["Error", session.error || "None"],
      ["Assistant last", session.assistantMessage || "None"],
      ["Human prompt", session.humanPrompt || "None"],
      ["Last event", session.lastEvent || "None"],
    ];

    els.detailMeta.innerHTML = detailRows
      .map(
        ([label, value]) => `
          <div class="meta-card">
            <span class="meta-label">${escapeHtml(label)}</span>
            <div class="meta-value">${escapeHtml(value)}</div>
          </div>
        `
      )
      .join("");

    els.messageCount.textContent = `${session.messages.length} messages`;
    els.lastUpdated.textContent = session.updatedAt ? `Updated ${formatRelative(session.updatedAt)}` : "No timestamp";
    renderControlPending(session);
    renderRunStatus(session);
    renderControlGuide(session);
    renderSessionMode(session);

    els.transcript.innerHTML = session.messages.length
      ? session.messages.map((message, index) => renderMessageCard(message, index)).join("")
      : `<div class="empty-state">The transcript is empty or the backend has not returned run messages yet.</div>`;

    requestAnimationFrame(() => {
      if (els.transcript.scrollHeight > els.transcript.clientHeight) {
        els.transcript.scrollTop = els.transcript.scrollHeight;
      }
    });
  }

  function updateControls() {
    const hasSelection = Boolean(state.selectedSessionId);
    const session = state.selectedSession;
    const actionLocked = !hasSelection || state.loading.action;
    const running = String(session?.status || "").toLowerCase() === "running";
    const stopped = String(session?.status || "").toLowerCase() === "stopped";
    const waitingForHuman = Boolean(session?.waitingForHuman);
    const hasReplayablePrompt = Boolean(session?.lastPrompt || session?.task);

    els.sendMessage.disabled = actionLocked || stopped || running;
    els.approveSession.disabled = actionLocked || stopped || running || !waitingForHuman;
    els.approveRunSession.disabled = actionLocked || stopped || running || !waitingForHuman;
    els.rejectSession.disabled = actionLocked || stopped || running || !waitingForHuman;
    els.rejectRunSession.disabled = actionLocked || stopped || running || !waitingForHuman;
    els.runSession.disabled = actionLocked || stopped || running;
    els.retrySession.disabled = actionLocked || stopped || running || !hasReplayablePrompt;
    els.cancelSession.disabled = actionLocked || stopped;
    els.stopSession.disabled = actionLocked || stopped;
    els.humanMessage.disabled = !hasSelection || stopped;

    els.createForm
      .querySelectorAll("button, input, textarea, select")
      .forEach((node) => {
        if (node.id === "seed-example") return;
        node.disabled = Boolean(state.loading.create);
      });

    const createState = createRunReadiness();
    const createSubmit = els.createForm.querySelector('button[type="submit"]');
    if (els.createRepoRoot) {
      els.createRepoRoot.required = !String(els.createManualRepoRoot?.value || "").trim();
    }
    if (createSubmit) {
      createSubmit.disabled =
        Boolean(state.loading.create) || !createState.hasWorkspace || !createState.hasTask;
    }
  }

  function renderAll() {
    els.streamStatus.textContent = state.streamStatus;
    renderProviderControls();
    renderRepoOptions();
    renderApprovalQueue();
    renderSessions();
    renderMeta();
    updateControls();
  }

  function refreshLiveSessionIndicators() {
    const session = state.selectedSession;
    if (!session) return;
    els.selectedSessionStatus.textContent = [
      session.status,
      session.waitingForHuman ? "waiting for human" : "",
      session.pauseReason ? session.pauseReason : "",
    ]
      .filter(Boolean)
      .join(" - ");
    els.syncStatus.textContent = state.loading.detail
      ? "Loading session detail"
      : `Updated ${formatRelative(session.updatedAt)}`;
    els.lastUpdated.textContent = session.updatedAt ? `Updated ${formatRelative(session.updatedAt)}` : "No timestamp";
    renderRunStatus(session);
  }

  async function loadProviders() {
    setLoading("providers", true);
    try {
      const payload = await apiFetch("/providers");
      const providers = sortProviders(
        normalizeArray(payload, ["providers", "items", "data"]).map(normalizeProvider)
      );
      const activeProvider = pick(payload, ["activeProvider", "active_provider", "selectedProvider"], null);
      state.providers = providers.length
        ? providers.map((provider) => ({
            ...provider,
            active: provider.id === activeProvider || provider.name === activeProvider || provider.active,
          }))
        : [];
      state.activeProvider =
        activeProvider || state.providers.find((provider) => provider.active)?.id || null;
      renderAll();
    } catch (error) {
      showNotice(`Provider refresh failed: ${error.message}`, "error");
    } finally {
      setLoading("providers", false);
    }
  }

  async function loadRepos() {
    try {
      const payload = await apiFetch("/repos");
      const repos = normalizeArray(payload, ["items", "repos", "data"]).map(normalizeRepo);
      state.repos = repos
        .filter((repo) => repo.root || repo.name)
        .map((repo) => ({
          ...repo,
          root: String(repo.root || "").trim(),
          name: String(repo.name || "").trim(),
        }))
        .sort((left, right) => {
          const leftName = left.name || basenameFromPath(left.root);
          const rightName = right.name || basenameFromPath(right.root);
          return String(leftName || left.root).localeCompare(String(rightName || right.root));
        });
    } catch {
      state.repos = [];
    } finally {
      renderRepoOptions();
      renderAll();
    }
  }

  async function loadSessions(selectIfNeeded = true) {
    setLoading("sessions", true);
    try {
      const payload = await apiFetch("/sessions");
      const sessions = normalizeArray(payload, ["sessions", "items", "data"]).map(normalizeSession);
      sessions.sort((a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0));
      state.sessions = sessions;
      if (selectIfNeeded) {
        const selectedStillExists =
          state.selectedSessionId && sessions.some((session) => session.id === state.selectedSessionId);
        if (!selectedStillExists && sessions.length) {
          await selectSession(sessions[0].id, { silent: true });
        }
      }
      renderAll();
    } catch (error) {
      showNotice(`Session refresh failed: ${error.message}`, "error");
    } finally {
      setLoading("sessions", false);
    }
  }

  async function selectSession(id, options = {}) {
    if (!id) return;
    setSelectedSession(id);
    disconnectStream();
    state.selectedSession = state.sessions.find((session) => session.id === id) || null;
    renderAll();
    await loadSessionDetail(id, { silent: options.silent });
    connectStream(id);
  }

  async function loadSessionDetail(id, options = {}) {
    setLoading("detail", true);
    try {
      const payload = await apiFetch(`/sessions/${encodeURIComponent(id)}`);
      state.selectedSession = normalizeSessionDetail(payload);
      state.sessions = state.sessions.map((session) =>
        session.id === id ? { ...session, ...state.selectedSession } : session
      );
      renderAll();
      if (!options.silent) {
        showNotice(`Loaded session ${state.selectedSession.title}`, "success");
      }
    } catch (error) {
      if (!options.silent) {
        showNotice(`Session detail failed: ${error.message}`, "error");
      }
    } finally {
      setLoading("detail", false);
    }
  }

  function disconnectStream() {
    if (state.stream) {
      state.stream.close();
      state.stream = null;
    }
    setStreamStatus("Disconnected");
  }

  function connectStream(id) {
    disconnectStream();
    if (!id) return;

    try {
      state.stream = new EventSource(`${API_BASE}/sessions/${encodeURIComponent(id)}/events`);
      setStreamStatus("Connecting");

      state.stream.onopen = () => {
        setStreamStatus("Connected");
      };

      const receiveEvent = (event) => {
        if (!event.data) return;
        try {
          const data = JSON.parse(event.data);
          handleStreamEvent(data);
        } catch {
          refreshSelectedSession({ silent: true });
        }
      };

      state.stream.onmessage = receiveEvent;
      [
        "snapshot",
        "session.created",
        "message.added",
        "run.started",
        "run.completed",
        "run.failed",
        "session.stopped",
        "session.cancelled",
      ].forEach((eventName) => {
        state.stream.addEventListener(eventName, receiveEvent);
      });

      state.stream.onerror = () => {
        setStreamStatus("Reconnecting");
      };
    } catch (error) {
      setStreamStatus("Unavailable");
      showNotice(`Live stream unavailable: ${error.message}`, "error");
    }
  }

  function handleStreamEvent(event) {
    if (!event || typeof event !== "object") {
      refreshSelectedSession({ silent: true });
      return;
    }

    const type = String(event.type || event.event || event.kind || "update").toLowerCase();
    if (["message", "snapshot", "session", "state", "update", "replace"].includes(type)) {
      refreshSelectedSession({ silent: true });
      loadSessions(false);
      return;
    }

    if (type === "error") {
      showNotice(event.message || "Session stream reported an error.", "error");
      refreshSelectedSession({ silent: true });
      return;
    }

    refreshSelectedSession({ silent: true });
  }

  async function refreshSelectedSession(options = {}) {
    if (!state.selectedSessionId) return;
    await loadSessionDetail(state.selectedSessionId, options);
  }

  async function postAction(path, body = {}, successMessage = "Action sent", onSuccess = null) {
    if (!state.selectedSessionId) return;
    setLoading("action", true);
    try {
      await apiFetch(`/sessions/${encodeURIComponent(state.selectedSessionId)}${path}`, {
        method: "POST",
        body,
      });
      await loadSessionDetail(state.selectedSessionId, { silent: true });
      await loadSessions(false);
      if (typeof onSuccess === "function") {
        onSuccess();
      }
      showNotice(successMessage, "success");
    } catch (error) {
      showNotice(`Action failed: ${error.message}`, "error");
    } finally {
      setLoading("action", false);
    }
  }

  async function postActionSequence(steps, successMessage = "Action sent", onSuccess = null) {
    if (!state.selectedSessionId) return;
    setLoading("action", true);
    try {
      for (const step of steps) {
        await apiFetch(`/sessions/${encodeURIComponent(state.selectedSessionId)}${step.path}`, {
          method: "POST",
          body: step.body || {},
        });
      }
      await loadSessionDetail(state.selectedSessionId, { silent: true });
      await loadSessions(false);
      if (typeof onSuccess === "function") {
        onSuccess();
      }
      showNotice(successMessage || "Action sent", "success");
    } catch (error) {
      showNotice(`Action failed: ${error.message}`, "error");
    } finally {
      setLoading("action", false);
    }
  }

  async function createSession(event) {
    event.preventDefault();
    const createState = createRunReadiness();
    if (!createState.hasWorkspace) {
      showNotice("Select a workspace or enter a manual path inside the scan root before creating the run.", "error");
      return;
    }
    if (!createState.hasTask) {
      showNotice("Enter an engineering prompt before creating the run.", "error");
      return;
    }
    setLoading("create", true);
    try {
      const body = {
        title: els.createTitle.value.trim(),
        task: createState.task,
        system_message: els.createSystemMessage.value.trim(),
        provider: els.createProvider.value,
        model: els.createModel.value.trim(),
        route_lane: els.createRouteLane?.value || "auto",
        repo_root: createState.workspaceRoot || null,
      };
      const created = await apiFetch("/sessions", {
        method: "POST",
        body,
      });
      showNotice("Session created", "success");
      els.createForm.reset();
      els.createProvider.value = body.provider;
      if (els.createRouteLane) {
        els.createRouteLane.value = "auto";
      }
      syncCreateRepoToSelection(body.repo_root || "", true);
      if (els.createManualRepoRoot) {
        els.createManualRepoRoot.value = "";
      }
      syncCreateModelToProvider(body.provider, true);
      renderCreateWorkspaceSummary();
      await loadSessions(false);
      const nextId = pick(created, ["id", "session_id", "sessionId"], null);
      if (nextId) {
        rememberSessionModel(nextId, body.model);
        await selectSession(nextId);
      }
    } catch (error) {
      showNotice(`Create failed: ${error.message}`, "error");
    } finally {
      setLoading("create", false);
      updateControls();
    }
  }

  function queueSelectSession(id) {
    if (!id) return;
    selectSession(id);
  }

  function createRunReadiness() {
    const workspaceRoot = effectiveCreateRepoRoot();
    const task = String(els.createTask?.value || "").trim();
    return {
      workspaceRoot,
      task,
      matchedRepo: findRepoByRoot(workspaceRoot),
      hasWorkspace: Boolean(workspaceRoot),
      hasTask: Boolean(task),
    };
  }

  function seedExample() {
    els.createTitle.value = exampleSession.title;
    els.createTask.value = exampleSession.task;
    els.createSystemMessage.value = exampleSession.systemMessage;
    const createProviders = eligibleCreateProviders();
    if (!els.createProvider.value && createProviders.length) {
      els.createProvider.value =
        createProviders.find((provider) => provider.ready)?.id || createProviders[0].id;
    }
    const preferredRepoRoot =
      els.createRepoRoot?.value || state.selectedRepoRoot || state.repos[0]?.root || "";
    syncCreateRepoToSelection(preferredRepoRoot, true);
    if (els.createManualRepoRoot) {
      els.createManualRepoRoot.value = "";
    }
    syncCreateModelToProvider(els.createProvider.value, true);
    renderCreateWorkspaceSummary();
    updateControls();
    showNotice("Example session seeded", "success");
  }

  function seedSmokeTest() {
    els.createTitle.value = smokeTestSession.title;
    els.createTask.value = smokeTestSession.task;
    els.createSystemMessage.value = smokeTestSession.systemMessage;
    const createProviders = eligibleCreateProviders();
    const geminiProvider = createProviders.find((provider) => provider.id === "gemini");
    if (geminiProvider) {
      els.createProvider.value = geminiProvider.id;
    } else if (!els.createProvider.value && createProviders.length) {
      els.createProvider.value = createProviders[0].id;
    }
    const preferredRepoRoot =
      state.selectedRepoRoot || els.createRepoRoot?.value || state.repos[0]?.root || "";
    syncCreateRepoToSelection(preferredRepoRoot, true);
    if (els.createManualRepoRoot) {
      els.createManualRepoRoot.value = "";
    }
    syncCreateModelToProvider(els.createProvider.value, true);
    renderCreateWorkspaceSummary();
    updateControls();
    showNotice("Smoke test session seeded", "success");
  }

  function wireEvents() {
    els.createForm.addEventListener("submit", createSession);
    els.seedSmokeTest.addEventListener("click", seedSmokeTest);
    els.seedExample.addEventListener("click", seedExample);
    els.refreshProviders.addEventListener("click", loadProviders);
    document.querySelectorAll("[data-operator-tab]").forEach((node) => {
      node.addEventListener("click", () => {
        setOperatorTab(node.getAttribute("data-operator-tab"));
      });
    });
    document.querySelectorAll("[data-session-mode]").forEach((node) => {
      node.addEventListener("click", () => {
        if (!state.selectedSessionId) return;
        const modeId = node.getAttribute("data-session-mode");
        const mode = sessionModeConfig(modeId);
        rememberSessionMode(state.selectedSessionId, mode.id);
        state.sessions = state.sessions.map((session) =>
          session.id === state.selectedSessionId ? { ...session, sessionMode: mode.id } : session
        );
        if (state.selectedSession && state.selectedSession.id === state.selectedSessionId) {
          state.selectedSession = { ...state.selectedSession, sessionMode: mode.id };
        }
        renderAll();
        showNotice(`Session mode set to ${mode.label}`, "success");
      });
    });
    if (els.createRepoRoot) {
      els.createRepoRoot.addEventListener("change", () => {
        syncCreateRepoToSelection(els.createRepoRoot.value, false);
        renderCreateWorkspaceSummary();
        updateControls();
      });
    }
    if (els.createManualRepoRoot) {
      els.createManualRepoRoot.addEventListener("input", () => {
        renderCreateWorkspaceSummary();
        updateControls();
      });
    }
    els.refreshSessions.addEventListener("click", () => loadSessions(true));
    els.refreshQueue.addEventListener("click", () => loadSessions(false));
    els.createProvider.addEventListener("change", () => {
      syncCreateModelToProvider(els.createProvider.value, false);
    });
    els.createModel.addEventListener("input", () => {
      state.createModelAutoValue = state.createModelAutoValue || defaultModelForProvider(els.createProvider.value);
    });
    els.createTask.addEventListener("input", () => {
      updateControls();
    });
    els.sessionFilter.addEventListener("change", (event) => {
      state.filter = event.target.value;
      renderSessions();
    });

    els.sendMessage.addEventListener("click", async () => {
      const message = els.humanMessage.value.trim();
      if (!message) {
        showNotice("Enter a message before sending.", "error");
        return;
      }
      await postAction(
        "/messages",
        { content: message },
        "Queued the note for the next run.",
        () => {
          els.humanMessage.value = "";
        }
      );
    });

    els.approveSession.addEventListener("click", async () => {
      const note = els.humanMessage.value.trim();
      await postAction(
        "/approve",
        note ? { note } : {},
        "Queued approval for the next run.",
        () => {
          els.humanMessage.value = "";
        }
      );
    });

    els.approveRunSession.addEventListener("click", async () => {
      const note = els.humanMessage.value.trim();
      await postActionSequence(
        [
          { path: "/approve", body: note ? { note } : {} },
          { path: "/run", body: {} },
        ],
        "Approved and started the next run.",
        () => {
          els.humanMessage.value = "";
        }
      );
    });

    els.rejectSession.addEventListener("click", async () => {
      const note = els.humanMessage.value.trim();
      await postAction(
        "/reject",
        note ? { note } : {},
        "Queued rejection for the next run.",
        () => {
          els.humanMessage.value = "";
        }
      );
    });

    els.rejectRunSession.addEventListener("click", async () => {
      const note = els.humanMessage.value.trim();
      await postActionSequence(
        [
          { path: "/reject", body: note ? { note } : {} },
          { path: "/run", body: {} },
        ],
        "Rejected and started the next run.",
        () => {
          els.humanMessage.value = "";
        }
      );
    });

    els.runSession.addEventListener("click", async () => {
      const input = els.humanMessage.value.trim();
      await postAction(
        "/run",
        input ? { input } : {},
        input ? "Started a run with the note box text." : "Started a run with the queued prompt.",
        () => {
          if (input) {
            els.humanMessage.value = "";
          }
        }
      );
    });

    els.retrySession.addEventListener("click", async () => {
      await postAction("/retry", {}, "Retry started.");
    });

    els.cancelSession.addEventListener("click", async () => {
      await postAction("/cancel", {}, "Cancelled the active session.");
    });

    els.stopSession.addEventListener("click", async () => {
      await postAction("/stop", {}, "Stopped the session.");
    });

    document.addEventListener("keydown", (event) => {
      if (!state.selectedSessionId || state.loading.action) return;
      if (event.key === "Escape" && document.activeElement === els.humanMessage) {
        if (els.humanMessage.value.trim()) {
          els.humanMessage.value = "";
          showNotice("Cleared the note box", "success");
        }
        return;
      }
      if (!event.ctrlKey || event.key !== "Enter") return;

      event.preventDefault();
      if (event.shiftKey) {
        if (!els.approveRunSession.disabled) {
          els.approveRunSession.click();
        }
        return;
      }
      if (!els.runSession.disabled) {
        els.runSession.click();
      }
    });
  }

  async function boot() {
    wireEvents();
    setOperatorTab(state.selectedOperatorTab, { render: false });
    renderAll();
    await Promise.allSettled([loadProviders(), loadRepos(), loadSessions(true)]);
    if (!state.selectedSessionId && state.sessions.length) {
      await selectSession(state.sessions[0].id, { silent: true });
    }

    setInterval(() => {
      loadProviders();
      loadRepos();
      loadSessions(false);
      if (state.selectedSessionId) {
        refreshSelectedSession({ silent: true });
      }
    }, 30000);

    setInterval(() => {
      refreshLiveSessionIndicators();
      if (
        state.selectedSessionId &&
        state.selectedSession &&
        state.selectedSession.statusKind === "running" &&
        !state.loading.detail &&
        !state.loading.action
      ) {
        refreshSelectedSession({ silent: true });
        loadSessions(false);
      }
    }, 2000);
  }

  boot().catch((error) => {
    showNotice(`Dashboard failed to start: ${error.message}`, "error");
    console.error(error);
  });
})();
