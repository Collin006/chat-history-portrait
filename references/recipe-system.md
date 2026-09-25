# Recipe system

A recipe is a declarative analysis plan. It tells the analysis layer which neutral questions to investigate, the minimum coverage required to call a pattern, and which Insight types to render. It is not an unrestricted prompt or a license to infer a trait.

Built-in recipes may analyze only conversational, working, learning, creative, and explicitly stated life-pattern material. User-authored recipes may request a new framing or renderer, but never diagnosis, protected-trait inference, raw excerpts in public output, automatic publication, or a claim when the evidence minimum is absent.

`recipes/CATALOG.md` is the user-facing choice set. The six JSON declarations in `recipes/` are the first fully specified, default-recommended recipes. When a user selects a catalog item without a JSON declaration, create an in-memory temporary recipe with the same required fields and evidence thresholds; save it as a reusable declaration only when the user asks to keep or share that recipe.

## Execution

1. Ensure the corpus audit, all batch checkpoints, session memories, and theme/time map are current.
2. Read the selected recipe and translate each dimension into a neutral evidence query.
3. Apply the evidence-engine protocol for each dimension and emit Insights.
4. Produce the private result from those Insights.
5. Render a public form only after calibration and the existing publication gate.

If the data cannot answer a recipe question, return an open question, request user context, or state that evidence is insufficient.
