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

function Box({ x, y, w, h, color, title, sub, onClick, theme }) {
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
        fill={c.bg} stroke={c.border} strokeWidth={0.6}
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
    trigger: "Fires before writing, at completion, when stuck, or before changing approach.",
    called:  "Takes zero parameters. The server builds the full context automatically.",
    opus:    "Opus sees your system prompt, all tool defs, every prior turn, every tool result.",
    result:  "Only the advice text reaches Sonnet — Opus's thinking blocks are dropped first.",
    done:    "Always write the file / commit / save BEFORE this call. If the session ends mid-advisor, a durable result survives.",
  };

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
        <Box x={20}  y={24} w={138} h={40} color="gray"  title="Run /advisor"          theme={theme}/>
        <Box x={200} y={24} w={172} h={40} color="gray"  title="Select advisor model"  theme={theme}/>
        <Box x={420} y={24} w={222} h={40} color="teal"  title="Advisor active · whole session" theme={theme}/>
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
        <Box x={20} y={114} w={210} h={40}  color="gray"  title="User sends task"            theme={theme}/>
        <Box x={20} y={168} w={210} h={52}  color="teal"  title="Read & orient" sub="files, context, history" theme={theme}/>
        <Box x={20} y={234} w={210} h={40}  color="coral" title="Trigger condition met?"
          onClick={() => setTooltip(tooltip === "trigger" ? null : "trigger")} theme={theme}/>
        <Box x={20} y={292} w={210} h={52}  color="blue"  title="advisor() called" sub="stream pauses silently"
          onClick={() => setTooltip(tooltip === "called" ? null : "called")} theme={theme}/>
        <Box x={20} y={490} w={210} h={52}  color="teal"  title="Sonnet resumes" sub="advice injected to context" theme={theme}/>
        <Box x={20} y={558} w={210} h={52}  color="blue"  title="Near completion?" sub="Call advisor again"
          onClick={() => setTooltip(tooltip === "done" ? null : "done")} theme={theme}/>
        <Box x={20} y={628} w={210} h={40}  color="gray"  title="Task complete"             theme={theme}/>

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
        <Box x={440} y={292} w={210} h={52}  color="blue"  title="Full transcript → Opus" sub="zero extra API calls"
          onClick={() => setTooltip(tooltip === "opus" ? null : "opus")} theme={theme}/>
        <Box x={440} y={358} w={210} h={52}  color="blue"  title="Opus sub-inference" sub="400–700 text tokens" theme={theme}/>
        <Box x={440} y={424} w={210} h={52}  color="teal"  title="advisor_tool_result" sub="returned to executor"
          onClick={() => setTooltip(tooltip === "result" ? null : "result")} theme={theme}/>

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
      {tooltip && (
        <div style={{
          margin: "0 4px 8px",
          padding: "10px 14px",
          borderRadius: 8,
          background: COLORS.blue.bg,
          borderLeft: `3px solid ${COLORS.blue.border}`,
          fontSize: 13,
          color: COLORS.blue.text,
          lineHeight: 1.6,
        }}>
          <strong style={{ marginRight: 6 }}>Note:</strong>{tips[tooltip]}
          <button
            onClick={() => setTooltip(null)}
            style={{
              float: "right", background: "none", border: "none",
              cursor: "pointer", fontSize: 14, color: COLORS.blue.sub,
            }}
          >✕</button>
        </div>
      )}

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
        <span style={{ marginLeft: "auto", opacity: 0.6 }}>Tap colored boxes for notes</span>
      </div>
    </div>
  );
}
