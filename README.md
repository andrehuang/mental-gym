# Mental Gym

**Grind your way to domain expertise.**

Mental Gym is a CLI tool that builds genuine expertise through AI-driven deliberate practice. It inverts the default AI workflow: instead of the AI producing and you reviewing, *you* produce and the AI challenges.

The AI is your personal trainer. It designs exercises, spots your form, increases the load, and tracks your progress. You do the lifting.

## Why This Exists

Most AI-assisted learning looks like this: AI generates a summary, you read it, you feel like you learned something. You didn't. You consumed information. Consumption is not learning.

The cognitive science is clear: **expertise is built through effortful retrieval, not passive exposure.** Every time you struggle to recall something, explain it from scratch, or defend a position under pressure, you're building the chunked mental representations that separate experts from people who've read a lot.

Mental Gym makes every hour of study maximally effortful in the right ways.

## How It Works

### Six Exercise Types

Each exercise targets a specific cognitive process that builds expertise.

**1. Explain It Cold**
The system picks a concept. You explain it from scratch — no references, no peeking. The AI evaluates accuracy, completeness, and depth. It tells you exactly what you got wrong or missed.

```
Q: Explain why Schelling's segregation model is significant beyond its 
   specific finding about residential patterns. What broader methodological 
   principle does it demonstrate?

Your answer: [you write from memory]

Score: Accuracy 4/5 | Completeness 3/5 | Depth 4/5
Feedback: Strong on the minimal models principle, but you missed the 
connection to emergence — the model demonstrates that macro patterns 
need not reflect micro preferences...
```

**2. Predict Before You Read**
The system describes a study's setup — research question, method, participants. You predict the findings before seeing them. The prediction error is where learning happens.

```
Q: Researchers tested whether LLM agents exhibit loss aversion in 
   mixed gambles (50/50 chance of gaining $X or losing $Y). They 
   varied the gain/loss ratio from 1.5x to 3x across 100 trials 
   per condition. What do you predict they found?
```

**3. Connect the Dots**
Two concepts that aren't obviously related. You must articulate the connection — is it a tension? A shared mechanism? Does one inform the other? Superficial answers ("both are about simulation") get low scores.

```
Q: What is the relationship between performative prediction and 
   the validation problem in social simulation? Are they the same 
   problem? Different? Does one make the other harder?
```

**4. Defend or Attack**
A debatable claim from the field. You must steelman it or tear it apart. The AI plays devil's advocate — whichever side you don't take.

```
Q: ATTACK the following claim: "LLM-based social simulation is 
   fundamentally limited because LLM agents cannot have genuine 
   stakes in outcomes."
```

**5. Teach the Confused Student**
The AI plays a smart but confused colleague with a specific misconception. You must identify exactly what's wrong and correct it clearly enough that they'd actually understand. Surface-level corrections score poorly.

```
Student: "So if I understand correctly, when we say a simulation 
has 'emergent' behavior, that means the agents are learning or 
adapting, right? The emergence comes from the agents getting 
smarter over time?"

You must identify and correct the misconception...
```

**6. Write It From Scratch**
Write a paragraph or section cold — a related work discussion, a methodology sketch, an introduction paragraph. The AI evaluates substance (correctness, completeness, understanding), not prose style.

```
Q: Write a 200-word methodology paragraph explaining how you would 
   validate an LLM-based social simulation against empirical data. 
   Cover at least two validation levels.
```

### Adaptive Curriculum

Mental Gym maintains a **topic graph** — a network of concepts in your domain with mastery levels. The system:

- **Starts with your materials.** Point it at a folder of notes, papers, or wiki pages. It generates 30-50 core topics with connections.
- **Adapts to you.** Topics you've mastered get tested less frequently but never disappear. Topics you struggle with come back sooner. Standard SM-2 spaced repetition, adapted for conceptual knowledge.
- **Increases difficulty.** Six levels from basic recall to expert-level evaluation. The system advances automatically based on your performance.
- **Connects, doesn't isolate.** Every session ends with a "Connect the Dots" exercise that forces you to relate today's work to the broader field.

### Structured Mastery Memory

Mastery isn't just a number. After each exercise, the system records *what specifically* you demonstrated, missed, or got wrong:

```
[demonstrated] basic mechanism of emergence in ABMs
[demonstrated] Schelling model as canonical example
[missed] distinction between weak and strong emergence
[misconception] conflated emergence with data leakage
```

This means the next exercise on the same topic targets your actual gaps, not a random re-ask.

### Knowledge Base Integration with Vector Search

If you point Mental Gym at a folder of markdown files (notes, wiki pages, paper summaries):

- It chunks and embeds all content locally using [fastembed](https://github.com/qdrant/fastembed)
- Stores vectors in SQLite via [sqlite-vec](https://github.com/asg017/sqlite-vec)
- When generating exercises, retrieves the most relevant passages from *your* notes

This means exercises reference your specific framing, the papers you cited, the connections you drew — not just the AI's general knowledge.

### Article Review Mode

Submit your own writing and get challenged on your claims:

```bash
mental-gym review paper_draft.md
```

The system extracts your key claims and arguments, then generates targeted challenges: "You argue X — defend it against this objection...", "Your reasoning assumes Z — is that justified?", "You didn't address Y, which contradicts your claim."

### Session Structure

A typical 25-minute session:

1. **Warm-up** (5 min): 2 quick recall exercises on topics due for spaced review
2. **Main workout** (15 min): 2-3 exercises on weak or focused topics, mixing exercise types at appropriate difficulty
3. **Cool-down** (5 min): 1 "Connect the Dots" exercise linking today's work to the broader domain

## Quick Start

### Install

```bash
# Clone
git clone https://github.com/andrehuang/mental-gym.git
cd mental-gym

# Create environment and install
uv venv && uv pip install -e .

# For knowledge base vector search (recommended):
uv pip install -e ".[search]"

# For Anthropic API backend:
uv pip install -e ".[api]"

# Or everything:
uv pip install -e ".[all]"
```

### Initialize

```bash
# Basic — AI generates topics from its knowledge of your domain
mental-gym init --domain "machine learning"

# With a knowledge base — much better exercises
mental-gym init --domain "machine learning" --knowledge-base ./my-notes/

# Choose your LLM backend
mental-gym init --domain "ecology" --backend anthropic-api  # requires ANTHROPIC_API_KEY
mental-gym init --domain "ecology" --backend claude-cli     # uses Claude Code OAuth (default)
mental-gym init --domain "ecology" --backend codex-cli      # uses Codex CLI
```

### Train

```bash
# Run a session
mental-gym train

# Focus on a specific topic
mental-gym train --focus "validation"

# Quick spaced-repetition warm-up
mental-gym warmup

# Challenge yourself on your own writing
mental-gym review path/to/draft.md

# Check your progress
mental-gym status
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `mental-gym init --domain "X"` | Set up a new domain with topic graph |
| `mental-gym train [--focus T]` | Run a training session |
| `mental-gym warmup` | Quick spaced-repetition review (~10 min) |
| `mental-gym review <file>` | Challenge yourself on your own writing |
| `mental-gym status` | View mastery dashboard |
| `mental-gym sync` | Sync topic graph with knowledge base changes |
| `mental-gym add-topic "name"` | Add a new topic to your graph |
| `mental-gym suggest` | Get a context-aware training suggestion |
| `mental-gym help` | Show detailed help |

## Configuration

Mental Gym stores its config in `mental_gym.yaml` (created by `init`):

```yaml
# Your study domain
domain: "machine learning"

# Path to knowledge base directory (markdown files)
knowledge_base: ./my-notes

# LLM backend
llm:
  # Options: claude-cli (default), anthropic-api, codex-cli
  backend: claude-cli
  # Model hint (used by API backend)
  model: claude-sonnet-4-6

# Target session duration in minutes
session_duration: 25

# Database path
db_path: data/mental_gym.db
```

### LLM Backends

| Backend | Auth | Best for |
|---------|------|----------|
| `claude-cli` | Claude Code OAuth (Max subscription) | Daily use — no API credits needed |
| `anthropic-api` | `ANTHROPIC_API_KEY` env var | Programmatic use, CI, sharing |
| `codex-cli` | Codex CLI auth | Codex users |

## Knowledge Base

Point Mental Gym at any directory of markdown files. It works especially well with:

- Research wikis (Obsidian vaults, markdown note systems)
- Paper summaries and reading notes
- Course notes
- Personal knowledge bases

The system scans `.md` files, extracts titles and descriptions from YAML frontmatter or headings, and uses them to generate the initial topic graph. With the `search` extra installed, it also builds a vector index for semantic retrieval during exercise generation.

### Keeping the KB in Sync

Your knowledge base is alive — you keep adding notes, updating pages, reorganizing. Mental Gym tracks this:

```bash
# Check for changes and update topics
mental-gym sync

# Auto-check happens at the start of every training session
```

## Architecture

```
mental-gym/
  src/mental_gym/
    cli.py                  # Entry point, argparse subcommands
    config.py               # YAML config loading
    ui.py                   # Terminal I/O, colors, multi-line input, $EDITOR support
    
    engine/
      llm.py                # LLMBackend protocol + 3 implementations
      trainer.py            # Session orchestration loop
      assessor.py           # LLM-based response evaluation
      curriculum.py         # Adaptive topic selection + session planning
      memory.py             # SM-2 spaced repetition
      kb_sync.py            # Knowledge base change detection
      kb_index.py           # Vector indexing + semantic retrieval
      reviewer.py           # Article claim extraction
    
    exercises/
      base.py               # ExerciseType protocol
      explain.py            # Type 1: Explain It Cold
      predict.py            # Type 2: Predict Before You Read
      connect.py            # Type 3: Connect the Dots
      defend.py             # Type 4: Defend or Attack
      teach.py              # Type 5: Teach the Confused Student
      write.py              # Type 6: Write It From Scratch
    
    db/
      schema.py             # SQLite schema
      store.py              # Data access layer
    
    prompts/
      generation.py         # Topic graph + KB scanning prompts
      evaluation.py         # Exercise type registry
```

**Tech stack:** Python, SQLite, Anthropic API (or Claude CLI). Optional: sqlite-vec + fastembed for vector search.

**All data is local.** The SQLite database stores your topic graph, session history, exercise records, mastery notes, and vector index. Only LLM API calls go to the network.

## Design Principles

1. **You do the work.** The AI never produces content you should be producing. It designs exercises, evaluates responses, and gives feedback.

2. **Friction is the feature.** If an exercise feels easy, the difficulty increases. Comfort means no learning.

3. **Specificity over generality.** "Explain social simulation" is a bad exercise. "Explain why Barrie & Tornberg's data leakage critique is or isn't a fatal problem for the field" is a good one.

4. **Honest assessment.** The AI is not encouraging when the answer is wrong. It is precise: "This is incorrect because..." Scores reflect actual quality.

5. **Connect, don't isolate.** Every exercise forces relating the current topic to other things you know. Isolated facts don't build expertise; networks do.

6. **Domain-agnostic engine, domain-specific content.** The exercise types, curriculum, and progression logic work for any domain. Only the topic graph and knowledge base are domain-specific.

## Claude Code Integration

If you use [Claude Code](https://claude.ai/claude-code), Mental Gym can auto-suggest training when you edit knowledge base files. Add a PostToolUse hook to your `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/mental-gym/hooks/mental_gym_hook.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

When you edit a markdown file in your knowledge base, you'll see:

```
━━ Mental Gym ━━
You just updated Performative Prediction in the wiki. 
Your mastery of Performativity and Reflexivity is 12%. 
Test your understanding?
Try: mental-gym train --focus "performativity"
```

## License

MIT
