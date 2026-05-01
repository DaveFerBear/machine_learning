# Mini Jazz Encyclopedia — agent practice

## What you're building

An agent that answers questions about a tiny knowledge base of four articles.
The agent should answer by reading the corpus _selectively_ — calling tools to
look things up — not by having the whole corpus jammed into the prompt.

## The corpus

> **Marcus Vega** (b. 1932, New Orleans) — Trumpeter. Played with the Eloise
> Park Quartet from 1955 to 1959. Composed "Bourbon Street Blues" in 1962.
> Mentored a young Tomás Reed in the late 1960s. Died 1991.

> **Eloise Park** (b. 1928) — Pianist and composer. Led the Eloise Park
> Quartet from 1953 to 1965. Her playing career ended after a hand injury at
> a Newport show in 1965; she went on to teach. Considered Marcus Vega's
> closest collaborator.

> **Tomás Reed** (b. 1948) — Saxophonist. Studied under Marcus Vega for two
> years starting 1967. Founded Reed Sessions, a Chicago club, in 1978.
> Recorded "Letters Home" (1981), his best-known album.

> **Nadia Wells** (b. 1955) — Vocalist. A regular performer at Reed Sessions
> throughout the 1980s. Recorded a vocal arrangement of "Bourbon Street Blues"
> on her 1989 album _Quietly_.

## What success looks like

Build an agent that answers each of these well. The "how" is up to you — the
point is to feel the API in your hands.

1. _"Tell me about Marcus Vega."_ — straightforward single-article question.
2. _"What's the connection between Eloise Park and Tomás Reed?"_ — they don't
   share an article. The agent has to bridge them via Marcus Vega.
3. _"Who has performed Marcus Vega's compositions?"_ — forces a search and
   then reads of multiple articles. **Ideal place for parallel tool calls.**
4. _"What happened in jazz in 1965?"_ — Park's injury. Tests whether your
   tool surface lets the agent search by something other than name.
5. _"Tell me about Charlie Parker."_ — not in the corpus. Agent should
   gracefully admit it doesn't know rather than make something up.

## Build it from scratch

Start with an empty `agent.py`. **Don't copy from the refund agent solution.**
The goal is to internalize the API, not pattern-match.

A path through it (loose suggestion — diverge if you want):

1. **Pick a single tool.** Decide what it does (search? read by title? both
   at once?) and write its JSON Schema by hand. Make one API call, parse the
   `tool_use` block, run the function locally, send the `tool_result` back,
   print the final text. No loop yet. Use prompt #1 as your test.
2. **Add the second tool. Write the loop.** Now it has to keep going until
   `stop_reason == "end_turn"`. Use prompt #2 — it should make at least three
   tool calls. Watch what your loop does.
3. **Push it on prompt #3.** Does the agent call your tools in parallel? If
   not, can you change your tool _descriptions_ (not the loop) to nudge it?
4. **Edge cases.** Prompt #5 is the hardest one. The agent has to decide it
   can't answer rather than hallucinating. Do you need a system prompt?

## Things worth deliberately poking at

You'll learn more by breaking these on purpose than by getting them right
first try:

- **Run prompt #3 twice.** Are the tool calls identical? Are they parallel?
  (Try `temperature=0` and see if that changes anything.)
- **Try terse vs. rich tool descriptions.** Does the model behave differently
  on prompt #4 if your `search` description says "search the corpus" vs.
  "search articles by name, year, song, or place"?
- **Forget `is_error: true`.** When a tool fails, return a plain string
  `"Error: not found"` and _don't_ set `is_error`. Compare to setting it.
- **Try `disable_parallel_tool_use=True`** in the `tools` config (it's a
  per-tool-config flag) and watch latency / behavior change on prompt #3.
- **Print the messages list at the end** of a multi-step run. Look at how
  it grows. This is the thing you'll be reasoning about for the rest of
  your career with this API — get an intuition for it now.

## Eyeball the results, don't write tests

For each prompt ask yourself:

- Did it call the right tools?
- Did it parallelize when it could have?
- Is the final answer grounded in the corpus, or fabricating?
- On prompt #5, did it actually say "I don't know" rather than guessing?

If you get stuck on the API shape itself, the docs you were sent are the
right reference: https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
