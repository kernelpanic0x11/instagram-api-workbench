---
publishDate: 2026-08-17T00:00:00Z
title: 'Build a Website with an AI Coding Assistant and Astro'
excerpt: AstroWind ships an AGENTS.md and skills that teach any AI coding assistant the template. Which requests work well and how to keep the results reviewable.
image: https://images.unsplash.com/photo-1527430253228-e93688616381?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80
imageAlt: A blue plastic toy robot
category: Tutorials
tags:
  - ai
  - astro
  - tailwind css
---

Most of the work on a marketing site is not hard, it is long: a new page that looks like the others, a section moved from one page to another, a blog post with the right front matter, a deployment setting nobody remembers. AI coding assistants are good at exactly this kind of work, provided they know the conventions of the project. AstroWind gives them those conventions in two places, so that the same assistant that can [create the project](/get-started-website-with-astro-tailwind-css) can also [rebrand it](/how-to-customize-astrowind-to-your-brand) or [explain how it works](/astrowind-template-in-depth) without guessing.

## What AstroWind ships for AI coding assistants

**`AGENTS.md`** at the root describes the stack, the directory layout, the commands to run and the rules the code follows. Most coding agents pick up an `AGENTS.md` on their own; check your tool's documentation (a `CLAUDE.md` in this repository simply points to it).

**`.agents/skills/`** contains one Markdown file per recurring task, written as a recipe: which files to touch, in which order, what to verify. A few examples:

| Skill                       | What it does                                                |
| --------------------------- | ----------------------------------------------------------- |
| `add-page.md`               | A new page composed of widgets, with metadata.              |
| `add-blog-post.md`          | A post with the right front matter and image handling.      |
| `styling.md`                | Colors, fonts and Tailwind tokens.                          |
| `configure-contact-form.md` | Connecting the contact form to a backend or a form service. |
| `deploy-cloudflare.md`      | Deploying to Cloudflare Pages.                              |

…and a dozen more, from the widget catalog to structured data and base-path deployments. `AGENTS.md` tells the assistant to look for a matching skill before doing anything project-specific, so you do not need to mention them. You can also read them yourself: they are short and make a decent manual.

## Prompts that work well with AI coding assistants

The following are the kind of instruction an assistant such as [Claude Code](https://claude.com/claude-code), [Cursor](https://cursor.com/) or [GitHub Copilot](https://github.com/features/copilot) can carry out end to end, with `npm run check` and a build to confirm:

- "Add a `/careers` page with a hero, a list of open positions as feature cards and a call to action, using the same header as the rest of the site."
- "Turn the pricing section of the sales landing page into a comparison table with three plans."
- "Write a blog post from these notes, with a cover image from `src/assets/images/`, the category `Product` and the tags `release`, `changelog`."
- "Change the brand colors to `#0f766e` and `#f59e0b`, in light and dark mode, and show me the pages where the contrast may be a problem."
- "Disable the blog and remove it from the menus and the footer."
- "Deploy this site under `/handbook` on GitHub Pages."
- "Add FAQ structured data to the pricing page."
- "Replace the testimonials on the home page with a logo strip and a single quote."

Each of these maps to one or two skills plus the widget catalog, which is why the result tends to match the rest of the site rather than introducing a new style.

## Habits that keep AI-generated code reviewable

**Point at a demo page.** "Like the product landing page but for a service" gives the assistant a concrete structure to copy, which is how the template is meant to be used anyway.

**Ask for the check.** `npm run check` runs `astro check`, ESLint and Prettier; `npm run build` catches broken imports and invalid front matter. Ask the assistant to run both before it reports back, and to show you the output when something fails.

**Review the diff, not the summary.** Assistants summarize generously. The diff is short for most of these tasks and is the thing to read. Look for hardcoded colors (they should be tokens), links to `#`, and demo content that was left in place.

**Keep content decisions yours.** The assistant is good at structure and mechanics; the headline, the offer and the proof are your job. Real testimonials, real numbers, real screenshots.

**One task per conversation.** A page, then a post, then a deployment. Long conversations drift; short ones finish.

## Adding your own AGENTS.md rules

The files are plain Markdown and belong to your repository, so adapt them:

- Add a skill for anything your team does repeatedly: how to add a case study, how to publish a release note, how to update the pricing table. Follow the shape of the existing files: steps, files involved, verification.
- Add your own rules to `AGENTS.md`: naming, the tone of voice, which pages are off limits, the branch and review process.
- When you change something structural (a new content collection, a different deployment target), update the affected skill in the same pull request. An outdated recipe is worse than none.

## Doing it without an AI assistant

Nothing here is required. The skills are also the shortest documentation of the template: reading the widget catalog and the landing page recipe takes ten minutes and covers most of what the [getting started guide](/get-started-website-with-astro-tailwind-css) and the [customization guide](/how-to-customize-astrowind-to-your-brand) explain at length.
