# Customizing

## In `config.json` (no code)

| Key | What |
| --- | --- |
| `adapter` | `sample`, `manual`, `ical` or the name of your own module |
| `weather` | `lat`/`lon` of home or school (2 decimals is enough), `enabled: false` to hide |
| `activities` | Weekly after-school activities: `title`, `weekday` (0 = Monday ... 6 = Sunday), `start`, `end`. Shown as "Fritid" on the timeline, never in the packing list |
| `remember_keywords` | Words that make a line in a teacher note a reminder |
| `screen` | When the kiosk screen is on (weekday/weekend) and off |

## In the clock settings (⚙️ on `clock.html`)

Phase names, how many minutes before school each phase starts, 1 to 3 tasks per phase, school
start per weekday (first lesson / fixed time / none), and whether the dashboard switches to the
clock automatically. Saved to `web/clock_config.json`. Defaults are in `web/clock-core.js`.

## In `web/dashboard.html`

- **Packing list items**: `PACK_DEFS` maps words in notes to an icon and a short label.
  `PACK_CLAUSE` decides which sentences are about packing.
- **Test words**: `KEY_RE`, `keyLabel()` and `STRONG_LABELS` decide what gets the purple chip.
- **Colours**: CSS variables at the top (`--accent-now`, `--accent-test`...), light and dark sets.
- **Tabs and default tab**: `defaultTab()` switches to "Imorgon" at 12:00.
- **Study sessions** are placed at 16:00; change in `getItemsForDate()`.

## Translating the interface

All visible text is Swedish and lives in `web/dashboard.html`, `web/clock.html` and the phase
defaults in `web/clock-core.js` (plus a few messages in `fetch.py`). Ask your AI assistant:

> Translate all user-visible text in web/ into English (or your language). Keep the code
> behaviour the same, also translate the keyword lists that match teacher notes.

Remember that keyword lists (`remember_keywords`, `PACK_DEFS`, `KEY_RE`, `ical.test_keywords`)
must match the language the *teachers* write in, which may differ from the interface language.

## Personal touches that stay private

The child's name in the greeting, photos, a favourite colour: fine in your local copy. If you
publish a fork, keep those out of the commits.
