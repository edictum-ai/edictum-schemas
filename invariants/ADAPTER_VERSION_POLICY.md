# L1.0 Adapter version policy

Claim: for every documented adapter we can state, and CI checks, which framework versions carry the native enforcement seam Edictum uses.

Cadence: weekly. Owner: python / ts / go (language of the adapter).

When latest breaks: flip the smoke-matrix row for that published version (mark unsupported, drop it, or raise floor). A red CI job is not the record.

How to measure: download the published tarball/wheel/module zip; open the typing or source; cite file:line. Mark UNVERIFIED only if the artifact could not be opened. None of the rows below are UNVERIFIED.

| id | owner | package | seam | first | floor | latest | evidence |
|---|---|---|---|---|---|---|---|
| langchain-py | python | langchain | HumanInTheLoopMiddleware (interrupt_on) | 1.0.0 | 1.0.0 | 1.3.15 | pypi langchain-1.0.0-py3-none-any.whl :: langchain/agents/middleware/human_in_the_loop.py:159 class HumanInTheLoopMiddleware(AgentMiddleware); also exported from langchain/agents/middleware/__init__.py:14. Predecessor langchain-0.3.30-py3-none-any.whl has no HumanInTheLoopMiddleware. |
| crewai | python | crewai | register_before_tool_call_hook / before_tool_call returning False | 1.5.0 | 1.5.0 | 1.15.16 | pypi crewai-1.5.0-py3-none-any.whl :: crewai/hooks/tool_hooks.py:119 def register_before_tool_call_hook; docstring lines 131-132 Return False to block tool execution. Predecessor crewai-1.4.1-py3-none-any.whl has no register_before_tool_call_hook. PyPI versions jump 1.4.1 -> 1.5.0. |
| agno | python | agno | tool_hooks (wrap-around middleware on Agent/Function) | 1.4.2 | 1.4.2 | 2.9.0 | pypi agno-1.4.2-py3-none-any.whl :: agno/agent/agent.py:148 tool_hooks: Optional[List[Callable]] = None (A function that acts as middleware and is called around tool calls.). Predecessor agno-1.4.1-py3-none-any.whl has no tool_hooks. |
| semantic-kernel | python | semantic-kernel | FilterTypes.AUTO_FUNCTION_INVOCATION | 1.0.0 | 1.0.0 | 1.44.1 | pypi semantic_kernel-1.0.0-py3-none-any.whl :: semantic_kernel/filters/filter_types.py:14 AUTO_FUNCTION_INVOCATION = auto_function_invocation. Also kernel_filters_extension.py ALLOWED_FILTERS_LITERAL includes FilterTypes.AUTO_FUNCTION_INVOCATION. |
| openai-agents-py | python | openai-agents | FunctionTool.needs_approval / function_tool(needs_approval=...) | 0.8.0 | 0.8.0 | 0.21.0 | pypi openai_agents-0.8.0-py3-none-any.whl :: agents/tool.py:252-254 needs_approval: bool / Callable[..., Awaitable[bool]] = False. Comment at tool.py:243 says guardrail fields were kept before needs_approval to preserve v0.7.0 positional constructor compatibility. Predecessor openai_agents-0.7.0-py3-none-any.whl: zero needs_approval hits. PyPI has no 0.7.1. |
| claude-agent-sdk-py | python | claude-agent-sdk | PreToolUseHookSpecificOutput.permissionDecision + ClaudeAgentOptions.can_use_tool | 0.1.2 | 0.1.2 | 0.2.139 | Combined seam first at 0.1.2: pypi claude_agent_sdk-0.1.2-py3-none-any.whl :: claude_agent_sdk/types.py:165 permissionDecision: NotRequired[Literal[allow, deny, ask]]. Predecessor 0.1.1 wheel has no permissionDecision. can_use_tool is older: first published wheel claude_agent_sdk-0.0.23-py3-none-any.whl (PyPI first release) already has types.py:329 can_use_tool: CanUseTool / None = None. |
| google-adk | python | google-adk | LlmAgent.before_tool_callback (returning a response skips the tool); BasePlugin.before_tool_callback from 1.7.0 | 0.0.2 | 0.0.2 | 2.7.0 | Callback seam: pypi google_adk-0.0.2-py3-none-any.whl :: google/adk/agents/llm_agent.py:202 before_tool_callback: Optional[BeforeToolCallback] = None; google/adk/flows/llm_flows/functions.py:153-157 skips the tool when the callback returns a response. Predecessor google_adk-0.0.1-py3-none-any.whl has no before_tool_callback. Plugin seam: pypi google_adk-1.7.0-py3-none-any.whl :: google/adk/plugins/base_plugin.py:42 class BasePlugin; :268 async def before_tool_callback. Predecessor 1.6.1 has no class BasePlugin. |
| claude-sdk-ts | ts | @anthropic-ai/claude-agent-sdk | PreToolUse hookSpecificOutput.permissionDecision + Options.canUseTool | 0.0.4 | 0.3.233 | 0.3.233 | opened 0.0.4 and 0.3.233 tarballs |
| langchain-ts | ts | langchain | humanInTheLoopMiddleware | 1.0.1 | 1.0.1 | 1.5.9 | langchain 1.0.1 :: package/dist/agents/middleware/hitl.d.ts:304 config type; index.d.ts:13 export; 1.0.0 404 |
| openai-agents-ts | ts | @openai/agents | needsApproval | 0.0.1 | 0.0.1 | 0.16.0 | @openai/agents 0.0.1 :: @openai/agents-core package/dist/tool.d.ts:47 needsApproval; also tool.js:98 runImplementation.js:294 |
| vercel-ai | ts | ai | tool-level needsApproval (6+); call-level toolApproval -> ToolApprovalStatus (7+) | 6.0.0 | 6.0.0 | 7.0.66 | ai-5.0.0.tgz: no needsApproval. ai-6.0.0.tgz dist/index.js:2516 isApprovalNeeded. ai-7.0.0.tgz src/generate-text/tool-approval-configuration.ts:25 ToolApprovalStatus. |
| adkgo | go | google.golang.org/adk | BeforeToolCallbacks | v0.1.0 | v0.1.0 | v1.6.0 | google.golang.org/adk v0.1.0 :: agent/llmagent/llmagent.go:44 BeforeToolCallbacks; first module version on proxy |
| anthropic-go | go | github.com/anthropics/anthropic-sdk-go | SessionToolRunner.routeToolEvent | v1.57.0 | v1.57.0 | v1.63.1 | github.com/anthropics/anthropic-sdk-go v1.57.0 :: betasessiontoolrunner.go:1260 routeToolEvent; :1267 EvaluatedPermission. v1.56.0 has runner but no router. Type first at v1.44.0. |
| eino | go | github.com/cloudwego/eino | ToolMiddleware | v0.5.14 | v0.5.14 | v0.9.14 | github.com/cloudwego/eino v0.5.14 :: compose/tool_node.go:115 type ToolMiddleware struct. v0.5.13 zip has no such type. |
| genkit | go | github.com/firebase/genkit/go | Middleware.WrapTool | v1.7.0 | v1.7.0 | v1.11.0 | github.com/firebase/genkit/go v1.7.0 :: ai/middleware.go:45 WrapTool func(... next ToolNext). v1.6.1 zip has no WrapTool func. |
| langchaingo | go | github.com/tmc/langchaingo | none block-capable; closest is callbacks.Handler.HandleToolStart (observational) | None | None | v0.1.14 | Opened v0.1.0 and v0.1.14 zips. v0.1.0 callbacks/callbacks.go:20 HandleToolStart has no return, cannot deny. v0.1.14 has no NeedsApproval/BeforeTool/ToolMiddleware. Not UNVERIFIED: artifacts opened; native block seam absent. |

## Notes

- Vercel peer range >=6 <8. Smoke matrix: 6.0.0 / 6.0.256 / 7.0.0 / 7.0.66.
- Claude TS floor 0.3.233 is the verified native contract, not first symbol appearance (0.0.4).
- Google ADK plugin path needs 1.7.0+; callback path from 0.0.2.
- LangChainGo: no block-capable native seam in published zips through v0.1.14.
- OpenAI Agents TS seam lives in @openai/agents-core, not the meta-package tarball.
