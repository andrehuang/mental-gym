# Mental Gym

A pattern for deliberate practice with LLMs: you produce, the AI challenges.

This is an idea file, designed to be copy-pasted to your own LLM agent (e.g. Claude Code, OpenAI Codex, OpenCode, or similar). Its goal is to communicate the pattern at a high level. Your agent will build out the specifics in collaboration with you.

### The core idea

The default LLM interaction looks like this: AI produces, you review. You ask a question, the LLM gives you an answer, you nod. You read the summary, you feel informed. You see the explanation, you feel you understand. You paste your draft, you get a polished version back, you feel like a writer. Each of these interactions is pleasant. Each one produces some output you can point at. And — this is the uncomfortable part — almost none of them builds expertise.

The problem is that **recognition is not understanding**. When the LLM explains a concept and you nod along, your brain is doing pattern matching against a passive input, not constructing the concept from scratch. This produces a feeling of mastery that disappears the moment you try to explain the same concept to someone else with no references in front of you. The gap between "I recognized that" and "I can produce that from memory under pressure" is enormous, and it's the gap where expertise actually lives.

The pattern here inverts the relationship. Instead of AI producing and you reviewing: **you produce, and the AI challenges.** You explain a concept from memory with no references. You predict what a study found before you read the results. You defend a claim while the AI attacks it. You write a paragraph cold. The AI's job is to design the challenge, evaluate what you actually produced (honestly, not gently), and remember what you demonstrated versus what you only recognized.

This is not a study tool. It's a coaching relationship. The AI is a sparring partner who's patient, available at any hour, doesn't care if you look foolish, and never gets bored of running you through the same drill until it sticks. You are the athlete. The AI is the gym.

The insight underneath is old. Expertise comes from effortful retrieval, not passive exposure. Anders Ericsson's research on deliberate practice — the thing the "10,000 hours" meme is based on — is really about *structured effortful practice*, not time served. Reading explanations doesn't build expertise. Watching someone else lift doesn't build muscle. LLMs don't change that. What they change is access: a structured sparring partner used to require a coach, a cohort, or a lot of self-discipline. Now it requires almost nothing. The scarce resource has become abundant, but only if you use it for the role it's actually good at.

### What the challenges look like

Deliberately: this is not a fixed taxonomy. It's a collection of examples. Your domain and your agent will suggest better ones over time.

Useful kinds of challenge include:

*   Ones where you **explain** something from memory with no references, and the AI scores you on accuracy, completeness, and depth.
*   Ones where you **predict** an outcome before seeing it — a study result, an experimental finding, what happens in a proof — because the prediction error is where learning actually happens.
*   Ones where you **defend or attack** a position while the AI plays the opposite side, forcing you to articulate arguments under pressure.
*   Ones where you **connect** two concepts that aren't obviously related, because relational knowledge is what distinguishes expertise from recall.
*   Ones where you **teach** a student who has a specific misconception (the AI plays the student), because clearly correcting a specific wrong belief is a harder skill than explaining a concept into the void.
*   Ones where you **generate** something from scratch — a paragraph for a paper, a research question, a methodology — without any scaffolding.

These are examples of one underlying move: **force the learner to produce knowledge, then evaluate the production against what they were supposed to know.** Your agent can invent new challenge types for your particular domain. A musician might transcribe from memory. A lawyer might construct an argument under adversarial pressure. A programmer might explain a codebase without opening the files. A chef might describe a flavor profile before tasting. The pattern is the inversion, not the specific drills.

Do not lock in a canonical set. Start with two or three that fit your domain and add more when you notice a skill the existing ones don't stress.

### Architecture

Three layers, all abstract:

**The topic layer.** A list of the concepts or skills the learner is trying to internalize. Each with some loose estimate of current mastery — "not tested," "struggled," "confident." This does not need to be a database. It can be a markdown file or a small YAML. The topic layer is small enough to inspect by eye and edit by hand when needed.

**The memory layer.** For each topic, a structured record of what the learner demonstrated and what they missed across past challenges. This is the most important data structure in the whole pattern. Not "score 4/5" but something like: *"demonstrated the definition and the canonical example; missed the relationship to the parent concept; confused this with the adjacent idea."* That level of granularity is what lets the next challenge attack a real gap instead of re-asking the same question at random. Scores decay into noise. Structured mastery notes compound.

**The source layer.** The learner's own notes, papers, wiki pages, lecture notes, codebase — whatever they're actually trying to internalize. Challenges are grounded in *this*, not in the LLM's general knowledge. The LLM reads your sources and quizzes you on *your* framing. This is what makes the gym personal. Generic quizzes test generic knowledge; this tests the specific understanding you actually need to own.

There's a fourth layer that shows up in more ambitious implementations — a scheduler that decides which topic to challenge next based on spaced repetition, mastery estimates, or the learner's explicit focus. This is useful but optional. A perfectly good version picks topics at random and still works.

### Operations

Two core operations define a session:

**Challenge.** The system picks a topic (using whatever policy you prefer — spaced repetition, weakest first, explicit focus, or random), generates a challenge grounded in the source layer, presents it, waits for the learner's production, evaluates the production, and updates the memory layer with structured notes. One challenge is a meaningful unit on its own; a session is just several challenges in a row.

**Review.** Periodically, the system surfaces what's been drifting, what's overdue, what's weakest, what you've gotten consistently wrong. Optionally, the learner can point the system at their own draft or paper and ask to be challenged on the specific claims in it — this is one of the highest-value operations, because it catches the "wrote a sentence I can't actually defend" problem before it reaches a reviewer.

That's it. Everything else — session structure, warmup/cooldown, difficulty progression, mastery dashboards, streak tracking, gamification — is optional complexity. Many useful versions of this will have none of it. Start with challenge and review. Add more only when you notice something the two don't cover.

### Why this works

Three reasons, in order of importance.

**Recognition doesn't compound; retrieval does.** You can recognize a million facts and understand none of them. Every effortful retrieval, however, strengthens the representation a little, and every correction adds a structured piece of information that the next challenge can attack. The compound effect is real and it's the difference between "I've been studying this field for years" and "I actually know this field."

**Personalized grounding beats generic content.** If you're a researcher, the concepts you need to own fluently are the concepts *your* papers use — not a textbook's. A challenge grounded in your own wiki forces you to internalize your own framing, which is what you'll eventually have to defend in talks, reviews, and conversations. Generic quizzes are good for initial exposure. Personalized challenges are good for the last mile.

**Structured memory beats scores.** If the system only records "you got 4/5," the next challenge has nothing to work with. If it records "you demonstrated X and Y, you missed Z, you confused W with V," the next challenge is targeted at real gaps. This is what makes the system feel like a coach instead of a quiz app.

### Minimal implementation

The smallest version of this is remarkably small. A list of topics in a text file. A script that picks one and asks the LLM to generate a challenge grounded in a source file the learner points at. The learner responds. The LLM scores the response with structured notes about what was demonstrated and missed. Append the notes to a log. That's a working Mental Gym in a few dozen lines of code.

Spaced repetition, vector search over the source layer, difficulty progression, mastery visualization, session structure — all of that is optional complexity to add when you find yourself wanting it. A reference implementation in Python (with optional SQLite storage, vector search, and a CLI) exists at [github.com/andrehuang/mental-gym](https://github.com/andrehuang/mental-gym) if you want something more concrete to read. But the pattern does not require any of that. Start with the minimum and let the need grow the system.

### Note

This document is intentionally abstract. The exact challenge types, the format of the memory layer, the scheduler, the tooling around evaluation — all of it will depend on your field, your learning style, your taste, and your agent. Start with the two moves that are load-bearing: **the inversion** (you produce, the AI challenges) and **the grounding** (challenges come from your own materials). Everything else is optional. Your agent can help you build a version that fits. The document's only job is to communicate the pattern.
