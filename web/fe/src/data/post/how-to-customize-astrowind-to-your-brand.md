---
publishDate: 2026-08-10T00:00:00Z
title: 'Customize Your Astro Template: Colors, Fonts, Logo'
excerpt: Customize the AstroWind Astro template to your brand. Light and dark colors, fonts, logo, favicons, header and footer, and tokens for your own components.
image: https://images.unsplash.com/photo-1709803056954-aff96d0faf1c?auto=format&fit=crop&w=2070&q=80
imageAlt: Steps painted in different colors against a blue sky
category: Documentation
tags:
  - astro
  - tailwind css
  - theme
---

Customizing the AstroWind template to your brand is a handful of files, and none of them is inside a component you would rather not touch. The demo is blue, uses Inter and says "AstroWind" everywhere; this guide goes through what to change, in the order most projects need it. If you have not created the project yet, start with the [getting started guide](/get-started-website-with-astro-tailwind-css).

**What you'll change**

- The color palette, for light and dark mode, in one file.
- The fonts, self-hosted through Astro's Fonts API.
- The logo, the favicons and the default social share image.
- The header menu, the header button and the footer.
- The tokens your own components and any shadcn/ui blocks will use.

## Change the theme colors (light and dark)

`src/components/CustomStyles.astro` declares the palette as CSS variables, once for light mode under `:root` and once for dark mode under `.dark`:

```css
:root {
  --aw-color-primary: rgb(1 97 239);
  --aw-color-secondary: rgb(1 84 207);
  --aw-color-accent: rgb(109 40 217);

  --aw-color-text-heading: rgb(0 0 0);
  --aw-color-text-default: rgb(16 16 16);
  --aw-color-text-muted: rgb(16 16 16 / 66%);
  --aw-color-bg-page: rgb(255 255 255);
}

.dark {
  --aw-color-primary: rgb(1 97 239);
  /* … */
  --aw-color-bg-page: rgb(8 9 10);
}
```

### Brand colors

`primary` is the brand color: buttons, links, icons, the active menu item. `secondary` is used for taglines and secondary emphasis; `accent` for the occasional highlight. Pick a dark-mode primary that stays readable on your dark background: the demo keeps the same blue and falls back to a lighter Tailwind blue in the few places where small text needs more contrast.

### Text and surfaces

The three text colors and the page background are what every widget reads for headings, body copy, muted captions and surfaces. Keep the contrast between `text-default` and `bg-page` above 4.5:1 in both modes; the muted color is derived from the default one with an alpha channel, so it follows automatically.

### What follows the palette, and what does not

Change the values and the site follows, because components use Tailwind utilities such as `text-primary`, `text-heading`, `text-muted` and `bg-page` that map to these variables in `src/assets/styles/tailwind.css`. One exception: a few components use a fixed `dark:text-blue-*` class for small text in dark mode. After a big palette change, `grep blue-` in `src/components` and adjust the handful of hits.

The header has its own link color if you want one: set `--aw-color-link` and the active menu item uses it instead of `primary`.

## Change the font

Fonts are loaded with Astro's Fonts API, declared in `astro.config.ts`:

```ts
fonts: [
  {
    provider: fontProviders.fontsource(),
    name: 'Inter',
    cssVariable: '--font-inter',
    weights: ['100 900'],
    styles: ['normal'],
    subsets: ['latin'],
    fallbacks: ['sans-serif'],
  },
],
```

Add another entry for a second face (a serif for headings, say), then point the `--aw-font-sans`, `--aw-font-serif` and `--aw-font-heading` variables in `CustomStyles.astro` at the new `cssVariable`. Astro downloads the files at build time, self-hosts them and generates the `@font-face` rules with metric-adjusted fallbacks, so there is no request to a third party at runtime and no layout shift when the font arrives. The `Font` component in `src/layouts/Layout.astro` injects them; see [Astro's fonts documentation](https://docs.astro.build/en/guides/fonts/) for the providers available.

## Replace the logo and site name

The name comes from `site.name` in `src/config.yaml`; `src/components/Logo.astro` renders it with a rocket emoji. Replace the component's content with your mark:

```astro
---
import { Image } from 'astro:assets';
import logo from '~/assets/images/logo.svg';
---

<Image src={logo} alt="Acme" width={120} height={32} class="self-center ml-2 rtl:ml-0 rtl:mr-2" />
```

Keep the alignment classes so the logo sits correctly inside the header. If your logo needs a light and a dark version, render both and toggle them with `dark:hidden` and `hidden dark:block`.

## Generate favicons and the social share image

The favicons live in `src/assets/favicons/`: `favicon.ico`, `favicon.svg` and `apple-touch-icon.png`. Replace the files keeping the names. The default Open Graph image used when a page does not set its own is `src/assets/images/default.png` (1200 × 628); replace it too, or point `metadata.openGraph.images` in `config.yaml` at a different file. The `set-open-graph-image` skill in `.agents/skills/` has the details.

## Header and footer

`src/navigation.ts` exports `headerData` (menu entries, with optional dropdown `links`, and the `actions` buttons) and `footerData` (column links, secondary links, social links and the footer note). Internal links go through `getPermalink()` so they respect `base` if you deploy under a sub-path.

The header itself is `src/components/widgets/Header.astro`. Its props cover the common needs without editing it: `isSticky`, `isDark`, `isFullWidth`, `showToggleTheme`, `showRssFeed`, `position` (`left`, `center`, `right`). Pages can pass their own header, as several demo pages do, through the `header` slot of `PageLayout`.

## Tokens for your own components

Two sets of tokens are available in any component or page:

- **AstroWind utilities**, such as `text-primary`, `text-heading`, `text-muted`, `bg-page`, the `btn-*` button classes and `font-heading`, declared in `tailwind.css`.
- **shadcn/ui-compatible tokens**, such as `bg-background`, `text-foreground`, `bg-card` and `border-border`, derived from the same variables in `src/assets/styles/shadcn.css`. Components copied from [shadcn/ui](https://ui.shadcn.com/) or from the community blocks built on it render with your colors without editing their classes. Note that `primary`, `secondary`, `accent` and `muted` keep their AstroWind meaning; the `use-shadcn-tokens` skill explains the mapping.

Utilities of your own belong in `tailwind.css` as `@utility` blocks, next to the existing ones; the [Tailwind CSS theme documentation](https://tailwindcss.com/docs/theme) covers the `@theme` syntax the file uses.

## Dark mode behavior

`ui.theme` in `config.yaml` decides the default: `system` follows the operating system and shows the toggle; `light` or `dark` set a default but keep the toggle; `light:only` and `dark:only` remove the toggle. The choice is stored in `localStorage` and applied before the first paint, so there is no flash.

## Before you ship

Run `npm run check`, then look at every page in light and dark mode, on a phone and on a desktop. Colors that work on the home page can fail on a [landing page](/landing) with a colored band or in a dark code block. Step-by-step versions of most of the tasks above live in `.agents/skills/`, written so that an AI coding assistant can carry them out and short enough to follow yourself; if you want to know why the files are wired the way they are, read [how the template works under the hood](/astrowind-template-in-depth).
