# Frontend page design

Use this during discussion when a change adds a page or changes what a user sees or can do on an existing page. Internal frontend refactoring with the same rendered result and interactions follows the ordinary workflow.

## Agree on the design

1. Identify the affected page, user task and relevant states. Start with the Penpot reference in the project or handoff, or inspect the file connected to Penpot MCP to find the matching pages and boards. If disconnected, connected to the wrong file or unsure of the match, offer to use the intended file or export, reconnect, or skip the mockup. Report what is accessible without inferring that the project is missing.
2. If the corresponding project is missing, offer to create it and connect its design file, or to skip the mockup and continue with the usual discussion. If only the board is missing, offer to draft it in the existing project or skip it. Create the missing resource when the user chooses creation. If the connector cannot create a project, prompt the user to create it in Penpot and connect the file.
3. Use Penpot MCP to draft or revise the affected boards as agreed. Show the boards or their previews and discuss the layout, viewport variations, states and interactions in scope. Ask the user to confirm the shown design or request changes before deciding implementation details that depend on it. Reuse an explicit confirmation that already covers the same version and scope.
4. At the normal discussion save, record which pages and states the user confirmed, their file/page/board links or IDs, and how to recognize the approved version (for example, a Penpot version or a retained export). Record agreed exceptions and behavior the board cannot show. If the user skips, record the affected scope and use the existing written requirements and acceptance criteria. A partial design applies only to the states it covers.

## Implement and verify

Use the confirmed design as the frontend implementation target for its recorded scope. Compare the running page to that version at the agreed viewport and state. Check the specified layout, spacing, typography and component states, and exercise the agreed interactions. Keep screenshots or equivalent runtime evidence with the tested build, route/state and viewport. Record material differences against the affected criterion and fix them or return the changed requirement to discussion.

If an approved source becomes inaccessible or has changed, use its confirmed version or matching export. When neither can be identified, resolve that affected item with the discussion owner before implementing or accepting it. Earlier implementation handoffs with no approved design reference continue under their written criteria and usual visual checks.
