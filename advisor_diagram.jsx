import { useState } from "react";

const COLORS = {
  gray:   { bg: "#F1EFE8", border: "#888780", text: "#444441", sub: "#5F5E5A" },
  teal:   { bg: "#E1F5EE", border: "#0F6E56", text: "#085041", sub: "#0F6E56" },
  coral:  { bg: "#FAECE7", border: "#993C1D", text: "#712B13", sub: "#993C1D" },
  blue:   { bg: "#E6F1FB", border: "#185FA5", text: "#0C447C", sub: "#185FA5" },
};

const DARK = {
  gray:   { bg: "#444441", border: "#888780", text: "#D3D1C7", sub: "#B4B2A9" },
  teal:   { bg: "#085041", border: "#5DCAA5", text: "#9FE1CB", sub: "#5DCAA5" },
  coral:  { bg: "#4A1B0C", border: "#D85A30", text: "#F5C4B3", sub: "#D85A30" },
  blue:   { bg: "#042C53", border: "#378ADD", text: "#B5D4F4", sub: "#378ADD" },
};

function useTheme() {
  const [dark] = useState(
    () => window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  return dark ? DARK : COLORS;
}

function Box({ x, y, w, h, color, title, sub, onClick, active, theme }) {
  const c = theme[color];
  return (
    <g
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default" }}
      role={onClick ? "button" : undefined}
      aria-label={onClick ? title : undefined}
    >
      <rect
        x={x} y={y} width={w} height={h} rx={8}
        fill={c.bg} stroke={active ? c.text : c.border}
        strokeWidth={active ? 1.5 : 0.6}
      />
      {sub ? (
        <>
          <text
            x={x + w / 2} y={y + h / 2 - 9}
            textAnchor="middle" dominantBaseline="central"
            fontSize={13} fontWeight={500} fill={c.text}
            fontFamily="system-ui, sans-serif"
          >{title}</text>
          <text
            x={x + w / 2} y={y + h / 2 + 11}
            textAnchor="middle" dominantBaseline="central"
            fontSize={11} fill={c.sub}
            fontFamily="system-ui, sans-serif"
          >{sub}</text>
        </>
      ) : (
        <text
          x={x + w / 2} y={y + h / 2}
          textAnchor="middle" dominantBaseline="central"
          fontSize={13} fontWeight={500} fill={c.text}
          fontFamily="system-ui, sans-serif"
        >{title}</text>
      )}
      {/* tap indicator dot */}
      {onClick && (
        <circle cx={x + w - 10} cy={y + 10} r={3}
          fill={active ? c.text : c.border} opacity={active ? 1 : 0.5}/>
      )}
    </g>
  );
}

function Arrow({ d, dashed, light }) {
  return (
    <path
      d={d}
      fill="none"
      stroke={light ? "#9c9a92" : "#5F5E5A"}
      strokeWidth={1.5}
      strokeDasharray={dashed ? "5 3" : undefined}
      markerEnd="url(#arrowhead)"
    />
  );
}

function Label({ x, y, text, anchor = "middle", size = 11 }) {
  return (
    <text
      x={x} y={y}
      textAnchor={anchor}
      dominantBaseline="central"
      fontSize={size} fill="#888780"
      fontFamily="system-ui, sans-serif"
    >{text}</text>
  );
}

export default function AdvisorDiagram() {
  const theme = useTheme();
  const [tooltip, setTooltip] = useState(null);

  const tips = {
    run:       "Available from Claude Code v2.1.101. Opens an interactive model picker. Session-scoped — re-run it each new session. Re-running mid-session lets you swap the advisor model without restarting.",
    model:     "Currently Sonnet 4.6 or Opus 4.6. No Haiku, no custom endpoints. The advisor must be at least as capable as the executor — you can't set a weaker model as advisor.",
    active:    "From this point Sonnet autonomously decides when to call Opus. You never trigger it manually. The configuration resets when the session ends. Running /compact collapses accumulated advice into a summary.",
    task:      "Advisor is armed but completely silent here. No calls happen just from receiving a task — Sonnet needs to orient first before it knows enough to benefit from advice.",
    orient:    "Reading files, fetching URLs, checking directory structure — this is orientation, not substantive work. The advisor stays silent. Only once Sonnet is about to commit to an interpretation does it escalate.",
    trigger:   "4 patterns fire reliably: (1) before writing or editing, (2) at perceived completion, (3) when stuck or errors are looping, (4) before changing approach. The key heuristic: orientation vs. substantive work.",
    called:    "Takes zero parameters — input is always an empty object {}. The server builds the full context automatically by forwarding the entire transcript. You cannot pass extra instructions to Opus here.",
    resumes:   "The advisor_tool_result block now lives in the conversation history permanently. Sonnet doesn't 'read and follow' instructions — the advice is part of the token context it generates from. Future advisor calls can see it too.",
    done:      "Always write the file / commit / save BEFORE this call. The advisor sub-inference takes time; if the session ends during it, a durable on-disk result survives but an unwritten one doesn't.",
    complete:  "Session ends here. All advisor_tool_result blocks persist in history for this session. If you /compact, they get compressed into a summary — resetting the advisor's accumulated guidance for future turns.",
    transcript:"Opus receives: your system prompt, all tool definitions, all prior turns, all tool results. It sees everything Sonnet saw. The server constructs this automatically — nothing you put in advisor() input reaches Opus.",
    inference: "Opus runs without tools and without context management. It can only reason over what the executor already gathered — it cannot read more files or run bash. Thinking blocks are dropped; only the final advice text is returned.",
    result:    "Two variants: advisor_result (plain text, normal case) and advisor_redacted_result (encrypted blob for ZDR compliance). Either way, Sonnet always sees readable advice. Round-trip the block verbatim — omitting it causes a 400 error.",
  };

  const tip = (key) => () => setTooltip(tooltip === key ? null : key);

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: "12px 0" }}>
      <svg width="100%" viewBox="0 0 680 690" aria-label="The /advisor command in Claude Code — dual-model flow diagram">
        <defs>
          <marker id="arrowhead" viewBox="0 0 10 10" refX={8} refY={5}
            markerWidth={6} markerHeight={6} orient="auto-start-reverse">
            <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
              strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"/>
          </marker>
        </defs>

        {/* ── SETUP ROW ── */}
        <Box x={20}  y={24} w={138} h={40} color="gray" title="Run /advisor"
          onClick={tip("run")} active={tooltip==="run"} theme={theme}/>
        <Box x={200} y={24} w={172} h={40} color="gray" title="Select advisor model"
          onClick={tip("model")} active={tooltip==="model"} theme={theme}/>
        <Box x={420} y={24} w={222} h={40} color="teal" title="Advisor active · whole session"
          onClick={tip("active")} active={tooltip==="active"} theme={theme}/>
        <Arrow d="M158 44 L200 44"/>
        <Arrow d="M372 44 L420 44"/>

        {/* divider */}
        <line x1={20} y1={82} x2={656} y2={82}
          stroke="#D3D1C7" strokeWidth={0.5} strokeDasharray="4 4"/>

        {/* column headers */}
        {[["Executor (Sonnet)", 125], ["Advisor (Opus)", 541]].map(([t, x]) => (
          <text key={t} x={x} y={97} textAnchor="middle" dominantBaseline="central"
            fontSize={13} fontWeight={600} fill="#888780"
            fontFamily="system-ui, sans-serif">{t}</text>
        ))}

        {/* ── EXECUTOR COLUMN ── */}
        <Box x={20} y={114} w={210} h={40} color="gray"  title="User sends task"
          onClick={tip("task")} active={tooltip==="task"} theme={theme}/>
        <Box x={20} y={168} w={210} h={52} color="teal"  title="Read & orient" sub="files, context, history"
          onClick={tip("orient")} active={tooltip==="orient"} theme={theme}/>
        <Box x={20} y={234} w={210} h={40} color="coral" title="Trigger condition met?"
          onClick={tip("trigger")} active={tooltip==="trigger"} theme={theme}/>
        <Box x={20} y={292} w={210} h={52} color="blue"  title="advisor() called" sub="stream pauses silently"
          onClick={tip("called")} active={tooltip==="called"} theme={theme}/>
        <Box x={20} y={490} w={210} h={52} color="teal"  title="Sonnet resumes" sub="advice injected to context"
          onClick={tip("resumes")} active={tooltip==="resumes"} theme={theme}/>
        <Box x={20} y={558} w={210} h={52} color="blue"  title="Near completion?" sub="Call advisor again"
          onClick={tip("done")} active={tooltip==="done"} theme={theme}/>
        <Box x={20} y={628} w={210} h={40} color="gray"  title="Task complete"
          onClick={tip("complete")} active={tooltip==="complete"} theme={theme}/>

        {/* executor vertical arrows */}
        <Arrow d="M125 154 L125 168"/>
        <Arrow d="M125 220 L125 234"/>
        <Arrow d="M125 274 L125 292"/>
        <Label x={136} y={286} text="yes" anchor="start"/>
        {/* dashed pause */}
        <Arrow d="M125 344 L125 490" dashed light/>
        <Arrow d="M125 542 L125 558"/>
        <Arrow d="M125 610 L125 628"/>

        {/* loop: no trigger */}
        <Arrow d="M230 254 L372 254 L372 194 L230 194" light/>
        <Label x={301} y={244} text="no trigger ↺"/>

        {/* ── ADVISOR COLUMN ── */}
        <Box x={440} y={292} w={210} h={52} color="blue" title="Full transcript → Opus" sub="zero extra API calls"
          onClick={tip("transcript")} active={tooltip==="transcript"} theme={theme}/>
        <Box x={440} y={358} w={210} h={52} color="blue" title="Opus sub-inference" sub="400–700 text tokens"
          onClick={tip("inference")} active={tooltip==="inference"} theme={theme}/>
        <Box x={440} y={424} w={210} h={52} color="teal" title="advisor_tool_result" sub="returned to executor"
          onClick={tip("result")} active={tooltip==="result"} theme={theme}/>

        {/* advisor vertical arrows */}
        <Arrow d="M545 344 L545 358"/>
        <Arrow d="M545 410 L545 424"/>

        {/* cross: executor → advisor */}
        <Arrow d="M230 318 L440 318"/>
        <Label x={335} y={308} text="full context"/>

        {/* cross: advisor → executor */}
        <Arrow d="M440 450 L335 450 L335 516 L230 516"/>
        <Label x={390} y={440} text="advice"/>

        {/* ── TRIGGER PANEL ── */}
        <rect x={440} y={558} width={210} height={110} rx={8}
          fill="none" stroke="#D3D1C7" strokeWidth={0.5} strokeDasharray="4 4"/>
        <text x={545} y={577} textAnchor="middle" dominantBaseline="central"
          fontSize={12} fontWeight={600} fill="#888780"
          fontFamily="system-ui, sans-serif">When advisor fires</text>
        <line x1={452} y1={589} x2={638} y2={589} stroke="#D3D1C7" strokeWidth={0.5}/>
        {[
          "① Before writing or editing",
          "② At perceived completion",
          "③ When stuck or looping",
          "④ Before changing approach",
        ].map((t, i) => (
          <text key={t} x={454} y={605 + i * 17}
            dominantBaseline="central" fontSize={11} fill="#888780"
            fontFamily="system-ui, sans-serif">{t}</text>
        ))}
      </svg>

      {/* Tooltip strip */}
      {tooltip && (() => {
        // pick accent color to match the box that was tapped
        const accentKey =
          ["run","model","task","complete"].includes(tooltip) ? "gray" :
          ["active","orient","resumes"].includes(tooltip)     ? "teal" :
          ["trigger"].includes(tooltip)                       ? "coral" : "blue";
        const ac = COLORS[accentKey];
        return (
          <div style={{
            margin: "0 4px 8px",
            padding: "10px 14px",
            borderRadius: 8,
            background: ac.bg,
            borderLeft: `3px solid ${ac.border}`,
            fontSize: 13,
            color: ac.text,
            lineHeight: 1.6,
          }}>
            <strong style={{ marginRight: 6 }}>Note:</strong>{tips[tooltip]}
            <button
              onClick={() => setTooltip(null)}
              style={{
                float: "right", background: "none", border: "none",
                cursor: "pointer", fontSize: 14, color: ac.sub,
              }}
            >✕</button>
          </div>
        );
      })()}

      {/* Legend */}
      <div style={{
        display: "flex", gap: 16, padding: "4px 8px",
        flexWrap: "wrap", fontSize: 11, color: "#888780",
      }}>
        {[
          ["teal", "Executor state"],
          ["blue", "Advisor system"],
          ["coral", "Decision / trigger"],
          ["gray", "Neutral / control"],
        ].map(([c, label]) => (
          <span key={c} style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{
              display: "inline-block", width: 10, height: 10, borderRadius: 3,
              background: COLORS[c].bg, border: `1.5px solid ${COLORS[c].border}`,
            }}/>
            {label}
          </span>
        ))}

      </div>
    </div>
  );
}
