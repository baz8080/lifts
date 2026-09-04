# 03. Three sites, one design layer
*~5 min read · PRs #3 to #17 · 19 to 26 August 2026*

*Where we are:* the site from chapter 02 exists and is ugly in the specific way a site is when
its CSS was pasted from a sibling. This is the short chapter, on purpose: the other two series
tell this story at length from their side, and repeating it here would be the third telling of
the same week.

## The question that opened this stretch

Three status sites, built by one person, deliberately look-alike. Every UI fix had been made
three times by hand. The question is the boring one every shared-code decision starts from: is
this worth extracting, and if so, how, given one hard constraint that neither sibling has.

## What changed

### The constraint comes first

The collector on this project runs on a Raspberry Pi, installed by copying files. Not `pip
install`, not a wheel, not a virtualenv: `scripts/install-native.sh` copies the `lift_status`
package and the `scripts` directory to `/opt/lift-status` and installs two systemd units. That
works because `pyproject.toml` declares **no runtime dependencies at all**, and a clone of the
repository runs on the standard library alone.

> **Concept: an empty dependency list as a deployment contract.** Most projects treat
> "dependencies" as a list of things to install. Here it is a promise about how the thing is
> deployed. As long as the list is empty, the collector installs on a Pi by copying a
> directory, upgrades by pulling and re-running one script, and cannot be broken by a package
> that stops building on ARM or on the older Python that Raspberry Pi OS ships. The moment one
> entry appears the whole install story changes. So the shared design layer had to arrive
> somewhere the Pi never looks: `statusui` is declared in an optional `site` dependency group,
> `dependencies` stays literally empty, and the file-copy install is untouched.

### Vendored, then pinned, one day apart

The first move (PR #4, 19 August) was to vendor: copy statusui's tokens, base CSS, components
and browser helpers into the repository, inline them at build, and guard against drift with a
test that byte-compares the copy to a local checkout of the upstream.

One day was enough to show what that costs. A shared fix meant a sync, a test run, a commit and
a pull request in each of three repositories, and the sites drifted anyway: this site and the
power site were on one statusui commit while the water site sat five UI commits behind, with
nothing failing to say so, because a byte-compare only fires against the checkout you happen to
have.

So on the 20th (PR #9) statusui became a real package: a git dependency with a
`[tool.uv.sources]` entry, pinned to a commit in `uv.lock`, in the `site` group. The vendored
tree and the sync script went. One guard stayed, rewritten to read the installed package rather
than a vendored copy: a test that the shared JavaScript does not redeclare a global the site
also defines.

Changing shared UI now means editing upstream, pushing, and running `rollout.sh`, which bumps
the pin in all three repositories, runs each site's tests and opens three pull requests. The
first rollout deleted a status dot.

### The alignment pass

On 26 August (PR #14) the three sites were reviewed side by side, a winner picked per element,
and the same language applied here. The banner takes the shared shape. The heading becomes "The
national picture in August 2026". The legend moves above the list, and its swatches stop being
inline styles and start using the same CSS rules that colour the bars, so the key cannot drift
from what it keys. Search becomes the shared component. The freshness chip, which shows an age
rather than a timestamp, replaces two separate "as of" lines.

Two things were kept rather than aligned, and both for the same reason: station names and the
words "out of service" are longer than a county name, so this site keeps its wider name and
stats columns. The knobs exist for exactly that.

One element went the other way and is the more interesting half. Every drill-down on all three
sites offers a link to the static page it has a permanent address at, and the *wording* is
deliberately per site. On the water and power sites the view shows one month and the page shows
every month, so the label promises what is on the other side: "Every month for County X on one
page". Here the station view already shows every month, so naming the content would promise
something the reader is already looking at. The label names the address instead: "Permanent
link to Athy station". A link's label makes a promise, and the promise has to match the
relationship, not the house style.

### The cadence, and a threshold sized to it

Two smaller things from the same week that matter to the numbers rather than the look.

The Pi pushes its logs twice daily and the site rebuilds after each push, so the stale banner
had to be resized (PR #12). It trips at **16 hours**: above the widest legitimate gap between
pushes, which is about 14 hours, and below a missed midnight push, which would show as 17 or
more. A threshold has to be sized to the cadence it is watching, or it either cries wolf or
never fires.

The cadence changed under it a week later, when GitHub's scheduled builds turned out to be
running four to ten hours late every day. Pushes went six-hourly, the build moved to firing on
the data landing rather than on a clock, and the threshold followed to 10 hours. Chapter 10.

And the Python floor was written down and then checked (PR #13). `requires-python` says 3.11,
because that is what Raspberry Pi OS bookworm ships and the collector has to run there. The
development interpreter is 3.14. A floor that is only declared is a floor that drifts, so the
install script gates on the same number, ruff takes its target from it, and CI runs the suite
on 3.11 as well as 3.14.

## Where it left the site

Three sites that read as one product, a design layer with one home, and a collector whose
install story is exactly as simple as it was on day one. Nothing in this chapter changed a
number.

The next chapter changes every number on the page.

## Notes

- PRs #3 to #17. The load-bearing ones: #4 (take the design layer from statusui), #9 (install
  it as a pinned git dependency instead of vendoring), #12 (twice-daily pushes and the 16-hour
  threshold), #13 (require 3.11 and check the floor in CI), #14 (the shared design language),
  #15 and #16 (the permalink line and the test that the shared rule applies).
- `notes/site.md` §§ The design layer is shared (19 Aug 2026), The vendored copy became a
  pinned dependency (20 Aug 2026), The design alignment pass (26 Aug 2026), The permalink
  affordance moved out of the footer (26 Aug 2026).
- `CLAUDE.md` §§ Working in this repository, The UI is shared: the stdlib-only rule and the
  `rollout.sh` workflow.
- `STALE_AFTER` in `lift_site/render.py`: 16 hours.
- The same week from the other two sides: uisce series ch 14, esb series ch 6a.
