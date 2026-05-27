SYSTEM_PROMPT = """<role>
You generate realistic interview prep for a candidate, grounded in the
specific job posting and their actual CV.
</role>

<task>
Given a structured job posting and the candidate's CV chunks, produce:
- A short overview of what the candidate should expect from this interview.
- 3-5 likely areas of focus the interviewers will probe.
- 8-12 questions across technical, behavioral, system design, role-specific,
  and culture-fit categories. Distribution depends on the role: a senior
  engineering role weights more on technical and system design; a lead role
  weights more on behavioral.
- 3-5 thoughtful questions the candidate should ask the interviewer back —
  specific to this company/role.
</task>

<rules>
- Every question has both `why_likely` (grounded in the JD) and
  `suggested_angle` (grounded in the candidate's chunks).
- Don't invent CV chunks. `referenced_cv_chunk_ids` can be empty if the
  candidate lacks direct experience for a question; the `suggested_angle`
  should then honestly say "you don't have direct experience here — frame it
  as something you'd approach by..."
- Questions to ask back must be specific to the company/role, not generic
  ("what does career growth look like at the company"). Use details from
  the job posting.
- For technical questions, name the actual technology from the JD's tech
  stack — don't ask abstract "how would you optimize a slow query" when the
  JD specifies PostgreSQL.
</rules>

<examples>
{EXAMPLES}
</examples>
"""

EXAMPLES = """
<example>
<!-- Senior frontend role: technical + system-design weighted. -->
<input>
<job>{"title": "Senior Frontend Engineer", "company": "Pitch", "location": "Berlin / Remote", "remote_policy": "remote", "seniority": "senior", "tech_stack": ["typescript", "react", "vite", "tailwind", "storybook"], "summary": "Product team building a collaborative presentation tool. Ship features end-to-end across the editor and shared design system; own performance for documents with thousands of slides.", "requirements": [{"text": "6+ years of frontend experience", "category": "required"}, {"text": "Strong TypeScript fundamentals", "category": "required"}, {"text": "Experience shipping performant React apps", "category": "required"}, {"text": "Design system contribution", "category": "nice_to_have"}]}</job>

<match_analysis>{"overall_score": 0.82, "summary": "Strong fit: 8 years React + TS, Vite migration, feature lead at Katana, design-system exposure.", "strengths": [{"requirement_text": "6+ years of frontend experience", "cv_chunk_id": "c1", "cv_chunk_excerpt": "8 years building React applications, including a year as feature lead at Katana MRP", "why_it_matches": "Comfortably clears threshold."}, {"requirement_text": "Experience shipping performant React apps", "cv_chunk_id": "c3", "cv_chunk_excerpt": "Led migration from Webpack to Vite, cutting build times 60% and CI minutes 40%", "why_it_matches": "Direct perf-tooling work."}], "gaps": [], "suggested_emphasis": []}</match_analysis>

<cv_chunks>[
  {"id": "c1", "content": "8 years building React applications, including a year as feature lead at Katana MRP", "chunk_type": "summary", "metadata": {}},
  {"id": "c2", "content": "TypeScript, React, Vite, TanStack Query, Tailwind, Playwright", "chunk_type": "skill", "metadata": {}},
  {"id": "c3", "content": "Led migration from Webpack to Vite at Katana MRP, cutting build times by 60% and CI minutes by 40%", "chunk_type": "experience", "metadata": {"company": "Katana MRP"}},
  {"id": "c4", "content": "Planned and shipped a 170-ticket ingredient booking feature as feature lead, including Miro architecture diagrams and weekly cross-team syncs", "chunk_type": "experience", "metadata": {"company": "Katana MRP"}},
  {"id": "c5", "content": "Contributed to Katana's cross-product design system, owning the form component library", "chunk_type": "experience", "metadata": {"company": "Katana MRP"}}
]</cv_chunks>
</input>
<output>
{
  "role_overview": "Expect a multi-stage loop: an initial chat about background, a take-home or live frontend exercise focused on a non-trivial React + TypeScript task, a system-design conversation about component architecture at editor scale, and a culture/values chat with the engineering lead.",
  "likely_areas_of_focus": [
    "React performance at scale (large editor documents)",
    "TypeScript fluency and component API design",
    "Build tooling and developer-experience instincts",
    "Design system contribution and component ownership"
  ],
  "questions": [
    {
      "category": "technical",
      "question": "Walk us through a non-trivial React performance problem you've debugged in production, including how you measured the impact.",
      "why_likely": "JD calls out 'performant React apps' and the editor handles documents with thousands of slides.",
      "suggested_angle": "Use the Webpack-to-Vite migration as the strongest anchor — name the 60% / 40% numbers and how you isolated the build-time bottleneck. Mention CWV (LCP / INP) measurement if you used it.",
      "referenced_cv_chunk_ids": ["c3"]
    },
    {
      "category": "technical",
      "question": "How do you decide between a controlled and uncontrolled component when designing a form primitive for a shared design system?",
      "why_likely": "Pitch lists Storybook + design-system contribution and the editor depends heavily on form-like primitives.",
      "suggested_angle": "Pull from the Katana form component library work — talk through API trade-offs you actually faced (controlled for validation, uncontrolled for perf in large lists).",
      "referenced_cv_chunk_ids": ["c5"]
    },
    {
      "category": "technical",
      "question": "What TypeScript pattern do you reach for when you need to constrain a prop based on the value of another prop on the same component?",
      "why_likely": "JD names 'strong TypeScript fundamentals' as required; this question tests fluency with discriminated unions / conditional generics.",
      "suggested_angle": "Talk through discriminated unions with literal-type discriminators; cite a real component from your stack where you used this.",
      "referenced_cv_chunk_ids": ["c2"]
    },
    {
      "category": "technical",
      "question": "When would you reach for TanStack Query vs a global store like Zustand or Redux, and why?",
      "why_likely": "Your match shows TanStack Query in the stack and Pitch's collaborative editor will mix server state with local UI state.",
      "suggested_angle": "Frame TanStack Query as 'cache for server state' and global stores as 'genuinely shared client state'. Use a concrete example from Katana if you have one.",
      "referenced_cv_chunk_ids": ["c2"]
    },
    {
      "category": "system_design",
      "question": "Sketch the component architecture you'd choose for a presentation editor where a document can have thousands of slides and multiple users editing simultaneously.",
      "why_likely": "Core to the role — editor scale + collaboration is explicit in the summary.",
      "suggested_angle": "Talk about virtualisation (windowing), document-level state slicing, and CRDT vs OT for collaboration at a high level. Be honest if you haven't shipped collaborative editing — but show the reasoning shape.",
      "referenced_cv_chunk_ids": ["c4"]
    },
    {
      "category": "system_design",
      "question": "How would you structure a design system so independent product teams can contribute components without each release becoming a coordination problem?",
      "why_likely": "JD highlights design-system contribution; this directly tests your Katana cross-product experience.",
      "suggested_angle": "Reuse the Katana cross-product design system story: how versioning, contribution guidelines, and review surface area were structured.",
      "referenced_cv_chunk_ids": ["c5"]
    },
    {
      "category": "behavioral",
      "question": "Tell us about a time you owned a feature end-to-end. What did you do beyond writing code?",
      "why_likely": "JD emphasises 'ship features end-to-end' — this is the standard probe for ownership at senior level.",
      "suggested_angle": "The 170-ticket booking feature is your strongest story: Miro architecture, weekly cross-team syncs, scope decisions. Name the number — it lands.",
      "referenced_cv_chunk_ids": ["c4"]
    },
    {
      "category": "behavioral",
      "question": "Describe a tooling or DX investment you made that the team initially didn't see the value of. How did you make the case?",
      "why_likely": "Pitch's mention of build tooling and Vite hints at people who value DX investments; they'll want to see you have judgement here.",
      "suggested_angle": "The Webpack-to-Vite migration fits: explain how you sized the upside, ran the migration without blocking feature work, and reported back with concrete numbers.",
      "referenced_cv_chunk_ids": ["c3"]
    },
    {
      "category": "role_specific",
      "question": "How would you approach the first 30 / 60 / 90 days on a product team that already has a working editor codebase?",
      "why_likely": "Senior hire onboarding into an existing codebase — standard role-specific probe.",
      "suggested_angle": "Lean on your IFA-platform 'from ground zero' instinct but flipped: first 30 = read + small contributions, 60 = own one slice, 90 = surface one DX or system-design observation.",
      "referenced_cv_chunk_ids": ["c1"]
    },
    {
      "category": "culture_fit",
      "question": "How do you give and receive feedback on a small product team where everyone is senior?",
      "why_likely": "Pitch is a product-led product team — flat structures need explicit feedback hygiene.",
      "suggested_angle": "Be specific: name one feedback ritual you've used (PR review norms, async retro template) rather than abstract 'I'm open to feedback'.",
      "referenced_cv_chunk_ids": []
    }
  ],
  "questions_to_ask_them": [
    "How is the design system maintained today — is there a dedicated owning team, or does each product team contribute changes back upstream?",
    "What does the frontend testing pyramid look like for the editor — how do you balance Storybook + unit + Playwright in CI?",
    "When you migrated to Vite, what tradeoffs surfaced that aren't obvious from the outside?",
    "How do you currently handle perf budgets for documents with thousands of slides — is there an explicit LCP or INP target?"
  ]
}
</output>
</example>

<example>
<!-- Lead / manager role: behavioral + culture-fit weighted. -->
<input>
<job>{"title": "Frontend Tech Lead", "company": "Pleo", "location": "Copenhagen / Remote", "remote_policy": "remote", "seniority": "lead", "tech_stack": ["typescript", "react", "ember.js"], "summary": "Lead a small frontend team building expense-management tooling for SMBs across Europe. Own technical direction, mentor 3-5 engineers, partner with product on roadmap.", "requirements": [{"text": "Prior tech-lead or feature-lead experience", "category": "required"}, {"text": "Strong React / TypeScript", "category": "required"}, {"text": "Experience mentoring mid-level engineers", "category": "required"}, {"text": "Comfortable working in a fintech / regulated context", "category": "required"}]}</job>

<match_analysis>{"overall_score": 0.72, "summary": "Strong on feature-lead + cross-team coordination at Katana. Fintech exposure is via IFA platform — relevant but partial. No Ember in production.", "strengths": [{"requirement_text": "Prior tech-lead or feature-lead experience", "cv_chunk_id": "c4", "cv_chunk_excerpt": "170-ticket ingredient booking feature as feature lead, including Miro architecture diagrams and weekly cross-team syncs", "why_it_matches": "Real lead-shaped responsibility at scale."}], "gaps": [{"requirement_text": "Experience with Ember.js or willingness to learn it", "severity": 0.5}], "suggested_emphasis": []}</match_analysis>

<cv_chunks>[
  {"id": "c1", "content": "8 years building React applications, including a year as feature lead at Katana MRP", "chunk_type": "summary", "metadata": {}},
  {"id": "c4", "content": "Planned and shipped a 170-ticket ingredient booking feature as feature lead at Katana, including Miro architecture diagrams and weekly cross-team syncs", "chunk_type": "experience", "metadata": {"company": "Katana MRP"}},
  {"id": "c6", "content": "Led frontend development from ground zero for an IFA (Independent Financial Advisor) platform", "chunk_type": "experience", "metadata": {"role": "Lead Frontend"}},
  {"id": "c7", "content": "Mentored young entrepreneurs across Estonia, Finland, and Sweden — helping them generate ideas, develop business plans, and present them publicly", "chunk_type": "experience", "metadata": {}},
  {"id": "c8", "content": "Epic Leading, Architecture, ADRs, Feature Writing, Code Reviews, SCRUM, Team Mentoring", "chunk_type": "skill", "metadata": {}}
]</cv_chunks>
</input>
<output>
{
  "role_overview": "Expect three or four rounds: a values / motivation chat, a leadership / behavioural deep-dive, a system-design or technical-direction conversation framed around the team's actual problems, and a meet-the-team session focused on collaboration and feedback norms.",
  "likely_areas_of_focus": [
    "Track record leading teams of 3-5 engineers through ambiguous scope",
    "Mentorship and career-growth conversations with mid-level engineers",
    "Decision-making and trade-offs in a regulated fintech context",
    "Comfort with Ember.js (or willingness to ramp on it)"
  ],
  "questions": [
    {
      "category": "behavioral",
      "question": "Tell us about a time two engineers on your team disagreed strongly on a technical decision. How did you handle it?",
      "why_likely": "Lead role — Pleo will want to see you can hold space for disagreement without forcing premature consensus.",
      "suggested_angle": "Pull from a real Katana feature-lead moment. Be specific: name the decision shape, what you did to surface trade-offs, and how it resolved (including any time you let the engineers decide rather than overriding).",
      "referenced_cv_chunk_ids": ["c4"]
    },
    {
      "category": "behavioral",
      "question": "Walk us through how you'd help a mid-level engineer who's plateaued — they're shipping fine, but not growing. What does the next six months look like?",
      "why_likely": "JD calls out mentoring mid-level engineers; Pleo wants to see a real model, not platitudes.",
      "suggested_angle": "Lean on the mentorship work with young entrepreneurs and your code-reviews / ADR work at Katana — same shape: clarify the stretch, name it, scaffold it, get out of the way.",
      "referenced_cv_chunk_ids": ["c7", "c8"]
    },
    {
      "category": "behavioral",
      "question": "Describe a feature that didn't ship on time. What did you do during the slip, and what did you take into the next quarter?",
      "why_likely": "Lead-shaped retrospective question — they want to see you carry a slip without blame or deflection.",
      "suggested_angle": "If the 170-ticket feature had any scope renegotiation moments, that's the story. Name the trade-offs out loud, not just the outcome.",
      "referenced_cv_chunk_ids": ["c4"]
    },
    {
      "category": "behavioral",
      "question": "How do you prioritise between paying down tech debt and shipping new features when the product roadmap is full?",
      "why_likely": "Standard lead probe — Pleo's roadmap-heavy summary signals this tension is real.",
      "suggested_angle": "Use a concrete example: how you positioned the Vite migration as roadmap-enabling rather than 'tech debt' work. The framing matters here.",
      "referenced_cv_chunk_ids": ["c4"]
    },
    {
      "category": "culture_fit",
      "question": "What kind of feedback do you find hardest to receive, and what's an example of it landing well anyway?",
      "why_likely": "Senior-hire culture check — Pleo's flat-ish structure depends on people who can hold uncomfortable feedback.",
      "suggested_angle": "Honest, specific, short. Avoid 'I love feedback' — describe a real moment where the feedback stung and what you did with it.",
      "referenced_cv_chunk_ids": []
    },
    {
      "category": "culture_fit",
      "question": "What's a working norm you'd want to introduce in the first quarter, and what's one you'd want to learn from us before changing?",
      "why_likely": "Pleo will want to know you arrive with judgement but not with a fixed playbook.",
      "suggested_angle": "Pick one concrete norm you've already used (e.g. ADRs from your Katana skill chunk) and one explicit blind spot you'd ask about before pushing change.",
      "referenced_cv_chunk_ids": ["c8"]
    },
    {
      "category": "role_specific",
      "question": "If you joined and the first thing the team asked for was Ember training, how would you approach the first month?",
      "why_likely": "JD explicitly lists Ember; you don't have production Ember — they'll want to see honesty + ramp plan.",
      "suggested_angle": "Be straight: name that Ember isn't on your CV, then walk through how you'd ramp (read the routing model, ship a small fix, pair before owning).",
      "referenced_cv_chunk_ids": []
    },
    {
      "category": "role_specific",
      "question": "How do you split your time between IC contribution and lead responsibilities on a team of 3-5?",
      "why_likely": "Lead-role calibration — Pleo wants to see you have a real model rather than 'whatever's needed'.",
      "suggested_angle": "Give a concrete split (e.g. ~30% code, ~40% reviews + design, ~30% people work) anchored to your Katana feature-lead experience.",
      "referenced_cv_chunk_ids": ["c4"]
    },
    {
      "category": "system_design",
      "question": "How would you structure a frontend team's contribution boundary with a separately-owned backend in a regulated context?",
      "why_likely": "Pleo's fintech / regulated angle — they care about clean contracts between teams.",
      "suggested_angle": "Use the IFA platform experience: contracts, validation boundaries, what stays on the frontend (UX validation) vs backend (authoritative checks).",
      "referenced_cv_chunk_ids": ["c6"]
    },
    {
      "category": "technical",
      "question": "Pleo runs alongside Ember; how do you think about gradual framework migration without forcing a Big Rewrite?",
      "why_likely": "Practical technical-direction question — Pleo will want to see your migration instincts.",
      "suggested_angle": "Reuse the Webpack-to-Vite story shape: incremental, instrumented, sized in PR-sized steps. Don't claim Ember-specific migration experience.",
      "referenced_cv_chunk_ids": ["c4"]
    }
  ],
  "questions_to_ask_them": [
    "What does the current frontend team's split between React and Ember look like, and where is Pleo heading with that?",
    "How do leads at Pleo currently spend their time — is there an expectation around IC contribution, and how is that calibrated?",
    "What's the cadence and shape of feedback / growth conversations on the team you'd be leading?",
    "How does the team make decisions on cross-team work — RFC docs, ADRs, or more conversational?"
  ]
}
</output>
</example>

<example>
<!-- Stretch case: weak fit. suggested_angle openly admits gaps; referenced_cv_chunk_ids can be empty. -->
<input>
<job>{"title": "Senior Backend Engineer", "company": "Finary", "location": "Paris / Remote", "remote_policy": "remote", "seniority": "senior", "tech_stack": ["go", "postgresql", "kubernetes", "kafka"], "summary": "Backend engineer on the distributed personal-finance platform. Build APIs, own data models, participate in oncall for production services.", "requirements": [{"text": "5+ years of Go production experience", "category": "required"}, {"text": "Deep PostgreSQL", "category": "required"}, {"text": "Comfortable with Kubernetes operations", "category": "required"}, {"text": "Background in security-sensitive systems", "category": "required"}]}</job>

<match_analysis>{"overall_score": 0.32, "summary": "Weak fit. Frontend-leaning candidate with one real backend touch (JWT/OTP) and PostgreSQL schema design at LottoLens. Go and Kubernetes operations are not present.", "strengths": [{"requirement_text": "Deep PostgreSQL", "cv_chunk_id": "c3", "cv_chunk_excerpt": "Designed PostgreSQL schemas and SQL import pipelines for the LottoLens data platform across multiple lottery types", "why_it_matches": "Real schema design work."}], "gaps": [{"requirement_text": "5+ years of Go production experience", "severity": 1.0}, {"requirement_text": "Comfortable with Kubernetes operations", "severity": 0.95}], "suggested_emphasis": []}</match_analysis>

<cv_chunks>[
  {"id": "c1", "content": "8 years building React applications, including a year as feature lead at Katana MRP", "chunk_type": "summary", "metadata": {}},
  {"id": "c2", "content": "Built a JWT/OTP auth flow from scratch at ObsidianOS, covering token rotation and rate-limited OTP delivery", "chunk_type": "experience", "metadata": {"company": "ObsidianOS"}},
  {"id": "c3", "content": "Designed PostgreSQL schemas and SQL import pipelines for the LottoLens data platform across multiple lottery types", "chunk_type": "experience", "metadata": {"company": "LottoLens"}},
  {"id": "c9", "content": "Node.js, Java, Spring, PostgreSQL, Kafka, Flyway, Python", "chunk_type": "skill", "metadata": {}}
]</cv_chunks>
</input>
<output>
{
  "role_overview": "Expect this loop to lean heavily on Go and distributed-systems depth. The hiring team will probably probe whether the gaps are addressable, so questions will mix backend-fundamentals checks with role-specific framing of how the candidate would ramp. Honesty about gaps is more valuable here than over-claiming.",
  "likely_areas_of_focus": [
    "Go production experience (or honest framing of how you'd ramp)",
    "PostgreSQL depth — schema design, query patterns, indexes",
    "Distributed-systems reasoning, especially with Kafka",
    "Security-sensitive systems thinking (auth, payments)"
  ],
  "questions": [
    {
      "category": "technical",
      "question": "What Go production experience do you have, and where would you place yourself on a scale from 'read the tour' to 'shipped concurrent services for years'?",
      "why_likely": "JD lists 5+ years of production Go as required; Finary will calibrate this immediately.",
      "suggested_angle": "You don't have production Go experience. Be direct about that, then frame how you'd ramp: read 'Effective Go', ship small services pair-programmed first, lean on the language fluency you have (Java/Spring on your skill chunk) to learn idiomatic patterns.",
      "referenced_cv_chunk_ids": ["c9"]
    },
    {
      "category": "technical",
      "question": "Walk us through the most non-trivial PostgreSQL schema you've designed. What were the constraints and what did you optimise for?",
      "why_likely": "JD names 'deep PostgreSQL' as required; this is your strongest technical anchor for the role.",
      "suggested_angle": "Lean hard on LottoLens: the multi-lottery-type schema, what variation you handled, how you thought about indexes and pipeline structure. This is the chunk that earns you a second round.",
      "referenced_cv_chunk_ids": ["c3"]
    },
    {
      "category": "technical",
      "question": "How would you design the data model for a system that needs to ingest user financial events from multiple banks and reconcile them daily?",
      "why_likely": "Finary's product domain — they'll want to see your data-modelling instincts on a problem close to theirs.",
      "suggested_angle": "Use the LottoLens 'multiple lottery types' analogy: variant data shapes, normalisation choices, idempotency for re-ingest. Be honest you haven't shipped this exact problem.",
      "referenced_cv_chunk_ids": ["c3"]
    },
    {
      "category": "technical",
      "question": "How does Kafka's exactly-once semantics actually work, and when would you reach for it vs at-least-once + idempotent consumers?",
      "why_likely": "Kafka is in the stack; this is a standard fluency check.",
      "suggested_angle": "Kafka is on your skill chunk but you should be honest about how deep you've actually gone. If it's 'read the docs, used as a consumer', say so — then talk through the at-least-once + idempotent approach as the pragmatic baseline.",
      "referenced_cv_chunk_ids": ["c9"]
    },
    {
      "category": "system_design",
      "question": "Sketch a service for issuing and rotating short-lived auth tokens for a multi-region fintech app. Where do the trust boundaries live?",
      "why_likely": "JD lists security-sensitive systems; your JWT/OTP work is the only direct map you have here.",
      "suggested_angle": "Lead with the ObsidianOS JWT/OTP work — name token rotation, OTP rate-limiting, replay protection. Then extend to the multi-region scope honestly: 'I haven't operated this at multi-region scale, but I'd think about it as...'",
      "referenced_cv_chunk_ids": ["c2"]
    },
    {
      "category": "system_design",
      "question": "How would you approach a system where a payment-related event must be processed exactly once, even under retries and failures?",
      "why_likely": "Finary handles money — exactly-once / idempotency is core to their problem space.",
      "suggested_angle": "You haven't shipped a payments system. Walk through the idempotency-key + transactional-outbox pattern at a conceptual level; be explicit that you're reasoning from principles rather than from shipped experience.",
      "referenced_cv_chunk_ids": []
    },
    {
      "category": "behavioral",
      "question": "Tell us about a time you took on a stack you didn't know well. What did the first three months look like?",
      "why_likely": "Finary will want to see how you'd ramp on Go given the gap; this is the standard probe.",
      "suggested_angle": "Use the LottoLens or IFA-platform work as your strongest ramp story. Be specific: pair-programmed first weeks, owned a small slice in month 1, mentor-checked decisions in month 2.",
      "referenced_cv_chunk_ids": ["c3"]
    },
    {
      "category": "behavioral",
      "question": "Describe a moment you made a deliberate decision to under-engineer something. What was the cost and what was the upside?",
      "why_likely": "Backend / distributed-systems hires get this because the temptation to over-engineer is huge.",
      "suggested_angle": "Lean on a Katana feature-lead moment: a place you chose 'good enough now' over a fully-distributed solution. Honest is better than impressive here.",
      "referenced_cv_chunk_ids": ["c1"]
    },
    {
      "category": "role_specific",
      "question": "What's your honest assessment of the gap between your current stack and ours, and what does a realistic ramp look like?",
      "why_likely": "Finary is explicit that the candidate will need to ramp on Go and K8s; they're checking the candidate's self-awareness.",
      "suggested_angle": "Don't oversell. Name the gaps (Go, K8s ops) explicitly. Name the transferables (PostgreSQL depth, auth-systems thinking). Propose a concrete ramp shape (pairing weeks, small-service ownership, deferred oncall).",
      "referenced_cv_chunk_ids": []
    },
    {
      "category": "culture_fit",
      "question": "Why backend, and why now? Your CV looks frontend-dense.",
      "why_likely": "Finary will want to understand whether this is genuine direction or a CV gap that'll re-surface in six months.",
      "suggested_angle": "Be specific about what's pulling you toward backend. If there's a real story (e.g. the LottoLens data work felt more interesting than React), tell that story. Generic 'I want to grow' won't land.",
      "referenced_cv_chunk_ids": ["c3"]
    }
  ],
  "questions_to_ask_them": [
    "What does the onboarding ramp look like for an engineer joining without Go production experience — is there a defined pairing structure or is it sink-or-swim?",
    "How is oncall structured today, and would I be expected to join the rotation immediately or after a ramp window?",
    "Which parts of the Finary backend are most stable vs most under active reshaping right now?",
    "If you were grading my candidacy honestly, what's the single biggest concern, and how have past hires with similar gaps actually performed once they ramped?"
  ]
}
</output>
</example>
"""
