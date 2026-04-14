# 把探索过程交给 Dashboard：从 RSEM 到 dashboard-governance-skill

  
作者：邰晓梅
首次发布日期：2026年4月14日
  
 配套项目：[dashboard-governance-skill](https://github.com/buccaneermethodology/dashboard-governance-skill)

  

不管我们使用的是哪一种大模型，哪一种 IDE，哪一种 Agent 工具，真正决定差异的不是“试一次”的惊艳，而是能不能持续使用起来。

这里的“持续”，不是每天打开 AI 工具问几个问题，也不是把任务拆成一串 prompt。更重要的是：人在使用 AI 的过程中，是否进入了一种持续探索的状态。你知道自己正在面对未知，知道每一步行动都会暴露新的信息，也知道下一步不应该机械服从最初计划，而应该基于刚刚发生的变化继续调整。

这就是理海盗派方法学中讲的 Mindful Exploration：有意识地探索。

在 AI 时代，这不是少数专家的特殊技能，而会成为一种通识能力。因为 AI 把人的行动半径放大了，一个人可以同时接触更多资料、生成更多方案、推进更多工程尝试。能力变强以后，真正稀缺的反而是过程管理：你是否知道自己探索到了哪里，哪些判断已经变成稳定认知，哪些只是临时猜测，哪些新问题刚刚浮出水面。

  
## 探索不是计划的失败，而是面对未知的正常方式


探索是关于 Unknown 的。

当你接到一个新任务时，你并不知道一段时间之后完成它会是什么样子。你也无法提前描述每一个细节。很多关键信息只有在行动发生之后才会出现：某个假设不成立，某个实现路径太重，某个原本不起眼的边界突然变成核心问题，某个副产物反而比原目标更有价值。

因此，探索不是计划不周的补救动作，而是面对未知时最自然的工作方式。

区别在于，有的人只是被动应付未知：任务来了就拆，问题来了就救火，AI 输出了就复制，下一次再从头开始。另一些人是在主动应对未知：他们保留过程痕迹，捕捉每一步变化，把新出现的信息结构化，把下一步选择建立在上一轮结果之上。

“应付”和“应对”只差一个字，工作状态却完全不同。

海盗派探索过程管理 RSEM，Risk and Session Based Exploration Management，处理的就是这个问题：在不确定性中，如何既保持行动，又不丢失方向。


## RSEM 的关键：Risk、Session、PRE

RSEM 不是把探索变成僵硬流程。它承认未知存在，也承认探索路径不可能一开始就是最优路径。你可以从任何一个已知点出发，基于经验、直觉和启发式判断，先做一次小的尝试。

关键在于，每做一次，就会产生一小步变化。这个变化可能是进步，也可能不是；但只要它被捕捉、被反思、被表达出来，它就会成为下一步探索的材料。

这正是 海盗派学习方法 PRE（Practice - Reflect - Explication）背后的精神：

- Practice：先做，进入真实问题。
- Reflect：回看刚刚发生了什么。
- Explication：把隐性的判断、发现和边界显性化。

在高质量探索中，PRE 并不一定需要被刻意喊出来。它会自然发生在每一次有效的过程记录、每一次阶段性总结、每一次“下一步应该做什么”的判断里。

RSEM 强调 Session，是因为探索需要专注的时间片。Session 不是普通任务卡片，而是一段聚焦于一个核心问题的探索单元。它可以是一次编码实现，也可以是一次文档梳理，可以是一次概念辨析，也可以是一次和 AI 的长对话。只要它面对的是一个真实未知，并且下一步基于上一步结果调整，它就是探索。

## Dashboard 是探索过程的有形载体

高质量探索不只看最终产出。不是发现了多少 bug、写了多少 prompt、提交了多少代码，就说明过程质量高。更重要的是：类似的探索能不能被重复开展？过程能不能被回看？新的参与者能不能接上？AI 换了模型、换了 session、换了工具以后，还能不能知道项目正在发生什么？

这时 Dashboard 就变成了 RSEM 中非常关键的工具载体。

Dashboard 不是传统任务列表。传统任务列表假设目标已经清楚，只需要排期、执行、打勾。Dashboard 面对的是目标仍在浮现、理解仍在变化、下一步经常要从刚刚完成的工作中涌现出来的探索型工作。

一个好的 Dashboard 至少承担三件事：

1. 记录长期方向：哪些 Big Ideas 仍在持续展开。
2. 记录阶段行动：哪些 Sessions 已经完成、正在进行、可以作为下一步候选。
3. 记录关键选择：哪些 Decisions 会影响多个 session，不应该被埋在任务行里。

它的价值不在于“记得多”，而在于帮助人和 AI 都保持放松的专注。大脑不用记住所有上下文，可以把更多注意力留给探索本身；AI 不依赖脆弱的聊天记忆，可以通过 repo 中的 Dashboard 重新获得项目状态。

## Semx-cli：一次真实的人-AI探索过程

过去一段时间，我在 semx-cli 项目中经历了一段很典型的”人-AI协作探索“。它一开始并不是“请 AI 直接把系统做出来”。如果那样做，模型大概率会很快生成大量代码，但边界、契约和验收都会漂移。

我们选择了另一条路径。

第一步，不急着写实现，而是冻结不可返工的边界。项目先形成 Implementation Constitution：目标是什么，非目标是什么，兼容性怎么处理，CLI 如何分阶段展开，什么变化必须进入 KB，什么状态只进入 Dashboard。

第二步，把长期真理和执行状态分开。`semx-kb/` 承载稳定知识：架构、术语、phase contract、策略、ADR。`Dashboard/` 承载执行状态：Big Ideas、Sessions、Decisions、优先级、阻塞、下一步。

第三步，进入 contract-first 的节奏。P00 manifest、P01 evidence、P02 M0.5、P03 semantic flow、P04 semantic slice。。。，不是先写运行时代码再补文档，而是先把 contract、schema、example、validation surface 建起来。

第四步，用 golden fixture 校准 AI。比如：对于 M0.5 这类复杂结构化产物，我们不是让模型自由发挥，而是先人工建立高质量 golden example，再让模型生成 candidate，用 schema validation、lineage validation、semantic diff、boundary audit 和 regression gate 逐步收紧验收。

第五步，开始考虑 runner 自动化。即使要让 LLM 参与生成候选 artifact，也必须把非确定性的 prompt-runner 和确定性的 contract-test 分开：runner 可以调用模型、保存 prompt/response/candidate metadata；但能不能进入下游，要交给 deterministic acceptance gate。

第六步，才开始进入M0.5的代码实现。

这整个过程，本质上就是 RSEM：在未知中不断尝试，但每一步都留下结构化痕迹；每一次发现都可能改变下一步；每一个新风险都要被转化成 contract、test、decision 或 session。

![[截屏2026-04-14 下午2.10.05.png]]


## 从 Dashboard 到 dashboard-governance-skill

在这个过程中，我逐渐发现：Dashboard 本身也需要治理。

如果没有清晰规则，Dashboard 很容易退化成 backlog。Big Idea 会被当成大任务，Session 会被当成普通待办，Decision 会混进任务备注，`todo` 会被误解成承诺，完成一个 session 以后也不会系统性检查是否出现了新的高优先级下一步。

于是我把这套 Dashboard 操作方法包装成了一个可复用的 Codex skill：`dashboard-governance`。

它做的事情很朴素，但非常关键：

- 维护 Big Ideas、Sessions、Decisions 的边界。
- 要求 Big Ideas 和 Sessions 暴露 TSP （这是海盗派方法学中的一个小工具，代表Topic、Scope、Purpose）。
- 在任务开始时识别 active session。
- 在任务结束时更新状态、交付物和 parent Big Idea。
- 检查是否出现新的 P0/P1 emergent sessions。
- 保持 `todo` 的语义：它是可见候选，不是执行承诺。
- 明确 KB 与 Dashboard 的边界：stable truth 进 KB，execution state 进 Dashboard。

这不是为了让 AI 多写几行表格，而是为了让 AI 真正进入可持续探索的工作方式。

## 为什么这件事在 Agent 时代更重要


Ryan Carson 提到的 Ralph 讨论也指向了类似问题：当 AI agent 需要长时间推进工作时，不能只依赖一个越来越长、越来越脆弱的上下文窗口。Ralph 的公开说明中，一个核心模式是让 Claude Code 在 fresh context 中持续工作，同时通过 `prd.json`、`progress.txt`、`AGENTS.md` 等文件保留目标、进度和经验。

这和 Dashboard-governance 的方向是相通的：真正可持续的 AI 工作，不是把所有上下文塞进对话，而是把关键状态沉淀为工具和模型都能读取的外部结构。

不同的是，Dashboard 更强调探索过程本身：不是只有“任务完成百分比”，还要保留长期方向、阶段性 session、开放决策和新涌现的下一步。它把 RSEM 的精神带进了 AI coding agent 的日常工作流。

当一个 agent 完成任务后，它不应该只是说“done”。它应该能回答：

- 这个 session 是否真的达到退出标准？
- 它推进了哪个 Big Idea？
- 是否暴露了新的风险或决策？
- 有没有新的 P0/P1 session 因为这次工作而浮现？
- 哪些信息应该进入 KB，哪些只应该留在 Dashboard？

一旦这些问题成为默认动作，AI 就不只是执行器，而变成了探索过程的协作者。

## 人仍然负责方向，AI 可以负责过程连续性

Dashboard-governance-skill 并不是要把探索判断完全交给 AI。恰恰相反，它把人和 AI 的分工变得更清楚。

人仍然负责关键方向：什么边界不能返工，什么 golden oracle 是可信的，哪些风险值得优先处理，哪些 next session 真的应该被选择。

AI 更适合负责过程连续性：读取 Dashboard，更新状态，识别新 session，检查 KB/Dashboard 边界，提醒哪些决策不该继续隐含在任务里。

这也是我认为 AI 时代更需要 RSEM 的原因。AI 会让尝试变得便宜，让生成变得快速，让并行变得常态。但如果没有探索过程管理，快速生成只会带来更快的漂移。

Dashboard 的作用，是让探索变得可见、可接续、可复盘。Dashboard-governance-skill 的作用，是让这个动作可以被 AI 自动执行，成为每一次非 trivial task 之后的默认收束动作。

## 结语：不是让 AI 替你探索，而是让 AI 和你一起保持探索

探索不可能被完全计划。真正重要的，是在未知不断浮现时，仍然知道自己在哪里，知道刚刚学到了什么，知道下一步为什么值得做。

Dashboard 是这个过程的载体。RSEM 是这个过程背后的方法论。dashboard-governance-skill 是把这套方法接入 AI coding agent 工作流的一小步。

如果你正在做一个长期项目，尤其是一个目标仍在浮现、边界仍在变化、AI 深度参与的项目，不妨试着给它建立一个 Dashboard。不要把它当任务列表，而是把它当探索过程的驾驶舱。

然后，在每一次有意义的工作结束后，让 AI 问自己一个问题：

> 这一步之后，新的未知变成了什么？新的下一步又在哪里？

这就是持续探索开始变得可管理的地方。

## 相关链接

  

- dashboard-governance-skill: https://github.com/buccaneermethodology/dashboard-governance-skill

- Exploration Dashboard Synthesizer: https://github.com/buccaneermethodology/ExplorationDashboardSynthesizer

- Dashboard method article: https://mp.weixin.qq.com/s/9XrmJUYoRppsLkl4JVnkBQ

- Ryan Carson's related X post: https://x.com/ryancarson/status/2008548371712135632

- Ralph project: https://github.com/snarktank/ralph
