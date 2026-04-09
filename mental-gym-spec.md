# Mental Gym: Grind Your Way to Domain Expertise

**Spec for Claude Code implementation**

---

## What This Is

A CLI tool (or local web app) that helps a person build genuine domain expertise through AI-driven deliberate practice. It replaces the default AI workflow (AI produces, human reviews) with the inverse (human produces, AI challenges).

The core insight from cognitive science: expertise = chunked mental representations built through effortful retrieval, not through passive exposure. This tool makes every hour of study maximally effortful in the right ways.

---

## Core Metaphor

A gym. You don't get stronger by watching someone else lift weights. The AI is a personal trainer: it designs exercises, spots your form, increases the load, and tracks your progress. You do the lifting.

---

## Architecture Overview

```
mental-gym/
  config.yaml              # User config: domain, knowledge base path, preferences
  db/
    sessions.db             # SQLite: all session history, scores, progression
  knowledge_base/           # Optional: user's domain materials (papers, notes, docs)
  exercises/                # Exercise type definitions
  engine/
    trainer.py              # Core training loop (orchestrates exercises)
    assessor.py             # Evaluates user responses via LLM
    curriculum.py           # Adaptive difficulty + topic selection
    memory.py               # Spaced repetition scheduler
  cli.py                    # Main entry point
  web/                      # Optional: local web UI (nice-to-have, not MVP)
```

**Tech stack:** Python, SQLite, Anthropic API (Claude as the backend brain). CLI-first, optional lightweight web UI later.

---

## The Six Exercise Types

Each exercise type targets a specific cognitive process that builds expertise.

### 1. Explain It Cold

**Cognitive target:** Retrieval practice, knowledge organization

**How it works:**
- System picks a concept from the domain (either from knowledge base or generated)
- User must explain it from scratch, with no references
- AI evaluates: accuracy, completeness, depth, and whether the explanation would be clear to a peer researcher
- AI gives specific feedback: "You missed X", "Your explanation of Y is imprecise — here's why", "You described the what but not the why"

**Example prompt:** "Explain the emergence vs. data leakage problem in LLM-based social simulation. Why does it matter, and what approaches exist to address it?"

**Scoring:** 1-5 on accuracy, completeness, depth. Track over time.

### 2. Predict Before You Read

**Cognitive target:** Hypothesis generation, testing mental models

**How it works:**
- System presents the setup of a paper/study/experiment (title, authors, research question, method overview)
- User must predict: What did they find? Why? What would surprise you?
- System then reveals the actual findings
- User reflects on the gap between prediction and reality

**Example prompt:** "Gao et al. (2025) tested whether LLMs can replicate human behavior distributions in the 11-20 money request game, using various advanced prompting approaches. What do you think they found? Be specific about which approaches you think worked and which didn't, and why."

**Why this works:** Forces the user to activate their mental model before receiving information. The prediction error is where learning happens (prediction error theory from neuroscience).

### 3. Connect the Dots

**Cognitive target:** Relational knowledge, seeing the field as a network

**How it works:**
- System names two concepts, papers, or ideas that are not obviously connected
- User must articulate the connection, tension, or relationship between them
- AI evaluates whether the connection is genuine, superficial, or wrong

**Example prompt:** "What is the relationship between Hardt's performative prediction framework and the validation problem in social simulation? Are they the same problem? Different problems? Does one inform the other?"

**Harder variant:** Three items. "Connect Schelling's segregation model, the MOSAIKS satellite approach, and the Oracle-vs-Simulator problem."

### 4. Defend or Attack

**Cognitive target:** Argumentation, understanding limitations, reviewer mindset

**How it works:**
- System presents a claim or position from the field
- User must either defend it (steelman) or attack it (find the weaknesses)
- AI plays the opposite role — if user defends, AI attacks; if user attacks, AI defends
- Forces engagement with both sides

**Example prompt (attack):** "Defend the following claim: 'LLM-based social simulation is fundamentally limited because LLM agents cannot have genuine stakes in outcomes.' Make the strongest possible case."

**Example prompt (defend):** "A reviewer writes: 'The Visual Census is just applying VLMs to more images — this is incremental over Gebru et al. 2017.' Write a rebuttal."

### 5. Teach the Confused Student

**Cognitive target:** The protégé effect — teaching forces deep processing

**How it works:**
- AI plays a smart but confused student/colleague who has misconceptions
- User must identify the misconception and correct it clearly
- AI's "confusion" is realistic and targets common misunderstandings in the domain

**Example:** AI says: "So from what I understand, if the Oracle and Simulator agree, that means the simulation is validated, right? Because the LLM 'knows' the right answer and the simulation converges to it?" User must explain why this reasoning is wrong.

### 6. Write It From Scratch

**Cognitive target:** Generative fluency, the ultimate test

**How it works:**
- System gives a writing prompt: a paragraph for a paper, a research question, a methodology sketch
- User writes it cold, no references
- AI evaluates against what an expert would write — not for style but for whether the substantive content is correct, complete, and shows genuine understanding
- AI highlights gaps, inaccuracies, and missing nuances

**Example prompt:** "Write a 200-word 'Related Work' paragraph positioning the Visual Census against Gebru et al. (2017), Jean et al. (2016), and MOSAIKS (Rolf et al. 2021). Explain what's different about your approach and why it matters."

---

## Adaptive Curriculum System

### Topic Graph

The system maintains a **topic graph** for the domain — a set of concepts/topics with estimated user mastery levels.

```python
# Simplified schema
topic = {
    "id": "emergence_vs_leakage",
    "name": "Emergence vs. Data Leakage Problem",
    "domain": "social_simulation",
    "connections": ["llm_behavioral_validation", "barrie_tornberg_2025", "training_data_contamination"],
    "mastery": 0.0,  # 0.0 to 1.0, updated after each exercise
    "last_tested": None,
    "times_tested": 0,
    "exercise_history": []
}
```

**How the topic graph is built:**
- **Cold start:** When user specifies a domain, AI generates an initial topic graph (30-50 core concepts) using its knowledge. If a knowledge base folder is provided, AI also scans it to extract additional topics and ground the graph in the user's specific focus.
- **Growth:** As the user engages, new topics emerge naturally. AI can propose: "You seem solid on X but we haven't covered Y, which is closely related. Want to add it?"
- **User control:** User can add topics manually ("I just read a paper about Z, add it"), mark topics as low-priority, or request focus areas.

### Difficulty Progression

- **Level 1 (Recall):** "What is X?" — basic retrieval
- **Level 2 (Comprehension):** "Explain why X matters for Y"
- **Level 3 (Application):** "Given scenario S, how would X apply?"
- **Level 4 (Analysis):** "Compare X and Y. Where do they agree and disagree?"
- **Level 5 (Synthesis):** "Design an approach to problem P, drawing on X, Y, and Z"
- **Level 6 (Evaluation):** "Here's a paper that claims C. Assess its validity."

System starts at Level 1-2 for new topics, advances based on performance.

### Spaced Repetition

Topics you've mastered get tested less frequently but never disappear. Topics you struggle with come back sooner. Standard SM-2 algorithm adapted for conceptual knowledge rather than flashcards.

### Session Design

A typical session (20-40 min) might look like:

1. **Warm-up (5 min):** 2-3 quick recall exercises on previously learned topics (spaced repetition)
2. **Main workout (15-25 min):** 2-3 exercises on current focus area, mixing exercise types, at appropriate difficulty
3. **Cool-down (5 min):** One "connect the dots" exercise linking today's work to the broader domain

---

## Knowledge Base Integration (Optional)

If the user points the tool at a folder of papers/notes/documents:

- System indexes the content (extract key concepts, claims, methods, findings)
- Uses it to generate more specific and grounded exercises
- Can reference specific papers in exercises: "In the paper you saved about AgentTorch, what was their key architectural innovation for scaling to millions of agents?"
- But the system should NOT just quiz on the knowledge base — it should also probe beyond it, introducing concepts the user hasn't encountered yet

**Important design principle:** The knowledge base is a starting point, not a ceiling. The system should gradually push the user beyond their existing materials toward the broader field. Otherwise it reinforces existing knowledge rather than building new expertise.

---

## Progress Tracking

### Per-Session Summary
After each session, display:
- Topics covered, exercise types, scores
- Mastery changes (which topics improved, which need work)
- Streak / consistency tracking

### Mastery Dashboard
- Topic graph visualization with mastery levels (color-coded)
- Weak spots highlighted
- Suggested next session focus
- Historical progression curves

### Expertise Milestones
Define concrete milestones tied to capability, not just hours:
- **Novice:** Can recall basic terminology and key papers
- **Apprentice:** Can explain core concepts and their relationships
- **Practitioner:** Can critique papers, identify gaps, propose approaches
- **Expert:** Can generate novel ideas, defend positions under pressure, teach others

The system should periodically run "milestone assessments" — harder, broader exercises that test whether the user has crossed a threshold.

---

## CLI Interface (MVP)

```bash
# Start a session
mental-gym train

# Start a session focused on a specific topic
mental-gym train --focus "validation"

# Quick 10-minute warm-up (spaced repetition only)
mental-gym warmup

# View progress dashboard
mental-gym status

# Add a new topic or paper
mental-gym add-topic "performative prediction"
mental-gym add-paper /path/to/paper.pdf

# Run a milestone assessment
mental-gym assess

# Initialize for a new domain
mental-gym init --domain "social simulation" --knowledge-base ./social_sim_kb/
```

### Session Flow (CLI)

```
$ mental-gym train

🏋️ Mental Gym — Session #14
Domain: Social Simulation
Focus: Adaptive (based on spaced repetition + weak spots)
Estimated time: 25 min

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WARM-UP (1/2) — Recall
Topic: Agent architecture patterns

Q: What are the main components of the standard LLM agent
   architecture used in systems like Generative Agents and
   AgentSociety? List them and briefly explain each.

Your answer (type, then press Enter twice to submit):
> _
```

After user submits, AI evaluates and gives feedback inline, then moves to next exercise.

---

## Key Design Principles

1. **The user does the work.** AI never produces content the user should be producing. AI designs exercises, evaluates responses, and gives feedback.

2. **Friction is the feature.** If an exercise feels easy, the difficulty should increase. Comfort = no learning.

3. **Specificity over generality.** "Explain social simulation" is a bad exercise. "Explain why Barrie & Tornberg's data leakage critique is or isn't a fatal problem for the field" is a good one.

4. **Honest assessment.** The AI should not be encouraging when the answer is wrong. It should be precise: "This is incorrect because..." or "This is partially right but misses..."

5. **Connect, don't isolate.** Every exercise should, where possible, force the user to relate the current topic to other things they know. Isolated facts don't build expertise; networks do.

6. **Domain-agnostic engine, domain-specific content.** The exercise types, curriculum system, and progression logic should work for any domain. Only the topic graph and knowledge base are domain-specific.

---

## Implementation Notes for Claude Code

- **LLM calls:** All exercise generation, evaluation, and feedback go through the Anthropic API. Use Claude Sonnet for cost efficiency on routine exercises; Claude Opus for milestone assessments and complex evaluations.
- **System prompts:** Each exercise type needs a carefully designed system prompt that instructs Claude on how to generate the exercise and evaluate the response. The evaluation prompt is the most important — it must be strict, specific, and constructive.
- **Database:** SQLite is sufficient. Store: sessions, exercises, responses, scores, topic mastery history.
- **Knowledge base indexing:** For MVP, simple approach: read text/markdown files, extract key terms and concepts using Claude. No need for vector DB initially — the topic graph + Claude's knowledge is sufficient.
- **Offline-first:** All progress data is local. Only API calls go to the network.
- **Session state:** Each session is a stateful conversation. Use a simple state machine: generate exercise → collect response → evaluate → feedback → next exercise or end.

---

## MVP Scope (Build This First)

1. `mental-gym init` — set up domain, optionally point at knowledge base folder
2. `mental-gym train` — run a session with 3-5 exercises, mixing types 1-4
3. Basic topic graph with mastery tracking in SQLite
4. Simple spaced repetition for topic selection
5. Per-session summary with scores

**Skip for MVP:** Web UI, milestone assessments, difficulty levels beyond basic/hard, knowledge base deep indexing, progress visualization.

---

## Future Extensions (Not MVP)

- **Paper reading mode:** User reads a paper, then system immediately quizzes on it — testing comprehension, asking for critiques, connecting to existing knowledge
- **Debate mode:** Extended back-and-forth argument on a controversial topic in the field
- **Seminar simulation:** AI plays multiple "researchers" with different views; user must navigate the discussion
- **Writing workshop:** User drafts paper sections; AI gives reviewer-quality feedback
- **Multi-domain transfer:** Train on two domains, then exercises that force cross-domain connections
- **Collaboration mode:** Two users can challenge each other, with AI as referee
