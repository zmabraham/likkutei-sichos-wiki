import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

const config: QuartzConfig = {
  configuration: {
    pageTitle: "ליקוטי שיחות — אוצר השיחות",
    pageTitleSuffix: " | ליקוטי שיחות",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "he-IL",
    baseUrl: "zmabraham.github.io/likkutei-sichos-wiki",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Frank Ruhl Libre",
        body: "Heebo",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#fdf6e3",
          lightgray: "#e8dcc8",
          gray: "#b5a48a",
          darkgray: "#4a3728",
          dark: "#2c1810",
          secondary: "#8b4513",
          tertiary: "#cd853f",
          highlight: "rgba(139, 69, 19, 0.15)",
          textHighlight: "#ffd70088",
        },
        darkMode: {
          light: "#1a0f08",
          lightgray: "#2d1f14",
          gray: "#6b5444",
          darkgray: "#c8b99a",
          dark: "#f0e6d3",
          secondary: "#cd853f",
          tertiary: "#daa520",
          highlight: "rgba(205, 133, 63, 0.15)",
          textHighlight: "#b5860088",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({ priority: ["frontmatter", "filesystem"] }),
      Plugin.SyntaxHighlighting({ theme: { light: "vitesse-light", dark: "vitesse-dark" }, keepBackground: false }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({ enableSiteMap: true, enableRSS: true }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
